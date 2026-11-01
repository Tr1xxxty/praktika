import logging
import os
import time
from functools import lru_cache
from pathlib import Path
import openai
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
log = logging.getLogger(__name__)
class LLMError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status
@lru_cache(maxsize=1)
def get_client():
    key = os.getenv("LLM_API_KEY")
    if not key or not os.getenv("LLM_MODEL") or not os.getenv("LLM_BASE_URL"):
        raise LLMError("Заповніть LLM_API_KEY, LLM_MODEL і LLM_BASE_URL у .env", 503)
    return openai.OpenAI(api_key=key, base_url=os.environ["LLM_BASE_URL"],
                         timeout=float(os.getenv("LLM_TIMEOUT", "30")), max_retries=0)

def complete(messages, temperature=None, response_format=None):
    client = get_client()
    params = dict(model=os.environ['LLM_MODEL'], messages=messages,
                  temperature=float(os.getenv('LLM_TEMPERATURE', '0.2')) if temperature is None else temperature,
                  max_tokens=int(os.getenv('LLM_MAX_TOKENS', '800')))
    if response_format: params['response_format'] = response_format
    attempts = min(3, max(1, int(os.getenv('LLM_ATTEMPTS', '3'))))
    for attempt in range(attempts):
        try:
            response = client.chat.completions.create(**params)
            if not response.choices: raise LLMError("Сервіс не повернув відповіді")
            choice = response.choices[0]
            if choice.finish_reason == 'length':
                raise LLMError("Відповідь обірвана: збільште LLM_MAX_TOKENS")
            if not choice.message.content: raise LLMError("Модель повернула порожню відповідь")
            return response
        except openai.AuthenticationError as exc:
            raise LLMError("Помилка налаштування ключа сервера", 503) from exc
        except (openai.APITimeoutError, openai.APIConnectionError, openai.APIStatusError) as exc:
            code = getattr(exc, 'status_code', None)
            retry = code is None or code == 429 or code >= 500
            log.warning("LLM failure: %s status=%s attempt=%s", type(exc).__name__, code, attempt+1)
            if retry and attempt + 1 < attempts:
                time.sleep(0.5 * 2 ** attempt)
                continue
            if isinstance(exc, openai.APITimeoutError):
                raise LLMError("Перевищено час очікування", 504) from exc
            if code == 429: raise LLMError("Ліміт запитів вичерпано. Спробуйте пізніше", 429) from exc
            raise LLMError("Сервіс моделі недоступний або відхилив налаштування", 503 if retry else 502) from exc

def checked_text(text):
    text = text.strip()
    if not text or len(text) > 8000: raise LLMError("Введіть звернення від 1 до 8000 символів", 422)
    return text

def usage_dict(response):
    return response.usage.model_dump() if response.usage else {}
