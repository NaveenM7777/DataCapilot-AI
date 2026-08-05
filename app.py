import streamlit as st
from streamlit_option_menu import option_menu

from ui.theme import apply_theme
from ui.sql_chat import show_sql_chat
from ui.excel_chat import show_excel_chat
from ui.pdf_chat import show_pdf_chat
from ui.ai_chat import show_ai_chat

from excel_agent.data_loader import load_default_data, get_file_modified_time as excel_mtime
from pdf_agent.pdf_loader import load_default_pdf, chunk_text, get_file_modified_time as pdf_mtime


st.set_page_config(
    page_title="DataCapilot AI",
    page_icon="D",
    layout="wide"
)

apply_theme()


current_excel_mtime = excel_mtime()

if (
    "excel_df" not in st.session_state
    or st.session_state.get("excel_loaded_mtime") != current_excel_mtime
):
    df, sheet_names, error = load_default_data()

    st.session_state.excel_df = df
    st.session_state.excel_sheet_names = sheet_names
    st.session_state.excel_load_error = error
    st.session_state.excel_loaded_mtime = current_excel_mtime

    if "excel_chat_history" not in st.session_state:
        st.session_state.excel_chat_history = []


current_pdf_mtime = pdf_mtime()

if (
    "pdf_chunks" not in st.session_state
    or st.session_state.get("pdf_loaded_mtime") != current_pdf_mtime
):
    full_text, page_texts, page_count, error = load_default_pdf()

    if error:
        st.session_state.pdf_chunks = None
        st.session_state.pdf_load_error = error
    else:
        st.session_state.pdf_chunks = chunk_text(page_texts)
        st.session_state.pdf_page_count = page_count
        st.session_state.pdf_load_error = None

    st.session_state.pdf_loaded_mtime = current_pdf_mtime

    if "pdf_chat_history" not in st.session_state:
        st.session_state.pdf_chat_history = []


with st.sidebar:

    st.markdown(
        "<h2 style='text-align:center;'>DataCapilot AI</h2>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<p style='text-align:center; opacity:0.6;'>AI Powered Data Assistant</p>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    selected = option_menu(

        menu_title=None,

        options=[
            "SQL Assistant", "Excel Agent", "PDF Agent", "AI Agent"
        ],

        icons=[
            "database", "file-earmark-spreadsheet", "file-earmark-text", "cpu"
        ],

        menu_icon="cast",

        default_index=0,

        styles={
            "container": {"padding": "5px", "background-color": "transparent"},
            "icon": {"color": "#8a93a8", "font-size": "18px"},
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "4px",
                "border-radius": "8px",
                "color": "#cbd3e1",
                "--hover-color": "#161d2e"
            },
            "nav-link-selected": {
                "background-color": "#2d5f5a",
                "color": "#e8ecf3",
                "font-weight": "600",
                "border": "1px solid #4fd1c5"
            },
        }
    )

    st.markdown("---")

    st.markdown("### Database")

    st.success("SQLite — Chinook Sample DB")

    st.markdown("### AI Model")

    st.info("Llama 3.3 70B (Groq)")


if selected == "SQL Assistant":

    show_sql_chat()

elif selected == "Excel Agent":

    show_excel_chat()

elif selected == "PDF Agent":

    show_pdf_chat()

elif selected == "AI Agent":

    show_ai_chat()