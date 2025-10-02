from datetime import datetime, timezone
import hashlib, json, os
from flask import Flask, request, jsonify
from models import SurveySubmission
from storage import append_ndjson, exists_submission_id

app = Flask(__name__)
DATA_PATH = "data/survey.ndjson"

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def compute_submission_id(email: str) -> str:
    ts_hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    return sha256(email + ts_hour)

@app.get("/ping")
def ping():
    return {
        "message": "API is alive",
        "status": "ok",
        "utc_time": datetime.now(timezone.utc).isoformat()
    }, 200

@app.post("/v1/survey")
def intake():
    if not request.is_json:
        return jsonify(error="Body must be JSON"), 400
    try:
        payload = request.get_json()
    except Exception:
        return jsonify(error="Invalid JSON"), 400

    # Server-enriched fields
    payload.setdefault("user_agent", request.headers.get("User-Agent"))
    payload.setdefault("source", payload.get("source", "other"))
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # Validate (Pydantic v1)
    try:
        sub = SurveySubmission(**payload)
    except Exception as e:
        # Pydantic v1 exposes .errors(); fall back to str(e) if missing
        errors = e.errors() if hasattr(e, "errors") else str(e)
        return jsonify(detail="Validation error", errors=errors), 422

    # Idempotency
    sub_id = sub.submission_id or compute_submission_id(sub.email)
    if exists_submission_id(DATA_PATH, sub_id):
        return jsonify(status="ok", duplicated=True, submission_id=sub_id), 201

    # Privacy: hash email & age; do NOT log plaintext PII
    record = {
        "name": sub.name,
        "email": sha256(sub.email),
        "age": sha256(str(sub.age)),
        "consent": sub.consent,
        "rating": sub.rating,
        "comments": sub.comments,
        "source": sub.source,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "ip": ip,
        "user_agent": sub.user_agent,
        "submission_id": sub_id,
    }

    append_ndjson(record, DATA_PATH)
    return jsonify(status="ok"), 201

if __name__ == "__main__":
    app.run(port=5000, debug=True))