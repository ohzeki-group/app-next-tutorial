// frontend/app/page.tsx
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="qa-landing">
      <h1 className="qa-title">Quantum Annealing Playground</h1>
      <p className="qa-subtitle">
        Next.js + FastAPI + OpenJij / D-Wave で量子アニーリングを体験しよう。
      </p>

      <div className="qa-card-grid">
        <Link href="/assignment" className="qa-card">
          <h2>Assignment Problem</h2>
          <p>コスト行列に基づいて、最適な割当を見つけます。</p>
        </Link>

        <Link href="/knapsack" className="qa-card">
          <h2>Knapsack Problem</h2>
          <p>制約付きの価値最大化問題。後で実装していきましょう。</p>
        </Link>
      </div>
    </div>
  );
}
