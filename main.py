from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import base64
import io
import numpy as np
from PIL import Image
import onnxruntime
import requests
import os

MODEL_URL = "https://huggingface.co/keras-io/nsfw-detection-efficientnet-b0-onnx/resolve/main/model.onnx"
MODEL_PATH = "model.onnx"

# Download and load the ONNX model
try:
    # Download the model if it doesn't exist
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading model from {MODEL_URL}")
        response = requests.get(MODEL_URL)
        if response.status_code == 200:
            with open(MODEL_PATH, "wb") as f:
                f.write(response.content)
            print("Model downloaded successfully")
        else:
            print(f"Failed to download model: HTTP {response.status_code}")
            raise Exception(f"Failed to download model: HTTP {response.status_code}")
    
    session = onnxruntime.InferenceSession(MODEL_PATH)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
except Exception as e:
    print(f"Error loading model: {e}")
    raise

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModerateRequest(BaseModel):
    images: List[str]  # List of base64 encoded images

class ModerateResponse(BaseModel):
    results: List[bool]  # Results for each image
    flagged: bool  # True if any image is flagged

def preprocess_image(img_base64: str):
    try:
        # Decode base64 image
        img_data = base64.b64decode(img_base64)
        img = Image.open(io.BytesIO(img_data))
        
        # Resize and convert to RGB if needed
        img = img.convert('RGB')
        img = img.resize((224, 224))  # EfficientNet B0 input size
        
        # Convert to numpy array and normalize
        img_array = np.array(img).astype(np.float32)
        
        # Normalize with EfficientNet preprocessing
        img_array = img_array / 255.0
        
        # Transpose from HWC to CHW format for ONNX model
        img_array = img_array.transpose(2, 0, 1)
        
        # Expand dimensions for batch processing
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@app.post("/video-moderation", response_model=ModerateResponse)
async def moderate_images(request: ModerateRequest):
    if not request.images:
        return ModerateResponse(results=[], flagged=False)
    
    results = []
    for img_base64 in request.images:
        # Preprocess image
        img_array = preprocess_image(img_base64)
        
        # Run inference
        try:
            pred = session.run([output_name], {input_name: img_array})[0]
            
            # EfficientNet B0 NSFW model outputs scores for [SFW, NSFW]
            # We want to check if NSFW probability is higher than threshold
            nsfw_score = pred[0][1]  # Index 1 corresponds to NSFW class
            is_nsfw = bool(nsfw_score > 0.5)  # Adjust threshold as needed
            results.append(is_nsfw)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error during inference: {str(e)}")
    
    # Determine if any image is flagged as NSFW
    flagged = any(results)
    
    return ModerateResponse(results=results, flagged=flagged)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
