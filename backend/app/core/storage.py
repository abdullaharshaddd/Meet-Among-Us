"""Cloudflare R2 (S3-compatible) object storage — see CLAUDE.md's locked
'Object storage' decision (zero egress fees, since audio gets pulled down
repeatedly for later milestones' ML work). boto3 talks to R2 exactly like S3;
only endpoint_url differs.
"""

from __future__ import annotations

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import EnrollmentAudioNotFoundError

_client = None


def _get_client():
    # Lazy + cached: constructing a boto3 client is not free, and every request
    # needing storage would otherwise pay for it again.
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",  # R2 has no regions; boto3 requires the field anyway
        )
    return _client


def presign_put(key: str, *, content_type: str, expires_in: int = 900) -> str:
    """A presigned URL lets the mobile client PUT the audio file directly to R2
    without ever handing it our R2 credentials — the backend only mints the URL."""
    return _get_client().generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def get_object_bytes(key: str) -> bytes:
    try:
        response = _get_client().get_object(Bucket=settings.r2_bucket_name, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            raise EnrollmentAudioNotFoundError(f"No uploaded audio found at {key}") from exc
        raise
    return response["Body"].read()


def delete_objects(keys: list[str]) -> None:
    """Best-effort: a hard reset must still clear the DB rows even if R2 is
    flaky or a key is already gone. A leftover object costs storage, not
    correctness — a reset stuck behind R2 would be the worse failure."""
    if not keys:
        return
    try:
        _get_client().delete_objects(
            Bucket=settings.r2_bucket_name,
            Delete={"Objects": [{"Key": key} for key in keys]},
        )
    except ClientError:
        pass
