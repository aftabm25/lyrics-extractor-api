# 🚀 Railway Deployment Guide

## Quick Setup (5 minutes)

### 1. Create Railway Account
- Go to [railway.app](https://railway.app)
- Sign up with GitHub (recommended)

### 2. Connect Your Repository
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose your repository

### 3. Deploy
- Railway will automatically detect Python
- It will install dependencies from `requirements.txt`
- Use `Procfile` to run the app

### 4. Get Your URL
- Railway provides a public URL (e.g., `https://your-app.railway.app`)
- Update your frontend to use this URL

## 🔧 Configuration

### Environment Variables (Optional)
Railway automatically detects your code, but you can add:
- `PORT`: Railway sets this automatically
- `FLASK_ENV`: Set to `production`

### Custom Domain (Optional)
- Add your domain in Railway dashboard
- Railway provides free SSL certificates

## 💰 Cost
- **Free tier**: $5 credit monthly
- **Your app**: Likely under $1/month
- **Scaling**: Pay as you grow

## 🚀 Alternative: Render (Also Free)

### 1. Go to [render.com](https://render.com)
### 2. Connect GitHub repository
### 3. Choose "Web Service"
### 4. Deploy automatically

**Free tier**: 750 hours/month (enough for 24/7)

## 📱 Update Frontend

After deployment, update your frontend API calls:

```javascript
// Change from localhost to your deployed URL
const API_BASE_URL = 'https://your-app.railway.app';
// or
const API_BASE_URL = 'https://your-app.onrender.com';
```

## 🎯 Why These Are Better Than Local

- **Always online**: No need to keep your computer running
- **Global access**: Anyone can use your API
- **Professional**: Production-ready infrastructure
- **Scalable**: Handles multiple users simultaneously
- **Free**: No cost for development and small apps 