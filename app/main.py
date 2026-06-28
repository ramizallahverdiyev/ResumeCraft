import json
import re
from datetime import date
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.ai import AIProvider
from app.reader import extract_text_from_pdf
from app.parser import parse_cv, cv_to_markdown
from app.writer import render_pdf
from app.parser import parse_jd
from app.optimizer import optimize
from app.models import CVData, JDData

app = FastAPI(title="CV Optimizer")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

PROVIDER_META = {
    "opencode": {
        "label": "OpenCode",
        "default_model": "deepseek-v4-flash-free",
        "needs_key": True,
        "default_base": "https://opencode.ai/zen/v1",
    },
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-4o",
        "needs_key": True,
        "default_base": "https://api.openai.com/v1",
    },
    "ollama": {
        "label": "Ollama (local)",
        "default_model": "llama3",
        "needs_key": False,
        "default_base": "http://localhost:11434",
    },
    "custom": {
        "label": "Custom",
        "default_model": "",
        "needs_key": True,
        "default_base": "",
    },
}

# In-memory runtime config — seeded from config.json at import time
CONFIG: dict = {}

def _load_config_from_file():
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}

CONFIG.update(_load_config_from_file())


def get_ai() -> AIProvider:
    return AIProvider(
        provider=CONFIG.get("provider", "opencode"),
        api_key=CONFIG.get("api_key", ""),
        model=CONFIG.get("model", ""),
        api_base=CONFIG.get("api_base", ""),
    )


def load_cv_data() -> dict | None:
    path = DATA_DIR / "cv-data.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_cv_data(cv: CVData):
    path = DATA_DIR / "cv-data.json"
    path.write_text(cv.to_json(), encoding="utf-8")
    md_path = DATA_DIR / "cv-data.md"
    md_path.write_text(cv_to_markdown(cv), encoding="utf-8")


def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '-')


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"request": request},
    )


@app.get("/api/config")
async def get_config():
    meta = {}
    for key, val in PROVIDER_META.items():
        meta[key] = {
            "label": val["label"],
            "default_model": val["default_model"],
            "needs_key": val["needs_key"],
            "default_base": val["default_base"],
        }
    return {
        "configured": bool(CONFIG.get("api_key") or CONFIG.get("provider") == "ollama"),
        "current": {
            "provider": CONFIG.get("provider", "opencode"),
            "model": CONFIG.get("model", ""),
            "api_base": CONFIG.get("api_base", ""),
        },
        "providers": meta,
    }


@app.post("/api/config")
async def save_config(data: dict):
    provider = data.get("provider", "opencode")
    api_key = data.get("api_key", "")
    model = data.get("model", "")
    api_base = data.get("api_base", "")

    meta = PROVIDER_META.get(provider)
    if not meta:
        raise HTTPException(400, f"Unknown provider '{provider}'")
    if meta["needs_key"] and not api_key:
        raise HTTPException(400, f"API key required for provider '{provider}'")

    CONFIG.update({
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "api_base": api_base,
    })

    # Persist so it survives a restart
    config_path = BASE_DIR / "config.json"
    try:
        config_path.write_text(json.dumps(CONFIG, indent=2), encoding="utf-8")
    except OSError:
        pass

    return {"status": "ok"}


@app.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    content = await file.read()
    pdf_path = BASE_DIR / "original-cv.pdf"
    pdf_path.write_bytes(content)

    raw_text = extract_text_from_pdf(str(pdf_path))
    if not raw_text.strip():
        raise HTTPException(400, "Could not extract text from PDF")

    ai = get_ai()
    cv = parse_cv(raw_text, ai)
    save_cv_data(cv)

    return {
        "status": "ok",
        "message": "CV extracted and saved",
        "cv_data": cv.to_dict(),
        "cv_markdown": cv_to_markdown(cv),
    }


@app.get("/cv-data")
async def get_cv_data():
    cv_data = load_cv_data()
    if cv_data is None:
        raise HTTPException(404, "No CV data found. Upload a CV first.")
    md_path = DATA_DIR / "cv-data.md"
    markdown = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    return {"cv_data": cv_data, "cv_markdown": markdown}


@app.put("/cv-data")
async def update_cv_data(data: dict):
    cv = CVData.from_dict(data)
    save_cv_data(cv)
    return {"status": "ok", "message": "CV data updated"}


@app.post("/parse-jd")
async def parse_jd_endpoint(jd_text: str = Form(...)):
    if not jd_text.strip():
        raise HTTPException(400, "Job description is empty")
    ai = get_ai()
    jd = parse_jd(jd_text, ai)
    return {"status": "ok", "jd_data": jd.to_dict()}


@app.post("/optimize")
async def optimize_endpoint(jd_text: str = Form(...)):
    cv_data = load_cv_data()
    if cv_data is None:
        raise HTTPException(400, "No CV data found. Upload a CV first.")

    ai = get_ai()
    cv = CVData.from_dict(cv_data)
    try:
        jd = parse_jd(jd_text, ai)
    except Exception as e:
        return {"status": "error", "detail": f"Failed to parse job description: {e}"}

    try:
        result = optimize(cv, jd, ai)
    except Exception as e:
        return {"status": "error", "detail": f"Failed to optimize CV: {e}"}

    company = sanitize_filename(jd.company or "Company")
    role = sanitize_filename(jd.role or "Role")
    today = date.today().isoformat()
    filename = f"optimized-{company}-{role}-{today}.pdf"
    output_path = OUTPUT_DIR / filename
    pdf_error = render_pdf(result.optimized_cv, str(output_path))

    ocv = result.optimized_cv
    preview_lines = []
    pi = ocv.get("personal_info", {})
    if pi.get("name"):
        preview_lines.append(f"# {pi['name']}")
    psum = ocv.get("professional_summary") or ocv.get("summary", "")
    if psum:
        preview_lines.append("")
        preview_lines.append(psum)
    raw_skills = ocv.get("skills", [])
    if isinstance(raw_skills, dict):
        flat = []
        if raw_skills.get("technical"):
            flat.extend(raw_skills["technical"])
        if raw_skills.get("soft"):
            flat.extend(raw_skills["soft"])
        raw_skills = flat
    if raw_skills:
        preview_lines.append("")
        preview_lines.append(f"Skills: {', '.join(raw_skills[:8])}")
    if ocv.get("experience"):
        preview_lines.append("")
        preview_lines.append("Experience:")
        for exp in ocv["experience"][:2]:
            line = f"  - {exp.get('role', '')}"
            if exp.get("company"):
                line += f" at {exp['company']}"
            preview_lines.append(line)

    return {
        "status": "ok" if not pdf_error else "pdf_error",
        "download_url": f"/download/{filename}" if not pdf_error else None,
        "filename": filename,
        "changes": result.changes,
        "preview": "\n".join(preview_lines),
        "pdf_error": pdf_error or None,
    }


@app.post("/retry-pdf")
async def retry_pdf():
    cv_data = load_cv_data()
    if cv_data is None:
        raise HTTPException(400, "No CV data found")

    company = sanitize_filename(cv_data.get("personal_info", {}).get("name", "Candidate"))
    today = date.today().isoformat()
    filename = f"optimized-{company}-{today}.pdf"
    output_path = OUTPUT_DIR / filename
    pdf_err = render_pdf(cv_data, str(output_path))
    if pdf_err:
        return {"status": "error", "detail": pdf_err}

    return {
        "status": "ok",
        "download_url": f"/download/{filename}",
        "filename": filename,
    }


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(str(file_path), media_type="application/pdf", filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
