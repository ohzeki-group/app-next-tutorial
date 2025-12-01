// frontend/components/solver/ConstraintTable.tsx
"use client";

import type { ConstraintCheck } from "@/lib/api";

type Props = {
  feasible: boolean;
  constraints: ConstraintCheck[];
};

export default function ConstraintTable({ feasible, constraints }: Props) {
  if (!constraints || constraints.length === 0) return null;

  return (
    <div className="qa-constraints">
      <div className="qa-constraints-summary">
        <span className={feasible ? "qa-tag-ok" : "qa-tag-ng"}>
          {feasible ? "Feasible" : "Not feasible"}
        </span>
        <span className="qa-constraints-note">
          （最小エネルギー解の制約チェック）
        </span>
      </div>

      <table className="qa-constraints-table">
        <thead>
          <tr>
            <th>Constraint</th>
            <th>Value</th>
            <th>Bound</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {constraints.map((c) => (
            <tr key={c.name}>
              <td>
                <div>{c.name}</div>
                {c.detail && (
                  <div className="qa-constraints-detail">{c.detail}</div>
                )}
              </td>
              <td>{c.value}</td>
              <td>{c.bound ?? "-"}</td>
              <td>
                <span className={c.satisfied ? "qa-pill-ok" : "qa-pill-ng"}>
                  {c.satisfied ? "✓" : "✗"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
