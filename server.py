from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import json

app = Flask(__name__)
CORS(app)

DOMAINS = [
    'zxcprime.xyz',
    'zxcstream.xyz',
]

def extract_video_url(html_content):
    # Try multiple patterns
    patterns = [
        # Direct video URLs
        r'https?://[^"\']*\.mp4[^"\']*',
        r'https?://[^"\']*\.m3u8[^"\']*',
        r'https?://[^"\']*\.ts[^"\']*',
        # Cloudflare workers
        r'https?://[^"\']*workers\.dev[^"\']*',
        r'https?://[^"\']*icarus[^"\']*',
        # Any video URL in the page
        r'https?://[^"\']*(?:video|stream|play)[^"\']*',
        # JSON data containing video URL
        r'"videoUrl"\s*:\s*"([^"]+)"',
        r'"url"\s*:\s*"([^"]+)"',
        r'"source"\s*:\s*"([^"]+)"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        if matches:
            # Return the first match (if it's a group match, use the group)
            if isinstance(matches[0], tuple):
                for match in matches:
                    for group in match:
                        if group and (group.startswith('http://') or group.startswith('https://')):
                            return group
            else:
                url = matches[0]
                if url.startswith('http://') or url.startswith('https://'):
                    return url
    
    # Try to find in script tags
    script_pattern = r'<script[^>]*>(.*?)</script>'
    scripts = re.findall(script_pattern, html_content, re.DOTALL)
    for script in scripts:
        for pattern in patterns:
            matches = re.findall(pattern, script)
            if matches:
                if isinstance(matches[0], tuple):
                    for match in matches:
                        for group in match:
                            if group and (group.startswith('http://') or group.startswith('https://')):
                                return group
                else:
                    url = matches[0]
                    if url.startswith('http://') or url.startswith('https://'):
                        return url
    
    return None

def fetch_video(media_type, media_id, season=1, episode=1):
    for domain in DOMAINS:
        try:
            # Try player URL
            if media_type == 'movie':
                urls_to_try = [
                    f'https://{domain}/player/movie/{media_id}',
                    f'https://{domain}/embed/movie/{media_id}',
                ]
            else:
                urls_to_try = [
                    f'https://{domain}/player/tv/{media_id}/{season}/{episode}',
                    f'https://{domain}/embed/tv/{media_id}/{season}/{episode}',
                ]
            
            for url in urls_to_try:
                print(f'🔍 Fetching: {url}')
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': f'https://{domain}/',
                    'Origin': f'https://{domain}',
                }
                
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    video_url = extract_video_url(response.text)
                    if video_url:
                        print(f'✅ Found video URL: {video_url}')
                        return {
                            'success': True,
                            'videoUrl': video_url,
                            'domain': domain,
                            'title': f'{media_type} {media_id}'
                        }
                    else:
                        # Save the page for debugging
                        print(f'⚠️ No video URL found on {url}')
                        print(f'📄 Page preview: {response.text[:500]}...')
                        
        except Exception as e:
            print(f'❌ Error with {domain}: {e}')
            continue
    
    return {'success': False, 'error': 'No video found on any domain'}

@app.route('/api/video', methods=['GET'])
def get_video():
    media_type = request.args.get('type', 'movie')
    media_id = request.args.get('id')
    season = request.args.get('season', 1)
    episode = request.args.get('episode', 1)
    
    if not media_id:
        return jsonify({'error': 'Missing media ID'}), 400
    
    print(f'📺 Request: type={media_type}, id={media_id}, season={season}, episode={episode}')
    
    # Try to convert season/episode to int if they're strings
    try:
        season = int(season)
        episode = int(episode)
    except ValueError:
        season = 1
        episode = 1
    
    result = fetch_video(media_type, media_id, season, episode)
    
    if result.get('success'):
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