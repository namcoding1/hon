from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)

# In-memory job postings list
jobs = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/jobs')
def job_list():
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/new', methods=['POST'])
def job_new():
    title = request.form.get('title')
    company = request.form.get('company')
    description = request.form.get('description')
    location = request.form.get('location')
    if title and company:
        jobs.append({
            'title': title,
            'company': company,
            'description': description,
            'location': location,
            'date_posted': datetime.utcnow()
        })
    return redirect(url_for('job_list'))

if __name__ == '__main__':
    app.run(debug=True)
