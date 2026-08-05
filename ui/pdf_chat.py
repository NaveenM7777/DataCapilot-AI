import time
import streamlit as st

from pdf_agent.retriever import retrieve_relevant_chunks
from pdf_agent.qa_generator import generate_answer


def show_pdf_chat():

    st.title("PDF Agent")

    st.write("Ask questions about the company document in plain English.")

    if st.session_state.get("pdf_load_error"):
        st.error(st.session_state.pdf_load_error)
        return

    st.subheader("Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Questions", value=len(st.session_state.pdf_chat_history))

    with col2:
        st.metric(label="Pages", value=st.session_state.pdf_page_count)

    with col3:
        st.metric(label="Chunks", value=len(st.session_state.pdf_chunks))

    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Ask a Question")

        user_question = st.text_input("Ask your question about this document:")

        generate_clicked = st.button("Get Answer")

    with right:
        st.subheader("Recent Questions")

        if st.session_state.pdf_chat_history:
            recent = st.session_state.pdf_chat_history[-5:]
            for chat in reversed(recent):
                st.caption("• " + chat["question"])
        else:
            st.caption("No questions yet.")

    if generate_clicked:

        if user_question:

            status = st.empty()

            status.info("Finding relevant sections...")
            relevant_chunks = retrieve_relevant_chunks(user_question, st.session_state.pdf_chunks)
            time.sleep(0.3)

            status.info("Generating answer...")
            answer = generate_answer(user_question, relevant_chunks, st.session_state.pdf_chat_history)
            time.sleep(0.3)

            status.empty()

            st.success("Answer Generated")

            st.session_state.pdf_chat_history.append(
                {
                    "question": user_question,
                    "answer": answer,
                    "sources": sorted(set(p for c in relevant_chunks for p in c["pages"]))
                }
            )

            st.rerun()

        else:
            st.warning("Please enter a question.")

    for chat in reversed(st.session_state.pdf_chat_history):

        st.markdown("---")

        st.subheader("User Question")
        st.write(chat["question"])

        st.subheader("Answer")
        st.info(chat["answer"].replace("$", "\\$"))

        if chat["sources"]:
            pages_str = ", ".join(str(p) for p in chat["sources"])
            st.caption(f"Referenced pages: {pages_str}")