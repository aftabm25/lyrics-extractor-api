#!/usr/bin/env python3
"""
Working Lyrics Extractor - Custom implementation that fixes the API endpoint issue
"""

import requests
from bs4 import BeautifulSoup
import re

class WorkingSongLyrics:
    """
    A working implementation of the lyrics extractor that uses the correct API endpoint
    """
    
    def __init__(self, gcs_api_key: str, gcs_engine_id: str):
        if not isinstance(gcs_api_key, str) or not isinstance(gcs_engine_id, str):
            raise TypeError("API key and engine ID must be strings.")
        
        self.GCS_API_KEY = gcs_api_key
        self.GCS_ENGINE_ID = gcs_engine_id
    
    def _search_for_lyrics(self, song_name: str):
        """Search for lyrics using Google Custom Search API"""
        url = "https://www.googleapis.com/customsearch/v1"  # Note: no /siterestrict
        
        params = {
            'key': self.GCS_API_KEY,
            'cx': self.GCS_ENGINE_ID,
            'q': f'{song_name} lyrics',
            'num': 10  # Get more results for better chances
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            
            data = response.json()
            
            # Check for spelling corrections
            if 'spelling' in data and 'correctedQuery' in data['spelling']:
                corrected_query = data['spelling']['correctedQuery']
                print(f"   🔍 Spelling corrected: '{song_name}' → '{corrected_query}'")
                
                # Search again with corrected query
                params['q'] = f'{corrected_query} lyrics'
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Search request failed: {e}")
        except ValueError as e:
            raise Exception(f"Invalid JSON response: {e}")
    
    def _extract_lyrics_from_url(self, url: str, title: str):
        """Extract lyrics from a given URL"""
        try:
            # Add headers to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try different scraping methods for different sites
            lyrics = self._try_genius_scraper(soup, title)
            if lyrics:
                return lyrics
            
            lyrics = self._try_lyrics_site_scraper(soup, title)
            if lyrics:
                return lyrics
            
            # Generic fallback - look for common lyrics patterns
            lyrics = self._try_generic_scraper(soup, title)
            if lyrics:
                return lyrics
            
            return None
            
        except Exception as e:
            print(f"   ⚠️  Failed to extract from {url}: {e}")
            return None
    
    def _try_genius_scraper(self, soup, title):
        """Try to extract lyrics from Genius.com"""
        try:
            # Method 1: Look for .lyrics class
            lyrics_div = soup.select_one('.lyrics')
            if lyrics_div:
                lyrics = lyrics_div.get_text().strip()
                if len(lyrics) > 100:  # Must be substantial
                    return lyrics
            
            # Method 2: Look for lyrics container divs
            lyrics_containers = soup.select('div[class*="Lyrics__Container"]')
            if lyrics_containers:
                lyrics = ''
                for container in lyrics_containers:
                    for br in container.find_all("br"):
                        br.replace_with("\n")
                    lyrics += container.get_text()
                
                if len(lyrics.strip()) > 100:
                    return lyrics.strip()
            
            return None
            
        except Exception:
            return None
    
    def _try_lyrics_site_scraper(self, soup, title):
        """Try to extract lyrics from various lyrics sites"""
        try:
            # Look for common lyrics selectors
            selectors = [
                '.lyrics-col p',
                '.lyric-content p',
                '#main_lyrics p',
                '.lyrics p',
                '[class*="lyrics"] p',
                '[id*="lyrics"] p'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    lyrics = ''
                    for element in elements:
                        lyrics += element.get_text().strip() + '\n\n'
                    
                    if len(lyrics.strip()) > 100:
                        return lyrics.strip()
            
            return None
            
        except Exception:
            return None
    
    def _try_generic_scraper(self, soup, title):
        """Generic fallback scraper"""
        try:
            # Look for text that might contain lyrics
            # Lyrics usually have repeated line breaks and are substantial
            text_blocks = soup.find_all(['p', 'div', 'span'])
            
            for block in text_blocks:
                text = block.get_text().strip()
                
                # Check if this looks like lyrics
                if (len(text) > 200 and 
                    text.count('\n') > 10 and
                    not any(word in text.lower() for word in ['copyright', 'privacy', 'terms', 'advertisement'])):
                    
                    # Clean up the text
                    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
                    text = re.sub(r'\[.*?\]', '', text)  # Remove [verse], [chorus], etc.
                    
                    return text.strip()
            
            return None
            
        except Exception:
            return None
    
    def get_lyrics(self, song_name: str):
        """
        Get lyrics for a song, even with misspelled names
        
        Args:
            song_name (str): Name of the song (can be misspelled)
            
        Returns:
            dict: Contains 'title' and 'lyrics' keys
            
        Raises:
            Exception: If lyrics cannot be found
        """
        print(f"🎵 Searching for lyrics: '{song_name}'")
        
        # Search for the song
        search_data = self._search_for_lyrics(song_name)
        
        if 'items' not in search_data or not search_data['items']:
            raise Exception("No search results found")
        
        print(f"   📊 Found {len(search_data['items'])} search results")
        
        # Try to extract lyrics from each result
        for i, item in enumerate(search_data['items']):
            url = item['link']
            title = item['title']
            
            print(f"   🔍 Trying result {i+1}: {title[:50]}...")
            
            try:
                lyrics = self._extract_lyrics_from_url(url, title)
                if lyrics:
                    print(f"   ✅ Successfully extracted lyrics from: {title}")
                    return {
                        'title': title,
                        'lyrics': lyrics
                    }
            except Exception as e:
                print(f"   ⚠️  Failed to extract from result {i+1}: {e}")
                continue
        
        raise Exception("Could not extract lyrics from any search result")

def main():
    """Test the working lyrics extractor"""
    # Your API credentials
    GCS_API_KEY = "AIzaSyCueYKFmg7Je4ywdg2ahmZ_To0AU97P0QI"
    GCS_ENGINE_ID = "e441df94c93ad4421"
    
    try:
        # Create instance
        print("🎵 Testing Working Lyrics Extractor")
        print("=" * 50)
        
        extractor = WorkingSongLyrics(GCS_API_KEY, GCS_ENGINE_ID)
        
        # Test with correct song name
        print("\n🔍 Test 1: Correct song name")
        data = extractor.get_lyrics("Shape of You")
        print(f"✅ Title: {data['title']}")
        print(f"📝 Lyrics preview: {data['lyrics'][:200]}...")
        
        # Test with misspelled song name
        print("\n🔍 Test 2: Misspelled song name")
        data_misspelled = extractor.get_lyrics("Shaep fo you")
        print(f"✅ Title: {data_misspelled['title']}")
        print(f"📝 Lyrics preview: {data_misspelled['lyrics'][:200]}...")
        print("🎉 Successfully handled misspelling!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 