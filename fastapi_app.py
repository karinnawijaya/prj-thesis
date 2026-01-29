import csv
import hashlib
import json
import os
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional for local runs without OpenAI
    OpenAI = None


DATASET_VERSION = "2026-01-26_v1"
DATASET_FILE = "Painting_Metadata_260127.csv"
PAINTINGS_DIR = Path("assets/paintings")
CACHE_DIR = Path("cache")
ALLOWED_SETS = {"A", "B"}


@dataclass
class Painting:
    id: str
    title: str
    artist: str
    year: int
    image_filename: str
    set_name: str

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
    diagram: Optional[Dict[str, Any]] = None


class CompareJob:
    def __init__(self, compare_id: str) -> None:
        self.compare_id = compare_id
        self.status = "processing"
        self.summary_markdown: Optional[str] = None
        self.diagram: Optional[Dict[str, Any]] = None

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
            set_name = (row.get("set") or "").strip()
            if set_name not in ALLOWED_SETS:
                continue
            year_value = row.get("year") or "0"
            try:
                year = int(year_value)
            except ValueError:
                year = 0
            painting = Painting(
                id=(row.get("id") or "").strip(),
                title=(row.get("title") or "").strip(),
                artist=(row.get("artist") or "").strip(),
                year=year,
                image_filename=(row.get("image_filename") or "").strip(),
                set_name=set_name,
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


def _generate_summary(client: OpenAI, left: Painting, right: Painting) -> str:
    prompt = (
        "Write a concise comparison summary of the two paintings. "
        "Focus on subject matter, style, technique, color, and mood."
    )
    response = client.responses.create(
        model="gpt-4o-mini",
        temperature=0.2,
        input=[
            {
                "role": "system",
                "content": "You are an art historian assistant.",
            },
            {
                "role": "user",
                "content": (
                    f"Painting A: {left.title} by {left.artist} ({left.year}).\n"
                    f"Painting B: {right.title} by {right.artist} ({right.year}).\n"
                    f"{prompt}"
                ),
            },
        ],
    )
    return response.output_text.strip()


def _generate_diagram(client: OpenAI, left: Painting, right: Painting) -> Dict[str, Any]:
    prompt = (
        "Return Cytoscape-compatible JSON with elements and layout. "
        "Include nodes for each painting and edges describing key contrasts."
    )
    response = client.responses.create(
        model="gpt-4o-mini",
        temperature=0.2,
        input=[
            {
                "role": "system",
                "content": (
                    "You output only valid JSON with keys 'elements' and 'layout'."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Painting A: {left.title} by {left.artist} ({left.year}).\n"
                    f"Painting B: {right.title} by {right.artist} ({right.year}).\n"
                    f"{prompt}"
                ),
            },
        ],
    )
    return json.loads(response.output_text)


def _run_compare_job(compare_id: str, set_name: str, left_id: str, right_id: str) -> None:
    left = _get_painting_by_id(set_name, left_id)
    right = _get_painting_by_id(set_name, right_id)

    client = _get_openai_client()

    summary = _generate_summary(client, left, right)
    with _jobs_lock:
        job = _jobs[compare_id]
        job.summary_markdown = summary
        job.status = "summary_ready"

    diagram = _generate_diagram(client, left, right)
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
            "diagram": diagram,
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
        job.summary_markdown = cached_payload.get("summary_markdown")
        job.diagram = cached_payload.get("diagram")
        job.status = "done"
        with _jobs_lock:
            _jobs[compare_id] = job
        return CompareStartResponse(compare_id=compare_id)

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