# Your Journal — a single-author blog

A small Flask + SQLite blog with:
- **One login only** — you. There's no sign-up page, no way for anyone else to create an account.
- **Journal page** (`/`) — list of your published posts.
- **Individual post pages** (`/post/<slug>`) — each post gets its own URL, written in Markdown.
- **Profile page** (`/profile`) — public "about me" page with a banner/header image, avatar, name, and bio — like a social media profile.
- **Dashboard** (`/dashboard`, login required) — write, edit, publish/unpublish, and delete posts, and edit your profile.

## 1. Install

```bash
cd personal-blog
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Create your account

This is the only account the site will ever have.

```bash
python init_admin.py
```

It'll ask you to choose a username and password (stored as a secure hash, never in plain text).

## 3. Run it locally

```bash
python app.py
```

Visit `http://127.0.0.1:5000`. Log in at `/login`, then go to `/dashboard` to write your first post and fill in your profile.

For anything beyond local testing, set a real secret key instead of the default:

```bash
export SECRET_KEY="a-long-random-string"
```

## 4. Put it online (deploy to Render.com — free)

This gets you a real URL like `https://your-blog.onrender.com` that works
from any phone or computer, anywhere — not just on your home WiFi.

**a) Push your code to GitHub** (Render deploys from a GitHub repo)
1. Create a free account at https://github.com if you don't have one
2. Create a new repository (keep it Private if you'd rather)
3. In your project folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git push -u origin main
   ```
   (Don't commit `blog.db` or `venv/` — they're excluded automatically if
   you use the included `.gitignore`, or Render will just start with a
   fresh empty database, which is fine — see the setup step below.)

**b) Create the web service on Render**
1. Sign up at https://render.com (free, no credit card needed for the free tier)
2. Click **New +** → **Web Service**
3. Connect your GitHub account and select your repo
4. Render usually auto-detects Python and pre-fills these — check they match:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Choose the **Free** instance type
6. Under **Environment**, add a variable: `SECRET_KEY` = some long random string (this replaces the default one in `app.py` for security)
7. Click **Create Web Service** and wait a few minutes for the first build

**c) Create your login**
Once it's live, visit `https://your-blog.onrender.com/setup` — since there's
no way to run `init_admin.py` on Render's free tier (no shell access), this
page lets you create your one account directly from the browser. It works
exactly once: after your account exists, `/setup` locks itself and always
redirects to `/login`.

**A heads-up about Render's free tier:**
- It spins down after 15 minutes of no traffic, and the next visit takes about a minute to "wake up" — normal for free tier, not a bug.
- More importantly: the free tier's disk isn't guaranteed to persist across deploys/restarts, which means your `blog.db` (posts, login) and anything in `static/uploads/` (avatar, banner) could reset if the service redeploys. For a personal project this is usually fine to start with, but if you don't want to risk losing posts, either back up `blog.db` periodically or look into Render's paid persistent disks before you rely on this long-term.

### Other options
- **Fly.io** — similar free-tier flow to Render, also deploys from GitHub or a CLI.
- **PythonAnywhere** — free tier, good for small personal sites, upload the folder directly through their web UI (has real persistent storage).
- **A VPS** (e.g. a $4-6/mo droplet) — full control, run behind gunicorn + nginx, get HTTPS via Let's Encrypt/certbot. More setup, but storage is genuinely persistent and nothing spins down.

## Notes

- Posts support Markdown (headings, **bold**, *italic*, links, code blocks, blockquotes, images).
- Uncheck "Published" when writing a post to save it as a private draft — only visible to you while logged in.
- To change your username/password later, just run `python init_admin.py` again.
- The database is a single file, `blog.db` — back it up occasionally if your posts matter to you (copy the file somewhere safe).
- **Avatar & banner image:** go to Dashboard → Edit profile to upload your avatar (small profile picture) and banner/header image (wide header graphic) directly from your computer (png/jpg/gif/webp, up to 8MB each). The banner also appears as a hero image at the top of your homepage. You can replace or remove either one at any time. Uploaded images are stored in `static/uploads/`.
- **Want to change the look?** See `DESIGN_GUIDE.md` — it walks through customizing colors, fonts, and layout yourself, no coding experience assumed.
