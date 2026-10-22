from typing import Literal

from pydantic import BaseModel

from app.models.enrollment_sample import EnrollmentLanguage
from app.models.user import EnrollmentStatus


class UploadUrlRequest(BaseModel):
    language: EnrollmentLanguage
    # "m4a" is what the real mobile app sends: Expo cannot record FLAC or WAV on
    # Android, see docs/adr/0019-accept-m4a-enrollment-audio.md. "wav" exists for
    # the /dev/enroll browser harness (docs/adr/0015-dev-enrollment-harness.md).
    # "webm" is what a browser records, used when the app runs on Expo web.
    audio_format: Literal["flac", "wav", "m4a", "webm"] = "flac"


class UploadUrlResponse(BaseModel):
    upload_url: str  # presigned R2 PUT — see app/core/storage.py
    audio_key: str  # pass this back to POST /enrollment/samples
    expires_in_seconds: int


class SubmitSampleRequest(BaseModel):
    language: EnrollmentLanguage
    audio_key: str


class SubmitSampleResponse(BaseModel):
    accepted: bool
    reason_code: str | None
    reason_message: str | None
    enrollment_status: EnrollmentStatus


class PassageStatus(BaseModel):
    language: EnrollmentLanguage
    state: str  # "not_attempted" | "accepted" | "rejected"
    reason_code: str | None
    reason_message: str | None


class EnrollmentStatusResponse(BaseModel):
    enrollment_status: EnrollmentStatus
    passages: list[PassageStatus]
