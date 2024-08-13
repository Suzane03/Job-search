from flask import Flask, render_template, request
import csv
from collections import defaultdict
import pandas as pd  # Optional for potential data manipulation (commented out)

app = Flask(__name__)

# Function to extract skills from a CSV row
def extract_skills_from_row(row):
    skills_str = row['skills']  # Assuming 'skills' is the column containing skills
    skills = skills_str.strip('[]').replace('"', '').split(',')  # Clean and split skills
    return skills

# Function to read data from CSV and retrieve related jobs
def retrieve_info_from_csv(user_skills):
    jobs = []
    job_skills_dict = defaultdict(list)  # Store skills efficiently for each job ID

    try:
        with open("jobs_data_csv.csv", 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row['_id']  # Assuming 'id' is the unique identifier
                skills = extract_skills_from_row(row)
                jobs.append(row)
                job_skills_dict[job_id].extend(skills)
    except FileNotFoundError:
        print("Error: CSV file not found!")
        return render_template('error.html')  # Redirect to an error page (optional)

    matched_jobs = []
    for job in jobs:
        job_id = job['_id']
        job_skills = job_skills_dict[job_id]
        match_count = sum(skill in user_skills for skill in job_skills)
        total_len = len(user_skills) + len(job_skills)
        if total_len > 0 and match_count > 0:  # Filter jobs with at least one matching skill
            job['rank'] = match_count / total_len
            matched_jobs.append(job)

    matched_jobs.sort(key=lambda job: job['rank'], reverse=True)
    return render_template('show_job.html', jobs=matched_jobs, user_skills=user_skills)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    # Basic validation (optional)
    if not text:
        return "Please enter your skills separated by commas."

    user_skills = [skill.strip() for skill in text.split(',')]  # Remove leading/trailing whitespace

    return retrieve_info_from_csv(user_skills)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
