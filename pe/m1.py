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


def extract_experience_from_row(row):
    experience_str = row.get('experience')  # Experience is optional (use .get)
    if experience_str:
        return experience_str.lower()  # Convert to lowercase for comparison
    else:
        return None  # Return None if no experience is present


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
def retrieve_info_from_csv(user_skills, user_location, user_experience):
    jobs = []
    job_skills_dict = defaultdict(list)  # Store skills efficiently for each job ID

    try:
        with open("job_data_csv.csv", 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_id = row['_id']  # Assuming 'id' is the unique identifier
                skills = extract_skills_from_row(row)
                location = extract_location_from_row(row)
                experience_str = extract_experience_from_row(row).lower()  # Convert to lowercase
                jobs.append(row)
                job_skills_dict[job_id].extend(skills)
    except FileNotFoundError:
        print("Error: CSV file not found!")
        return render_template('error.html')  # Redirect to an error page (optional)

    matched_jobs = []
    top_matched_jobs = []  # List to store jobs with all skills

    for job in jobs:
        job_id = job['_id']
        job_skills = job_skills_dict[job_id]
        job_location = extract_location_from_row(job)
        job_experience = extract_experience_from_row(job).lower()  # Convert to lowercase

        # Filter based on skills, location (consider both user_location and no location), and experience
        # Handle incomplete user input and case-insensitivity
        user_experience_lower = user_experience.lower() if user_experience else None
        if (any(skill in job_skills for skill in user_skills) and
                (not user_location or user_location.strip() == job_location or not job_location) and
                (not user_experience_lower or
                 (user_experience_lower in ("fresher", "experienced") and
                  (user_experience_lower == job_experience)))):
            match_count = sum(skill in job_skills for skill in user_skills)
            total_len = len(user_skills) + len(job_skills)
            if total_len > 0 and match_count > 0:  # Filter jobs with at least one matching skill
                job['rank'] = match_count / total_len

                # Check if
                # Check if all skills are present, add to top_matched_jobs if yes
                if all(skill in job_skills for skill in user_skills):
                    top_matched_jobs.append(job)
                else:
                    matched_jobs.append(job)

    # Sort jobs (top_matched_jobs first, then others)
    matched_jobs.sort(key=lambda job: job['rank'], reverse=True)
    top_matched_jobs.sort(key=lambda job: job['rank'], reverse=True)
    jobs = top_matched_jobs + matched_jobs

    # Handle no matching jobs scenario
    if not jobs:
        no_match_message = "No jobs found matching your criteria. Try adjusting your skills, location, or experience."
    else:
        no_match_message = None

    return render_template('show_job.html', jobs=jobs, user_skills=user_skills,
                           user_location=user_location, user_experience=user_experience,
                           no_match_message=no_match_message)


@app.route('/')
def hello():
    return render_template('i.html')


@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['skills']  # Assuming skills are retrieved from a form element with name 'skills'
    location = request.form.get('location')  # Assuming location is retrieved (optional)
    experience = request.form.get('experience')  # Assuming experience is retrieved from a dropdown (optional)

    # Basic validation (check if skills are provided)
    if not text:
        return render_template('error.html', message="Please enter your skills.")  # Redirect to an error page

    # Extract user skills (optional: clean and process user input)
    user_skills = extract_user_skills(text)  # Utilize the function for processing

    return retrieve_info_from_csv(user_skills, location, experience)


if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask development server
