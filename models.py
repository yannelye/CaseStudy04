from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, conint, constr, validator

class SurveySubmission(BaseModel):
    name: constr(min_length=1, max_length=100)  # type: ignore
    email: EmailStr
    age: conint(ge=13, le=120)  # type: ignore
    consent: Literal[True]  # must be true
    rating: conint(ge=1, le=5)  # type: ignore
    comments: Optional[constr(strip_whitespace=True, max_length=1000)] = None  # type: ignore
    source: Optional[Literal["web", "mobile", "other"]] = "other"
    submission_id: Optional[str] = None
    user_agent: Optional[str] = None

    @validator("comments", pre=True, always=True)
    def _trim_comments(cls, v):
        if v is None:
            return v
        return v.strip()