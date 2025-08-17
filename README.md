# 🎵 Lyrics Extractor API

A clean, production-ready Python Flask API that extracts song lyrics using Google Custom Search API.

## 🌟 Features

- **🎯 Single Responsibility**: Pure lyrics extraction API
- **🔍 Fuzzy Search**: Handles misspelled song names automatically
- **🌐 CORS Enabled**: Ready for frontend integration
- **📱 Production Ready**: Deployable to Railway, Render, Heroku, etc.
- **🔒 Secure**: Input validation and error handling
- **📊 Rich Data**: Returns lyrics with metadata (words, lines, characters)

## 🏗️ Architecture

```
backend/
├── api.py                    # Main Flask API
├── core/                     # Core functionality
│   └── working_lyrics_extractor.py  # Lyrics extraction logic
├── requirements.txt          # Python dependencies
├── Procfile                 # Railway/Heroku deployment
├── runtime.txt              # Python version specification
├── DEPLOYMENT.md            # Deployment guide
└── README.md                # This file
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd lyrics-extractor-api
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the API:**
   ```bash
   python api.py
   ```

5. **API will be available at:** `http://localhost:8080`

## 📚 API Endpoints

### `GET /`
Returns API information and usage instructions.

### `GET /api/health`
Health check endpoint.

### `POST /api/lyrics`
Get lyrics for a song.

**Request Body:**
```json
{
    "song_name": "Shape of You"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "title": "Ed Sheeran – Shape of You Lyrics | Genius Lyrics",
        "lyrics": "Full song lyrics...",
        "song_name": "Shape of You",
        "characters": 4917,
        "lines": 100,
        "words": 946
    }
}
```

## 🔧 Configuration

### Environment Variables
- `GCS_API_KEY`: Your Google Custom Search API key
- `GCS_ENGINE_ID`: Your Google Custom Search Engine ID

**Note**: These are currently hardcoded in `api.py` for development. For production, use environment variables.

## 🌐 Frontend Integration

This API is designed to be consumed by any frontend application:

```javascript
const response = await fetch('https://your-api-url.com/api/lyrics', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        song_name: 'Shape of You'
    })
});

const data = await response.json();
```

## 🚀 Deployment

### Railway (Recommended - Free)
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

### Other Platforms
- **Render**: Free tier available
- **Heroku**: Paid plans
- **Google Cloud Run**: Free tier available
- **AWS Lambda**: Serverless option

## 🧪 Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8080/api/health

# Get lyrics
curl -X POST http://localhost:8080/api/lyrics \
  -H "Content-Type: application/json" \
  -d '{"song_name": "Shape of You"}'
```

## 🔍 How It Works

1. **Search**: Uses Google Custom Search API to find lyrics pages
2. **Correct**: Automatically corrects misspelled song names
3. **Scrape**: Extracts lyrics from various websites (Genius, Lyrics sites, etc.)
4. **Return**: Clean, formatted lyrics with metadata

## 🐛 Troubleshooting

- **Port 8080 in use**: Change the port in `api.py`
- **Import errors**: Ensure all dependencies are installed
- **CORS issues**: The API has CORS enabled for all origins
- **API limits**: Google Custom Search has 100 free queries/day

## 📝 Development Notes

- Built with Flask 3.1.1
- Uses BeautifulSoup4 for web scraping
- Implements proper error handling
- Ready for production deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes. The `lyrics_extractor` module is subject to its own license terms.

## 🆘 Support

- **Issues**: Create an issue on GitHub
- **API Problems**: Check Google Custom Search API documentation
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**🎵 Ready to extract lyrics? Deploy this API and start building your frontend!** 