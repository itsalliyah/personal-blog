import os
import re
import sqlite3
from datetime import datetime
from functools import wraps

import uuid

from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import markdown as md

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "blog.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-this-in-production")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    """Save an uploaded image with a unique name, return its public URL path (or None)."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        flash(f'"{file_storage.filename}" isn\'t a supported image type (use png, jpg, gif, or webp).')
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, unique_name))
    return url_for("static", filename=f"uploads/{unique_name}")


# ---------- Database helpers ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL DEFAULT 'Your Name',
            bio TEXT NOT NULL DEFAULT 'Write something about yourself here.',
            avatar_url TEXT NOT NULL DEFAULT '',
            banner_url TEXT NOT NULL DEFAULT '',
            contact_email TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS post (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )
    # Migration: older databases won't have this column yet — add it if missing.
    try:
        db.execute("ALTER TABLE user ADD COLUMN banner_url TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        db.execute("ALTER TABLE user ADD COLUMN contact_email TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        db.execute("ALTER TABLE post ADD COLUMN category TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    # Migration: earlier versions of this project called it "cover_url" —
    # carry that value over so nobody loses their uploaded image.
    try:
        cols = [r[1] for r in db.execute("PRAGMA table_info(user)").fetchall()]
        if "cover_url" in cols:
            db.execute("UPDATE user SET banner_url = cover_url WHERE banner_url = '' AND cover_url != ''")
    except sqlite3.OperationalError:
        pass
    db.commit()
    db.close()


# Run once on import, so this works whether started via `python app.py`
# (local) or via gunicorn (hosted) — gunicorn never executes the
# `if __name__ == "__main__"` block below.
init_db()


# ---------- Helpers ----------

def slugify(title):
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug or "post"


def unique_slug(db, title, ignore_id=None):
    base = slugify(title)
    slug = base
    i = 2
    while True:
        row = db.execute(
            "SELECT id FROM post WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None or (ignore_id is not None and row["id"] == ignore_id):
            return slug
        slug = f"{base}-{i}"
        i += 1


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_site_owner():
    db = get_db()
    user = db.execute("SELECT * FROM user LIMIT 1").fetchone()
    return {"site_owner": user, "logged_in": bool(session.get("user_id"))}


# ---------- Public routes ----------

@app.route("/")
def index():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM post WHERE published = 1 ORDER BY created_at DESC"
    ).fetchall()
    return render_template("index.html", posts=posts)


@app.route("/post/<slug>")
def view_post(slug):
    db = get_db()
    post = db.execute("SELECT * FROM post WHERE slug = ?", (slug,)).fetchone()
    if post is None:
        abort(404)
    if not post["published"] and not session.get("user_id"):
        abort(404)
    html_content = md.markdown(post["content"], extensions=["fenced_code", "tables"])
    return render_template("post.html", post=post, html_content=html_content)


@app.route("/profile")
def profile():
    db = get_db()
    user = db.execute("SELECT * FROM user LIMIT 1").fetchone()
    if user is None:
        abort(404)
    return render_template("profile.html", user=user)


@app.route("/contact")
def contact():
    db = get_db()
    user = db.execute("SELECT * FROM user LIMIT 1").fetchone()
    return render_template("contact.html", user=user)


@app.route("/archive")
def archive():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM post WHERE published = 1 ORDER BY created_at DESC"
    ).fetchall()

    groups = []  # [(label, [posts]), ...] grouped by Month Year
    current_label = None
    current_bucket = None
    for post in posts:
        dt = datetime.fromisoformat(post["created_at"])
        label = dt.strftime("%B %Y")
        if label != current_label:
            current_label = label
            current_bucket = []
            groups.append((label, current_bucket))
        current_bucket.append(post)

    categories = db.execute(
        "SELECT category, COUNT(*) as count FROM post "
        "WHERE published = 1 AND category != '' GROUP BY category ORDER BY category"
    ).fetchall()

    return render_template("archive.html", groups=groups, categories=categories)


@app.route("/category/<name>")
def by_category(name):
    db = get_db()
    posts = db.execute(
        "SELECT * FROM post WHERE published = 1 AND category = ? ORDER BY created_at DESC",
        (name,),
    ).fetchall()
    return render_template("category.html", posts=posts, category=name)


# ---------- Auth ----------

@app.route("/setup", methods=["GET", "POST"])
def setup():
    """One-time account creation for hosted deployments where you can't run
    init_admin.py directly on the server. Locks itself once an account exists."""
    db = get_db()
    existing = db.execute("SELECT * FROM user LIMIT 1").fetchone()
    if existing:
        flash("An account already exists — log in instead.")
        return redirect(url_for("login"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or len(password) < 6:
            error = "Choose a username and a password of at least 6 characters."
        else:
            from werkzeug.security import generate_password_hash
            db.execute(
                "INSERT INTO user (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
            flash("Account created — log in below.")
            return redirect(url_for("login"))
    return render_template("setup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    db = get_db()
    if db.execute("SELECT id FROM user LIMIT 1").fetchone() is None:
        return redirect(url_for("setup"))
    error = None
    if request.method == "POST":
        db = get_db()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        error = "Incorrect username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- Admin / dashboard (owner only) ----------

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    posts = db.execute("SELECT * FROM post ORDER BY created_at DESC").fetchall()
    return render_template("dashboard.html", posts=posts)


@app.route("/dashboard/upload-image", methods=["POST"])
@login_required
def upload_image():
    """Used by the post editor's 'Insert image' button — uploads a picture
    and returns its URL as JSON so it can be inserted into the Markdown
    content without leaving the page."""
    file_storage = request.files.get("image")
    if not file_storage or file_storage.filename == "":
        return {"error": "No file selected."}, 400
    if not allowed_file(file_storage.filename):
        return {"error": "Unsupported file type — use png, jpg, gif, or webp."}, 400
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, unique_name))
    url = url_for("static", filename=f"uploads/{unique_name}")
    return {"url": url}


@app.route("/dashboard/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        db = get_db()
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "").strip()
        published = 1 if request.form.get("published") else 0
        if not title or not content:
            flash("Title and content are required.")
            return render_template("edit_post.html", post=None)
        slug = unique_slug(db, title)
        now = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO post (title, slug, content, category, published, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, slug, content, category, published, now, now),
        )
        db.commit()
        flash("Post created.")
        return redirect(url_for("dashboard"))
    return render_template("edit_post.html", post=None)


@app.route("/dashboard/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM post WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        category = request.form.get("category", "").strip()
        published = 1 if request.form.get("published") else 0
        if not title or not content:
            flash("Title and content are required.")
            return render_template("edit_post.html", post=post)
        slug = unique_slug(db, title, ignore_id=post_id)
        now = datetime.utcnow().isoformat()
        db.execute(
            "UPDATE post SET title=?, slug=?, content=?, category=?, published=?, updated_at=? WHERE id=?",
            (title, slug, content, category, published, now, post_id),
        )
        db.commit()
        flash("Post updated.")
        return redirect(url_for("dashboard"))
    return render_template("edit_post.html", post=post)


@app.route("/dashboard/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (post_id,))
    db.commit()
    flash("Post deleted.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    db = get_db()
    user = db.execute("SELECT * FROM user WHERE id = ?", (session["user_id"],)).fetchone()
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip() or "Your Name"
        bio = request.form.get("bio", "").strip()
        contact_email = request.form.get("contact_email", "").strip()

        # Start with whatever is already saved, then overwrite only if the
        # person uploaded a new photo this time.
        avatar_url = user["avatar_url"]
        banner_url = user["banner_url"]

        new_avatar = save_upload(request.files.get("avatar_file"))
        if new_avatar:
            avatar_url = new_avatar

        new_banner = save_upload(request.files.get("banner_file"))
        if new_banner:
            banner_url = new_banner

        if request.form.get("remove_avatar"):
            avatar_url = ""
        if request.form.get("remove_banner"):
            banner_url = ""

        db.execute(
            "UPDATE user SET display_name=?, bio=?, avatar_url=?, banner_url=?, contact_email=? WHERE id=?",
            (display_name, bio, avatar_url, banner_url, contact_email, user["id"]),
        )
        db.commit()
        flash("Profile updated.")
        return redirect(url_for("profile"))
    return render_template("edit_profile.html", user=user)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
