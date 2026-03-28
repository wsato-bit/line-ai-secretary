"""Google Cloud Vision OCR service."""

import logging

from google.cloud import vision

logger = logging.getLogger(__name__)


def _get_vision_client() -> vision.ImageAnnotatorClient:
    """Get Vision API client instance."""
    return vision.ImageAnnotatorClient()


def extract_text(image_url: str) -> str:
    """Extract text from an image using Google Cloud Vision OCR.

    Args:
        image_url: Public URL of the image to process.

    Returns:
        Extracted text string. Empty string if no text found or on error.
    """
    client = _get_vision_client()

    image = vision.Image()
    image.source.image_uri = image_url

    try:
        response = client.text_detection(image=image)

        if response.error.message:
            logger.error("Vision API error: %s", response.error.message)
            return ""

        annotations = response.text_annotations
        if not annotations:
            logger.info("No text detected in image: %s", image_url)
            return ""

        # First annotation contains the full extracted text
        full_text = annotations[0].description.strip()
        logger.info(
            "OCR extracted %d characters from: %s",
            len(full_text),
            image_url,
        )
        return full_text

    except Exception:
        logger.exception("OCR extraction failed for: %s", image_url)
        return ""
