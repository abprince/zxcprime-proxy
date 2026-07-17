from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import re
import json

app = Flask(__name__)
CORS(app)

# ✅ Working video sources
def get_video_from_vidsrc(media_type, media_id, season=1, episode=1):
    """Try vidsrc API"""
    try:
        if media_type == 'movie':
            url = f'https://vidsrc.in/embed/movie/{media_id}'
        else:
            url = f'https://vidsrc.in/embed/tv/{media_id}/{season}/{episode}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://vidsrc.in/',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Look for video URL
            patterns = [
                r'https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*',
                r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*',
                r'https?://[^"\'\s<>]*\.cloudfront\.net[^"\'\s<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    return matches[0]
    except:
        pass
    return None

def get_video_from_2embed(media_type, media_id, season=1, episode=1):
    """Try 2embed API"""
    try:
        if media_type == 'movie':
            url = f'https://www.2embed.cc/embed/movie/{media_id}'
        else:
            url = f'https://www.2embed.cc/embed/tv/{media_id}/{season}/{episode}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.2embed.cc/',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            patterns = [
                r'https?://[^"\'\s<>]+\.mp4[^"\'\s<>]*',
                r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches:
                    return matches[0]
    except:
        pass
    return None

def get_video_from_zxcprime(media_type, media_id, season=1, episode=1):
    """Try zxcprime embed - just return the embed URL"""
    if media_type == 'movie':
        return f'https://zxcprime.xyz/embed/movie/{media_id}'
    else:
        return f'https://zxcprime.xyz/embed/tv/{media_id}/{season}/{episode}'

@app.route('/api/video', methods=['GET'])
def get_video():
    media_type = request.args.get('type', 'movie')
    media_id = request.args.get('id')
    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))
    
    if not media_id:
        return jsonify({'error': 'Missing media ID'}), 400
    
    print(f'📺 Fetching: type={media_type}, id={media_id}', flush=True)
    
    # ✅ Try each source
    video_url = None
    source = None
    
    # Try vidsrc
    print('🔍 Trying vidsrc...', flush=True)
    video_url = get_video_from_vidsrc(media_type, media_id, season, episode)
    if video_url:
        source = 'vidsrc'
        print(f'✅ Found from vidsrc: {video_url}', flush=True)
        return jsonify({
            'success': True,
            'videoUrl': video_url,
            'source': source
        })
    
    # Try 2embed
    print('🔍 Trying 2embed...', flush=True)
    video_url = get_video_from_2embed(media_type, media_id, season, episode)
    if video_url:
        source = '2embed'
        print(f'✅ Found from 2embed: {video_url}', flush=True)
        return jsonify({
            'success': True,
            'videoUrl': video_url,
            'source': source
        })
    
    # ✅ Fallback: Return zxcprime embed URL
    print('🔍 Returning zxcprime embed URL...', flush=True)
    embed_url = get_video_from_zxcprime(media_type, media_id, season, episode)
    
    return jsonify({
        'success': False,
        'error': 'No direct video URL found',
        'embedUrl': embed_url,
        'message': 'Use WebView to open embed URL',
        'fallback': True
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'video proxy',
        'version': '1.0'
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'message': 'Server is running!',
        'endpoints': {
            'movie': '/api/video?type=movie&id=1273221',
            'tv': '/api/video?type=tv&id=94997&season=1&episode=1'
        },
        'sources': ['vidsrc', '2embed', 'zxcprime']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)