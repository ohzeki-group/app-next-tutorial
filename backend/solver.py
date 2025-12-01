# 環境変数の読み込み
import os
from abc import ABC, abstractmethod
from collections.abc import Hashable, Mapping

# 型関連
from typing import Any, cast

# SA / SQA
import openjij as oj
from dimod import BinaryQuadraticModel, SampleSet
from dwave.embedding import embed_bqm, unembed_sampleset
from dwave.embedding.chain_breaks import MinimizeEnergy
from dwave.samplers import SteepestDescentSampler

# QA
from dwave.system import DWaveSampler
from minorminer import find_embedding

QUBO = Mapping[tuple[Hashable, Hashable], float]
SampleConfig = Mapping[str, Any]


class SolverBase(ABC):
    """QUBO を解く汎用ソルバーの基底クラス."""

    def __init__(self):
        # デフォルトのサンプリング設定
        self.sample_config: dict[str, Any] = {"num_reads": 10}

    @abstractmethod
    def solve(self, Q: QUBO, sample_config: SampleConfig | None = None) -> SampleSet:
        """QUBO を解き、SampleSet を返す."""
        raise NotImplementedError

    def _merge_config(self, sample_config: SampleConfig | None) -> dict[str, Any]:
        if sample_config is None:
            return dict(self.sample_config)
        # ユーザー指定で上書き
        return {**self.sample_config, **sample_config}


class SASolver(SolverBase):
    """
    Simulated Annealing (SA) ソルバー.
    """

    def __init__(self):
        super().__init__()

    def solve(self, Q: QUBO, sample_config: SampleConfig | None = None) -> SampleSet:
        return self._solve_with_oj(Q, sample_config)

    def _solve_with_oj(
        self, Q: QUBO, sample_config: SampleConfig | None = None
    ) -> SampleSet:
        cfg = self._merge_config(sample_config)
        sampler = oj.SASampler()
        sampleset = sampler.sample_qubo(Q, **cfg)
        return cast(SampleSet, sampleset)


class QASolver(SolverBase):
    """
    D-Wave 実機（またはクラウド）を使った Quantum Annealing ソルバー.

    Parameters
    ----------
    use_greedy : bool, optional
        取得したサンプルを BinaryQuadraticModel 上で SteepestDescent で
        局所改善するかどうか。デフォルト False。
        これを使うと、D-Wave から返ってきた解が厳密に QUBO の最適解でなくても、
        局所的にエネルギーを下げることができる場合があります。
    """

    def __init__(self, use_greedy: bool = False):
        from dotenv import load_dotenv

        # 環境変数の読み込み (.env.local)
        load_dotenv(dotenv_path=".env.local")
        solver_name = os.getenv("DWAVE_SOLVER_NAME")
        token = os.getenv("DWAVE_API_TOKEN")
        endpoint = os.getenv("DWAVE_API_ENDPOINT")

        if not (solver_name and token and endpoint):
            raise RuntimeError(
                "D-Wave の環境変数 (DWAVE_SOLVER_NAME, DWAVE_API_TOKEN, "
                "DWAVE_API_ENDPOINT) が設定されていません。"
            )

        self.sampler = DWaveSampler(solver=solver_name, token=token, endpoint=endpoint)
        self.use_greedy = use_greedy
        super().__init__()

    def solve(self, Q: QUBO, sample_config: SampleConfig | None = None) -> SampleSet:
        return self._solve_with_advantage(Q, sample_config)

    def _solve_with_advantage(
        self, Q: QUBO, sample_config: SampleConfig | None = None
    ) -> SampleSet:
        cfg = self._merge_config(sample_config)

        # QUBO -> BQM
        bqm = self._convert_bqm_from_qubo(Q)

        # 論理グラフをハードウェアグラフへ埋め込み
        embedding = self._find_embedding(bqm)
        embedded_bqm = self._embed_bqm(bqm, embedding)

        # サンプリング
        response = self.sampler.sample(embedded_bqm, **cfg)

        # 埋め込みの解除
        sampleset = unembed_sampleset(
            response,
            embedding,
            bqm,
            chain_break_method=MinimizeEnergy(bqm, embedding),
            chain_break_fraction=True,
        )
        if not isinstance(sampleset, SampleSet):
            raise ValueError("Unembedding failed, resulting object is not a SampleSet.")

        # Greedy で解を改善する (Optional)
        if self.use_greedy:
            sampleset = SteepestDescentSampler().sample(bqm, initial_states=sampleset)

        return sampleset

    def _find_embedding(self, bqm: BinaryQuadraticModel, timeoutsec: int = 1000):
        logical_edges = list(bqm.quadratic.keys())
        hardware_edges = self.sampler.edgelist

        emb = find_embedding(
            logical_edges,
            hardware_edges,
            timeout=timeoutsec,
            verbose=0,  # 1 にすると埋め込み過程のログを出力
        )

        # 埋め込み失敗のチェック
        if not emb:
            raise ValueError("No embedding found.")

        # 型キャスト
        emb = cast(Mapping[int, list[int]], emb)

        # 全ての論理変数をカバーしているかチェック
        logical_vars = set(bqm.variables)
        if set(emb.keys()) != logical_vars:
            raise ValueError("Embedding does not cover all logical variables.")

        return emb

    def _convert_bqm_from_qubo(self, Q: QUBO) -> BinaryQuadraticModel:
        return BinaryQuadraticModel.from_qubo(Q)

    def _embed_bqm(
        self,
        bqm: BinaryQuadraticModel,
        embedding: Mapping[int, list[int]],
        chain_strength: float | None = None,
    ) -> BinaryQuadraticModel:
        embedded_bqm = embed_bqm(
            bqm,
            embedding,
            self.sampler.adjacency,
            chain_strength,
        )
        if not isinstance(embedded_bqm, BinaryQuadraticModel):
            raise ValueError(
                "Embedding failed, resulting object is not a BinaryQuadraticModel."
            )
        return embedded_bqm


class SQASolver(SolverBase):
    """
    Simulated Quantum Annealing (SQA) solver using OpenJij.
    SQAは量子アニーリングを古典コンピューター上で模擬する手法です。

    Parameters
    ----------
    use_greedy : bool, optional
        取得したサンプルを BinaryQuadraticModel 上で SteepestDescent で
        局所改善するかどうか。デフォルト False。
    """

    def __init__(self, use_greedy: bool = False):
        self.use_greedy = use_greedy
        super().__init__()

    def solve(self, Q: QUBO, sample_config: SampleConfig | None = None) -> SampleSet:
        sampler = oj.SQASampler()
        cfg = self._merge_config(sample_config)
        sampleset = sampler.sample_qubo(Q, **cfg)
        sampleset = cast(SampleSet, sampleset)

        # Greedy で解を改善する (Optional)
        if self.use_greedy:
            bqm = BinaryQuadraticModel.from_qubo(Q)
            sampleset = SteepestDescentSampler().sample(bqm, initial_states=sampleset)

        return sampleset
