from app.core.rlm_client import rlm

QUERY = """
Sua tarefa é gerar um resumo completo deste livro técnico em português.

1. Use código Python para identificar os capítulos (busque padrões como
   "Chapter", "Capítulo", numeração, seções principais, etc.)
2. Para cada capítulo identificado, use recursive_llm() para gerar um resumo
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


def summarize(book_text: str) -> tuple[str, int]:
    """Returns (markdown_content, chapters_processed)."""
    markdown = rlm.complete(query=QUERY, context=book_text)
    chapters = markdown.count("\n## ")
    return markdown, chapters
