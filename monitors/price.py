import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT_SECONDS = 15


class PriceFetchError(Exception):
    pass


def fetch_price_text(url: str, selector: str) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as e:
        raise PriceFetchError(f"не удалось загрузить страницу: {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    try:
        element = soup.select_one(selector)
    except Exception as e:
        raise PriceFetchError(f"некорректный CSS-селектор: {e}") from e

    if element is None:
        raise PriceFetchError(f"элемент по селектору '{selector}' не найден на странице")

    text = element.get_text(strip=True)
    if not text:
        raise PriceFetchError("найденный элемент пуст")

    return text
