import hashlib

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError
from models import SurveySubmission, StoredSurveyRecord
from storage import append_json_line

app = Flask(__name__)
# Allow cross-origin requests so the static HTML can POST from localhost or file://
CORS(app, resources={r"/v1/*": {"origins": "*"}})

@app.route("/ping", methods=["GET"])
def ping():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "API is alive",
        "utc_time": datetime.now(timezone.utc).isoformat()
    })

@app.post("/v1/survey")
def submit_survey():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "invalid_json", "detail": "Body must be application/json"}), 400

    try:
        submission = SurveySubmission(**payload)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "detail": ve.errors()}), 422

    email_norm = submission.email.strip().lower() 
    hashed_email = sha256_hex(email_norm) 
    hashed_age = sha256_hex(str(submission.age)) 
    
    hour_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    submission_id = submission.submission_id or sha256_hex(email_norm + hour_stamp) 
    
    record = StoredSurveyRecord( 
        name=submission.name,
        consent=submission.consent,
        rating=submission.rating,
        comments=submission.comments,
        source=submission.source,
        user_agent=submission.user_agent, 
        
        hashed_email=hashed_email,
        hashed_age=hashed_age,
        submission_id=submission_id, 
        
        received_at=datetime.now(timezone.utc),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or "") )
    append_json_line(record.dict())
    return jsonify({"status": "ok", "submission_id" : submission_id}), 201

if __name__ == "__main__":
    app.run(port=5000, debug=True)
