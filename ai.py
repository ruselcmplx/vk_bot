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
    """Р—Р°РіСЂСѓР·РєР° JSON СЃ РєСЂРµРґР°РјРё РёР· СѓРєР°Р·Р°РЅРЅРѕРіРѕ РїСѓС‚Рё."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeError(f"Р¤Р°Р№Р» СЃ РєСЂРµРґР°РјРё РЅРµ РЅР°Р№РґРµРЅ РїРѕ РїСѓС‚Рё {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ JSON РІ С„Р°Р№Р»Рµ РєСЂРµРґРѕРІ РїРѕ РїСѓС‚Рё {path}") from exc


class ImageGenerator:
    """РџСЂРѕСЃС‚РѕР№ РІСЂР°РїРїРµСЂ РЅР°Рґ HF endpoint РґР»СЏ РіРµРЅРµСЂР°С†РёРё РёР·РѕР±СЂР°Р¶РµРЅРёР№."""

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
        """Р—Р°РїСЂРѕСЃРёС‚СЊ РёР·РѕР±СЂР°Р¶РµРЅРёРµ РїРѕ С‚РµРєСЃС‚РѕРІРѕРјСѓ РїСЂРѕРјРїС‚Сѓ Рё РІРµСЂРЅСѓС‚СЊ Р±СѓС„РµСЂ Р±Р°Р№С‚."""
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
            print(f"РћС€РёР±РєР° РѕС‚РІРµС‚Р° СЃРµСЂРІРµСЂР°: {error}")
            return None

        if response.status_code != 200:
            print(f"РћС€РёР±РєР° РѕС‚РІРµС‚Р° СЃРµСЂРІРµСЂР°: {response.text}")
            return None

        image_bytes = response.content
        if not image_bytes:
            print(f"РќРµС‚ Р±Р°Р№С‚РєРѕРґР° РёР·РѕР±СЂР°Р¶РµРЅРёСЏ: {response}")
            return None

        return io.BytesIO(image_bytes)
