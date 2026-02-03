def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())

def normalize_date(date_str: str) -> str:
    # TODO: Implement using dateparser
    return date_str
