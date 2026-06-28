import json
import sys
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_config():
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def main():
    config = load_config()
    api_key = config.get("api_key", "")

    if not api_key:
        print("No API key found in config.json")
        print("Create one at https://opencode.ai, then add it to config.json:")
        print('  "api_key": "your-api-key-here"')
        input("\nPress Enter to open the keys page in your browser...")
        webbrowser.open("https://opencode.ai/workspace/wrk_01KV2JRR3CC1QFG8W4SS62TM87/keys")
        sys.exit(1)

    import uvicorn
    url = "http://127.0.0.1:8000"
    print(f"Starting CV Optimizer...")
    print(f"Open {url} in your browser")
    print("Press Ctrl+C to stop the server")
    print()

    webbrowser.open(url)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
