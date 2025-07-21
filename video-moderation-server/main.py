from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from nsfw_detector import predict
from PIL import Image
import os, io, uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模型路径（使用默认 mobilenet_v2_140_224）
MODEL_PATH = os.getenv("NSFW_MODEL_PATH", "mobilenet_v2_140_224")
model = predict.load_model(MODEL_PATH)

@app.post("/video-moderate")
async def moderate_image(file: UploadFile = File(...)):
    # 读取上传的文件
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    # 临时保存图像（模型只支持文件路径）
    temp_path = f"/tmp/{uuid.uuid4()}.jpg"
    image.save(temp_path)

    # 模型预测（返回是 dict：{路径: {class: score, ...}}）
    result = model.predict(temp_path)

    # 清理临时文件
    os.remove(temp_path)

    return {"result": result[temp_path]}
