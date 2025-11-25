from __future__ import annotations

import os
from urllib.parse import urljoin

import requests
import streamlit as st


API_BASE = os.environ.get("FIN_RAG_API_BASE", "http://localhost:8000")


def _resolve_url(path_or_url: str) -> str:
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    base = API_BASE.rstrip("/") + "/"
    return urljoin(base, path_or_url.lstrip("/"))


def _parse_query(question: str) -> dict:
    """Call the parse-query endpoint to extract entities from the question."""
    try:
        resp = requests.post(
            f"{API_BASE}/chat/parse-query",
            json={"question": question},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {
            "tickers": None,
            "period": None,
            "needs_clarification": True,
            "clarification_message": f"Failed to analyze query: {exc}",
        }


def main() -> None:
    st.title("Financial RAG Chatbot")
    st.write("Ask questions about company financials from filings, press releases, and transcripts.")

    # Initialize session state for inferred values
    if "inferred_tickers" not in st.session_state:
        st.session_state.inferred_tickers = ""
    if "inferred_period" not in st.session_state:
        st.session_state.inferred_period = ""
    if "query_analyzed" not in st.session_state:
        st.session_state.query_analyzed = False
    if "clarification_message" not in st.session_state:
        st.session_state.clarification_message = None

    # Question input
    question = st.text_area(
        "Question",
        value="How much money did Amazon make in Q3 2025?",
        help="Enter your question about company financials",
    )

    # Analyze Query button
    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_clicked = st.button("🔍 Analyze Query", type="secondary")

    if analyze_clicked and question.strip():
        with st.spinner("Analyzing your query..."):
            parsed = _parse_query(question)

        # Update session state with inferred values
        tickers = parsed.get("tickers") or []
        st.session_state.inferred_tickers = ", ".join(tickers) if tickers else ""
        st.session_state.inferred_period = parsed.get("period") or ""
        st.session_state.query_analyzed = True

        if parsed.get("needs_clarification"):
            st.session_state.clarification_message = parsed.get("clarification_message")
        else:
            st.session_state.clarification_message = None

    # Sidebar with editable inferred values
    with st.sidebar:
        st.header("Query Parameters")

        # Status indicator
        if st.session_state.query_analyzed:
            if st.session_state.clarification_message:
                st.warning("⚠️ Needs clarification")
            else:
                st.success("✅ Query analyzed")
        else:
            st.info("💡 Click 'Analyze Query' to auto-detect parameters")

        st.markdown("---")

        # Editable ticker field
        tickers_input = st.text_input(
            "Ticker(s)",
            value=st.session_state.inferred_tickers,
            help="Comma-separated stock ticker symbols (e.g., AMZN, AAPL)",
            placeholder="e.g., AMZN, AAPL",
        )

        # Editable period field
        period_input = st.text_input(
            "Period",
            value=st.session_state.inferred_period,
            help="Fiscal quarter and year (e.g., Q3-2025)",
            placeholder="e.g., Q3-2025",
        )

        st.markdown("---")

        # Advanced options
        with st.expander("Advanced Options"):
            top_k = st.slider(
                "Top K context chunks",
                min_value=4,
                max_value=16,
                value=8,
                step=1,
                help="Number of relevant document chunks to retrieve",
            )

    # Show clarification warning if needed
    if st.session_state.clarification_message:
        st.warning(f"⚠️ {st.session_state.clarification_message}")

    # Ask button
    if st.button("💬 Ask", type="primary"):
        # Validate inputs
        if not question.strip():
            st.error("Please enter a question.")
            return

        if not tickers_input.strip() and not period_input.strip():
            st.warning(
                "No ticker or period specified. The search will look across all available documents. "
                "For more targeted results, please specify a ticker and/or period."
            )

        # Parse tickers from input
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        period = period_input.strip() if period_input.strip() else None

        # Build payload
        payload = {
            "question": question,
            "tickers": tickers if tickers else None,
            "period": period,
            "top_k": top_k,
        }

        try:
            with st.spinner("Searching documents and generating answer..."):
                resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            st.error(f"Request failed: {exc}")
            return

        st.subheader("Answer")
        st.write(data.get("answer", ""))

        citations = data.get("citations", [])
        if citations:
            st.subheader("Citations")
            for idx, citation in enumerate(citations, start=1):
                label = f"[{idx}] {citation.get('ticker','')} {citation.get('filing_type','')} {citation.get('period','')}"
                st.markdown(f"**{label}**")
                st.write(
                    f"Doc ID: {citation.get('doc_id','')} | Page: {citation.get('page','?')} | "
                    f"Lines: {citation.get('line_start','?')} - {citation.get('line_end','?')}"
                )
                highlight_url = citation.get("highlight_url")
                if highlight_url:
                    st.link_button("Open highlighted PDF", _resolve_url(highlight_url), type="primary")
                source_url = citation.get("source_url")
                if source_url:
                    st.markdown(f"[Open source document]({source_url})")


if __name__ == "__main__":
    main()
