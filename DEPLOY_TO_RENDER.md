# How to Deploy to Render

Follow this guide to host your PES Super League application on Render.

## Prerequisites
1. A **GitHub** account.
2. A **Render** account (https://render.com).

## Step 1: Push your code to GitHub
Make sure your latest code is pushed to a GitHub repository.
1. Initialize git (if not done):
   ```bash
   git init
   git add .
   git commit -m "Ready for deployment"
   ```
2. Create a new repository on GitHub.
3. Push your code:
   ```bash
   git remote add origin <your-github-repo-url>
   git branch -M main
   git push -u origin main
   ```

## Step 2: Create a Web Service on Render
1. Log in to your Render Dashboard.
2. Click the **"New +"** button and select **"Web Service"**.
3. Connect your GitHub account and select your repository (`pes-super-league` or whatever you named it).
4. Configure the service:
   - **Name**: Choose a name (e.g., `pes-super-league`).
   - **Region**: Select the one closest to you (e.g., Singapore, Frankfurt, Oregon).
   - **Branch**: `main` (or master).
   - **Runtime**: `Python 3`.
   - **Build Command**: `pip install -r requirements.txt` (Render usually detects this automatically).
   - **Start Command**: `gunicorn app:app` (Render usually detects this from the Procfile).

## Step 3: Configure Environment Variables
**CRITICAL:** Your app will crash if you skip this step because `SUPABASE_URL` and `SUPABASE_KEY` are not in the code (they are in `.env` which is not mistakenly uploaded to GitHub).

1. Scroll down to the **"Environment Variables"** section in the Render setup page.
2. Click **"Add Environment Variable"**.
3. Add the following keys and values (copy them from your local `.env` file):
   - Key: `SUPABASE_URL`
     Value: `...your supabase url...`
   - Key: `SUPABASE_KEY`
     Value: `...your supabase key...`
   - Key: `PYTHON_VERSION` (Optional)
     Value: `3.10.0` (or leave blank to use default)

## Step 4: Deploy
1. Click **"Create Web Service"**.
2. Render will start building your application. You can watch the logs in the dashboard.
3. Once the build finishes, you will see a green "Live" badge.
4. Click the URL provided (e.g., `https://pes-super-league.onrender.com`) to visit your live site!

## Troubleshooting
- **Build Failed?** Check the logs. Usually it means a missing dependency in `requirements.txt` (but we have checked it, it looks good).
- **Application Error (502)?** Check the "Logs" tab. If implies a database connection error, double-check your Environment Variables in Render settings.
