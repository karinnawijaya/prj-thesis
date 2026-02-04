"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { IconButton } from "@/components/IconButton";

interface PageShellProps {
  children: ReactNode;
  showNav?: boolean;
  backHref?: string;
  homeHref?: string;
}

export function PageShell({
  children,
  showNav = true,
  backHref = "/",
  homeHref = "/",
}: PageShellProps) {
  const router = useRouter();

  return (
    <div className="relative min-h-screen">
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-10">
        {children}
      </div>
      {showNav ? (
        <div className="fixed bottom-6 right-6 flex items-center gap-3">
          <IconButton
            label="Home"
            onClick={() => router.push(homeHref)}
            icon={
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 10.5L12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M5 9.5V21h14V9.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            }
          />
          <IconButton
            label="Back"
            onClick={() => router.push(backHref)}
            icon={
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 19l-7-7 7-7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            }
          />
        </div>
      ) : null}
    </div>
  );
}