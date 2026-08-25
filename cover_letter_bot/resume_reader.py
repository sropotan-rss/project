from pypdf import PdfReader


class ResumeReadError(Exception):
    pass


def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        raise ResumeReadError(f"не удалось прочитать PDF: {e}") from e

    text = text.strip()
    if not text:
        raise ResumeReadError(
            "не удалось извлечь текст из PDF (возможно, это скан без текстового слоя)"
        )

    return text
