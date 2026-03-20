import subprocess
import sys

def install_and_extract():
    try:
        import fitz
    except ImportError:
        print("Installing pymupdf to read PDF...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pymupdf"])
        import fitz

    print("Extracting text from PDF...")
    doc = fitz.open(r"c:\fake job detection\Secure Image Publishing System Using Facial Identity Verification (1).pdf")
    text = ""
    for page in doc:
        text += page.get_text()

    with open(r"c:\fake job detection\pdf_structure.txt", "w", encoding='utf-8') as f:
        f.write(text)
    print("Done! Check pdf_structure.txt")

if __name__ == "__main__":
    install_and_extract()
