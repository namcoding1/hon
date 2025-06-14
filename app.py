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

if __name__ == '__main__':
    app.run(debug=True)
