import math
from collections.abc import Mapping
import jijmodeling as jm
from ommx.v1 import Instance


# QUBOの型ヒント： Mapping[tuple[int, int], float]
# 例：{ (0,0): 1, (0,1): 0.5 , (1,1): -9.2 }


def build_knapsack_qubo(
    weights: list[int],
    values: list[float],
    capacity: int,
    penalty: float = 1.0,
) -> Mapping[tuple[int, int], float]:
    """
    0-1 ナップザック問題の QUBO を構成する。

    問題設定:
        maximize  sum_i values[i] * x_i
        subject to sum_i weights[i] * x_i <= capacity
        x_i ∈ {0, 1}

    QUBO ハミルトニアン:
        H(x, y) = -sum_i values[i] * x_i
                  + penalty * ( sum_i w_i x_i + sum_k 2^k y_k - capacity )^2

    Parameters
    ----------
    weights : list[int]
        各アイテムの重さ w_i
    values : list[float]
        各アイテムの価値 v_i
    capacity : int
        ナップザック容量 C
    penalty : float, optional
        制約違反に対するペナルティ係数 A。
        大きいほど制約を満たす解が優先される。

    Returns
    -------
    Q : Qubo
        Q[(i, j)] 形式の QUBO 係数。
        i <= j のペアのみが含まれる。
    """
    if len(weights) != len(values):
        raise ValueError("weights と values の長さが一致していません。")

    n_items = len(weights)

    # slack 変数のビット数: 2^m - 1 >= capacity を満たす最小の m
    if capacity <= 0:
        raise ValueError("capacity は正の整数である必要があります。")

    m_slack = math.ceil(math.log2(capacity + 1))  # capacity を表現できるだけのビット数
    # 変数インデックス
    # x_i: 0 .. n_items-1
    # y_k: n_items .. n_items + m_slack - 1

    # (i, j) -> Q_ij
    Q: dict[tuple[int, int], float] = {}

    def add_Q(i: int, j: int, value: float):
        """Q[(i, j)] (i <= j) に value を加算するヘルパー。"""
        if i > j:
            i, j = j, i
        if (i, j) in Q:
            Q[(i, j)] += value
        else:
            Q[(i, j)] = value

    # 1. 目的関数: -sum_i v_i x_i
    #    QUBO では線形項は対角成分 Q(ii) に入る (バイナリ変数なので x_i = x_i*x_i が成立する。)
    for i, v in enumerate(values):
        add_Q(i, i, -float(v))

    # 2. 制約項: penalty * ( sum_i w_i x_i + sum_k 2^k y_k - capacity )^2
    #    a_u: 各変数 z_u の係数 (x, y をまとめて z と見る)
    #    H_c = penalty * ( sum_u a_u z_u - C )^2
    #        = penalty * [ sum_u a_u^2 z_u^2
    #                      + 2 * sum_{u < v} a_u a_v z_u z_v
    #                      - 2C sum_u a_u z_u
    #                      + C^2 ]
    #    z_u^2 = z_u なので、線形項と二次項だけを Q に入れる

    # まず、全変数の係数 a_u を配列にまとめる
    a: list[float] = [0.0] * (n_items + m_slack)

    # アイテム x_i の係数は w_i
    for i, w in enumerate(weights):
        a[i] = float(w)

    # slack y_k の係数は 2^k
    for k in range(m_slack):
        idx = n_items + k
        a[idx] = float(2**k)

    # 対角項 (線形 + 制約由来の線形・自己二乗)
    for u in range(n_items + m_slack):
        au = a[u]
        # penalty * [ a_u^2 z_u^2 - 2C a_u z_u ]
        # = penalty * [ (a_u^2 - 2C a_u) z_u ]
        coeff = penalty * (au * au - 2.0 * capacity * au)
        add_Q(u, u, coeff)

    # 非対角項 (制約の二次項)
    for u in range(n_items + m_slack):
        for v in range(u + 1, n_items + m_slack):
            coeff = 2.0 * penalty * a[u] * a[v]
            add_Q(u, v, coeff)

    # 定数項 penalty * C^2 は QUBO エネルギーの差に影響しないので、省略してよい
    return Q


###############################################################################


def build_knapsack_qubo_jijmodeling(
    weights: list[int],
    values: list[float],
    capacity: int,
    penalty: float = 1.0,
) -> Mapping[tuple[int, int], float]:
    """
    Openjijのjijmodelingを使ってQUBOを作ってみる
    """

    if len(weights) != len(values):
        raise ValueError("weights と values の長さが一致していません。")

    if capacity <= 0:
        raise ValueError("capacity は正の整数である必要があります。")

    # ================================
    # 1. JijModeling で数理モデルを定義
    # ================================
    #
    # Placeholder は「インスタンスデータが後から入る箱」。
    #   v[i] … 価値
    #   w[i] … 重さ
    #   W    … 容量
    #
    v = jm.Placeholder("v", ndim=1)  # アイテムの価値 v_i
    w = jm.Placeholder("w", ndim=1)  # アイテムの重さ w_i
    W = jm.Placeholder("W")  # ナップサック容量 C

    # アイテム数 N（= len(v)）をシンボリックに表現
    N = v.len_at(0, latex="N")

    # 決定変数 x_i ∈ {0,1}
    x = jm.BinaryVar("x", shape=(N,))

    # 添字 i：0 .. N-1
    i = jm.Element("i", belong_to=(0, N))

    # 最大化問題として Problem を定義
    problem = jm.Problem("Knapsack (JijModeling)", sense=jm.ProblemSense.MAXIMIZE)

    # 目的関数：価値の総和を最大化
    #   max sum_i v[i] * x[i]
    problem += jm.sum(i, v[i] * x[i])

    # 制約：重量の総和が容量を超えない
    #   sum_i w[i] * x[i] <= W
    constraint_expr = jm.sum(i, w[i] * x[i])
    problem += jm.Constraint("weight", constraint_expr <= W)

    # ================================
    # 2. インスタンスデータを与える
    # ================================
    #
    # Placeholder に対応する実データを dict で渡す。
    #
    instance_data = {
        "v": [float(v_i) for v_i in values],
        "w": [int(w_i) for w_i in weights],
        "W": int(capacity),
    }

    # Interpreter で「モデル × データ」から OMMX Instance を生成
    interpreter = jm.Interpreter(instance_data)
    instance: Instance = interpreter.eval_problem(problem)

    # ================================
    # 3. OMMX Instance → QUBO に変換
    # ================================
    #
    # ペナルティ法を使って、制約付き最大化問題を QUBO に変換する。
    # instance.to_qubo(uniform_penalty_weight=penalty) は
    #
    #   H(x, y, …) = -sum_i v_i x_i
    #                + penalty * (制約違反の二乗和)
    #
    # のような形の QUBO を自動的に構成してくれる。
    #
    # 戻り値:
    #   qubo   : dict[(int, int), float] 形式の QUBO 係数
    #   offset : 定数項（エネルギーに一律に足されるだけなので、
    #            最適解探索だけを考えるなら無視してよい）
    #
    qubo, offset = instance.to_qubo(uniform_penalty_weight=penalty)

    return qubo
