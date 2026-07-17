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
                'Origin': f'https://{domain}',
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f'📄 Status: {response.status_code}', flush=True)
            
            if response.status_code == 200:
                html = response.text
                
                # ✅ Save the HTML for debugging (first 1000 chars)
                print(f'📄 HTML Preview: {html[:500]}', flush=True)
                
                # Try to find video URL patterns
                patterns = [
                    # Direct video URLs
                    r'https?://[^"\'\s<>]+\.(mp4|m3u8|ts)[^"\'\s<>]*',
                    # Cloudflare workers
                    r'https?://[^"\'\s<>]*\.workers\.dev[^"\'\s<>]*',
                    # Data attributes
                    r'data-url=["\']([^"\']+)["\']',
                    r'data-src=["\']([^"\']+)["\']',
                    # JSON in scripts
                    r'"url"\s*:\s*"([^"]+)"',
                    r'"videoUrl"\s*:\s*"([^"]+)"',
                    r'"src"\s*:\s*"([^"]+)"',
                    # Iframe sources
                    r'<iframe[^>]*src=["\']([^"\']+)["\'][^>]*>',
                ]
                
                found_urls = []
                for pattern in patterns:
                    matches = re.findall(pattern, html)
                    if matches:
                        # Clean up matches (some may be tuples)
                        clean_matches = []
                        for match in matches:
                            if isinstance(match, tuple):
                                clean_matches.extend([m for m in match if m and isinstance(m, str)])
                            else:
                                clean_matches.append(match)
                        
                        # Filter for valid URLs
                        valid_urls = [u for u in clean_matches if u and u.startswith('http')]
                        if valid_urls:
                            found_urls.extend(valid_urls)
                            print(f'🎬 Found potential URLs: {valid_urls[:3]}', flush=True)
                
                # ✅ If we found any URLs, return the first one
                if found_urls:
                    # Prefer video files
                    for url in found_urls:
                        if any(ext in url for ext in ['.mp4', '.m3u8', '.ts', 'workers.dev']):
                            return {
                                'success': True,
                                'videoUrl': url,
                                'domain': domain,
                                'source': 'direct'
                            }
                    # Fallback to first URL
                    return {
                        'success': True,
                        'videoUrl': found_urls[0],
                        'domain': domain,
                        'source': 'fallback'
                    }
                
                print(f'⚠️ No video found on {domain}', flush=True)
                
            else:
                print(f'⚠️ Status {response.status_code} from {domain}', flush=True)
                
        except Exception as e:
            print(f'❌ Error with {domain}: {e}', flush=True)
            continue
    
    return {'success': False, 'error': 'No video found on any domain'}

@app.route('/api/debug', methods=['GET'])
def debug_page():
    """Debug endpoint to fetch and return the raw HTML"""
    domain = request.args.get('domain', 'zxcprime.xyz')
    media_type = request.args.get('type', 'tv')
    media_id = request.args.get('id', '94997')
    season = request.args.get('season', '1')
    episode = request.args.get('episode', '1')
    
    try:
        if media_type == 'movie':
            url = f'https://{domain}/embed/movie/{media_id}'
        else:
            url = f'https://{domain}/embed/tv/{media_id}/{season}/{episode}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': f'https://{domain}/',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'url': url,
                'status': response.status_code,
                'html_preview': response.text[:2000],
                'html_length': len(response.text)
            })
        else:
            return jsonify({
                'success': False,
                'url': url,
                'status': response.status_code,
                'error': 'Failed to fetch page'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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