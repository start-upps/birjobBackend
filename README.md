# Job Posting Application

This repository contains a Django-based job posting application with a React frontend. The platform allows recruiters to post job openings and manage them, while candidates can browse jobs and apply without authentication.

## Features

- Recruiters can create, update, and delete job posts.
- Candidates can browse job listings and apply without needing to log in.
- HR users can view applicants for their posted jobs.

## Installation

### Backend

1. Clone the repository:
    ```bash
    git clone https://github.com/Ismat-Samadov/job_posting.git
    ```
2. Navigate to the backend directory:
    ```bash
    cd backend
    ```
3. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
5. Create a `.env` file in the backend directory and add the following environment variables:
    ```
    DB_HOST=your_db_host
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_PORT=your_db_port
    SECRET_KEY=your_secret_key
    DEBUG=True
    ```
   Replace the placeholder values (`your_db_host`, `your_db_name`, etc.) with your actual database and environment settings.

6. Run migrations:
    ```bash
    python manage.py migrate
    ```
7. Start the Django development server:
    ```bash
    python manage.py runserver
    ```

### Frontend

1. Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2. Install dependencies:
    ```bash
    npm install
    ```
3. Start the React development server:
    ```bash
    npm start
    ```

## Usage

- Access the application at `http://127.0.0.1:8000/` for the backend and `http://localhost:3000/` for the frontend.
- Use the React frontend to browse job listings, apply for jobs, and manage postings as a recruiter.

## Contributing

1. Fork the repository.
2. Create a new branch.
3. Make your changes and commit them.
4. Push to your branch.
5. Create a pull request.
