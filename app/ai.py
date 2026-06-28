import json
import time
import httpx

API_BASE = "https://opencode.ai/zen/v1"
MAX_RETRIES = 3
RETRY_DELAY = 2


class AIProvider:
    def __init__(self, model: str = "deepseek-v4-flash", api_key: str = ""):
        self.model = model
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

    def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        format: str | None = None,
    ) -> str:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        body = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": 8192,
        }
        if format == "json":
            body["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.post("/chat/completions", json=body)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 503 and attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    print(f"API temporarily unavailable (503), retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    print(f"API connection error, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise

        raise last_error if last_error else RuntimeError("API call failed after retries")
