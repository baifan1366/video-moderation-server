
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import base64
from PIL import Image
import io
from opennsfw_standalone import OpenNSFWInferenceRunner

app = FastAPI()

runner = OpenNSFWInferenceRunner.load()

class PredictRequest(BaseModel):
    images: List[str]  # base64 encoded images

@app.post("/video-moderation")
async def video_moderation(request: PredictRequest):
    results = []
    for img_b64 in request.images:
        try:
            img_bytes = base64.b64decode(img_b64)
            score = runner.infer(img_bytes)
            results.append(score > 0.7)  # Threshold for NSFW
        except Exception:
            results.append(False)
    return {
        "results": results,
        "flagged": any(results)
    }
