"use client";

import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  text: string;
  classname?: string;
}

export function Button({ text, classname = "", ...props }: ButtonProps) {
  return (
    <button type="button" className={classname} {...props}>
      {text}
    </button>
  );
}