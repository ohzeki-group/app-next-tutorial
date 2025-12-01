// frontend/components/solver/KnapsackForm.tsx
"use client";

import { useState } from "react";
import {
  solveKnapsack,
  KnapsackResponse,
  SolverName,
} from "@/lib/api";
import EnergyHistogram from "./EnergyHistogram";
import ConstraintTable from "./ConstraintTable";

const defaultWeightsText = "2 3 4 5";
const defaultValuesText = "3 4 5 8";

function parseNumberList(text: string): number[] {
  if (!text.trim()) return [];
  return text
    .trim()
    .split(/\s+/)
    .map((v) => Number(v));
}

export default function KnapsackForm() {
  const [weightsText, setWeightsText] = useState(defaultWeightsText);
  const [valuesText, setValuesText] = useState(defaultValuesText);
  const [capacity, setCapacity] = useState(5);
  const [solver, setSolver] = useState<SolverName>("sa");
  const [numReads, setNumReads] = useState(100);
  const [penalty, setPenalty] = useState(5);

  const [result, setResult] = useState<KnapsackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSolve = async () => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const weights = parseNumberList(weightsText);
      const values = parseNumberList(valuesText);

      if (weights.length !== values.length) {
        throw new Error("weights と values の要素数が一致していません。");
      }

      const res = await solveKnapsack({
        weights,
        values,
        capacity,
        solver,
        num_reads: numReads,
        penalty,
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
          weights / values はスペース区切りで入力します。
          同じインデックスの要素が同じアイテムを表します。
        </p>

        <label className="qa-field">
          <span>Weights</span>
          <input
            type="text"
            value={weightsText}
            onChange={(e) => setWeightsText(e.target.value)}
            placeholder="例: 2 3 4 5"
          />
        </label>

        <label className="qa-field">
          <span>Values</span>
          <input
            type="text"
            value={valuesText}
            onChange={(e) => setValuesText(e.target.value)}
            placeholder="例: 3 4 5 8"
          />
        </label>

        <div className="qa-field-group">
          <label className="qa-field-inline">
            <span>Capacity</span>
            <input
              type="number"
              value={capacity}
              onChange={(e) => setCapacity(Number(e.target.value))}
              min={0}
            />
          </label>

          <label className="qa-field-inline">
            <span>Penalty</span>
            <input
              type="number"
              value={penalty}
              onChange={(e) => setPenalty(Number(e.target.value))}
            />
          </label>
        </div>

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
                <span className="qa-label">Total Weight</span>
                <span>{result.total_weight}</span>
              </div>
              <div>
                <span className="qa-label">Total Value</span>
                <span>{result.total_value}</span>
              </div>
            </div>

            <h3>Chosen Items</h3>
            <ul className="qa-assignment-list">
              {result.chosen_items.length === 0 && (
                <li>選択されたアイテムはありません。</li>
              )}
              {result.chosen_items.map((i) => (
                <li key={i}>
                  <span className="qa-chip">item {i}</span>
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
