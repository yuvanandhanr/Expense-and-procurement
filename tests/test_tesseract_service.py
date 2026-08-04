import os
import pytest
from PIL import Image, ImageDraw
from src.ocr.services.tesseract_service import TesseractService
from src.core.config import settings


@pytest.fixture
def temp_image_path(tmp_path):
    # Create a simple image with text "TEST" using PIL
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    # Use default PIL font to draw a simple string
    d.text((10, 10), "TEST", fill=(0, 0, 0))

    path = tmp_path / "test_image.png"
    img.save(path)
    return str(path)


def test_tesseract_service_initialization():
    service = TesseractService()
    assert service.tesseract_cmd == settings.TESSERACT_CMD


def test_ocr_extraction(temp_image_path):
    service = TesseractService()

    # Skip extraction tests if Tesseract executable is not installed
    if not os.path.exists(service.tesseract_cmd):
        pytest.skip("Tesseract executable not found, skipping extraction test.")

    # Test extraction from file path
    text = service.extract_text_from_image_path(temp_image_path)
    assert isinstance(text, str)

    # Test extraction from PIL Image object
    with Image.open(temp_image_path) as img:
        text_from_img = service.extract_text_from_image(img)
        assert isinstance(text_from_img, str)

    # Test extraction from raw bytes
    with open(temp_image_path, "rb") as f:
        image_bytes = f.read()
    text_from_bytes = service.extract_text_from_bytes(image_bytes)
    assert isinstance(text_from_bytes, str)
