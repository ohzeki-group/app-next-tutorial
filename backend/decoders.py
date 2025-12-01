# backend/decoders.py

from typing import Any


def decode_assignment_solution(
    sample: dict[int, Any],
    costs: list[list[float]],
) -> tuple[list[tuple[int, int]], float]:
    """
    割当問題:
      sample（0/1） → (worker, job) のペアと total_cost に変換
    """
    n_workers = len(costs)
    n_jobs = len(costs[0])

    def var_index(i: int, j: int) -> int:
        return i * n_jobs + j

    assignments: list[tuple[int, int]] = []

    for i in range(n_workers):
        for j in range(n_jobs):
            u = var_index(i, j)
            if sample.get(u, 0) == 1:
                assignments.append((i, j))

    total_cost = sum(costs[i][j] for (i, j) in assignments)
    return assignments, total_cost


def decode_knapsack_solution(
    sample: dict[int, Any],
    weights: list[int],
    values: list[float],
) -> tuple[list[int], int, float]:
    """
    ナップザック:
      sample（0/1） → 選んだアイテムと重さ・価値
    """
    n_items = len(weights)
    chosen_items = [i for i in range(n_items) if sample.get(i, 0) == 1]
    total_weight = sum(weights[i] for i in chosen_items)
    total_value = sum(values[i] for i in chosen_items)
    return chosen_items, total_weight, total_value


# ========= 制約チェック用 =========


def check_assignment_constraints(
    sample: dict[int, Any],
    costs: list[list[float]],
) -> tuple[bool, list[int], list[int]]:
    """
    各 worker がちょうど 1 つの job、
    各 job がちょうど 1 人の worker に割り当てられているかチェック
    """
    n_workers = len(costs)
    n_jobs = len(costs[0])

    def var_index(i: int, j: int) -> int:
        return i * n_jobs + j

    worker_counts = [0] * n_workers
    job_counts = [0] * n_jobs

    for i in range(n_workers):
        for j in range(n_jobs):
            u = var_index(i, j)
            if sample.get(u, 0) == 1:
                worker_counts[i] += 1
                job_counts[j] += 1

    feasible = all(c == 1 for c in worker_counts) and all(c == 1 for c in job_counts)
    return feasible, worker_counts, job_counts


def check_knapsack_constraints(
    sample: dict[int, Any],
    weights: list[int],
    capacity: int,
) -> tuple[bool, int]:
    """
    sum(weights[i] * x_i) <= capacity かどうかをチェック
    """
    total_weight = sum(weights[i] for i in range(len(weights)) if sample.get(i, 0) == 1)
    feasible = total_weight <= capacity
    return feasible, total_weight
