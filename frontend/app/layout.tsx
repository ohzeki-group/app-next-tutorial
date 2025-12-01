// frontend/app/layout.tsx
import "./globals.css";
import type { Metadata } from "next";
import { ReactNode } from "react";
import Header from "@/components/layout/Header";
import MainContainer from "@/components/layout/MainContainer";

export const metadata: Metadata = {
  title: "Quantum Annealing Playground",
  description: "Next.js + FastAPI + Quantum Annealing Demo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <Header />
        <MainContainer>{children}</MainContainer>
      </body>
    </html>
  );
}
