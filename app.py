import json
import threading
import time
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, abort
from datetime import datetime

app = Flask(__name__)

# Job categories and types
categories = ["근린상가", "단지내상가", "복합상가", "테마쇼핑몰", "기타"]
job_types = ["분양", "홍보", "관리"]

# Premium levels
premium_levels = ["상", "하", "없음"]

# Post types
post_types = ["구인", "구직"]

# In-memory job postings list
# Each job is a dictionary with details
jobs = []

# Paths for blog automation data
DATA_DIR = Path(__file__).resolve().parent / "data"
BLOG_POSTS_FILE = DATA_DIR / "blog_posts.json"
BLOG_SCHEDULE_FILE = DATA_DIR / "blog_schedule.json"

# In-memory storage for published and scheduled blog posts
blog_posts = []
scheduled_posts = []
blog_lock = threading.Lock()
blog_next_id = 0
schedule_next_id = 0
scheduler_started = False


def _ensure_data_files() -> None:
    """Create data directory and JSON files if they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)
    for path in (BLOG_POSTS_FILE, BLOG_SCHEDULE_FILE):
        if not path.exists():
            path.write_text("[]", encoding="utf-8")


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _generate_excerpt(text: str, limit: int = 150) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


def load_blog_posts() -> None:
    """Load published blog posts from disk."""
    global blog_posts, blog_next_id
    raw_posts = _read_json(BLOG_POSTS_FILE)
    posts = []
    max_id = 0
    for entry in raw_posts:
        try:
            publish_at = datetime.fromisoformat(entry.get("publish_at"))
        except (TypeError, ValueError):
            continue
        created_at = entry.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_at) if created_at else publish_at
        except ValueError:
            created_at = publish_at
        post_id = entry.get("id")
        if post_id is None:
            post_id = len(posts)
        posts.append({
            "id": post_id,
            "title": entry.get("title", ""),
            "content": entry.get("content", ""),
            "tags": entry.get("tags", []),
            "excerpt": entry.get("excerpt") or _generate_excerpt(entry.get("content", "")),
            "publish_at": publish_at,
            "created_at": created_at,
        })
        max_id = max(max_id, post_id)
    posts.sort(key=lambda p: p["publish_at"], reverse=True)
    blog_posts = posts
    blog_next_id = max_id + 1


def load_scheduled_posts() -> None:
    """Load scheduled blog posts from disk."""
    global scheduled_posts, schedule_next_id
    raw_schedule = _read_json(BLOG_SCHEDULE_FILE)
    schedule = []
    max_id = 0
    for entry in raw_schedule:
        try:
            publish_at = datetime.fromisoformat(entry.get("publish_at"))
        except (TypeError, ValueError):
            continue
        created_at = entry.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_at) if created_at else datetime.now()
        except ValueError:
            created_at = datetime.now()
        schedule_id = entry.get("id")
        if schedule_id is None:
            schedule_id = len(schedule)
        schedule.append({
            "id": schedule_id,
            "title": entry.get("title", ""),
            "content": entry.get("content", ""),
            "tags": entry.get("tags", []),
            "excerpt": entry.get("excerpt") or _generate_excerpt(entry.get("content", "")),
            "publish_at": publish_at,
            "created_at": created_at,
        })
        max_id = max(max_id, schedule_id)
    schedule.sort(key=lambda p: p["publish_at"])
    scheduled_posts = schedule
    schedule_next_id = max_id + 1


def save_blog_posts() -> None:
    data = []
    for post in blog_posts:
        data.append({
            "id": post["id"],
            "title": post.get("title", ""),
            "content": post.get("content", ""),
            "tags": post.get("tags", []),
            "excerpt": post.get("excerpt", ""),
            "publish_at": post["publish_at"].isoformat(),
            "created_at": post.get("created_at", post["publish_at"]).isoformat(),
        })
    _write_json(BLOG_POSTS_FILE, data)


def save_scheduled_posts() -> None:
    data = []
    for entry in scheduled_posts:
        data.append({
            "id": entry["id"],
            "title": entry.get("title", ""),
            "content": entry.get("content", ""),
            "tags": entry.get("tags", []),
            "excerpt": entry.get("excerpt", ""),
            "publish_at": entry["publish_at"].isoformat(),
            "created_at": entry.get("created_at", datetime.now()).isoformat(),
        })
    _write_json(BLOG_SCHEDULE_FILE, data)


def publish_due_posts() -> None:
    """Publish scheduled posts whose time has arrived."""
    global blog_next_id, scheduled_posts
    now = datetime.now()
    with blog_lock:
        if not scheduled_posts:
            return
        remaining = []
        new_posts = []
        for entry in scheduled_posts:
            if entry["publish_at"] <= now:
                new_posts.append({
                    "id": blog_next_id,
                    "title": entry.get("title", ""),
                    "content": entry.get("content", ""),
                    "tags": entry.get("tags", []),
                    "excerpt": entry.get("excerpt") or _generate_excerpt(entry.get("content", "")),
                    "publish_at": entry["publish_at"],
                    "created_at": entry.get("created_at", entry["publish_at"]),
                })
                blog_next_id += 1
            else:
                remaining.append(entry)
        if not new_posts:
            return
        scheduled_posts = remaining
        blog_posts.extend(new_posts)
        blog_posts.sort(key=lambda p: p["publish_at"], reverse=True)
        save_blog_posts()
        save_scheduled_posts()


def _scheduler_loop(interval: int = 30) -> None:
    """Background loop that continuously publishes due posts."""
    while True:
        publish_due_posts()
        time.sleep(interval)


def start_scheduler() -> None:
    """Start the background scheduler once."""
    global scheduler_started
    if scheduler_started:
        return
    scheduler_started = True
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()


_ensure_data_files()
load_blog_posts()
load_scheduled_posts()
publish_due_posts()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jobs')
def job_list():
    category = request.args.get('category', '')
    job_type = request.args.get('job_type', '')
    q = request.args.get('q', '').lower()
    post_type = request.args.get('type', '')

    filtered = []
    for job in jobs:
        if category and job['category'] != category:
            continue
        if post_type and job.get('post_type') != post_type:
            continue
        if job_type and job['job_type'] != job_type:
            continue
        text = f"{job['title']} {job['company']} {job['description']}"
        if q and q not in text.lower():
            continue
        filtered.append(job)

    premium_top = [j for j in filtered if j.get('premium') == '상']
    premium_bottom = [j for j in filtered if j.get('premium') == '하']
    normal_jobs = [j for j in filtered if j.get('premium') not in ('상', '하')]

    return render_template(
        'jobs.html',
        premium_top=premium_top,
        premium_bottom=premium_bottom,
        jobs=normal_jobs,
        categories=categories,
        job_types=job_types,
        premium_levels=premium_levels,
        post_types=post_types,
        selected_type=post_type,
        selected_category=category,
        selected_job_type=job_type,
        search_query=q,
    )

@app.route('/jobs/<int:job_id>')
def job_detail(job_id: int):
    job = next((j for j in jobs if j['id'] == job_id), None)
    if not job:
        abort(404)
    return render_template('job_detail.html', job=job, job_id=job_id)

@app.route('/jobs/map')
def job_map():
    return render_template('jobs_map.html', jobs=jobs)

@app.route('/jobs/delete/<int:job_id>', methods=['POST'])
def job_delete(job_id: int):
    idx = next((i for i, j in enumerate(jobs) if j['id'] == job_id), None)
    if idx is None:
        abort(404)
    jobs.pop(idx)
    return redirect(url_for('job_list'))

@app.route('/jobs/new', methods=['POST'])
def job_new():
    title = request.form.get('title')
    company = request.form.get('company')
    category = request.form.get('category')
    job_type = request.form.get('job_type')
    description = request.form.get('description')
    location = request.form.get('location')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    contact = request.form.get('contact')
    premium = request.form.get('premium', '없음')
    post_type = request.form.get('post_type', '구인')
    if title and company:
        lat_val = float(lat) if lat else None
        lng_val = float(lng) if lng else None
        jobs.append({
            'id': len(jobs),
            'title': title,
            'company': company,
            'category': category or '',
            'job_type': job_type or '',
            'description': description,
            'location': location,
            'lat': lat_val,
            'lng': lng_val,
            'contact': contact or '',
            'premium': premium,
            'post_type': post_type,
            'date_posted': datetime.utcnow()
        })
    return redirect(url_for('job_list'))


@app.route('/blog')
def blog_list():
    publish_due_posts()
    with blog_lock:
        posts = list(blog_posts)
    return render_template('blog_list.html', posts=posts)


@app.route('/blog/<int:post_id>')
def blog_detail(post_id: int):
    publish_due_posts()
    with blog_lock:
        post = next((p for p in blog_posts if p['id'] == post_id), None)
    if not post:
        abort(404)
    return render_template('blog_detail.html', post=post)


@app.route('/blog/schedule', methods=['GET', 'POST'])
def blog_schedule():
    error = None
    status = request.args.get('status')
    form_data = {}
    publish_due_posts()
    if request.method == 'POST':
        form_data = request.form.to_dict()
        title = form_data.get('title', '').strip()
        content = form_data.get('content', '').strip()
        excerpt = form_data.get('excerpt', '').strip()
        tags_raw = form_data.get('tags', '')
        publish_at_raw = form_data.get('publish_at', '').strip()

        if not title or not content or not publish_at_raw:
            error = '제목, 내용, 발행일시는 필수입니다.'
        else:
            try:
                publish_at = datetime.fromisoformat(publish_at_raw)
            except ValueError:
                error = '발행일시는 YYYY-MM-DD HH:MM 형식으로 입력해 주세요.'

        if not error:
            tags = [tag.strip() for tag in tags_raw.split(',') if tag.strip()]
            excerpt_value = excerpt or _generate_excerpt(content)
            with blog_lock:
                global schedule_next_id
                scheduled_posts.append({
                    'id': schedule_next_id,
                    'title': title,
                    'content': content,
                    'tags': tags,
                    'excerpt': excerpt_value,
                    'publish_at': publish_at,
                    'created_at': datetime.now(),
                })
                schedule_next_id += 1
                scheduled_posts.sort(key=lambda p: p['publish_at'])
                save_scheduled_posts()
            return redirect(url_for('blog_schedule', status='created'))

    with blog_lock:
        scheduled = list(scheduled_posts)
    return render_template(
        'blog_schedule.html',
        scheduled=scheduled,
        status=status,
        error=error,
        form_data=form_data,
    )


@app.route('/blog/schedule/delete/<int:schedule_id>', methods=['POST'])
def blog_schedule_delete(schedule_id: int):
    with blog_lock:
        idx = next((i for i, entry in enumerate(scheduled_posts) if entry['id'] == schedule_id), None)
        if idx is None:
            abort(404)
        scheduled_posts.pop(idx)
        save_scheduled_posts()
    return redirect(url_for('blog_schedule', status='deleted'))


@app.before_first_request
def initialize_scheduler():
    start_scheduler()

if __name__ == '__main__':
    app.run(debug=True)
