# ArtWeave (prj-thesis)

ArtWeave is an artwork-comparison app:

- Pick a set (A or B)
- Pick two artworks
- The backend generates a short comparison summary (OpenAI)
- The backend generates a structured diagram spec from the summary + dataset facts
- The frontend renders the summary + diagram on `/compare`

## Repo Structure

- `fastapi_app.py` — FastAPI backend (port `8000`)
- `diagram_utils.py` — diagram builder + validation
- `Painting_Metadata_260127.csv` — painting dataset (2 sets, 5 paintings each)
- `frontend/` — Next.js frontend (port `3000`)

## Prerequisites

- Python 3.11+ (tested with 3.12)
- Node.js 18+ and npm

## Environment Variables

The backend requires an OpenAI API key:

- `OPENAI_API_KEY`

Example (macOS / zsh):

```bash
export OPENAI_API_KEY="your_key_here"
```

## Run Locally (Dev)

### 1) Start the backend (FastAPI)

From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn fastapi_app:app --reload --port 8000
```

The backend serves:

- API endpoints under `http://localhost:8000/api/...`
- painting images under `http://localhost:8000/static/paintings/<filename>`

> Note: the backend expects painting images at `frontend/assets/paintings/`.

### 2) Start the frontend (Next.js)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

- `http://localhost:3000`

## Frontend → Backend Proxy (No CORS in Dev)

The frontend must call the backend through the Next.js rewrite:

- Frontend calls `http://localhost:3000/api/...`
- Next rewrites to `http://localhost:8000/...`

If you hit CORS issues, verify `frontend/next.config.js` has the `/api/:path*` rewrite.

## Key Endpoints

- `GET /api/sets`
- `GET /api/paintings?set=A|B`
- `POST /api/compare/start`
  - body: `{ "set": "A"|"B", "left_id": "...", "right_id": "..." }`
- `GET /api/compare/{compare_id}`

## Diagram Output Contract

Backend returns:

```json
{
  "nodes": [{ "id": "artworkA", "type": "artwork", "label": "...", "level": 0, "x": 0, "y": 0 }],
  "edges": [{ "id": "edge-1", "source": "artworkA", "target": "L1", "kind": "direct", "label": "Created by" }],
  "layout": { "direction": "TB" }
}
```

Notes:

- Node `x/y` are deterministic positions for React Flow.
- Edge `label` is optional; the UI renders labels with a background.

## Troubleshooting

### Backend fails with `OPENAI_API_KEY is not configured`

Set `OPENAI_API_KEY` in your shell (or your process manager env).

### Backend fails: `Directory 'assets/paintings' does not exist`

Painting images are expected at:

- `frontend/assets/paintings`

### Changes not showing up / diagram looks stale

The backend caches compare results under `cache/`.

If you change diagram generation logic:

1. stop the backend
2. delete `cache/` (optional)
3. restart the backend

## Development Notes

- In dev mode, `/compare` shows a `<details>` debug block with the live diagram JSON.
- Diagram rendering uses React Flow custom nodes; edges require handles (already included in the custom node components).
