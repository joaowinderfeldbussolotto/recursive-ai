import time
import requests
import streamlit as st

API_BASE = "http://api:8000/api/v1"
POLL_INTERVAL = 3  # seconds


def submit_pdf(file_bytes: bytes, filename: str) -> str:
    resp = requests.post(
        f"{API_BASE}/summarize",
        files={"file": (filename, file_bytes, "application/pdf")},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["job_id"]


def poll_job(job_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/jobs/{job_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_content(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content.decode("utf-8")


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Book Summarizer", page_icon="📚", layout="wide")
st.title("📚 Book Summarizer")
st.caption("Envie um PDF de livro técnico e receba um resumo em Markdown gerado por IA.")

# ── Session state ─────────────────────────────────────────────────────────────
if "job_id" not in st.session_state:
    st.session_state.job_id = None
if "job_done" not in st.session_state:
    st.session_state.job_done = False
if "summary_content" not in st.session_state:
    st.session_state.summary_content = None

# ── Upload section ────────────────────────────────────────────────────────────
if not st.session_state.job_id:
    uploaded = st.file_uploader("Selecione um arquivo PDF", type=["pdf"])
    if uploaded:
        if st.button("Gerar Resumo", type="primary"):
            with st.spinner("Enviando arquivo..."):
                try:
                    job_id = submit_pdf(uploaded.read(), uploaded.name)
                    st.session_state.job_id = job_id
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao enviar: {e}")

# ── Polling section ───────────────────────────────────────────────────────────
if st.session_state.job_id and not st.session_state.job_done:
    job_id = st.session_state.job_id
    st.info(f"Job ID: `{job_id}`")

    status_box = st.empty()
    progress_bar = st.progress(0, text="Aguardando processamento...")

    progress_map = {"PENDING": 5, "PROCESSING": 50}

    while True:
        try:
            job = poll_job(job_id)
        except Exception as e:
            status_box.error(f"Erro ao consultar status: {e}")
            time.sleep(POLL_INTERVAL)
            continue

        status = job.get("status")
        pct = progress_map.get(status, 0)
        progress_bar.progress(pct, text=f"Status: **{status}**")

        if status == "DONE":
            progress_bar.progress(100, text="Concluído!")
            st.session_state.job_done = True
            content = fetch_content(job["download_url"])
            st.session_state.summary_content = content
            st.session_state.chapters = job.get("chapters_processed")
            st.session_state.completed_at = job.get("completed_at")
            st.rerun()

        elif status == "FAILED":
            progress_bar.empty()
            st.error(f"Falha no processamento: {job.get('error', 'erro desconhecido')}")
            if st.button("Tentar novamente"):
                st.session_state.job_id = None
                st.rerun()
            break

        time.sleep(POLL_INTERVAL)
        st.rerun()

# ── Result section ────────────────────────────────────────────────────────────
if st.session_state.job_done and st.session_state.summary_content:
    content = st.session_state.summary_content

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.success("Resumo gerado com sucesso!")
    with col2:
        if st.session_state.get("chapters"):
            st.metric("Capítulos processados", st.session_state.chapters)
    with col3:
        if st.button("Novo resumo"):
            for key in ("job_id", "job_done", "summary_content", "chapters", "completed_at"):
                st.session_state.pop(key, None)
            st.rerun()

    st.download_button(
        label="⬇ Baixar Markdown",
        data=content.encode("utf-8"),
        file_name=f"{st.session_state.job_id}.md",
        mime="text/markdown",
        type="primary",
    )

    st.divider()
    st.markdown(content)
