# Mergington High School Activities API

A simple FastAPI application that lets students view activities and teachers manage sign-ups.

## Features

- View all available extracurricular activities
- Teachers can sign students up for or unregister them from activities after logging in

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Configure a teacher account and session-signing key, then start the server:

   ```sh
   export ADMIN_USERNAME=teacher
   export ADMIN_PASSWORD='use-a-strong-password'
   export ADMIN_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
   export ADMIN_COOKIE_SECURE=false  # Local HTTP only; leave unset when using HTTPS
   uvicorn app:app --app-dir src --reload
   ```

   Keep these values out of source control. In production, use HTTPS and leave
   `ADMIN_COOKIE_SECURE` at its default (`true`).

3. Open your browser and go to:
   - Activities page: http://localhost:8000/
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                        |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| GET    | `/activities`                                                     | View activities and current participants                           |
| POST   | `/admin/login`                                                     | Log in as a teacher and set a signed, HTTP-only session cookie     |
| GET    | `/admin/session`                                                   | Check whether the current browser has an active teacher session    |
| POST   | `/admin/logout`                                                    | End the current teacher session                                    |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only: sign up a student                                    |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only: unregister a student                              |

The signup and unregister endpoints reject requests without a valid teacher
session, even if called directly instead of through the web page.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and participant data is stored in memory, so it resets when the server
restarts. Configure `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and a
`ADMIN_SESSION_SECRET` of at least 32 characters to enable teacher login.
