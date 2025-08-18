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
import json
import re

try:
    import google.generativeai as genai
except Exception:
    genai = None

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

def _normalize_and_validate_lyrics(raw_lyrics: str) -> str:
    if not isinstance(raw_lyrics, str):
        raise ValueError('lyrics must be a string')
    # Normalize newlines and strip excessive whitespace at ends
    normalized = raw_lyrics.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse 3+ blank lines to at most 2 to save tokens
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = normalized.strip()
    # Basic size guardrails (rough, helps control LLM cost)
    if len(normalized) == 0:
        raise ValueError('lyrics must not be empty')
    if len(normalized) > 20000:
        raise ValueError('lyrics too long; please provide fewer than 20,000 characters')
    return normalized

def _configure_gemini() -> None:
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        # Fail clearly so users set the environment variable securely
        raise RuntimeError('GEMINI_API_KEY environment variable is not set')
    if genai is None:
        raise RuntimeError('google-generativeai package is not installed')
    genai.configure(api_key=api_key)

def _call_gemini_lyrics_meaning(lyrics: str, song_id: int | None, custom_instructions: str = None) -> dict:
    _configure_gemini()
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Base prompt with schema and rules
    base_prompt = (
        "You are given song lyrics. Produce ONLY valid JSON matching EXACTLY this schema, "
        "with no markdown, no commentary, and no extra keys.\n\n"
        "Schema: {\n"
        "  \"songId\": number | null,\n"
        "  \"lyricsMeaning\": [\n"
        "    { \"LineNo\": number, \"Line\": string, \"Type\": \"Lyric\" | \"Meaning\" | \"Stanza\" }\n"
        "  ]\n"
        "}\n\n"
        "Rules:\n"
        "- Start LineNo at 0 and increment by 1 for each item in lyricsMeaning; strictly ascending.\n"
        "- For each non-empty lyric line from the input, include one Lyric entry with the original line text.\n"
        "- Immediately after each Lyric entry, include a Meaning entry explaining ONLY that lyric line concisely.\n"
        "- After each group of 4-5 lyric/meaning pairs, insert one Stanza entry summarizing the preceding group.\n"
        "- Omit Meaning/Stanza for purely blank lines; skip empty lines in Lyric entries.\n"
        "- Keep explanations faithful, concise, and neutral.\n"
        "- Output must be minified JSON (no code fences).\n\n"
    )
    
    # Add custom instructions if provided
    if custom_instructions:
        base_prompt += f"Additional Instructions:\n{custom_instructions}\n\n"
    
    # Complete prompt with lyrics and songId
    prompt = (
        f"{base_prompt}"
        "Input lyrics begin after this line:\n"
        "================================\n"
        f"{lyrics}\n"
        "================================\n"
        f"songId to include: {song_id if song_id is not None else 'null'}\n"
    )
    
    response = model.generate_content(
        prompt,
        generation_config={
            'temperature': 0.4,
            'top_p': 0.9,
            'max_output_tokens': 4096,
            'response_mime_type': 'application/json',
        },
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.4,
                'top_p': 0.9,
                'max_output_tokens': 4096,
                'response_mime_type': 'application/json',
            },
        )
    except Exception as e:
        error_msg = str(e)
        if 'quota' in error_msg.lower() or '429' in error_msg:
            raise RuntimeError('Gemini API quota exceeded. Please wait a few minutes or upgrade your plan.')
        elif 'rate' in error_msg.lower():
            raise RuntimeError('Gemini API rate limit exceeded. Please wait before retrying.')
        else:
            raise RuntimeError(f'Gemini API error: {error_msg}')

    text = getattr(response, 'text', None)
    if not text:
        raise RuntimeError('Gemini returned an empty response')

    # Some models may still wrap JSON in fences; try to sanitize
    cleaned = text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3].strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        # Best-effort: remove stray trailing commas and try again
        cleaned2 = re.sub(r",\s*([}\]])", r"\1", cleaned)
        try:
            payload = json.loads(cleaned2)
        except json.JSONDecodeError:
            raise RuntimeError('Gemini returned invalid JSON format')

    # Basic schema checks
    if not isinstance(payload, dict) or 'lyricsMeaning' not in payload:
        raise RuntimeError('Invalid model output: missing lyricsMeaning')
    if not isinstance(payload.get('lyricsMeaning'), list):
        raise RuntimeError('Invalid model output: lyricsMeaning must be an array')
    return payload

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

@app.route('/api/lyrics/meaning', methods=['POST'])
def get_lyrics_meaning():
    """
    Get line-by-line meaning for provided lyrics via Gemini.

    Request body:
    {
        "lyrics": "string",                    // required: full lyrics text
        "songId": 123,                         // optional: number to echo back
        "title": "string",                     // optional
        "artist": "string",                    // optional
        "customInstructions": "string"         // optional: custom instructions for Gemini
    }

    Example customInstructions:
    - "Focus on emotional interpretation and metaphors"
    - "Explain cultural references and historical context"
    - "Keep meanings simple and accessible for children"
    - "Highlight literary devices like alliteration and rhyme"
    - "Focus on the song's message and life lessons"
    
    Note: Custom instructions allow you to control the analysis style for each request.
    Use them to focus on specific aspects like emotions, metaphors, cultural context, etc.

    Response:
    {
        "success": true,
        "data": {
            "songId": 123 | null,
            "lyricsMeaning": [
               {"LineNo": 0, "Line": "...", "Type": "Lyric"|"Meaning"|"Stanza"}
            ]
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body is required'}), 400

        raw_lyrics = data.get('lyrics', '')
        song_id = data.get('songId')
        custom_instructions = data.get('customInstructions')  # New field for custom instructions

        lyrics = _normalize_and_validate_lyrics(raw_lyrics)

        payload = _call_gemini_lyrics_meaning(
            lyrics, 
            song_id if isinstance(song_id, int) else None,
            custom_instructions
        )

        return jsonify({
            'success': True,
            'data': payload
        })
    except (ValueError, RuntimeError) as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Lyrics Extractor API',
        'version': '1.0.0',
        'endpoints': {
            'lyrics': '/api/lyrics (POST)',
            'lyrics_meaning': '/api/lyrics/meaning (POST)',
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
            'lyrics_meaning': '/api/lyrics/meaning (POST)',
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