# CV Optimizer

AI-powered CV optimization tool. Upload your CV, paste a job description, and get an ATS-optimized resume PDF tailored to the role.

## How it works

1. **Upload your CV** (PDF) — the app extracts and structures your data
2. **Paste a job description** — the app parses it into structured requirements
3. **Optimize** — AI rewrites your CV to match the job, keeping everything truthful
4. **Download** — a professional PDF with your optimized CV, ready to submit

## Prerequisites

- Python 3.10+
- An API key from [OpenCode](https://opencode.ai)

## Setup

```bash
# Clone the repository
git clone <repo-url>
cd cv-optimizer

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up your API key
copy config.example.json config.json   # Windows
cp config.example.json config.json     # macOS/Linux
# Edit config.json — replace "your-api-key-here" with your actual API key

# Run the app
python run_ui.py
```

Open http://127.0.0.1:8000 in your browser.

## Project structure

```
cv-optimizer/
├── app.py             # FastAPI server + routes
├── ai_provider.py     # AI client wrapper
├── cv_reader.py       # Extract text from PDF
├── cv_parser.py       # AI: parse raw CV → structured JSON
├── cv_writer.py       # Generate professional PDF with reportlab
├── jd_parser.py       # AI: parse job description → structured JSON
├── optimizer.py       # AI: optimize CV for target role
├── models.py          # Data models (CVData, JDData, OptimizeResult)
├── run_ui.py          # Startup script (checks API key, launches server)
├── templates/         # HTML templates
├── static/            # CSS styles
├── data/              # Your CV data (auto-generated)
├── output/            # Generated PDFs (auto-generated)
└── config.json        # API key + model config (not tracked by git)
```

## Tech stack

- **Backend:** Python + FastAPI
- **AI:** OpenCode API (DeepSeek models)
- **PDF:** ReportLab
- **Frontend:** Single-page HTML + CSS (no frameworks)

## Notes

- Your CV data is stored locally in `data/cv-data.json`. Nothing is uploaded to any server except the AI API calls.
- Generated PDFs are saved in `output/`.
- The `config.json` file contains your API key — it is excluded from git by default.
