import streamlit as st

class UserInfoForm:
    def display(self):
        st.subheader("기본 정보 입력")
        
        with st.form("user_info_form"):
            # 출신 국가 선택
            origin_country = st.selectbox(
                "출신 국가",
                options=["베트남", "중국", "필리핀", "태국", "캄보디아", "일본", "몽골", "네팔", "우즈베키스탄", "기타"],
            )
            
            # 출신 국가에 따른 기본 언어 매핑
            language_map = {
                "베트남": "베트남어",
                "중국": "중국어",
                "필리핀": "타갈로그어",
                "태국": "태국어",
                "캄보디아": "크메르어",
                "일본": "일본어",
                "몽골": "몽골어",
                "네팔": "네팔어",
                "우즈베키스탄": "우즈베크어",
                "기타": "영어"
            }
            
            # 기본 언어 설정
            default_language = language_map.get(origin_country, "한국어")
            
            # 체류 자격 상태
            visa_status = st.selectbox(
                "체류 자격 상태",
                options=["결혼이민", "국적취득", "방문동거", "기타"],
            )
            
            # 거주 지역
            residence_area = st.text_input("거주 지역 (예: 강남구)")
            
            # 가족 구성원
            family_members = st.multiselect(
                "가족 구성원",
                options=["배우자", "자녀", "배우자의 부모", "본국 가족"],
            )
            
            # 관심 분야
            interests = st.multiselect(
                "관심 분야",
                options=["비자/체류", "국적취득", "자녀교육", "취업/일자리", "의료/건강", "복지혜택", "가정폭력", "문화적응"],
            )
            
            # 폼 제출 버튼
            submitted = st.form_submit_button("저장")
            
            if submitted:
                # 필수 필드 검증
                if not residence_area:
                    st.error("거주 지역을 입력해주세요.")
                    return
                
                # 사용자 정보 저장 (선호 언어는 출신 국가 기반으로 자동 설정)
                st.session_state.user_info = {
                    "origin_country": origin_country,
                    "preferred_language": default_language,  # 출신 국가에 따른 언어 자동 설정
                    "visa_status": visa_status,
                    "residence_area": residence_area,
                    "family_members": family_members,
                    "interests": interests
                }
                
                # 성공 메시지
                st.success("정보가 저장되었습니다!")
                
                # 페이지 리로드
                st.rerun() 