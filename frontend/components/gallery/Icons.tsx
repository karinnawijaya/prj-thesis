"use client";

import { useRouter } from "next/navigation";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowLeft, faHouse } from "@fortawesome/free-solid-svg-icons";

interface IconsProps {
  nav: string;
}

export function Icons({ nav }: IconsProps) {
  const router = useRouter();

  return (
    <div className="icons-menu" aria-label="Page navigation">
      <button
        type="button"
        className="icons-btn"
        onClick={() => router.push(nav)}
        aria-label="Go back"
      >
        <FontAwesomeIcon icon={faArrowLeft} />
      </button>
      <button
        type="button"
        className="icons-btn"
        onClick={() => router.push("/")}
        aria-label="Go home"
      >
        <FontAwesomeIcon icon={faHouse} />
      </button>
    </div>
  );
}