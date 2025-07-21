
# Video Moderation API

使用 EfficientNet B0 ONNX 模型实现的轻量级视频帧 NSFW 检测服务，适合 Render 免费部署。

## 模型信息

本服务使用 Hugging Face 上的 EfficientNet B0 NSFW 检测模型:
- 模型来源: [keras-io/nsfw-detection-efficientnet-b0-onnx](https://huggingface.co/keras-io/nsfw-detection-efficientnet-b0-onnx)
- 输入尺寸: 224x224 像素 RGB 图像

## 接口

**POST** `/video-moderation`

### 请求体：
```json
{
  "images": ["<base64-image>", "<base64-image>", ...]
}
```

### 响应体：
```json
{
  "results": [false, true],
  "flagged": true
}
```

- `results[i] = true` 表示第 i 张图像疑似 NSFW。
- `flagged = any(results)`
