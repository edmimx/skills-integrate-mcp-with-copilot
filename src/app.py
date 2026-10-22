"""
High School Management System API

A simple FastAPI application that allows students to view activities and teachers to manage sign-ups
for extracurricular activities at Mergington High School.
"""

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_SESSION_DURATION_SECONDS = 8 * 60 * 60


class AdminCredentials(BaseModel):
    username: str
    password: str


def _admin_settings() -> tuple[str, str, bytes]:
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    secret = os.getenv("ADMIN_SESSION_SECRET")
    if not username or not password or not secret:
        raise HTTPException(
            status_code=503,
            detail="Admin login is not configured. Set ADMIN_USERNAME, "
                   "ADMIN_PASSWORD, and ADMIN_SESSION_SECRET.",
        )
    if len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="ADMIN_SESSION_SECRET must be at least 32 characters long.",
        )
    return username, password, secret.encode("utf-8")


def _make_session(username: str, secret: bytes) -> str:
    payload = json.dumps(
        {
            "username": username,
            "expires_at": int(time.time()) + ADMIN_SESSION_DURATION_SECONDS,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(
        secret, encoded_payload.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{encoded_payload}.{signature}"


def _is_admin_session_valid(token: str, expected_username: str, secret: bytes) -> bool:
    try:
        encoded_payload, signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return False

        payload_bytes = base64.urlsafe_b64decode(
            encoded_payload + "=" * (-len(encoded_payload) % 4)
        )
        payload = json.loads(payload_bytes)
        return (
            payload.get("username") == expected_username
            and isinstance(payload.get("expires_at"), int)
            and payload["expires_at"] > int(time.time())
        )
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        return False


def require_admin(request: Request) -> None:
    username, _, secret = _admin_settings()
    token = request.cookies.get(ADMIN_SESSION_COOKIE, "")
    if not _is_admin_session_valid(token, username, secret):
        raise HTTPException(status_code=401, detail="Teacher login required")


# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/admin/login")
def admin_login(credentials: AdminCredentials, response: Response):
    username, password, secret = _admin_settings()
    if not (
        hmac.compare_digest(credentials.username.encode("utf-8"), username.encode("utf-8"))
        and hmac.compare_digest(credentials.password.encode("utf-8"), password.encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=_make_session(username, secret),
        max_age=ADMIN_SESSION_DURATION_SECONDS,
        httponly=True,
        secure=os.getenv("ADMIN_COOKIE_SECURE", "true").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"authenticated": True}


@app.get("/admin/session")
def get_admin_session(request: Request):
    token = request.cookies.get(ADMIN_SESSION_COOKIE)
    if not token:
        return {"authenticated": False}

    username, _, secret = _admin_settings()
    return {
        "authenticated": _is_admin_session_valid(token, username, secret)
    }


@app.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie(
        key=ADMIN_SESSION_COOKIE,
        httponly=True,
        secure=os.getenv("ADMIN_COOKIE_SECURE", "true").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"authenticated": False}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _: None = Depends(require_admin)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _: None = Depends(require_admin)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
