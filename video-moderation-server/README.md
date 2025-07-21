
# OpenNSFW Video Moderation API

使用 opennsfw-standalone 实现的轻量级视频帧 NSFW 检测服务，适合 Render 免费部署。

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
