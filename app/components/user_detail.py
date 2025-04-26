import streamlit as st
from app.components.translations import (
    LANG_CODE_MAP,
    get_translation,
    reverse_value_translation,
    translate_options
)

class UserDetailForm:
    def display(self):
        user_info = st.session_state.get("user_info")

        lang = LANG_CODE_MAP.get(user_info["preferred_language"], "ko")

        st.subheader(get_translation(lang, "detailed_info"))

        visa_options = ["결혼이민", "국적취득", "방문동거", "기타"]
        family_options = ["배우자", "자녀", "배우자의 부모", "본국 가족"]
        interest_options = [
            "비자/체류", "국적취득", "자녀교육", "취업/일자리",
            "의료/건강", "복지혜택", "가정폭력", "문화적응"
        ]

        translated_visa = translate_options(visa_options, lang)
        translated_family = translate_options(family_options, lang)
        translated_interests = translate_options(interest_options, lang)

        with st.form(key=f"user_detail_form_{st.session_state.get('step', 'detail')}"):
            visa_status_display = st.selectbox(get_translation(lang, "visa_status"), translated_visa)
            residence_area = st.text_input(f"{get_translation(lang, 'residence_area')} \n{get_translation(lang, 'write_korean')} \n(강남구, 금천구, ...)")
            family_members_display = st.multiselect(get_translation(lang, "family_members"), translated_family)
            interests_display = st.multiselect(get_translation(lang, "interests"), translated_interests)
            submitted = st.form_submit_button(get_translation(lang, "save_button"))

            if submitted:
                # 필수 필드 검증
                if not residence_area:
                    st.error(get_translation(lang, "write_residence"))
                    return
                
                st.session_state.user_info.update({
                    "visa_status": reverse_value_translation(lang, visa_status_display),
                    "residence_area": residence_area,
                    "family_members": [reverse_value_translation(lang, f) for f in family_members_display],
                    "interests": [reverse_value_translation(lang, i) for i in interests_display]
                })

                st.success(get_translation(lang, "info_saved"))
                st.session_state.step = "chat"
                st.rerun()