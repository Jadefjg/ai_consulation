import io

import pytest
from PIL import Image

from utils.file_security import UploadSecurityError, validate_avatar, validate_knowledge_file


def test_rejects_path_traversal_filename():
    with pytest.raises(UploadSecurityError):
        validate_knowledge_file("../secret.txt", b"safe", "text/plain")


def test_rejects_spoofed_pdf():
    with pytest.raises(UploadSecurityError):
        validate_knowledge_file("report.pdf", b"not a pdf", "application/pdf")


def test_rejects_binary_text():
    with pytest.raises(UploadSecurityError):
        validate_knowledge_file("notes.txt", b"hello\x00world", "text/plain")


def test_accepts_real_png():
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(buffer, format="PNG")
    assert validate_avatar("avatar.png", buffer.getvalue()) == ".png"

