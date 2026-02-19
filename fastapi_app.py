import csv
import hashlib
import json
import logging
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from diagram_utils import (
    DiagramPayload,
    build_deterministic_diagram,
    build_fallback_diagram,
    parse_diagram_payload,
    repair_diagram_json,
)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional for local runs without OpenAI
    OpenAI = None


DATASET_VERSION = "2026-02-19_v10"
DATASET_FILE = "Painting_Metadata_260127.csv"
# Images live under the Next.js frontend assets folder.
PAINTINGS_DIR = Path("frontend/assets/paintings")
CACHE_DIR = Path("cache")
ALLOWED_SETS = {"A", "B"}

logger = logging.getLogger("artweave")
logging.basicConfig(level=logging.INFO)


@dataclass
class Painting:
    id: str
    title: str
    artist: str
    year: int
    image_filename: str
    set_name: str
    metadata: Dict[str, Any]

    def as_payload(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "year": self.year,
            "image_url": f"/static/paintings/{self.image_filename}",
        }


class CompareStartRequest(BaseModel):
    set: str = Field(..., pattern="^[AB]$")
    left_id: str
    right_id: str


class CompareStartResponse(BaseModel):
    compare_id: str


class CompareStatusResponse(BaseModel):
    status: str
    summary_markdown: Optional[str] = None
    diagram: Optional[DiagramPayload] = None


class CompareJob:
    def __init__(self, compare_id: str) -> None:
        self.compare_id = compare_id
        self.status = "processing"
        self.summary_markdown: Optional[str] = None
        self.diagram: Optional[DiagramPayload] = None

    def as_response(self) -> CompareStatusResponse:
        return CompareStatusResponse(
            status=self.status,
            summary_markdown=self.summary_markdown,
            diagram=self.diagram,
        )


app = FastAPI(title="ArtWeave API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/paintings", StaticFiles(directory=PAINTINGS_DIR), name="paintings")

CACHE_DIR.mkdir(parents=True, exist_ok=True)

_paintings_lock = threading.Lock()
_paintings_by_set: Dict[str, List[Painting]] = {"A": [], "B": []}

_jobs_lock = threading.Lock()
_jobs: Dict[str, CompareJob] = {}


def _load_paintings() -> None:
    dataset_path = Path(DATASET_FILE)
    if not dataset_path.exists():
        raise RuntimeError(f"Dataset file not found: {dataset_path}")

    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        entries: Dict[str, List[Painting]] = {"A": [], "B": []}
        for row in reader:
            normalized_row: Dict[str, Any] = {}
            normalized_lower: Dict[str, Any] = {}
            for key, value in row.items():
                cleaned_key = (key or "").strip()
                if not cleaned_key:
                    continue
                if isinstance(value, str):
                    cleaned_value = value.strip()
                    if cleaned_value == "":
                        continue
                    normalized_row[cleaned_key] = cleaned_value
                    normalized_lower[cleaned_key.lower()] = cleaned_value
                elif value is not None:
                    normalized_row[cleaned_key] = value
                    normalized_lower[cleaned_key.lower()] = value

            set_name = (normalized_lower.get("set") or "").strip()
            if set_name not in ALLOWED_SETS:
                continue
            year_value = normalized_lower.get("year") or "0"
            try:
                year = int(year_value)
            except ValueError:
                year = 0
            painting = Painting(
                id=(normalized_lower.get("id") or "").strip(),
                title=(normalized_lower.get("title") or "").strip(),
                artist=(normalized_lower.get("artist") or "").strip(),
                year=year,
                image_filename=(normalized_lower.get("image_filename") or "").strip(),
                set_name=set_name,
                metadata=normalized_row,
            )
            if painting.id:
                entries[set_name].append(painting)

    for set_name, paintings in entries.items():
        if len(paintings) != 5:
            raise RuntimeError(
                f"Set {set_name} must contain exactly 5 paintings (found {len(paintings)})"
            )

    with _paintings_lock:
        _paintings_by_set.update(entries)


def _get_painting_by_id(set_name: str, painting_id: str) -> Painting:
    with _paintings_lock:
        for painting in _paintings_by_set.get(set_name, []):
            if painting.id == painting_id:
                return painting
    raise HTTPException(status_code=404, detail="Painting not found in selected set.")


def _cache_key(set_name: str, left_id: str, right_id: str) -> str:
    ids = sorted([left_id, right_id])
    payload = f"{DATASET_VERSION}|{set_name}|{ids[0]}|{ids[1]}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    safe_ids = "__".join(ids)
    return f"{set_name}__{safe_ids}__{digest}.json"


def _read_cache(cache_path: Path) -> Optional[Dict[str, Any]]:
    if not cache_path.exists():
        return None
    with cache_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_cache(cache_path: Path, payload: Dict[str, Any]) -> None:
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="OpenAI SDK is not installed.")
    return OpenAI(api_key=api_key)


def _format_metadata(meta: Dict[str, Any]) -> str:
    ordered_keys = [
        "Artwork Location",
        "Artist Location",
        "Medium",
        "Classification",
        "Art Movement",
        "Composition",
        "Color Palette",
        "History",
        "Narrative",
        "Symbolism",
        "Patron",
        "Subject",
        "Art Education",
        "Influenced by",
        "Influenced",
        "Links",
    ]
    lines: List[str] = []
    for key in ordered_keys:
        value = meta.get(key)
        if value:
            lines.append(f"{key}: {value}")
    return "\n".join(lines) if lines else "No additional metadata."


def _generate_summary(client: OpenAI, left: Painting, right: Painting) -> str:

    prompt = (
        "ArtWeave - Concise Context + Focused Relation\n\n"
        "Purpose:\n"
        "ArtWeave analyzes and compares two artworks using the provided dataset. "
        "It identifies both broad contextual links (e.g., movement, period, or location) "
        "and specific relational ties (e.g., artist relationship, ownership, or exhibition history).\n\n"
        "Guidelines:\n"
        "- Keep the broad context brief and use the specific connection as the central insight.\n"
        "- All information must be factual and dataset-based — no assumptions or invented context.\n"
        "- If the dataset lacks a field, acknowledge the absence and use the nearest relevant one "
        "(e.g., if ownership data is missing, reference exhibition or location link).\n"
        "- Do NOT repeat placeholders like [title] or [artist]. Always fill with actual values.\n"
        "- In the Comparison Summary, refer to artworks by their titles (not 'Artwork A/B').\n\n"
        "Output Format (exact):\n"
        "**Overview**\n"
        "- Artwork A: <title>, <artist>, <year>\n"
        "- Artwork B: <title>, <artist>, <year>\n\n"
        "**Comparison Summary**\n"
        "Both artworks <broad context: movement/era/location>. "
        "<Specific connection highlighting relation or shared circumstance>."
    )
    response = client.responses.create(
        model="gpt-4o-mini",
        temperature=0.2,
        input=[
            {
                "role": "system",
                "content": (
                    "You are ArtWeave, an art historian assistant that only uses the provided "
                    "dataset fields. Do not invent facts; if a field is missing, say so explicitly. "
                    "Never output placeholder brackets like [title]."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Use only the provided fields.\n\n"
                    f"Artwork A title: {left.title}\n"
                    f"Artwork A artist: {left.artist}\n"
                    f"Artwork A year: {left.year}\n"
                    f"Artwork A metadata:\n{_format_metadata(left.metadata)}\n\n"
                    f"Artwork B title: {right.title}\n"
                    f"Artwork B artist: {right.artist}\n"
                    f"Artwork B year: {right.year}\n"
                    f"Artwork B metadata:\n{_format_metadata(right.metadata)}\n\n"
                    f"{prompt}"
                ),
            },
        ],
    )
    return response.output_text.strip()


def _generate_diagram(
    client: OpenAI, left: Painting, right: Painting, summary_text: str
) -> DiagramPayload:
    movement_a = (left.metadata.get("Art Movement") or "").strip()
    movement_b = (right.metadata.get("Art Movement") or "").strip()
    movement: Optional[str] = None
    if movement_a and movement_b and movement_a.lower() == movement_b.lower():
        movement = movement_a
    elif movement_a and movement_a.lower() in summary_text.lower():
        movement = movement_a
    elif movement_b and movement_b.lower() in summary_text.lower():
        movement = movement_b

    artwork_a = {
        "title": left.title,
        "artist": left.artist,
        "year": left.year,
        **left.metadata,
    }
    artwork_b = {
        "title": right.title,
        "artist": right.artist,
        "year": right.year,
        **right.metadata,
    }

    try:
        diagram = build_deterministic_diagram(
            summary=summary_text,
            artwork_a=artwork_a,
            artwork_b=artwork_b,
            movement=movement,
        )
        return diagram
    except (ValidationError, ValueError) as exc:
        logger.warning("Deterministic diagram failed, using fallback: %s", exc)
        artwork_a_label = f"Artwork A — {left.title}, {left.artist}, {left.year}"
        artwork_b_label = f"Artwork B — {right.title}, {right.artist}, {right.year}"
        return build_fallback_diagram(artwork_a_label, artwork_b_label)


def _run_compare_job(compare_id: str, set_name: str, left_id: str, right_id: str) -> None:
    left = _get_painting_by_id(set_name, left_id)
    right = _get_painting_by_id(set_name, right_id)

    client = _get_openai_client()

    summary = _generate_summary(client, left, right)
    logger.info("Summary generated for %s vs %s", left.id, right.id)
    with _jobs_lock:
        job = _jobs[compare_id]
        job.summary_markdown = summary
        job.status = "summary_ready"

    diagram = _generate_diagram(client, left, right, summary)
    logger.info(
        "Diagram generated for %s vs %s (nodes=%s edges=%s)",
        left.id,
        right.id,
        len(diagram.nodes),
        len(diagram.edges),
    )
    with _jobs_lock:
        job = _jobs[compare_id]
        job.diagram = diagram
        job.status = "done"

    cache_name = _cache_key(set_name, left_id, right_id)
    cache_path = CACHE_DIR / cache_name
    _write_cache(
        cache_path,
        {
            "summary_markdown": summary,
            "diagram": diagram.model_dump(),
        },
    )


@app.on_event("startup")
def startup_event() -> None:
    _load_paintings()


@app.get("/api/sets", response_model=List[str])
def list_sets() -> List[str]:
    return sorted(ALLOWED_SETS)


@app.get("/api/paintings")
def list_paintings(set: str) -> List[Dict[str, Any]]:
    if set not in ALLOWED_SETS:
        raise HTTPException(status_code=400, detail="Set must be A or B.")
    with _paintings_lock:
        return [painting.as_payload() for painting in _paintings_by_set[set]]


@app.post("/api/compare/start", response_model=CompareStartResponse)
def start_compare(
    payload: CompareStartRequest, background_tasks: BackgroundTasks
) -> CompareStartResponse:
    if payload.left_id == payload.right_id:
        raise HTTPException(status_code=400, detail="left_id and right_id must differ.")
    if payload.set not in ALLOWED_SETS:
        raise HTTPException(status_code=400, detail="Set must be A or B.")

    left = _get_painting_by_id(payload.set, payload.left_id)
    right = _get_painting_by_id(payload.set, payload.right_id)

    sorted_ids = sorted([left.id, right.id])
    cache_name = _cache_key(payload.set, sorted_ids[0], sorted_ids[1])
    cache_path = CACHE_DIR / cache_name
    cached_payload = _read_cache(cache_path)

    compare_id = str(uuid.uuid4())
    job = CompareJob(compare_id)

    if cached_payload:
        cached_diagram = cached_payload.get("diagram")
        if cached_diagram:
            try:
                job.summary_markdown = cached_payload.get("summary_markdown")
                job.diagram = DiagramPayload.model_validate(cached_diagram)
                job.status = "done"
                with _jobs_lock:
                    _jobs[compare_id] = job
                return CompareStartResponse(compare_id=compare_id)
            except (ValidationError, ValueError) as exc:
                logger.warning("Cached diagram invalid, regenerating: %s", exc)

    with _jobs_lock:
        _jobs[compare_id] = job

    background_tasks.add_task(
        _run_compare_job,
        compare_id,
        payload.set,
        sorted_ids[0],
        sorted_ids[1],
    )
    return CompareStartResponse(compare_id=compare_id)


@app.get("/api/compare/{compare_id}", response_model=CompareStatusResponse)
def get_compare_status(compare_id: str) -> CompareStatusResponse:
    with _jobs_lock:
        job = _jobs.get(compare_id)
        if not job:
            raise HTTPException(status_code=404, detail="Compare job not found.")
        return job.as_response()
