// frontend/app/assignment/page.tsx
import AssignmentForm from "@/components/solver/AssignmentForm";

export default function AssignmentPage() {
  return (
    <div className="qa-page">
      <section className="qa-page-header">
        <h1>Assignment Problem</h1>
        <p>
          コスト行列を入力して、SA / SQA / QA を使った割当最適化を試せます。
        </p>
      </section>

      <AssignmentForm />
    </div>
  );
}
