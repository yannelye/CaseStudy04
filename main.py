from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import hashlib
import json
import os

# ------------------------
# Utility functions
# ------------------------

# Hash function
def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

# Generate submission_id using email + YYYYMMDDHH
def generate_submission_id(email: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H")
    return hash_sha256(email + timestamp)

# ------------------------
# Pydantic model
# ------------------------
class UserSubmission(BaseModel):
    email: str
    age: int
    submission_id: Optional[str] = None
    user_agent: Optional[str] = None

# ------------------------
# Submission prep
# ------------------------
def prepare_submission(data: UserSubmission) -> dict:
    hashed_email = hash_sha256(data.email)
    hashed_age = hash_sha256(str(data.age))
    submission_id = data.submission_id or generate_submission_id(data.email)
    return {
        "email": hashed_email,
        "age": hashed_age,
        "submission_id": submission_id,
        "user_agent": data.user_agent,
    }

# ------------------------
# FastAPI app
# ------------------------
app = FastAPI()

# Health check endpoint
@app.get("/ping")
def ping():
    return {
        "message": "API is alive",
        "status": "ok",
        "utc_time": datetime.now(timezone.utc).isoformat()
    }

# Root route
@app.get("/")
def root():
    return {"message": "Welcome to the API! Use /ping or /docs"}

# Submission route
@app.post("/submit")
def submit(data: UserSubmission):
    record = prepare_submission(data)

    # Make sure file exists
    if not os.path.exists("submissions.json"):
        with open("submissions.json", "w") as f:
            f.write("")

    # Append submission
    with open("submissions.json", "a") as f:
        f.write(json.dumps(record) + "\n")

    return {"status": "success", "submission_id": record["submission_id"]}

# ------------------------
# Local entrypoint
# ------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
    

