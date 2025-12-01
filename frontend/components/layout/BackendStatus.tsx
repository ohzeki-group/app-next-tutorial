"use client";

import { useEffect, useState } from "react";
import { fetchHealth, HealthResponse } from "@/lib/api";

type StatusState = "idle" | "ok" | "degraded" | "down";

export default function BackendStatus() {
  const [status, setStatus] = useState<StatusState>("idle");
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  useEffect(() => {
    let canceled = false;

    const check = async () => {
      try {
        const res: HealthResponse = await fetchHealth();
        if (canceled) return;

        if (res.status === "ok") setStatus("ok");
        else if (res.status === "degraded") setStatus("degraded");
        else setStatus("down");

        setLastChecked(new Date(res.timestamp).toLocaleTimeString());
      } catch {
        if (!canceled) {
          setStatus("down");
          setLastChecked(null);
        }
      }
    };

    // 初回チェック
    check();

    // 30秒ごとに再チェック
    const id = setInterval(check, 30_000);

    return () => {
      canceled = true;
      clearInterval(id);
    };
  }, []);

  let label = "Checking…";
  let className = "qa-status-dot qa-status-idle";

  if (status === "ok") {
    label = "Backend OK";
    className = "qa-status-dot qa-status-ok";
  } else if (status === "degraded") {
    label = "Backend Degraded";
    className = "qa-status-dot qa-status-degraded";
  } else if (status === "down") {
    label = "Backend Down";
    className = "qa-status-dot qa-status-down";
  }

  return (
    <div className="qa-backend-status" title={label}>
      <span className={className} />
      <span className="qa-backend-status-text">
        {label}
        {lastChecked && (
          <span className="qa-backend-status-time">
            （{lastChecked} チェック）
          </span>
        )}
      </span>
    </div>
  );
}
