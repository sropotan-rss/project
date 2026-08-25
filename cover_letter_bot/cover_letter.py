import anthropic

import config

MAX_RESUME_CHARS = 8000
MAX_DESCRIPTION_CHARS = 6000

SYSTEM_PROMPT = (
    "Ты — помощник по трудоустройству. Пишешь сопроводительные письма на "
    "русском языке: по делу, без канцеляризмов и без воды, на основе резюме "
    "кандидата и текста вакансии. Подчёркивай тот опыт и навыки из резюме, "
    "которые реально совпадают с требованиями вакансии — не выдумывай то, "
    "чего нет в резюме. Объём — 150-250 слов. Выведи только текст письма, "
    "без пояснений и заголовков."
)


class CoverLetterError(Exception):
    pass


def generate_cover_letter(resume_text: str, vacancy: dict) -> str:
    resume_excerpt = resume_text[:MAX_RESUME_CHARS]
    description_excerpt = vacancy["description"][:MAX_DESCRIPTION_CHARS]

    vacancy_block = (
        f"Вакансия: {vacancy['title']}\n"
        f"Компания: {vacancy['employer'] or '—'}\n"
        f"Ключевые навыки: {', '.join(vacancy['key_skills']) or '—'}\n\n"
        f"Описание вакансии:\n{description_excerpt}"
    )

    user_prompt = (
        f"Резюме кандидата:\n{resume_excerpt}\n\n---\n\n{vacancy_block}\n\n---\n\n"
        "Напиши сопроводительное письмо для этой вакансии на основе этого резюме."
    )

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        raise CoverLetterError(f"не удалось сгенерировать письмо: {e}") from e

    return response.content[0].text.strip()
