import streamlit as st
import sys
import os
from PIL import Image

# 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from RAG_chatbot.model import RAGModel
from app.components.translations import TRANSLATIONS, VALUE_TRANSLATIONS, LANG_CODE_MAP, COUNTRY_FLAGS, get_translation, get_value_translation

# 응답 캐싱
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(query, user_info_str):
    user_info = eval(user_info_str)
    model = RAGModel()
    return model.get_response(query, user_info)


class ChatInterface:
    def __init__(self, user_info: dict, rag_model: RAGModel, chat_history: list):
        self.user_info = user_info
        self.rag_model = rag_model
        self.chat_history = chat_history
        self.lang = LANG_CODE_MAP.get(self.user_info["preferred_language"], "ko")
        self.t = TRANSLATIONS[self.lang]

    def show_user_info(self):
        with st.sidebar:
            st.subheader(self.t["sidebar_title"])

            vt = VALUE_TRANSLATIONS.get(self.lang, {})

            origin_country_translated = get_value_translation(self.lang, self.user_info["origin_country"])
            preferred_language_translated = get_value_translation(self.lang, self.user_info["preferred_language"])
            flag = COUNTRY_FLAGS.get(self.user_info["origin_country"], "🌐")

            st.write(f"{self.t['origin_country']}: {origin_country_translated} {flag}")
            st.write(f"{self.t['visa_status']}: {vt.get(self.user_info['visa_status'], self.user_info['visa_status'])}")
            st.write(f"{self.t['residence_area']}: {self.user_info['residence_area']}")
            st.write(f"{self.t['family_members']}: {', '.join([vt.get(f, f) for f in self.user_info['family_members']])}")
            st.write(f"{self.t['interests']}: {', '.join([vt.get(i, i) for i in self.user_info['interests']])}")
            st.write(f"{self.t['preferred_language']}: {preferred_language_translated}")

            if st.button(self.t["edit_button"]):
                st.session_state.step = "detail"  # ✅ detail 단계로 이동
                st.rerun()

    def show_chat_history(self):
        for message in self.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

    def display(self):
        self.show_user_info()
        st.subheader(self.t["help_title"])
        self.show_chat_history()
        self.handle_user_input()

    def handle_user_input(self):
        self.query = st.chat_input(self.t["chat_input"])
        if self.query:
            with st.chat_message("user"):
                st.write(self.query)
            self.chat_history.append({"role": "user", "content": self.query})

            with st.spinner(self.t["chat_spinner"]):
                response = get_cached_response(self.query, str(self.user_info))

            with st.chat_message("assistant"):
                st.write(response)
            self.chat_history.append({"role": "assistant", "content": response})
