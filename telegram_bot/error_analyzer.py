import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

class ErrorAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        if not self.api_key or not self.folder_id:
            raise ValueError("❌ Укажи YANDEX_API_KEY и YANDEX_FOLDER_ID в .env")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt-lite"

    def _parse_label_and_explanation(self, raw_text: str):
        """Устойчивый парсер ответа YandexGPT"""
        cleaned = re.sub(r'`([^`]+)`', r'\1', raw_text)
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        label = None
        explanation = ""

        valid_labels = ["correct", "syntax_error", "logic_error", "style_issue"]

        for i, line in enumerate(lines):
            maybe_label = line.lower().rstrip('.,;:!?')
            if maybe_label in valid_labels:
                label = maybe_label
                if i + 1 < len(lines):
                    explanation = '\n'.join(lines[i+1:])
                break

        if label is None:
            lower_text = cleaned.lower()
            if "правильно" in lower_text or "верно" in lower_text or "ошибок нет" in lower_text:
                label = "correct"
            elif "синтаксис" in lower_text:
                label = "syntax_error"
            elif "логич" in lower_text:
                label = "logic_error"
            elif "стил" in lower_text or "эффектив" in lower_text:
                label = "style_issue"
            else:
                label = "unknown"
            explanation = cleaned

        return label, explanation

    def analyze(self, user_code: str, reference_code: str) -> dict:
        prompt = f"""Ты — эксперт по программированию, проверяющий решения задач с технических собеседований.
Дано эталонное решение задачи и ответ пользователя.
Проанализируй ответ и определи, есть ли ошибки.
Если ошибок нет, напиши "correct".
Если есть синтаксическая ошибка (пропущена скобка, двоеточие, неверное ключевое слово), напиши "syntax_error".
Если есть логическая ошибка (неверное условие, границы цикла, алгоритм), напиши "logic_error".
Если код работает, но неэффективен или плохо написан, напиши "style_issue".
После метки напиши краткое пояснение на русском языке (1-2 предложения).

Эталонное решение:
        {reference_code}


        Ответ пользователя:
        {user_code}

        Формат ответа (СТРОГО):
        <метка>
        <пояснение>"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }
        payload = {
            "modelUri": self.model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.2,
                "maxTokens": "200"
            },
            "messages": [
                {"role": "system", "text": "Ты — эксперт по программированию."},
                {"role": "user", "text": prompt}
            ]
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload)
            if resp.status_code != 200:
                return {"label": "error", "explanation": f"⚠️ Ошибка YandexGPT: {resp.status_code} {resp.text[:200]}"}
            result = resp.json()
            content = result["result"]["alternatives"][0]["message"]["text"].strip()
        except Exception as e:
            return {"label": "error", "explanation": f"⚠️ Ошибка соединения: {str(e)}"}

        label, explanation = self._parse_label_and_explanation(content)

        return {"label": label, "explanation": explanation}