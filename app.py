from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# Job categories and types
categories = ["근린상가", "단지내상가", "복합상가", "테마쇼핑몰", "기타"]
job_types = ["분양", "홍보", "관리"]

# In-memory job postings list
jobs = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jobs')
def job_list():
    category = request.args.get('category', '')
    q = request.args.get('q', '').lower()

    filtered = []
    for job in jobs:
        if category and job['category'] != category:
            continue
        text = f"{job['title']} {job['company']} {job['description']}"
        if q and q not in text.lower():
            continue
        filtered.append(job)

    return render_template(
        'jobs.html',
        jobs=filtered,
        categories=categories,
        job_types=job_types,
        selected_category=category,
        search_query=q,
    )

@app.route('/jobs/new', methods=['POST'])
def job_new():
    title = request.form.get('title')
    company = request.form.get('company')
    category = request.form.get('category')
    job_type = request.form.get('job_type')
    description = request.form.get('description')
    location = request.form.get('location')
    if title and company:
        jobs.append({
            'title': title,
            'company': company,
            'category': category or '',
            'job_type': job_type or '',
            'description': description,
            'location': location,
            'date_posted': datetime.utcnow()
        })
    return redirect(url_for('job_list'))

if __name__ == '__main__':
    app.run(debug=True)
