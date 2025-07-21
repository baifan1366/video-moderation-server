
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import base64
from PIL import Image
import io
import numpy as np
import tensorflow as tf
import os
import requests
import shutil
from pathlib import Path

app = FastAPI()

# Setup model paths
MODEL_FILENAME = "nsfw_mobilenet2.224x224.h5"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_FILENAME)

# Download model if it doesn't exist
def download_model():
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    if not os.path.exists(MODEL_PATH):
        print("Downloading NSFW model...")
        url = "https://s3.amazonaws.com/ir_public/nsfwjscdn/nsfw_mobilenet2.224x224.h5"
        response = requests.get(url, stream=True)
        with open(MODEL_PATH, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        print("Model downloaded successfully!")
    return MODEL_PATH

# Load model - adding module path to sys.path
import sys
nsfw_model_path = os.path.join(os.path.dirname(__file__), "nsfw_model-1.2.0")
sys.path.append(nsfw_model_path)
from nsfw_detector import predict

# Download model and load it
model_path = download_model()
model = predict.load_model(model_path)

class PredictRequest(BaseModel):
    images: List[str]  # base64 encoded images

@app.post("/video-moderation")
async def video_moderation(request: PredictRequest):
    results = []
    for img_b64 in request.images:
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(img_b64)
            img_io = io.BytesIO(img_bytes)
            
            # Save to a temporary file (the model requires a file path)
            temp_img_path = os.path.join(MODEL_DIR, "temp_image.jpg")
            with open(temp_img_path, "wb") as f:
                f.write(img_bytes)
            
            # Classify the image
            predictions = predict.classify(model, temp_img_path)
            prediction = list(predictions.values())[0]  # Get the first (only) prediction
            
            # The categories are ['drawings', 'hentai', 'neutral', 'porn', 'sexy']
            # We'll flag if it's either porn, hentai, or sexy
            nsfw_score = prediction['hentai'] + prediction['porn'] + prediction['sexy']
            results.append(nsfw_score > 0.7)  # Threshold for NSFW
            
            # Clean up temporary file
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)
                
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            results.append(False)
    
    return {
        "results": results,
        "flagged": any(results)
    }
