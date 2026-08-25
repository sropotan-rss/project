import shutil
import subprocess

MAX_RESUME_CHARS = 8000
MAX_DESCRIPTION_CHARS = 6000
CLI_TIMEOUT_SECONDS = 180

SYSTEM_INSTRUCTIONS = (
    "Ты — помощник по трудоустройству. Пишешь сопроводительные письма на "
    "русском языке: по делу, без канцеляризмов и без воды, на основе резюме "
    "кандидата и текста вакансии. Подчёркивай тот опыт и навыки из резюме, "
    "которые реально совпадают с требованиями вакансии — не выдумывай то, "
    "чего нет в резюме. Объём — 150-250 слов. Выведи только готовый текст "
    "письма, без пояснений, заголовков и уточняющих вопросов."
)


class CoverLetterError(Exception):
    pass


def generate_cover_letter(resume_text: str, vacancy: dict) -> str:
    claude_cli = shutil.which("claude")
    if claude_cli is None:
        raise CoverLetterError(
            "команда 'claude' не найдена. Установи Claude Code CLI "
            "(npm install -g @anthropic-ai/claude-code) и выполни 'claude' "
            "один раз, чтобы войти в аккаунт"
        )

    resume_excerpt = resume_text[:MAX_RESUME_CHARS]
    description_excerpt = vacancy["description"][:MAX_DESCRIPTION_CHARS]

    vacancy_block = (
        f"Вакансия: {vacancy['title']}\n"
        f"Компания: {vacancy['employer'] or '—'}\n"
        f"Ключевые навыки: {', '.join(vacancy['key_skills']) or '—'}\n\n"
        f"Описание вакансии:\n{description_excerpt}"
    )

    prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Резюме кандидата:\n{resume_excerpt}\n\n---\n\n{vacancy_block}\n\n---\n\n"
        "Напиши сопроводительное письмо для этой вакансии на основе этого резюме."
    )

    try:
        result = subprocess.run(
            [claude_cli, "-p", prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CLI_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as e:
        raise CoverLetterError("Claude CLI не ответил за отведённое время") from e

    if result.returncode != 0:
        raise CoverLetterError(f"Claude CLI вернул ошибку: {result.stderr.strip()}")

    letter = result.stdout.strip()
    if not letter:
        raise CoverLetterError("Claude CLI вернул пустой ответ")

    return letter
