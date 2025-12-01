// frontend/components/solver/AssignmentForm.tsx
"use client";


import { useState } from "react";
import {
  solveAssignment,
  AssignmentResponse,
  SolverName,
} from "@/lib/api";
import EnergyHistogram from "./EnergyHistogram";
import ConstraintTable from "./ConstraintTable";

const defaultCostsText = `3 1 2
2 3 3
2 1 2`;

function parseCosts(text: string): number[][] {
  return text
    .trim()
    .split("\n")
    .map((line) =>
      line
        .trim()
        .split(/\s+/)
        .map((v) => Number(v))
    );
}

export default function AssignmentForm() {
  const [costsText, setCostsText] = useState(defaultCostsText);
  const [solver, setSolver] = useState<SolverName>("sa");
  const [numReads, setNumReads] = useState(100);
  const [penaltyRow, setPenaltyRow] = useState(5);
  const [penaltyCol, setPenaltyCol] = useState(5);

  const [result, setResult] = useState<AssignmentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSolve = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const costs = parseCosts(costsText);

      const res = await solveAssignment({
        costs,
        solver,
        num_reads: numReads,
        penalty_row: penaltyRow,
        penalty_col: penaltyCol,
      });

      setResult(res);
    } catch (e: any) {
      setError(e.message ?? "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qa-solver-grid">
      {/* 入力パネル */}
      <section className="qa-panel">
        <h2>Input</h2>
        <p className="qa-panel-desc">
          各行が worker、各列が job です（スペース区切り）。
        </p>

        <label className="qa-field">
          <span>Cost Matrix</span>
          <textarea
            value={costsText}
            onChange={(e) => setCostsText(e.target.value)}
            rows={6}
          />
        </label>

        <div className="qa-field-group">
          <label className="qa-field-inline">
            <span>Solver</span>
            <select
              value={solver}
              onChange={(e) => setSolver(e.target.value as SolverName)}
            >
              <option value="sa">SA (OpenJij)</option>
              <option value="sqa">SQA (OpenJij)</option>
              <option value="qa">QA (D-Wave)</option>
            </select>
          </label>

          <label className="qa-field-inline">
            <span>num_reads</span>
            <input
              type="number"
              value={numReads}
              onChange={(e) => setNumReads(Number(e.target.value))}
              min={1}
            />
          </label>
        </div>

        <div className="qa-field-group">
          <label className="qa-field-inline">
            <span>penalty (row)</span>
            <input
              type="number"
              value={penaltyRow}
              onChange={(e) => setPenaltyRow(Number(e.target.value))}
            />
          </label>

          <label className="qa-field-inline">
            <span>penalty (col)</span>
            <input
              type="number"
              value={penaltyCol}
              onChange={(e) => setPenaltyCol(Number(e.target.value))}
            />
          </label>
        </div>

        <button
          className="qa-button-primary"
          onClick={onSolve}
          disabled={loading}
        >
          {loading ? "Solving..." : "Solve"}
        </button>

        {error && <p className="qa-error">Error: {error}</p>}
      </section>

      {/* 結果パネル */}
      <section className="qa-panel">
        <h2>Result</h2>
        {!result && !loading && (
          <p className="qa-placeholder">
            パラメータを設定して「Solve」を押すと結果が表示されます。
          </p>
        )}
        {result && (
          <div className="qa-result">
            <div className="qa-result-summary">
              <div>
                <span className="qa-label">Solver</span>
                <span>{result.solver}</span>
              </div>
              <div>
                <span className="qa-label">Total Cost</span>
                <span>{result.total_cost}</span>
              </div>
            </div>

            <h3>Assignments (worker → job)</h3>
            <ul className="qa-assignment-list">
              {result.assignments.map(([i, j], idx) => (
                <li key={idx}>
                  <span className="qa-chip">worker {i}</span>
                  <span className="qa-arrow">→</span>
                  <span className="qa-chip qa-chip-secondary">
                    job {j}
                  </span>
                </li>
              ))}
            </ul>
            <ConstraintTable
              feasible={result.feasible ?? false}
              constraints={result.constraints ?? []}
            />
            {result.energy_histogram && result.energy_histogram.length > 0 && (
              <EnergyHistogram
                bins={result.energy_histogram}
                title="Energy distribution (top 10)"
              />
            )}
          </div>
        )}
      </section>
    </div>
  );
}
