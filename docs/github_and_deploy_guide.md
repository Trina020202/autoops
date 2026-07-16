# GitHub and Deployment Guide

Use this after you review the local demo and confirm it runs.

## 1. Create a GitHub repository

1. Go to GitHub.
2. Click `New repository`.
3. Repository name: `autoops`.
4. Visibility: public if you want recruiters to open it, private if you only want to share on request.
5. Do not add another README because this project already has one.
6. Create the repository.

## 2. Push local code

Run these commands inside the `autoops` folder:

```bash
git init
git add .
git commit -m "Build AutoOps full-stack MVP"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/autoops.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

## 3. Add screenshots

1. Start the app locally.
2. Open `http://127.0.0.1:5000`.
3. Take screenshots of:
   - Login page
   - Dashboard
   - Vehicle management
   - Create sale
   - Sales management
4. Put screenshots in `docs/screenshots/`.
5. Add them to README later.

## 4. Deploy to Render

Render works well for a quick Flask demo.

The repository now includes `render.yaml`, so the easiest path is to create a Render Blueprint from the GitHub repository. Render will read the service name, runtime, build command, start command, and environment variables from that file.

### Option A: Blueprint deploy

1. Push the latest code to GitHub.
2. Go to Render.
3. Choose `New` -> `Blueprint`.
4. Connect the `Trina020202/autoops` GitHub repository.
5. Confirm the detected service named `autoops`.
6. Click `Apply` or `Deploy`.
7. Wait until the deploy status becomes `Live`.

### Option B: Manual Web Service deploy

1. Push code to GitHub first.
2. Go to Render and create a new Web Service.
3. Connect the GitHub repository.
4. Runtime: Python.
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
gunicorn app:app
```

7. Add environment variable:

```text
SECRET_KEY=use-a-long-random-secret
AUTOOPS_DATABASE=/tmp/autoops.sqlite
```

8. Deploy.

After deployment, open the Render URL and sign in with:

```text
demo@autoops.local
autoops123
```

Only add the live demo link to your resume after the Render URL opens successfully.

## 5. PostgreSQL upgrade path

The current MVP uses SQLite to keep the project fast and easy to run locally. If a job description strongly expects PostgreSQL, upgrade after the MVP is stable:

1. Add SQLAlchemy or psycopg.
2. Replace `app/db.py` with a PostgreSQL connection layer.
3. Create a managed PostgreSQL database on Render.
4. Put the external database URL in an environment variable.
5. Update README and resume wording only after the deployed PostgreSQL version works.

Do not claim PostgreSQL deployment on your resume until that version is actually live.
