# api.py - Vercel Serverless API for YouTube Video Download using Clipto
# Deployment: 
# 1. Install deps: pip install fastapi uvicorn requests
# 2. Create requirements.txt with: fastapi, uvicorn, requests
# 3. vercel.json: {"rewrites": [{"source": "/(.*)", "destination": "/api"}]}
# 4. Deploy: vercel --prod
# Endpoint: https://your-app.vercel.app/linkyt?yt={YT_URL}
# It fetches highest quality direct URL from Clipto, then streams the video for download

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import requests

app = FastAPI()

CLIPTO_API = "https://www.clipto.com/api/youtube"

def get_highest_quality_url(yt_url: str):
    try:
        resp = requests.post(CLIPTO_API, json={"url": yt_url}, headers={"Content-Type": "application/json"})
        data = resp.json()
        if data.get("success"):
            medias = data.get("medias", [])
            # Sort by quality (height + bitrate)
            medias_sorted = sorted(medias, key=lambda m: (m.get("height", 0), m.get("bitrate", 0)), reverse=True)
            if medias_sorted:
                return medias_sorted[0].get("url")
    except Exception as e:
        print(f"Error: {e}")
    return None

@app.get("/linkyt")
async def download(yt: str = Query(...)):
    video_url = get_highest_quality_url(yt)
    if not video_url:
        return {"error": "Failed to fetch video. Try again or check URL."}

    # Stream the video from Google server
    def stream_video():
        with requests.get(video_url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=8192):
                yield chunk

    headers = {
        "Content-Disposition": "attachment; filename=video.mp4",
        "Content-Type": "video/mp4",
    }
    return StreamingResponse(stream_video(), headers=headers, media_type="video/mp4")

# For local test: uvicorn api:app --reload
