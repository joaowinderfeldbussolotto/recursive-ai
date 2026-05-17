import os

from rlm import RLM
from rlm.logger import RLMLogger
from app.core.config import settings

ROOT_PROMPT = """
Você tem acesso ao texto completo de um livro técnico na variável `context`.
Sua tarefa:
1. Use código Python para identificar os capítulos do livro (busque por padrões como
   "Chapter", "Capítulo", numeração, seções principais, etc.)
2. Para cada capítulo identificado, faça uma sub-chamada LM para gerar um resumo
   detalhado daquele capítulo em português
3. Consolide todos os resumos em um único documento Markdown bem estruturado

O Markdown final deve ter:
- Título do livro (se identificável)
- Índice com os capítulos
- Para cada capítulo: título, resumo in-depth com pontos principais, conceitos-chave,
  exemplos relevantes e insights práticos
- Seção de conclusão com os principais aprendizados do livro

Escreva em português, de forma clara e envolvente.
"""


def summarize(book_text: str, job_id: str) -> tuple[str, int]:
    """Returns (markdown_content, chapters_processed)."""
    log_dir = f"./logs/{job_id}"
    os.makedirs(log_dir, exist_ok=True)

    rlm = RLM(
        backend="litellm",
        backend_kwargs={
            "model_name": settings.mistral_model,
            "api_key": settings.mistral_api_key,
            "base_url": "https://api.mistral.ai/v1",
            "rpm": settings.mistral_rpm,
        },
        environment="local",
        logger=RLMLogger(log_dir=log_dir),
        verbose=True,
    )

    result = rlm.completion(prompt=book_text, root_prompt=ROOT_PROMPT)
    markdown = result.response
    return markdown, markdown.count("\n## ")
