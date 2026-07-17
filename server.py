from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import json
import time
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
CORS(app)

# ✅ Updated domains (keeping your original structure)
DOMAINS = [
    'zxcprime.xyz',      # ✅ Added this as primary
    'zxcstream.xyz',     # ✅ Kept as fallback
]

def extract_video_url(html_content):
    # Look for video URLs in the page
    patterns = [
        r'https?://[^"\']*\.mp4[^"\']*',
        r'https?://[^"\']*\.m3u8[^"\']*',
        r'https?://[^"\']*workers\.dev[^"\']*',
        r'https?://[^"\']*icarus[^"\']*',
        r'https?://[^"\']*\.ts[^"\']*',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            return matches[0]
    
    # Try to find video URL in script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, html_content, re.DOTALL)
    for script in scripts:
        for pattern in patterns:
            matches = re.findall(pattern, script)
            if matches:
                return matches[0]
    
    return None

def fetch_video(media_type, media_id, season=1, episode=1):
    # ✅ Try each domain
    for domain in DOMAINS:
        try:
            # Build the URL
            if media_type == 'movie':
                url = f'https://{domain}/player/movie/{media_id}'
            else:
                url = f'https://{domain}/player/tv/{media_id}/{season}/{episode}'
            
            print(f'🔍 Fetching from: {url}')
            
            # Make request with browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': f'https://{domain}/',
                'Origin': f'https://{domain}',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                video_url = extract_video_url(response.text)
                if video_url:
                    print(f'✅ Found video URL from {domain}: {video_url}')
                    return {
                        'success': True,
                        'videoUrl': video_url,
                        'domain': domain,
                        'title': f'{media_type} {media_id}'
                    }
            
            # ✅ Try embed URL as fallback
            if media_type == 'movie':
                embed_url = f'https://{domain}/embed/movie/{media_id}'
            else:
                embed_url = f'https://{domain}/embed/tv/{media_id}/{season}/{episode}'
            
            print(f'🔄 Trying embed: {embed_url}')
            embed_response = requests.get(embed_url, headers=headers, timeout=30)
            
            if embed_response.status_code == 200:
                video_url = extract_video_url(embed_response.text)
                if video_url:
                    print(f'✅ Found video URL from {domain} (embed): {video_url}')
                    return {
                        'success': True,
                        'videoUrl': video_url,
                        'domain': domain,
                        'title': f'{media_type} {media_id}',
                        'source': 'embed'
                    }
                    
        except Exception as e:
            print(f'❌ Error with {domain}: {e}')
            continue
    
    return {'success': False, 'error': 'No video found on any domain'}

@app.route('/api/video', methods=['GET'])
def get_video():
    media_type = request.args.get('type', 'movie')
    media_id = request.args.get('id')
    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))
    
    if not media_id:
        return jsonify({'error': 'Missing media ID'}), 400
    
    print(f'📺 Request: type={media_type}, id={media_id}, season={season}, episode={episode}')
    
    result = fetch_video(media_type, media_id, season, episode)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 404

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'zxcprime proxy',
        'domains': DOMAINS
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Backend server is running!',
        'domains': DOMAINS,
        'endpoints': {
            'movie': '/api/video?type=movie&id=1273221',
            'tv': '/api/video?type=tv&id=94997&season=1&episode=1'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)