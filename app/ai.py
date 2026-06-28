import time
import httpx

PROVIDERS = {
    "opencode": {
        "base_url": "https://opencode.ai/zen/v1",
        "default_model": "deepseek-v4-flash-free",
        "auth": "bearer",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "auth": "bearer",
    },
    "ollama": {
        "base_url": "http://localhost:11434",
        "default_model": "llama3",
        "auth": None,
    },
    "custom": {
        "base_url": None,
        "default_model": None,
        "auth": "bearer",
    },
}

MAX_RETRIES = 3
RETRY_DELAY = 2


class AIProvider:
    def __init__(self, provider: str = "opencode", api_key: str = "", model: str = "", api_base: str = ""):
        info = PROVIDERS.get(provider, PROVIDERS["custom"])

        base_url = api_base or info["base_url"]
        if not base_url:
            raise ValueError(f"No api_base specified for provider '{provider}'. Set 'api_base' in config.json")

        self.model = model or info["default_model"]
        if not self.model:
            raise ValueError(f"No model specified for provider '{provider}'. Set 'model' in config.json")

        self.api_key = api_key
        headers = {"Content-Type": "application/json"}
        if info["auth"] == "bearer" and api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.Client(base_url=base_url, headers=headers, timeout=120)

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
