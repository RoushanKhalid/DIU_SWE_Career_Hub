from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="diu_swe_career_hub"
    )

db = get_db_connection()
cursor = db.cursor()

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")  # Get API key securely

def chat_with_gpt(prompt):
    try:
        # Fetch relevant data from the database
        cursor.execute("SELECT job_title, description, requirements, salary FROM jobs")
        jobs = cursor.fetchall()
        
        # Create a context string with job information
        job_info = "\n".join([f"Job Title: {job[0]}, Description: {job[1]}, Requirements: {job[2]}, Salary: {job[3]}" for job in jobs])
        
        # Add project information
        project_info = "DIU SWE Career Hub is a platform to connect students with job opportunities. You can find job listings, apply for jobs, and get assistance from our chatbot."
        
        # Combine the context with the user prompt
        context = f"{project_info}\n\nJob Listings:\n{job_info}\n\nUser: {prompt}"
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": context}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in chat_with_gpt: {e}")
        return "Sorry, I couldn't process your request at the moment."

@app.before_request
def before_request():
    global db, cursor
    try:
        db.ping(reconnect=True, attempts=3, delay=5)
    except mysql.connector.Error:
        db = get_db_connection()
        cursor = db.cursor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    project_info = {
        "description": "DIU SWE Career Hub is a platform to connect students with job opportunities. You can find job listings, apply for jobs, and get assistance from our chatbot.",
        "contributors": [
            {"name": "Sk. Roushan Khalid", "email": "skroushankhalid.17@gmail.com", "phone": "01760535087"},
            {"name": "Morsaline Ahmed", "email": "morsaline12025@gmail.com", "phone": "01796237248"},
            {"name": "Md. Shahrul Zakaria", "email": "zakaria35-1033@diu.edu.bd", "phone": "01705716310"}
        ]
    }
    return render_template('about.html', project_info=project_info)

@app.route('/form')
def form():
    job_id = request.args.get('job_id')
    return render_template('form.html', job_id=job_id)

@app.route('/submit', methods=['POST'])
def submit():
    job_id = request.form['job_id']
    name = request.form['name']
    address = request.form['address']
    email = request.form['email']
    contact = request.form['contact']
    desired_salary = request.form['desired_salary']
    employability_desire = request.form['employability_desire']
    citizenship = request.form['citizenship']
    religion = request.form['religion']
    previous_teaching_experience = request.form['previous_teaching_experience']
    university_cgpa = request.form['university_cgpa']
    passing_year = request.form['passing_year']
    ssc_year = request.form['ssc_year']
    hsc_year = request.form['hsc_year']

    cursor.execute("""
        INSERT INTO applications (job_id, name, address, email, contact, desired_salary, employability_desire, citizenship, religion, previous_teaching_experience, university_cgpa, passing_year, ssc_year, hsc_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (job_id, name, address, email, contact, desired_salary, employability_desire, citizenship, religion, previous_teaching_experience, university_cgpa, passing_year, ssc_year, hsc_year))
    db.commit()
    return render_template('submit_success.html', name=name, email=email)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['username'] = username
            return redirect('/admin')
        return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/profile')
def profile():
    if 'username' in session:
        return f"Welcome, {session['username']}!"
    return "You are not logged in."

@app.route('/redirect_home')
def redirect_home():
    return redirect(url_for('login'))

submissions = []

@app.route('/submissions')
def show_submissions():
    return str(submissions)

@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    if request.method == 'POST':
        job_title = request.form['job_title']
        description = request.form['description']
        requirements = request.form['requirements']
        salary = request.form['salary']
        cursor.execute("INSERT INTO jobs (job_title, description, requirements, salary) VALUES (%s, %s, %s, %s)", (job_title, description, requirements, salary))
        db.commit()
        return redirect('/admin')
    return render_template('add_job.html')

@app.route('/edit_job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if request.method == 'POST':
        job_title = request.form['job_title']
        description = request.form['description']
        requirements = request.form['requirements']
        salary = request.form['salary']
        cursor.execute("UPDATE jobs SET job_title = %s, description = %s, requirements = %s, salary = %s WHERE job_id = %s", (job_title, description, requirements, salary, job_id))
        db.commit()
        return redirect('/admin')
    cursor.execute("SELECT job_title, description, requirements, salary FROM jobs WHERE job_id = %s", (job_id,))
    job = cursor.fetchone()
    return render_template('edit_job.html', job=job, job_id=job_id)

@app.route('/delete_job/<int:job_id>')
def delete_job(job_id):
    cursor.execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    db.commit()
    return redirect('/admin')

@app.route('/jobs')
def jobs():
    cursor.execute("SELECT job_id, job_title, description, requirements, salary FROM jobs")
    jobs = cursor.fetchall()
    return render_template('jobs.html', jobs=jobs)

@app.route('/admin')
def admin():
    if 'username' in session:
        cursor.execute("SELECT job_id, job_title, description, requirements, salary, vacancy FROM jobs")
        jobs = cursor.fetchall()

        cursor.execute("""
            SELECT applications.application_id, jobs.job_title, applications.name, applications.email, applications.address, applications.contact, applications.desired_salary, applications.employability_desire, applications.citizenship, applications.religion, applications.previous_teaching_experience, applications.university_cgpa, applications.passing_year, applications.ssc_year, applications.hsc_year
            FROM applications
            JOIN jobs ON applications.job_id = jobs.job_id
            ORDER BY jobs.job_title
        """)
        applications = cursor.fetchall()

        # Group applications by job title
        grouped_applications = {}
        for application in applications:
            job_title = application[1]
            if job_title not in grouped_applications:
                grouped_applications[job_title] = []
            grouped_applications[job_title].append(application)

        return render_template('admin.html', jobs=jobs, grouped_applications=grouped_applications)
    return redirect('/login')

@app.route('/delete_application/<int:application_id>')
def delete_application(application_id):
    cursor.execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
    db.commit()
    return redirect('/admin')

@app.route('/star_application/<int:application_id>', methods=['POST'])
def star_application(application_id):
    star_rating = request.form['star_rating']
    cursor.execute("UPDATE applications SET star_rating = %s WHERE application_id = %s", (star_rating, application_id))
    db.commit()
    return redirect('/admin')

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if request.method == 'POST':
        user_message = request.json['message']
        bot_response = chat_with_gpt(user_message)
        return jsonify({'response': bot_response})
    return render_template('chatbot.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/careers')
def careers():
    cursor.execute("SELECT job_id, job_title, description, requirements, salary FROM jobs")
    jobs = cursor.fetchall()
    return render_template('careers.html', jobs=jobs)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    return render_template('form.html', job_id=job_id)

if __name__ == '__main__':
    app.run(debug=True)