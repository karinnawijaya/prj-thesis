"use client";

import type { ButtonHTMLAttributes } from "react";

interface PrimaryButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
}

export function PrimaryButton({ label, className = "", ...props }: PrimaryButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-full bg-indigo-600 px-8 py-3 text-base font-semibold text-white shadow-soft transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    >
      {label}
    </button>
  );
}
