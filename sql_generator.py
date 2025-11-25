import uuid
from loguru import logger
from openai import OpenAI

from core.config import settings

client = OpenAI(api_key=settings.PROJETO_TAES_OPENAI_API_KEY)


def improve_prompt(original_prompt: str) -> str:
    """
    Chama a OpenAI para melhorar/expandir o prompt que foi enviado pelo usuário.
    """
    logger.info("Chamando OpenAI para melhorar prompt SQL...")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente especializado em melhorar prompts "
                        "para geração de código SQL. Melhore o prompt mantendo "
                        "a intenção original."
                    ),
                },
                {"role": "user", "content": original_prompt},
            ],
        )

        improved = response.choices[0].message.content.strip()
        logger.info(f"Prompt melhorado: {improved}")
        return improved

    except Exception as e:
        logger.error(f"Erro ao melhorar prompt: {e}")
        raise Exception("Erro ao melhorar prompt.") from e


def generate_sql_from_prompt(prompt: str) -> str:
    """
    Chama a OpenAI para gerar SQL a partir do prompt melhorado.
    """
    logger.info("Chamando OpenAI para gerar SQL...")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um gerador de código SQL. Gere estritamente código SQL "
                        "sem explicações."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        sql_code = response.choices[0].message.content.strip()
        logger.info("SQL gerado com sucesso.")
        return sql_code

    except Exception as e:
        logger.error(f"Erro ao gerar SQL: {e}")
        raise Exception("Erro ao gerar SQL.") from e



def pipeline_generate_sql(original_prompt: str, request_id: uuid.UUID | None = None) -> str:
    """
    Fluxo completo:
    1. Recebe prompt via FastAPI
    2. Melhora prompt usando OpenAI
    3. Usa prompt melhorado para gerar SQL final
    """
    request_id = request_id or uuid.uuid4()
    logger.info(f"{request_id}, pipeline_generate_sql, started")

    improved_prompt = improve_prompt(original_prompt)
    final_sql = generate_sql_from_prompt(improved_prompt)

    logger.info(f"{request_id}, pipeline_generate_sql, done")
    return final_sql
