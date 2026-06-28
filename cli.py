import json
import sys
from datetime import date
from pathlib import Path

from app.ai import AIProvider
from app.reader import extract_text_from_pdf
from app.parser import parse_cv, cv_to_markdown
from app.writer import render_pdf
from app.parser import parse_jd
from app.optimizer import optimize
from app.models import CVData

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def load_config():
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {"model": "deepseek-v4-flash", "api_key": ""}


def get_ai() -> AIProvider:
    config = load_config()
    return AIProvider(
        provider=config.get("provider", "opencode"),
        api_key=config.get("api_key", ""),
        model=config.get("model", ""),
        api_base=config.get("api_base", ""),
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
    print(f"CV saved to {path}")
    print(f"Preview saved to {md_path}")


def cmd_upload(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f"Error: File not found: {pdf_path}")
        return
    print("Extracting text from PDF...")
    raw_text = extract_text_from_pdf(str(path))
    if not raw_text.strip():
        print("Error: Could not extract text from PDF")
        return
    print("Parsing CV with AI...")
    ai = get_ai()
    cv = parse_cv(raw_text, ai)
    save_cv_data(cv)
    print("\nExtracted CV:")
    print("-" * 40)
    print(cv_to_markdown(cv))


def cmd_view():
    cv_data = load_cv_data()
    if cv_data is None:
        print("No CV saved yet. Use 'upload' command first.")
        return
    md_path = DATA_DIR / "cv-data.md"
    if md_path.exists():
        print(md_path.read_text(encoding="utf-8"))
    else:
        print(json.dumps(cv_data, indent=2, ensure_ascii=False))


def cmd_optimize(jd_text: str | None = None):
    cv_data = load_cv_data()
    if cv_data is None:
        print("No CV saved yet. Use 'upload' command first.")
        return

    if not jd_text:
        print("Paste the job description below (Ctrl+Z then Enter to finish):")
        jd_text = sys.stdin.read().strip()
        if not jd_text:
            print("No job description provided.")
            return

    ai = get_ai()
    cv = CVData.from_dict(cv_data)

    print("Parsing job description...")
    jd = parse_jd(jd_text, ai)
    print(f"  Role: {jd.role or 'N/A'}")
    print(f"  Company: {jd.company or 'N/A'}")

    print("Optimizing CV... (this may take a minute)")
    result = optimize(cv, jd, ai)

    company = "".join(c if c.isalnum() or c in " -" else "" for c in (jd.company or "Company")).strip().replace(" ", "-")
    role = "".join(c if c.isalnum() or c in " -" else "" for c in (jd.role or "Role")).strip().replace(" ", "-")
    today = date.today().isoformat()
    filename = f"optimized-{company}-{role}-{today}.pdf"
    output_path = OUTPUT_DIR / filename
    error = render_pdf(result.optimized_cv, str(output_path))
    if error:
        print(f"\nPDF generation failed: {error}")
    else:
        print(f"\nOptimized CV saved: {output_path}")

    if result.changes:
        print("\nChanges made by AI:")
        for c in result.changes:
            print(f"  - {c}")


def print_help():
    print("Usage:")
    print("  python cli.py upload <pdf_path>   Extract CV from PDF")
    print("  python cli.py view                View saved CV")
    print("  python cli.py optimize [text]     Optimize CV for a job")
    print("  python cli.py                     Interactive mode")


def interactive():
    print("CV Optimizer - Interactive Mode")
    print("=" * 40)

    cv_data = load_cv_data()
    if cv_data is None:
        print("\nNo CV found. Please provide your CV PDF path:")
        pdf_path = input("Path: ").strip()
        if pdf_path:
            cmd_upload(pdf_path)
    else:
        print("\nSaved CV found:")
        print("-" * 40)
        md_path = DATA_DIR / "cv-data.md"
        if md_path.exists():
            print(md_path.read_text(encoding="utf-8"))
        else:
            print(json.dumps(cv_data, indent=2))

    print("\n" + "=" * 40)
    print("Paste the job description (type 'done' on a new line when finished):")
    lines = []
    while True:
        line = input()
        if line.strip().lower() == "done":
            break
        lines.append(line)
    jd_text = "\n".join(lines).strip()
    if jd_text:
        cmd_optimize(jd_text)
    else:
        print("No job description provided.")


def main():
    if len(sys.argv) < 2:
        interactive()
        return

    cmd = sys.argv[1]

    if cmd == "upload":
        if len(sys.argv) < 3:
            print("Usage: python cli.py upload <pdf_path>")
            return
        cmd_upload(sys.argv[2])
    elif cmd == "view":
        cmd_view()
    elif cmd == "optimize":
        jd_text = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_optimize(jd_text)
    elif cmd in ("-h", "--help", "help"):
        print_help()
    else:
        print(f"Unknown command: {cmd}")
        print_help()


if __name__ == "__main__":
    main()
