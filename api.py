#!/usr/bin/env python3
"""
Clean Lyrics Extractor API
Provides a simple REST endpoint for lyrics extraction
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from core.working_lyrics_extractor import WorkingSongLyrics
import os
import requests

app = Flask(__name__)
CORS(app, origins=[
    'http://localhost:3000',  # Local development
    'https://lyrics-extractor-frontend.vercel.app',  # Vercel deployment
    'https://lyrics-extractor-frontend.vercel.app/'  # With trailing slash
])  # Enable CORS for specific origins

# Your API credentials
GCS_API_KEY = "AIzaSyCueYKFmg7Je4ywdg2ahmZ_To0AU97P0QI"
GCS_ENGINE_ID = "e441df94c93ad4421"

# Spotify credentials
SPOTIFY_CLIENT_ID = "957aa328bc7b4e06a53da49f15834b63"
SPOTIFY_CLIENT_SECRET = "200c8c94bbbd408c92c419e131e7e844"

# Initialize the lyrics extractor
lyrics_extractor = WorkingSongLyrics(GCS_API_KEY, GCS_ENGINE_ID)

@app.route('/api/lyrics', methods=['POST'])
def get_lyrics():
    """
    Get lyrics for a song
    
    Request body:
    {
        "song_name": "string"  // Song name (can be misspelled)
    }
    
    Response:
    {
        "success": true,
        "data": {
            "title": "string",
            "lyrics": "string",
            "song_name": "string",
            "characters": number,
            "lines": number,
            "words": number
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        song_name = data.get('song_name', '').strip()
        
        if not song_name:
            return jsonify({
                'success': False,
                'error': 'song_name is required'
            }), 400
        
        # Get lyrics using our working extractor
        result = lyrics_extractor.get_lyrics(song_name)
        
        return jsonify({
            'success': True,
            'data': {
                'title': result['title'],
                'lyrics': result['lyrics'],
                'song_name': song_name,
                'characters': len(result['lyrics']),
                'lines': result['lyrics'].count('\n') + 1,
                'words': len(result['lyrics'].split())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Lyrics Extractor API',
        'version': '1.0.0',
        'endpoints': {
            'lyrics': '/api/lyrics (POST)',
            'health': '/api/health (GET)',
            'spotify_token': '/api/spotify/token (POST)'
        }
    })

@app.route('/api/spotify/token', methods=['POST'])
def spotify_token_exchange():
    """Exchange Spotify authorization code for access token"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        code = data.get('code')
        redirect_uri = data.get('redirect_uri')
        
        if not code or not redirect_uri:
            return jsonify({
                'success': False,
                'error': 'code and redirect_uri are required'
            }), 400
        
        # Exchange authorization code for access token
        token_url = "https://accounts.spotify.com/api/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
        
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        
        token_response = response.json()
        
        return jsonify({
            'success': True,
            'data': token_response
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Token exchange failed: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'Lyrics Extractor API',
        'version': '1.0.0',
        'endpoints': {
            'lyrics': '/api/lyrics (POST)',
            'health': '/api/health (GET)',
            'spotify_token': '/api/spotify/token (POST)'
        },
        'usage': {
            'method': 'POST',
            'endpoint': '/api/lyrics',
            'body': {
                'song_name': 'string (required)'
            }
        }
    })

if __name__ == '__main__':
    print("🎵 Starting Lyrics Extractor API...")
    print("🌐 API will be available at: http://localhost:8080")
    print("📚 API Documentation:")
    print("   GET  /              - API info")
    print("   GET  /api/health    - Health check")
    print("   POST /api/lyrics    - Get lyrics")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 