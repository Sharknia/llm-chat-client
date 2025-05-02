import re


def normalize_keyword(title: str) -> str:
    title = title.replace(" ", "").lower()
    # 특수문자 제거
    title = re.sub(r"[^\w\s]", "", title)
    return title
