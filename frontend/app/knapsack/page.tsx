// frontend/app/knapsack/page.tsx
import KnapsackForm from "@/components/solver/KnapsackForm";

export default function KnapsackPage() {
  return (
    <div className="qa-page">
      <section className="qa-page-header">
        <h1>Knapsack Problem</h1>
        <p>
          アイテムの重さ・価値と容量を指定して、ナップザック問題を解きます。
        </p>
      </section>

      <KnapsackForm />
    </div>
  );
}
