from flask import Flask, render_template, request
import csv
from collections import defaultdict
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords  # Optional for stop word removal
from nltk.stem import PorterStemmer  # Optional for stemming

app = Flask(__name__)


# Function to extract skills from a CSV row
def extract_skills_from_row(row):
    skills_str = row['skills']  # Assuming 'skills' is the column containing skills
    skills = skills_str.strip('[]').replace('"', '').split(',')  # Basic split
    return skills


def extract_location_from_row(row):
    location_str = row.get('location')  # Location is optional (use .get)
    if location_str:
        locations = location_str.strip().split(',')  # Handle comma-separated locations
        return locations[0]  # Return the first location (assuming primary)
    else:
        return None  # Return None if no location is present


# Function to extract skills from user input (using NLTK)
def extract_user_skills(text):
    # Tokenize the user input (split into words)
    tokens = word_tokenize(text.lower())

    # Remove stop words (optional)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]

    # Apply stemming (optional)
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return stemmed_tokens


# Function to read data from CSV and retrieve related jobs
def retrieve_info_from_csv(user_skills, user_location):
    jobs = []
    job_skills_dict = defaultdict(list)  # Store skills efficiently for each job ID

    try:
        with open("job_data_csv.csv", 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row['_id']  # Assuming 'id' is the unique identifier
                skills = extract_skills_from_row(row)
                location = extract_location_from_row(row)
                jobs.append(row)
                job_skills_dict[job_id].extend(skills)
    except FileNotFoundError:
        print("Error: CSV file not found!")
        return render_template('error.html')  # Redirect to an error page (optional)

    matched_jobs = []
    for job in jobs:
        job_id = job['_id']
        job_skills = job_skills_dict[job_id]
        job_location = extract_location_from_row(job)

        # Filter based on skills (consider both user_location and no location)
        if (any(skill in job_skills for skill in user_skills) and
                (not user_location or user_location.strip() == job_location or not job_location)):
            match_count = sum(skill in job_skills for skill in user_skills)
            total_len = len(user_skills) + len(job_skills)
            if total_len > 0 and match_count > 0:  # Filter jobs with at least one matching skill
                job['rank'] = match_count / total_len
                matched_jobs.append(job)

    matched_jobs.sort(key=lambda job: job['rank'], reverse=True)

    # Handle no matching jobs scenario
    if not matched_jobs:
        no_match_message = "No jobs found matching your criteria. Try adjusting your skills or location."
    else:
        no_match_message = None

    return render_template('show_job.html', jobs=matched_jobs, user_skills=user_skills,
                           user_location=user_location, no_match_message=no_match_message)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['skills']  # Assuming skills are retrieved from a form element with name 'skills'
    location = request.form.get('location')  # Assuming location is retrieved (optional)

 

    # Basic validation (optional)
    if not text:
        return "Please enter your skills separated by commas."

    user_skills = [skill.strip() for skill in text.split(',')]  # Remove leading/trailing whitespace

    return retrieve_info_from_csv(user_skills, location)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
