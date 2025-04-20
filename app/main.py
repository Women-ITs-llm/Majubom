import streamlit as st
import sys
import os
from PIL import Image
from base64 import b64encode

# 프로젝트 루트 경로를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RAG_chatbot.model import RAGModel
from app.components.user_info import UserInfoForm
from app.components.chat_ui import ChatInterface

def init_session_state():
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "rag_model" not in st.session_state:
        st.session_state.rag_model = RAGModel()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def render_logo_and_title():
    logo_path = os.path.join(os.path.dirname(__file__), "static/images/logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 30px;'>
                <img src="data:image/png;base64,{logo_base64}" width="100"/>
                <h1 style='font-size: 28px; margin-top: 15px;'>다문화가족 상담 도우미 마주봄👩‍💼</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.title("다문화가족 상담 도우미 마주봄👩‍💼")

def main():
    init_session_state()

    st.set_page_config(page_title="다문화가족 상담 도우미 마주봄👩‍💼", layout="centered")

    render_logo_and_title()

    if st.session_state.user_info is None:
        UserInfoForm().display()
    else:
        ChatInterface(
            rag_model=st.session_state.rag_model,
            user_info=st.session_state.user_info,
            chat_history=st.session_state.chat_history
        ).display()

if __name__ == "__main__":
    main()
