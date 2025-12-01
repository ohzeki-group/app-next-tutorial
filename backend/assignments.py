from collections.abc import Mapping
import jijmodeling as jm
from ommx.v1 import Instance

# QUBO の型： Mapping[tuple[int, int], float]
# 例：{ (0,0): 1, (0,1): 0.5 , (1,1): -9.2}


def build_assignment_qubo_jijmodeling(
    costs: list[list[float]],
    penalty_row: float = 5.0,
    penalty_col: float = 5.0,
) -> Mapping[tuple[int, int], float]:
    if not costs:
        raise ValueError("costs が空です。少なくとも 1 行は必要です。")

    len(costs)
    n_jobs = len(costs[0])

    if any(len(row) != n_jobs for row in costs):
        raise ValueError(
            "costs の各行の長さが一致していません。矩形行列である必要があります。"
        )

    # ================================
    # 1. JijModeling で数理モデルを定義
    # ================================

    # C[i, j] : 人 i が仕事 j を担当したときのコスト
    C = jm.Placeholder("C", ndim=2, description="assignment cost matrix")

    # 行数 N, 列数 M をプレースホルダの shape から取得
    N = C.len_at(0, latex="N", description="number of workers")
    M = C.len_at(1, latex="M", description="number of jobs")

    # 添字 i, j
    i = jm.Element("i", belong_to=(0, N), description="worker index")
    j = jm.Element("j", belong_to=(0, M), description="job index")

    # 決定変数 x[i, j] ∈ {0,1}
    x = jm.BinaryVar(
        "x",
        shape=(N, M),
        description="x[i, j] = 1 if worker i takes job j",
    )

    # 問題は「コストの最小化」
    problem = jm.Problem("Assignment (JijModeling)", sense=jm.ProblemSense.MINIMIZE)

    # 目的関数: Σ_{i,j} C[i,j] * x[i,j]
    problem += jm.sum([i, j], C[i, j] * x[i, j])

    # 行方向のワンホット制約: 各 worker はちょうど 1 つの job を持つ
    #
    #   ∑_j x[i,j] = 1,  ∀i
    #
    problem += jm.Constraint(
        "row_onehot",
        jm.sum(j, x[i, j]) == 1,
        forall=i,
    )

    # 列方向のワンホット制約: 各 job はちょうど 1 人に割り当てられる
    #
    #   ∑_i x[i,j] = 1,  ∀j
    #
    problem += jm.Constraint(
        "col_onehot",
        jm.sum(i, x[i, j]) == 1,
        forall=j,
    )

    # ================================
    # 2. インスタンスデータを与える
    # ================================
    instance_data = {"C": costs}
    interpreter = jm.Interpreter(instance_data)
    instance: Instance = interpreter.eval_problem(problem)

    # ================================
    # 3. penalty_weights で縦・横別ペナルティ
    # ================================
    #
    # instance.constraints は pandas.DataFrame っぽいテーブルで、
    # index が「Constraint table の id」になっている。
    # その id をキーに penalty_weights を渡すと、制約ごとに
    # ペナルティの大きさを変えられる。
    #
    penalty_weights: dict[int, float] = {}

    for c in instance.constraints:
        cid = c.id
        name = c.name

        if name == "row_onehot":
            penalty_weights[cid] = penalty_row
        elif name == "col_onehot":
            penalty_weights[cid] = penalty_col

    # ================================
    # 3. OMMX Instance → QUBO に変換
    # ================================
    #
    # penalty を一様ペナルティとして使って QUBO に変換。
    #   qubo_raw : {(u, v): coeff, ...}
    #   offset   : 定数項（最適化に関しては無視してよい）
    #
    qubo, offset = instance.to_qubo(penalty_weights=penalty_weights)

    return qubo
