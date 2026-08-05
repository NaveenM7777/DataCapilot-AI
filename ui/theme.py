import streamlit as st


def apply_theme():

    st.markdown("""
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background-color: #0f1420;
            color: #cbd3e1;
        }

        h1, h2, h3 {
            font-family: 'Inter', sans-serif !important;
            color: #f1f4f9 !important;
            font-weight: 600 !important;
        }

        h1 {
            color: #ffffff !important;
            font-weight: 700 !important;
            border-bottom: 1px solid #263047;
            padding-bottom: 0.4em;
        }

        .main .block-container {
            animation: fadeIn 0.4s ease-out;
        }

        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(8px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        div[data-testid="stMetric"], .stDataFrame, div[data-testid="stExpander"] {
            background: #161d2e;
            border: 1px solid #263047;
            border-radius: 10px;
            padding: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
            transition: border 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            border: 1px solid #3b4a6b;
        }

        div[data-testid="stMetricValue"] {
            color: #f1f4f9 !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #8a93a8 !important;
        }

        .stAlert {
            border-radius: 10px;
            border: 1px solid #263047;
            background: #161d2e;
        }

        .stButton > button, .stDownloadButton > button {
            background: #2d5f5a;
            color: #e8ecf3;
            font-weight: 500;
            border: 1px solid #4fd1c5;
            border-radius: 8px;
            padding: 0.5em 1.3em;
            transition: all 0.2s ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            background: #357b73;
            border: 1px solid #6ee0d5;
            box-shadow: 0 2px 8px rgba(79, 209, 197, 0.15);
        }

        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #161d2e !important;
            border: 1px solid #263047 !important;
            border-radius: 8px !important;
            color: #e8ecf3 !important;
        }

        .stTextInput input:focus {
            border: 1px solid #4fd1c5 !important;
            box-shadow: 0 0 0 1px #4fd1c5 !important;
        }

        div[data-testid="stChatMessage"] {
            background: #161d2e;
            border-radius: 10px;
            border: 1px solid #263047;
        }

        section[data-testid="stSidebar"] {
            background: #0b0f18;
            border-right: 1px solid #263047;
        }

        .stCodeBlock, pre {
            border: 1px solid #263047 !important;
            border-radius: 8px !important;
            background: #0b0f18 !important;
        }

        .stSpinner > div {
            border-top-color: #4fd1c5 !important;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0f1420;
        }
        ::-webkit-scrollbar-thumb {
            background: #263047;
            border-radius: 10px;
        }

        </style>
    """, unsafe_allow_html=True)