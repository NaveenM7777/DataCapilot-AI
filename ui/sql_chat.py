import time
import streamlit as st

from sql_agent.sql_generator import generate_sql
from sql_agent.sql_executor import execute_sql
from llm.groq_client import explain_sql


def show_sql_chat():

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.title("DataCapilot AI")

    st.write("Ask questions about your SQLite database in plain English.")

    st.subheader("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Questions", value=len(st.session_state.chat_history))

    with col2:
        st.metric(label="Database", value="Chinook")

    with col3:
        st.metric(label="Tables", value=11)

    with col4:
        st.metric(label="Model", value="Llama 3.3")

    st.markdown("---")

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Ask a Question")

        user_question = st.text_input("Ask your question:")

        generate_clicked = st.button("Generate SQL")

    with right:
        st.subheader("Recent Questions")

        if st.session_state.chat_history:
            recent = st.session_state.chat_history[-5:]
            for chat in reversed(recent):
                st.caption("• " + chat["question"])
        else:
            st.caption("No questions yet.")

    if generate_clicked:

        if user_question:

            status = st.empty()

            status.info("Understanding your question...")
            time.sleep(0.5)

            status.info("Generating SQL...")
            sql_query = generate_sql(user_question, st.session_state.chat_history)

            time.sleep(0.5)

            status.info("Explaining SQL...")
            explanation = explain_sql(sql_query)

            time.sleep(0.5)

            status.info("Executing SQL...")
            result, error = execute_sql(sql_query)

            time.sleep(0.5)

            status.empty()

            if error:
                st.error("SQL Execution Failed")
                st.warning(error)

            else:
                st.success("SQL Generated Successfully")

                st.session_state.chat_history.append(
                    {
                        "question": user_question,
                        "sql": sql_query,
                        "explanation": explanation,
                        "result": result
                    }
                )

                st.rerun()

        else:
            st.warning("Please enter a question.")

    for chat in reversed(st.session_state.chat_history):

        st.markdown("---")

        st.subheader("User Question")
        st.write(chat["question"])

        st.subheader("Generated SQL")
        st.code(chat["sql"], language="sql")

        st.subheader("SQL Explanation")
        st.info(chat["explanation"].replace("$", "\\$"))

        st.subheader("Query Result")
        st.dataframe(chat["result"], use_container_width=True)

        df = chat["result"]

        if len(df.columns) >= 2:

            try:
                first_col = df.columns[0]
                second_col = df.columns[1]

                if df[second_col].dtype in ["int64", "float64", "int32", "float32"]:
                    st.subheader("Visualization")
                    chart_df = df.set_index(first_col)
                    st.bar_chart(chart_df)

            except Exception:
                pass

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="query_result.csv",
            mime="text/csv",
            key=f"download_{chat['question']}"
        )