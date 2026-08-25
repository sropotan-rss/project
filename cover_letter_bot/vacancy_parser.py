import re

import requests
from bs4 import BeautifulSoup

HH_API_URL = "https://api.hh.ru/vacancies/{vacancy_id}"
HEADERS = {"User-Agent": "cover-letter-bot/1.0"}
TIMEOUT_SECONDS = 15


class VacancyFetchError(Exception):
    pass


def _extract_vacancy_id(url: str) -> str:
    match = re.search(r"/vacancy/(\d+)", url)
    if not match:
        raise VacancyFetchError("не удалось найти ID вакансии в ссылке hh.ru")
    return match.group(1)


def fetch_vacancy(url: str) -> dict:
    vacancy_id = _extract_vacancy_id(url)

    try:
        response = requests.get(
            HH_API_URL.format(vacancy_id=vacancy_id), headers=HEADERS, timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise VacancyFetchError(f"не удалось загрузить вакансию: {e}") from e

    data = response.json()

    description_html = data.get("description") or ""
    description = BeautifulSoup(description_html, "html.parser").get_text("\n", strip=True)

    if not description:
        raise VacancyFetchError("не удалось получить описание вакансии")

    return {
        "title": data.get("name") or "",
        "employer": (data.get("employer") or {}).get("name") or "",
        "description": description,
        "key_skills": [s["name"] for s in data.get("key_skills") or []],
    }
