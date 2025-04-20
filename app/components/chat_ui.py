import streamlit as st
import sys
import os
from PIL import Image

# 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from RAG_chatbot.model import RAGModel

# 응답 캐싱
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(query, user_info_str):
    user_info = eval(user_info_str)
    model = RAGModel()
    return model.get_response(query, user_info)

# 국가 코드 to 이모지 플래그
COUNTRY_FLAGS = {
    "베트남": "🇻🇳",
    "중국": "🇨🇳",
    "필리핀": "🇵🇭",
    "우즈베키스탄": "🇺🇿",
    "태국": "🇹🇭",
    "몽골": "🇲🇳",
    "한국": "🇰🇷",
    "기타": "🌐"
}

class ChatInterface:
    def __init__(self, user_info: dict, rag_model: RAGModel, chat_history: list):
        self.user_info = user_info
        self.rag_model = rag_model
        self.chat_history = chat_history

        # 봇 아이콘 경로 설정
        # self.bot_icon_path = "https://imagekit.io/tools/asset-public-link?detail=%7B%22name%22%3A%22bot_icon.png%22%2C%22type%22%3A%22image%2Fpng%22%2C%22signedurl_expire%22%3A%222028-04-18T13%3A03%3A22.232Z%22%2C%22signedUrl%22%3A%22https%3A%2F%2Fmedia-hosting.imagekit.io%2F20728253eccb4c4d%2Fbot_icon.png%3FExpires%3D1839675802%26Key-Pair-Id%3DK2ZIVPTIP2VGHC%26Signature%3DHcAOIpNOVe5vIwjJWWdxlTEVD3ZEZCwpr3Jw~AqcDGkfmxadi1VAU9ZwKEHwang3x9gMH99Bb-7CipRI61-ZzaNKC4B9tmG7MP4HyOTGFC39syzteLb2OB1cLtV~6DicOgJVURTrQRRe5c8oovBcIUN1D528vqgbar4tVerT8aK2lCBsMiJkZYzlKxv3TyHjQeaDW4vONWhtFjumVh6mTRHfE72J1yLc3eqKXQRTUYU3aKSg2YUiq2PHPn4-ah2QKYebPlBZrKAF621v0eaXutCCRMcYn1VikRp1eJ2DZSIWMI9t~aOcQTk5i6q-sF~8tlu6KZugQojZFyCJ5JXe8w__%22%7D"

    def show_user_info(self):
        with st.sidebar:
            st.subheader("사용자 정보")

            flag = COUNTRY_FLAGS.get(self.user_info["origin_country"], "🌐")
            st.write(f"출신 국가: {self.user_info['origin_country']} {flag}")
            st.write(f"체류 자격: {self.user_info['visa_status']}")
            st.write(f"거주 지역: {self.user_info['residence_area']}")
            st.write(f"가족 구성원: {', '.join(self.user_info['family_members'])}")
            st.write(f"관심 분야: {', '.join(self.user_info['interests'])}")
            st.write(f"선호 언어: {self.user_info['preferred_language']}")

            if st.button("정보 수정"):
                st.session_state.user_info = None
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
        st.subheader("무엇을 도와드릴까요?")
        self.show_chat_history()
        self.handle_user_input()

    def handle_user_input(self):
        self.query = st.chat_input("질문을 입력하세요...")
        if self.query:
            with st.chat_message("user"):
                st.write(self.query)
            self.chat_history.append({"role": "user", "content": self.query})

            with st.spinner("답변 생성 중..."):
                response = get_cached_response(self.query, str(self.user_info))

            with st.chat_message("assistant"):
                st.write(response)
            self.chat_history.append({"role": "assistant", "content": response})
