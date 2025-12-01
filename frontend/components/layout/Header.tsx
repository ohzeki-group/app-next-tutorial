"use client";

import Link from "next/link";
import ThemeToggle from "./ThemeToggle";
import BackendStatus from "./BackendStatus";

export default function Header() {
  return (
    <header className="qa-header">
      <div className="qa-header-inner">
        <Link href="/" className="qa-logo">
          QA Playground
        </Link>
        <nav className="qa-nav">
          <Link href="/assignment">Assignment</Link>
          <Link href="/knapsack">Knapsack</Link>
          <BackendStatus />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
