# 🚀 Railway.app Deployment Guide

## FREE HOSTING with $5/month credit

### Step 1: Prepare Your Project
```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit for Railway deployment"
```

### Step 2: Create Railway Account & Project
1. Go to [railway.app](https://railway.app)
2. Sign up (free)
3. Click "Create New Project"
4. Select "Deploy from GitHub"
   - OR use "Deploy from Git" for private repos
   - OR use "CLI Deploy" if you prefer command line

### Step 3: Set Up MySQL Database on Railway
1. In your Railway project dashboard
2. Click "Add Service"
3. Select "MySQL"
4. Railway will automatically provision a MySQL database
5. Copy the database credentials (they'll be in your environment)

### Step 4: Configure Environment Variables
In Railway dashboard, add these variables:

```
DB_HOST=<your-railway-mysql-host>
DB_USER=<your-railway-mysql-user>
DB_PASSWORD=<your-railway-mysql-password>
DB_NAME=quizmasterpro
DB_PORT=3306
SECRET_KEY=your-secret-key-here-make-it-strong
DEBUG=False
HOST=0.0.0.0
```

**Get these from Railroad's MySQL service details**

### Step 5: Deploy via CLI (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link your project
railway link

# Deploy
railway up

# View logs
railway logs
```

### Step 6: Initialize Database on Railway
After deployment:
```bash
# Connect to your Railway app and initialize DB
railway run python -c "from database import init_database; init_database()"
```

OR via Railway dashboard:
1. Go to Deployments
2. Click your deployment
3. Open "Shell"
4. Run: `python -c "from database import init_database; init_database()"`

### Step 7: Access Your App
Your app will be live at: `https://your-project-name.railway.app`

---

## Alternative: Render.com (Also Free)
If Railway doesn't work, use Render.com:
1. Connect GitHub repo
2. Select "Python" environment
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn --worker-class eventlet -w 1 app:app`
5. Add PostgreSQL (free tier included)

---

## Troubleshooting

**Issue: Database connection timeout**
- Check if MySQL credentials are correct
- Ensure IP whitelist allows Railway servers (usually automatic)

**Issue: WebSocket not connecting**
- Ensure `async_mode='threading'` is set (✓ already configured)
- Check browser console for connection errors

**Issue: App crashes after deploy**
- View logs: `railway logs`
- Check all environment variables are set
- Run database init command

---

## Cost
- **Free tier**: Includes $5/month credit
- **After free credit**: ~$10-20/month depending on usage
- Most hobby projects stay within free tier
