from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

DOMAINS = ['zxcprime.xyz', 'zxcstream.xyz']

def fetch_video(media_type, media_id, season=1, episode=1):
    """Fetch video URL directly from zxcprime embed pages"""
    
    for domain in DOMAINS:
        try:
            # Build embed URL (these often work better)
            if media_type == 'movie':
                url = f'https://{domain}/embed/movie/{media_id}'
            else:
                url = f'https://{domain}/embed/tv/{media_id}/{season}/{episode}'
            
            print(f'🔍 Fetching embed: {url}', flush=True)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': f'https://{domain}/',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f'📄 Status: {response.status_code}', flush=True)
            
            if response.status_code == 200:
                html = response.text
                
                # Try to find video URL in the page
                # Look for iframe src that points to video
                iframe_pattern = r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*>'
                iframes = re.findall(iframe_pattern, html)
                for iframe in iframes:
                    if iframe.startswith('http'):
                        print(f'📺 Found iframe: {iframe}', flush=True)
                        return {
                            'success': True,
                            'videoUrl': iframe,
                            'domain': domain,
                            'source': 'iframe'
                        }
                
                # Look for video URL in script tags
                script_pattern = r'<script[^>]*>(.*?)</script>'
                scripts = re.findall(script_pattern, html, re.DOTALL)
                for script in scripts:
                    # Look for URLs in the script
                    url_pattern = r'https?://[^"\'\s<>]+\.(mp4|m3u8|ts|workers\.dev)[^"\'\s<>]*'
                    matches = re.findall(url_pattern, script)
                    if matches:
                        print(f'🎬 Found video URL in script: {matches[0]}', flush=True)
                        return {
                            'success': True,
                            'videoUrl': matches[0],
                            'domain': domain,
                            'source': 'script'
                        }
                
                # Look for any URL pattern in the page
                direct_pattern = r'https?://[^"\'\s<>]+\.(mp4|m3u8|ts)[^"\'\s<>]*'
                matches = re.findall(direct_pattern, html)
                if matches:
                    print(f'🎬 Found direct video URL: {matches[0]}', flush=True)
                    return {
                        'success': True,
                        'videoUrl': matches[0],
                        'domain': domain,
                        'source': 'direct'
                    }
                
                print(f'⚠️ No video found on {domain}', flush=True)
                print(f'📄 Page length: {len(html)}', flush=True)
                
        except Exception as e:
            print(f'❌ Error with {domain}: {e}', flush=True)
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
    
    result = fetch_video(media_type, media_id, season, episode)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 404

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'zxcprime proxy'})

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Backend server is running!',
        'domains': DOMAINS
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)