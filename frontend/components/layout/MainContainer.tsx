// frontend/components/layout/MainContainer.tsx
import { ReactNode } from "react";

export default function MainContainer({ children }: { children: ReactNode }) {
  return <main className="qa-main">{children}</main>;
}
