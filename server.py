from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import os

app = Flask(__name__)
CORS(app)

# ==============================
# Home Route
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "service": "Video Proxy API",
        "version": "1.0",
        "message": "Server is running successfully on Render!",
        "endpoints": {
            "health": "/api/health",
            "test": "/api/test",
            "video": "/api/video?type=movie&id=1273221"
        }
    })


# ==============================
# Video Source 1 - Vidsrc
# ==============================
def get_video_from_vidsrc(media_type, media_id, season=1, episode=1):
    try:
        if media_type == "movie":
            url = f"https://vidsrc.in/embed/movie/{media_id}"
        else:
            url = f"https://vidsrc.in/embed/tv/{media_id}/{season}/{episode}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://vidsrc.in/"
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            patterns = [
                r'https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*',
                r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*',
                r'https?://[^"\'\s<>]*\.cloudfront\.net[^"\'\s<>]*'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    return matches[0]

    except Exception as e:
        print("vidsrc error:", e, flush=True)

    return None


# ==============================
# Video Source 2 - 2embed
# ==============================
def get_video_from_2embed(media_type, media_id, season=1, episode=1):
    try:
        if media_type == "movie":
            url = f"https://www.2embed.cc/embed/movie/{media_id}"
        else:
            url = f"https://www.2embed.cc/embed/tv/{media_id}/{season}/{episode}"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.2embed.cc/"
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            patterns = [
                r'https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*',
                r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    return matches[0]

    except Exception as e:
        print("2embed error:", e, flush=True)

    return None


# ==============================
# Video Source 3 - ZXCPrime
# ==============================
def get_video_from_zxcprime(media_type, media_id, season=1, episode=1):
    if media_type == "movie":
        return f"https://zxcprime.xyz/embed/movie/{media_id}"
    else:
        return f"https://zxcprime.xyz/embed/tv/{media_id}/{season}/{episode}"


# ==============================
# Video API
# ==============================
@app.route("/api/video", methods=["GET"])
def get_video():

    media_type = request.args.get("type", "movie")
    media_id = request.args.get("id")

    if not media_id:
        return jsonify({
            "success": False,
            "error": "Missing media ID"
        }), 400

    season = int(request.args.get("season", 1))
    episode = int(request.args.get("episode", 1))

    print(
        f"Request: type={media_type} id={media_id}",
        flush=True
    )

    # Try vidsrc
    print("Trying vidsrc...", flush=True)

    video = get_video_from_vidsrc(
        media_type,
        media_id,
        season,
        episode
    )

    if video:
        return jsonify({
            "success": True,
            "source": "vidsrc",
            "videoUrl": video
        })

    # Try 2embed
    print("Trying 2embed...", flush=True)

    video = get_video_from_2embed(
        media_type,
        media_id,
        season,
        episode
    )

    if video:
        return jsonify({
            "success": True,
            "source": "2embed",
            "videoUrl": video
        })

    # Fallback
    embed = get_video_from_zxcprime(
        media_type,
        media_id,
        season,
        episode
    )

    return jsonify({
        "success": False,
        "fallback": True,
        "embedUrl": embed,
        "message": "No direct stream found. Use embed URL.",
        "source": "zxcprime"
    })


# ==============================
# Health API
# ==============================
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "video proxy",
        "version": "1.0"
    })


# ==============================
# Test API
# ==============================
@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({
        "status": "ok",
        "message": "Server is running!",
        "sources": [
            "vidsrc",
            "2embed",
            "zxcprime"
        ],
        "examples": {
            "movie":
                "/api/video?type=movie&id=1273221",
            "tv":
                "/api/video?type=tv&id=94997&season=1&episode=1"
        }
    })


# ==============================
# Error Handlers
# ==============================
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({
        "success": False,
        "error": "Internal Server Error"
    }), 500


# ==============================
# Run
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )