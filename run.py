import webbrowser

import uvicorn


def main():
    url = "http://127.0.0.1:8000"
    print(f"Starting CV Optimizer...")
    print(f"Open {url} in your browser")
    print("Press Ctrl+C to stop the server")
    print()

    webbrowser.open(url)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
