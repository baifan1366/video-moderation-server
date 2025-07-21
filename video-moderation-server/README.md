
# Video Moderation Server

## Endpoint

POST `/video-moderate`

### Payload
Upload an image file as form-data.

### Response
```json
{
  "result": {
    "porn": 0.01,
    "hentai": 0.02,
    "sexy": 0.05,
    "neutral": 0.9
  }
}
```

## Usage

```bash
docker build -t video-moderation .
docker run -p 8002:8002 --env-file .env video-moderation
```
