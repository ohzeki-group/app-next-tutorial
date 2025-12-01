// frontend/lib/api.ts

export type SolverName = "sa" | "sqa" | "qa";

export type HealthStatus = "ok" | "degraded" | "down";

export type HealthResponse = {
  status: HealthStatus;
  timestamp: string;
  version?: string | null;
  detail?: string | null;
}

export type EnergyBin = {
  energy: number;
  count: number;
}

export type ConstraintCheck = {
  name: string;
  satisfied: boolean;
  value: number;
  bound?: number | null;
  detail?: string | null;
};

export type AssignmentRequest = {
  costs: number[][];
  solver?: SolverName;
  num_reads?: number;
  penalty_row?: number;
  penalty_col?: number;
  use_greedy?: boolean;
};

export type AssignmentResponse = {
  assignments: [number, number][];
  total_cost: number;
  solver: SolverName;
  energy_histogram?: EnergyBin[];
  feasible?: boolean;
  constraints?: ConstraintCheck[];
};

// 🔽 ここからナップザック用
export type KnapsackRequest = {
  weights: number[];
  values: number[];
  capacity: number;
  solver?: SolverName;
  num_reads?: number;
  penalty?: number;
  use_greedy?: boolean;
};

export type KnapsackResponse = {
  chosen_items: number[];
  total_weight: number;
  total_value: number;
  solver: SolverName;
  energy_histogram?: EnergyBin[];
  feasible?: boolean;
  constraints?: ConstraintCheck[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function solveAssignment(
  payload: AssignmentRequest
): Promise<AssignmentResponse> {
  const res = await fetch(`${API_BASE}/solve/assignment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail ?? "API error");
  }

  return res.json();
}

// 🔽 ナップザック用の API 呼び出し
export async function solveKnapsack(
  payload: KnapsackRequest
): Promise<KnapsackResponse> {
  const res = await fetch(`${API_BASE}/solve/knapsack`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail ?? "API error");
  }

  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`, {
    method: "GET",
  });

  if (!res.ok) {
    throw new Error(`Health check failed with status ${res.status}`);
  }

  return res.json();
}