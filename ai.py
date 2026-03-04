from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Optional

import requests

API_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "stabilityai/stable-diffusion-3-medium-diffusers"
)


def _load_creds(path: Path) -> dict:
    """Загрузка JSON с кредами из указанного пути."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Файл с кредами не найден по пути {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Некорректный JSON в файле кредитов по пути {path}") from exc


class ImageGenerator:
    """Простой враппер над HF endpoint для генерации изображений."""

    def __init__(self, creds_path: Optional[Path] = None) -> None:
        if creds_path is None:
            creds_path = Path("./mnt/creds.json")
        self._headers = {"Authorization": self._build_auth_header(creds_path)}

    @staticmethod
    def _build_auth_header(creds_path: Path) -> str:
        creds = _load_creds(creds_path)
        token = creds.get("HF_TOKEN") or ""
        return f"Bearer {token}" if token else ""

    def get_image(self, payload: str) -> Optional[io.BytesIO]:
        """Запросить изображение по текстовому промпту и вернуть буфер байт."""
        try:
            response = requests.post(
                API_URL,
                headers=self._headers,
                json={
                    "inputs": payload.strip(),
                    "options": {"wait_for_model": True},
                },
                timeout=300,
            )
        except Exception as error:
            print(f"Ошибка ответа сервера: {error}")
            return None

        if response.status_code != 200:
            print(f"Ошибка ответа сервера: {response.text}")
            return None

        image_bytes = response.content
        if not image_bytes:
            print(f"Нет байткода изображения: {response}")
            return None

        return io.BytesIO(image_bytes)
