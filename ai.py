import io
import json

import requests
from PIL import Image

API_URL = "https://api-inference.huggingface.co/models/openskyml/midjourney-mini"
headers = {"Authorization": ""}


class ImageGenerator():
    headers = {"Authorization": ""}

    def __init__(self):
        token = self.get_token()
        if (token):
            self.headers["Authorization"] = token

    def get_token(self):
        creds = json.loads(
            open("./mnt/creds.json", "r", encoding="utf-8").read())
        return "Bearer {token}".format(token=creds["HF_TOKEN"]) if creds["HF_TOKEN"] else ""

    def get_image(self, payload: str):
        response = requests.post(
            API_URL, headers=self.headers, json={
                "inputs": payload.strip(),
            })
        if (response.status_code == 200):
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            image.save("mnt/image.png")
            return io.BytesIO(image_bytes)
