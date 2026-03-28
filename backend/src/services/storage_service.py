"""Google Cloud Storage service for file uploads."""

import logging
import uuid
from datetime import datetime

from google.cloud import storage

from src.config import config

logger = logging.getLogger(__name__)


def _get_gcs_client() -> storage.Client:
    """Get GCS client instance."""
    return storage.Client()


def _get_bucket() -> storage.Bucket:
    """Get the configured GCS bucket."""
    client = _get_gcs_client()
    return client.bucket(config.GCS_BUCKET_NAME)


def upload_image(user_id: str, file_data: bytes, filename: str) -> str:
    """Upload an image to GCS and return the public URL.

    Args:
        user_id: Owner user ID.
        file_data: Raw image bytes.
        filename: Original filename (used for extension).

    Returns:
        Public URL of the uploaded image.
    """
    bucket = _get_bucket()

    # Generate unique path: memos/{user_id}/{date}/{uuid}.{ext}
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "png"
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    blob_name = f"memos/{user_id}/{date_prefix}/{uuid.uuid4().hex}.{ext}"

    blob = bucket.blob(blob_name)
    content_type = _guess_content_type(ext)
    blob.upload_from_string(file_data, content_type=content_type)

    # Make publicly readable
    blob.make_public()
    public_url = blob.public_url

    logger.info("Uploaded image: %s (%d bytes)", blob_name, len(file_data))
    return public_url


def delete_image(url: str) -> bool:
    """Delete an image from GCS by its public URL.

    Args:
        url: Public URL of the image to delete.

    Returns:
        True if deletion succeeded, False otherwise.
    """
    bucket = _get_bucket()

    # Extract blob name from URL
    # URL format: https://storage.googleapis.com/{bucket}/{blob_name}
    prefix = f"https://storage.googleapis.com/{config.GCS_BUCKET_NAME}/"
    if not url.startswith(prefix):
        logger.warning("URL does not match expected GCS format: %s", url)
        return False

    blob_name = url[len(prefix):]
    blob = bucket.blob(blob_name)

    try:
        blob.delete()
        logger.info("Deleted image: %s", blob_name)
        return True
    except Exception:
        logger.exception("Failed to delete image: %s", blob_name)
        return False


def _guess_content_type(ext: str) -> str:
    """Guess content type from file extension."""
    mapping = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }
    return mapping.get(ext.lower(), "application/octet-stream")
