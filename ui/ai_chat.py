import streamlit as st

from ai_agent.orchestrator import run_agent


if "ai_chat_history" not in st.session_state:
    st.session_state.ai_chat_history = []


TOOL_LABELS = {
    "query_database": "Database",
    "query_spreadsheet": "Spreadsheet",
    "query_pdf": "PDF",
}


def show_ai_chat():

    st.title("AI Agent")

    st.write(
        "Ask anything — this agent decides whether to check the database, "
        "the company spreadsheet, the company PDF, or a combination, and "
        "gives you one combined answer."
    )

    st.markdown("---")

    st.subheader("Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Questions", value=len(st.session_state.ai_chat_history))

    with col2:
        spreadsheet_status = "Loaded" if st.session_state.get("excel_df") is not None else "None"
        st.metric(label="Spreadsheet", value=spreadsheet_status)

    with col3:
        pdf_status = "Loaded" if st.session_state.get("pdf_chunks") else "None"
        st.metric(label="PDF", value=pdf_status)

    st.markdown("---")

    st.subheader("Ask a Question")

    user_question = st.text_input("Ask anything about your database, spreadsheet, or PDF:")

    generate_clicked = st.button("Ask Agent")

    if generate_clicked:

        if user_question:

            status = st.empty()
            status.info("Deciding which tools to use...")

            result = run_agent(user_question, st.session_state.ai_chat_history)

            status.empty()

            st.session_state.ai_chat_history.append({
                "question": user_question,
                "answer": result["answer"],
                "tools_used": result["tools_used"],
                "steps": result["steps"]
            })

            st.rerun()

        else:
            st.warning("Please enter a question.")

    for chat in reversed(st.session_state.ai_chat_history):

        st.markdown("---")

        st.subheader("User Question")
        st.write(chat["question"])

        if chat["tools_used"]:
            labels = [TOOL_LABELS.get(t, t) for t in chat["tools_used"]]
            st.caption("Tools used: " + ", ".join(labels))

        st.subheader("Answer")
        st.info(chat["answer"].replace("$", "\\$"))

        if chat["steps"]:
            with st.expander("See what each tool returned"):
                for step in chat["steps"]:
                    label = TOOL_LABELS.get(step["tool"], step["tool"])
                    st.markdown(f"**{label}**")
                    st.code(step["result"]["content"], language="text")