from backend.app.config import settings

def perform_ocr(page) -> str:
    """OCR fallback. Only runs if ENABLE_OCR is enabled and pytesseract/easyocr installed."""
    if not settings.ENABLE_OCR:
        return ""
    # Optional P2 OCR stub
    try:
        import pytesseract
        from PIL import Image
        import io
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img)
    except Exception:
        return ""
