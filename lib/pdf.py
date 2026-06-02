"""DOCX -> PDF via LibreOffice headless. Works on Streamlit Cloud (Linux)."""
from __future__ import annotations
import os, shutil, subprocess, tempfile, uuid


def _libreoffice_bin() -> str | None:
    for cmd in ("libreoffice", "soffice"):
        p = shutil.which(cmd)
        if p: return p
    # mac default
    mac = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.exists(mac): return mac
    return None


def docx_to_pdf(docx_bytes: bytes) -> bytes | None:
    """Convert DOCX bytes to PDF bytes. Returns None if LibreOffice not available."""
    lo = _libreoffice_bin()
    if not lo:
        return None
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, f"in_{uuid.uuid4().hex}.docx")
        with open(src, "wb") as f:
            f.write(docx_bytes)
        try:
            subprocess.run(
                [lo, "--headless", "--norestore", "--nologo",
                 "--convert-to", "pdf", "--outdir", td, src],
                check=True, capture_output=True, timeout=90,
            )
        except subprocess.CalledProcessError:
            return None
        except subprocess.TimeoutExpired:
            return None
        pdf_path = src.replace(".docx", ".pdf")
        if not os.path.exists(pdf_path):
            return None
        with open(pdf_path, "rb") as f:
            return f.read()
