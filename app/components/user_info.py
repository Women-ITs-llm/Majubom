import streamlit as st

from app.components.translations import COUNTRY_DISPLAY_TO_KEY, LANGUAGE_DISPLAY_TO_KEY, LANGUAGE_MAP

COUNTRY_OPTIONS = list(COUNTRY_DISPLAY_TO_KEY.keys())
LANGUAGE_OPTIONS = list(LANGUAGE_DISPLAY_TO_KEY.keys())

class UserInfoForm:
    def display(self):
        st.subheader("기본 정보 입력")

        with st.form(key=f"{st.session_state.get('step', 'basic')}"):
            selected_country_display = st.selectbox("출신 국가", COUNTRY_OPTIONS)
            origin_country = COUNTRY_DISPLAY_TO_KEY[selected_country_display]

            # 기본 언어 설정 (선택 UI의 초기값)
            default_language_name = LANGUAGE_MAP.get(origin_country, "한국어")
            default_display = next(k for k, v in LANGUAGE_DISPLAY_TO_KEY.items() if v == default_language_name)

            # 사용자가 선호 언어 선택
            selected_language_display = st.selectbox(
                "선호 언어",
                LANGUAGE_OPTIONS,
                index=LANGUAGE_OPTIONS.index(default_display)
            )

            # 최종적으로 선택된 언어를 저장
            preferred_language = LANGUAGE_DISPLAY_TO_KEY[selected_language_display]

            submitted = st.form_submit_button("저장")

            if submitted:
                st.session_state.user_info = {
                    "origin_country": origin_country,
                    "preferred_language": preferred_language
                }
                st.success("정보가 저장되었습니다!")
                st.session_state.step = "detail"
                st.rerun()
