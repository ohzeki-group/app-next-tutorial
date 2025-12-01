# backend/main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
from dimod import SampleSet
from datetime import datetime
from zoneinfo import ZoneInfo

from solver import SASolver, SQASolver, QASolver
from assignments import build_assignment_qubo_jijmodeling
from knapsack import build_knapsack_qubo_jijmodeling
from decoders import (
    decode_assignment_solution,
    decode_knapsack_solution,
    check_assignment_constraints,
    check_knapsack_constraints,
)
from typing import List
from collections import defaultdict


app = FastAPI(title="Quantum Annealing API")

# ★ フロントのオリジンを許可（ローカル）
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# 本番用のオリジンを環境変数から追加
vercel_origin = os.environ.get("FRONTEND_ORIGIN")
if vercel_origin:
    origins.append(vercel_origin)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================
# リクエスト / レスポンス型
# ======================

SolverName = Literal["sa", "sqa", "qa"]


class EnergyBin(BaseModel):
    energy: float
    count: int


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    timestamp: datetime
    version: str | None = None
    detail: str | None = None


class ConstraintCheck(BaseModel):
    name: str
    satisfied: bool
    value: float
    bound: float | None = None
    detail: str | None = None


class AssignmentRequest(BaseModel):
    costs: list[list[float]] = Field(
        ..., description="コスト行列 costs[i][j]: worker i が job j をやるコスト"
    )
    solver: SolverName = "sa"
    num_reads: int = 100
    penalty_row: float = 5.0
    penalty_col: float = 5.0
    use_greedy: bool = False  # SQA / QA 用の局所改善


class AssignmentResponse(BaseModel):
    assignments: list[tuple[int, int]]
    total_cost: float
    solver: SolverName
    energy_histogram: List[EnergyBin]
    feasible: bool
    constraints: List[ConstraintCheck]


class KnapsackRequest(BaseModel):
    weights: list[int]
    values: list[float]
    capacity: int
    solver: SolverName = "sa"
    num_reads: int = 100
    penalty: float = 5.0
    use_greedy: bool = False


class KnapsackResponse(BaseModel):
    chosen_items: list[int]
    total_weight: int
    total_value: float
    solver: SolverName
    energy_histogram: List[EnergyBin]
    feasible: bool
    constraints: List[ConstraintCheck]


# ======================
# ヘルパー: ソルバー生成
# ======================


def get_solver(name: SolverName, use_greedy: bool = False):
    if name == "sa":
        return SASolver()
    if name == "sqa":
        return SQASolver(use_greedy=use_greedy)
    if name == "qa":
        # D-Wave 用の環境変数 (DWAVE_SOLVER_NAME, DWAVE_API_TOKEN, DWAVE_API_ENDPOINT)
        # が .env.local に入っている前提
        try:
            return QASolver(use_greedy=use_greedy)
        except RuntimeError as e:
            # 環境変数がないなど
            raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=400, detail=f"Unknown solver: {name}")


# ======================
# ヘルパー: エネルギーヒストグラム作成
# ======================


def build_energy_histogram(sampleset: SampleSet) -> list[EnergyBin]:
    """
    dimod.SampleSet を想定して energy と num_occurrences から
    ヒストグラムを作る
    """
    # OpenJij / D-Wave の SampleSet は record.energy / record.num_occurrences を持つ
    energies = sampleset.record.energy
    counts = (
        sampleset.record.num_occurrences
    )  # 今のSolver設定だとcounts = 1 しかないはず。（同じレコードを分割している）
    energy_counts: dict[float, int] = defaultdict(int)

    for e, c in zip(energies, counts):
        energy_counts[float(e)] += int(c)

    sorted_items = sorted(energy_counts.items(), key=lambda x: x[0])
    bins = [EnergyBin(energy=energy, count=count) for energy, count in sorted_items]

    # エネルギー昇順にソート
    bins.sort(key=lambda b: b.energy)
    return bins


@app.get("/health", response_model=HealthResponse)
def health():
    # ここで本当は色々チェックしても良い（DB, D-Wave接続など）
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(ZoneInfo("Asia/Tokyo")),
        version="0.1.0",
        detail="backend running normally",
    )


# ======================
# エンドポイント: 割当問題
# ======================


@app.post("/solve/assignment", response_model=AssignmentResponse)
def solve_assignment(req: AssignmentRequest):
    if not req.costs or not req.costs[0]:
        raise HTTPException(status_code=400, detail="costs が空です。")

    # 1. QUBO 構築（JijModeling 版）
    Q = build_assignment_qubo_jijmodeling(
        costs=req.costs,
        penalty_row=req.penalty_row,
        penalty_col=req.penalty_col,
    )

    # 2. ソルバー選択
    solver = get_solver(req.solver, use_greedy=req.use_greedy)

    # 3. サンプリング
    sampleset = solver.solve(Q, sample_config={"num_reads": req.num_reads})

    # 4. ベストサンプルをデコード
    best_sample = sampleset.first.sample
    assignments, total_cost = decode_assignment_solution(best_sample, req.costs)

    # 5. エネルギーヒストグラム作成
    energy_histogram = build_energy_histogram(sampleset)

    feasible, worker_counts, job_counts = check_assignment_constraints(
        best_sample, req.costs
    )

    constraints: list[ConstraintCheck] = []

    # worker ごとの制約チェック
    for i, c in enumerate(worker_counts):
        constraints.append(
            ConstraintCheck(
                name=f"Worker_{i}_assignment",
                satisfied=(c == 1),
                value=c,
                bound=1,
                detail=f"Assigned to {c} jobs",
            )
        )

    # job ごとの制約チェック
    for j, c in enumerate(job_counts):
        constraints.append(
            ConstraintCheck(
                name=f"Job_{j}_assignment",
                satisfied=(c == 1),
                value=c,
                bound=1,
                detail=f"Assigned to {c} workers",
            )
        )

    return AssignmentResponse(
        assignments=assignments,
        total_cost=total_cost,
        solver=req.solver,
        energy_histogram=energy_histogram,
        feasible=feasible,
        constraints=constraints,
    )


# ======================
# エンドポイント: ナップザック
# ======================


@app.post("/solve/knapsack", response_model=KnapsackResponse)
def solve_knapsack(req: KnapsackRequest):
    if len(req.weights) != len(req.values):
        raise HTTPException(
            status_code=400, detail="weights と values の長さが一致していません。"
        )

    # 1. QUBO 構築（JijModeling 版）
    Q = build_knapsack_qubo_jijmodeling(
        weights=req.weights,
        values=req.values,
        capacity=req.capacity,
        penalty=req.penalty,
    )

    # 2. ソルバー選択
    solver = get_solver(req.solver, use_greedy=req.use_greedy)

    # 3. サンプリング
    sampleset = solver.solve(Q, sample_config={"num_reads": req.num_reads})

    # 4. ベストサンプルをデコード
    best_sample = sampleset.first.sample
    chosen_items, total_weight, total_value = decode_knapsack_solution(
        best_sample, req.weights, req.values
    )

    # 5. エネルギーヒストグラム作成
    energy_histogram = build_energy_histogram(sampleset)

    feasible, total_weight_check = check_knapsack_constraints(
        best_sample, req.weights, req.capacity
    )

    constraints: list[ConstraintCheck] = []

    constraints.append(
        ConstraintCheck(
            name="Weight_constraint",
            satisfied=feasible,
            value=total_weight_check,
            bound=req.capacity,
            detail=f"Total weight {total_weight_check} / Capacity {req.capacity}",
        )
    )

    return KnapsackResponse(
        chosen_items=chosen_items,
        total_weight=total_weight,
        total_value=total_value,
        solver=req.solver,
        energy_histogram=energy_histogram,
        feasible=feasible,
        constraints=constraints,
    )
