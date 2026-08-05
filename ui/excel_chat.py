import os
import time
import streamlit as st

from excel_agent.data_loader import load_sheet_by_name, DATA_FILE_PATH
from excel_agent.code_generator import generate_pandas_code, explain_pandas_code
from excel_agent.code_executor import execute_pandas_code


def show_excel_chat():

    st.title("Excel / CSV Agent")

    st.write("Ask questions about the company spreadsheet in plain English.")

    if st.session_state.get("excel_load_error"):
        st.error(st.session_state.excel_load_error)
        return

    df = st.session_state.excel_df

    if st.session_state.excel_sheet_names and len(st.session_state.excel_sheet_names) > 1:

        selected_sheet = st.selectbox("Sheet:", st.session_state.excel_sheet_names)

        new_df, sheet_error = load_sheet_by_name(selected_sheet)

        if sheet_error:
            st.error(sheet_error)
            return

        df = new_df
        st.session_state.excel_df = df

    st.subheader("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Questions", value=len(st.session_state.excel_chat_history))

    with col2:
        st.metric(label="Source", value=os.path.basename(DATA_FILE_PATH))

    with col3:
        st.metric(label="Rows", value=len(df))

    with col4:
        st.metric(label="Columns", value=len(df.columns))

    st.markdown("---")

    with st.expander("Preview data"):
        st.dataframe(df.head(20), use_container_width=True)

    left, right = st.columns([2, 1])

    with left:
        st.subheader("Ask a Question")

        user_question = st.text_input("Ask your question about this data:")

        generate_clicked = st.button("Generate Answer")

    with right:
        st.subheader("Recent Questions")

        if st.session_state.excel_chat_history:
            recent = st.session_state.excel_chat_history[-5:]
            for chat in reversed(recent):
                st.caption("• " + chat["question"])
        else:
            st.caption("No questions yet.")

    if generate_clicked:

        if user_question:

            status = st.empty()

            status.info("Understanding your question...")
            time.sleep(0.5)

            status.info("Generating pandas code...")
            code = generate_pandas_code(user_question, df, st.session_state.excel_chat_history)

            time.sleep(0.5)

            status.info("Explaining code...")
            explanation = explain_pandas_code(code)

            time.sleep(0.5)

            status.info("Running analysis...")
            result, error = execute_pandas_code(code, df)

            time.sleep(0.5)

            status.empty()

            if error:
                st.error("Analysis Failed")
                st.warning(error)

            else:
                st.success("Answer Generated Successfully")

                st.session_state.excel_chat_history.append(
                    {
                        "question": user_question,
                        "code": code,
                        "explanation": explanation,
                        "result": result
                    }
                )

                st.rerun()

        else:
            st.warning("Please enter a question.")

    for chat in reversed(st.session_state.excel_chat_history):

        st.markdown("---")

        st.subheader("User Question")
        st.write(chat["question"])

        st.subheader("Generated Pandas Code")
        st.code(chat["code"], language="python")

        st.subheader("Explanation")
        st.info(chat["explanation"].replace("$", "\\$"))

        st.subheader("Result")
        st.dataframe(chat["result"], use_container_width=True)

        result_df = chat["result"]

        if len(result_df.columns) >= 2:

            try:
                first_col = result_df.columns[0]
                second_col = result_df.columns[1]

                if result_df[second_col].dtype in ["int64", "float64", "int32", "float32"]:
                    st.subheader("Visualization")
                    chart_df = result_df.set_index(first_col)
                    st.bar_chart(chart_df)

            except Exception:
                pass

        csv = result_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Result CSV",
            data=csv,
            file_name="query_result.csv",
            mime="text/csv",
            key=f"excel_download_{chat['question']}"
        )