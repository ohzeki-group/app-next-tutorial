// frontend/components/solver/EnergyHistogram.tsx
"use client";

import type { EnergyBin } from "@/lib/api";

type Props = {
  bins: EnergyBin[];
  title?: string;
};

export default function EnergyHistogram({ bins, title }: Props) {
  if (!bins || bins.length === 0) return null;

  const maxCount = Math.max(...bins.map((b) => b.count));

  return (
    <div className="qa-energy">
      {title && <h3>{title}</h3>}

      <table className="qa-energy-table">
        <thead>
          <tr>
            <th>Energy</th>
            <th>Count</th>
          </tr>
        </thead>
        <tbody>
          {bins.slice(0, 10).map((bin, idx) => (
            <tr key={idx}>
              <td>{bin.energy.toFixed(3)}</td>
              <td>{bin.count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="qa-energy-chart">
        {bins.slice(0, 10).map((bin, idx) => {
          const ratio = maxCount ? bin.count / maxCount : 0;
          return (
            <div className="qa-energy-bar-row" key={idx}>
              <span className="qa-energy-label">
                {bin.energy.toFixed(2)}
              </span>
              <div className="qa-energy-bar-track">
                <div
                  className="qa-energy-bar-fill"
                  style={{ width: `${ratio * 100}%` }}
                />
              </div>
              <span className="qa-energy-count">{bin.count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
