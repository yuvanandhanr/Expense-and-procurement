import io
import logging
import os
from PIL import Image
import pytesseract
from src.core.config import settings

logger = logging.getLogger(__name__)


class TesseractService:
    """
    Service wrapper for Tesseract OCR utilizing the pytesseract wrapper.
    """

    def __init__(self, tesseract_cmd: str = None):
        """
        Initializes the service by setting the Tesseract path configuration.
        """
        # Load from config settings if not explicitly passed
        self.tesseract_cmd = tesseract_cmd or settings.TESSERACT_CMD
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        # Check if file exists and log warning/info accordingly
        if not os.path.exists(self.tesseract_cmd):
            logger.warning(
                f"Tesseract executable not found at: '{self.tesseract_cmd}'. "
                "Ensure Tesseract OCR is installed and the environment configuration is correct."
            )
        else:
            logger.info(f"Tesseract OCR path configured successfully: '{self.tesseract_cmd}'")

    def extract_text_from_image_path(self, image_path: str, lang: str = "eng") -> str:
        """
        Extracts text from a given image file path.

        :param image_path: Absolute or relative path to the image file.
        :param lang: Language code for OCR (default 'eng').
        :return: Extracted text as a string.
        """
        logger.info(f"Performing OCR on image file: '{image_path}' using lang='{lang}'")
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found at: '{image_path}'")

            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img, lang=lang)
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image path '{image_path}': {e}", exc_info=True)
            raise e

    def extract_text_from_image(self, image: Image.Image, lang: str = "eng") -> str:
        """
        Extracts text directly from a PIL Image object.

        :param image: PIL Image instance.
        :param lang: Language code for OCR (default 'eng').
        :return: Extracted text as a string.
        """
        logger.info(f"Performing OCR on PIL Image using lang='{lang}'")
        try:
            text = pytesseract.image_to_string(image, lang=lang)
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PIL Image object: {e}", exc_info=True)
            raise e

    def extract_text_from_bytes(self, image_bytes: bytes, lang: str = "eng") -> str:
        """
        Extracts text from raw image bytes.

        :param image_bytes: Raw bytes of the image file.
        :param lang: Language code for OCR (default 'eng').
        :return: Extracted text as a string.
        """
        logger.info(f"Performing OCR on image bytes using lang='{lang}'")
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                text = pytesseract.image_to_string(img, lang=lang)
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image bytes: {e}", exc_info=True)
            raise e
