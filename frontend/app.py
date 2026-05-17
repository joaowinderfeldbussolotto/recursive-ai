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


def fetch_logs(job_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/jobs/{job_id}/logs", timeout=10)
    resp.raise_for_status()
    return resp.json()


def _render_log_tab(log_data: dict | None):
    if log_data is None:
        st.warning("Logs não disponíveis para este job.")
        return

    status = log_data.get("status")

    if status == "empty":
        st.info("Nenhum log encontrado para este job.")
        return

    if status == "pending":
        st.info("Logs ainda sendo gerados. Recarregue a página em instantes.")
        return

    meta = log_data.get("metadata") or {}
    if meta:
        with st.expander("Metadados da execução", expanded=False):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Modelo", meta.get("root_model", "—"))
            col_b.metric("Max Depth", meta.get("max_depth", "—"))
            col_c.metric("Max Iterations", meta.get("max_iterations", "—"))
            st.caption(
                f"Backend: {meta.get('backend', '—')}  |  "
                f"Ambiente: {meta.get('environment_type', '—')}  |  "
                f"Iniciado: {meta.get('timestamp', '—')}"
            )

    total = log_data.get("total_iterations", 0)
    errors = log_data.get("parse_errors", 0)
    col1, col2 = st.columns(2)
    col1.metric("Iterações", total)
    if errors:
        col2.warning(f"{errors} linha(s) com erro de parse ignorada(s)")

    st.divider()

    iterations = log_data.get("iterations", [])
    if not iterations:
        st.info("Sem iterações registradas.")
        return

    for it in iterations:
        iter_num = it.get("iteration", "?")
        iter_time = it.get("iteration_time")
        is_final = it.get("final_answer") is not None
        label_suffix = " — Resposta Final" if is_final else ""
        time_suffix = f"  ({iter_time:.2f}s)" if iter_time is not None else ""
        expander_label = f"Iteração {iter_num}{label_suffix}{time_suffix}"

        with st.expander(expander_label, expanded=is_final):

            prompt_msgs = it.get("prompt", [])
            if prompt_msgs:
                with st.expander(f"Prompt ({len(prompt_msgs)} mensagens)", expanded=False):
                    for msg in prompt_msgs:
                        role = msg.get("role", "unknown")
                        body = msg.get("content", "")
                        st.markdown(f"**{role.upper()}**")
                        st.text(body[:2000] + ("..." if len(body) > 2000 else ""))
                        st.divider()

            st.markdown("**Resposta do LLM**")
            st.markdown(it.get("response", ""))

            for cb_idx, cb in enumerate(it.get("code_blocks", [])):
                st.markdown(f"**Bloco de Código {cb_idx + 1}**")
                st.code(cb.get("code", ""), language="python")

                exec_time = cb.get("execution_time")
                if exec_time is not None:
                    st.caption(f"Tempo de execução: {exec_time:.3f}s")

                stdout = cb.get("stdout") or ""
                stderr = cb.get("stderr") or ""
                if stdout:
                    with st.expander("stdout", expanded=True):
                        st.code(stdout, language="text")
                if stderr:
                    with st.expander("stderr", expanded=True):
                        st.code(stderr, language="text")

                rlm_calls = cb.get("rlm_calls", [])
                if rlm_calls:
                    with st.expander(f"Sub-chamadas LM ({len(rlm_calls)})", expanded=False):
                        for call_idx, call in enumerate(rlm_calls):
                            st.markdown(
                                f"**Chamada {call_idx + 1}** — "
                                f"modelo: `{call.get('root_model', '?')}`  |  "
                                f"tempo: `{call.get('execution_time', 0):.2f}s`"
                            )
                            with st.expander("Prompt", expanded=False):
                                st.text(call.get("prompt", ""))
                            with st.expander("Resposta", expanded=False):
                                st.markdown(call.get("response", ""))
                            if call_idx < len(rlm_calls) - 1:
                                st.divider()


# ── Page config ───────────────────────────────────────────────────────────────
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
if "log_data" not in st.session_state:
    st.session_state.log_data = None

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
            try:
                st.session_state.log_data = fetch_logs(job_id)
            except Exception:
                st.session_state.log_data = None
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
    log_data = st.session_state.get("log_data")

    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.success("Resumo gerado com sucesso!")
    with col2:
        if st.session_state.get("chapters"):
            st.metric("Capítulos processados", st.session_state.chapters)
    with col3:
        if st.button("Novo resumo"):
            for key in ("job_id", "job_done", "summary_content", "chapters", "completed_at", "log_data"):
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

    tab_summary, tab_logs = st.tabs(["Resumo", "Logs RLM"])

    with tab_summary:
        st.markdown(content)

    with tab_logs:
        _render_log_tab(log_data)
