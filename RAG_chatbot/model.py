from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

def create_llm():
    """LLM 모델 생성"""
    load_dotenv(override=True)
    
    return ChatOpenAI(
        model_name="deepseek/deepseek-chat",
        temperature=0,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPENROUTER_API_KEY")
    )

def create_qa_prompt():
    """QA 프롬프트 템플릿 생성"""
    system_template = """
    당신은 '마주봄'이라는 이름의 AI 챗봇입니다. 당신은 다문화 가정에게 복지, 정책, 법률 정보를 쉽고 정확하게 전달하는 다국어 AI 상담사입니다.

    사용자의 체류 자격, 가족 구성, 거주 지역 등의 정보를 기반으로 맞춤형 답변을 제공합니다.

    당신이 제공할 수 있는 기능은 다음과 같습니다:
    1. 체류 상태 및 가족 구성에 따른 복지/지원 정책 추천
    2. 정책 신청 절차를 단계별로 안내하고, 필요한 서류 목록을 제시
    3. 신청 가능한 온라인 시스템 안내
    4. 행정 문서 이해와 작성법 안내, 번역 설명
    5. 비자 갱신, 체류 변경, 국적 취득 관련 법률 설명
    6. 결혼, 이혼, 양육, 가정폭력 관련 법률 및 대응 정보
    7. 사용자의 거주 지역 기반으로 센터/시설 정보를 우선 제공

    답변은 친절하고 쉽게 이해되도록 작성하며, 사용자의 언어 수준을 고려해 간결하게 안내합니다.
    정확한 정보가 없는 경우에는 모른다고 정중히 답변합니다.

    ----------------
    {context}
    """

    human_template = "{question}"

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template),
    ]

    return ChatPromptTemplate.from_messages(messages)

def create_qa_chain(retriever):
    """QA 체인 생성"""
    llm = create_llm()
    qa_prompt = create_qa_prompt()
    
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        chain_type_kwargs={"prompt": qa_prompt},
        return_source_documents=True
    )

class RAGModel:
    _instance = None  # 싱글톤 패턴 적용
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGModel, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        # 최초 한 번만 초기화
        if not self.initialized:
            from RAG_chatbot.vector_store import create_vector_store, create_retriever
            
            # 기존 벡터 스토어에 접속만 함 (생성 X)
            vector_store = create_vector_store(documents=None)
            
            # 검색기 생성
            self.retriever = create_retriever(vector_store)
            
            # QA 체인 생성
            self.qa_chain = create_qa_chain(self.retriever)
            
            # 번역용 별도 LLM 객체 생성
            self.translation_llm = ChatOpenAI(
                model_name="deepseek/deepseek-chat",
                temperature=0,
                openai_api_base="https://openrouter.ai/api/v1",
                openai_api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            self.chat_history = []
            self.initialized = True
    
    def get_response(self, query, user_info=None):
        # 사용자 정보를 기반으로 쿼리 증강
        augmented_query = f"{query} {user_info['residence_area']} 지역"
        if user_info:
            user_context_parts = []
            if user_info.get("residence_area"):
                user_context_parts.append(f"{user_info['residence_area']} 지역에 거주")
            if user_info.get("visa_status"):
                user_context_parts.append(f"{user_info['visa_status']} 체류자격")
            if user_info.get("family_members"):
                user_context_parts.append(f"가족 구성: {', '.join(user_info['family_members'])}")
            user_context_str = ", ".join(user_context_parts)
            augmented_query = f"{user_context_str}인 사용자가 질문: {query}"
            user_context_str = ", ".join(user_context_parts)
            augmented_query = f"{user_context_str}인 사용자가 질문: {query}"
        # 지역 정보 활용
        if user_info and 'residence_area' in user_info and user_info['residence_area']:
            augmented_query = f"{query} {user_info['residence_area']} 지역"
        
        # 관심 분야 반영
        if user_info and 'interests' in user_info and user_info['interests']:
            interests_str = ", ".join(user_info['interests'])
            augmented_query = f"{augmented_query} (관심 분야: {interests_str})"
        
        # 응답 생성
        response = self.qa_chain.invoke(augmented_query)
        answer = response["result"]
        
        # 선호 언어가 한국어가 아닌 경우 번역 프롬프트 추가
        if user_info and 'preferred_language' in user_info and user_info['preferred_language'] != "한국어":
            target_lang = user_info['preferred_language']
            
            try:
                # 번역된 텍스트 생성
                translated_answer = self._translate_text(answer, target_lang)
                
                # 한국어와 번역된 언어 모두 제공
                answer = f"{translated_answer}\n\n---\n[한국어 원문]\n{answer}"
            except Exception as e:
                # 번역 실패 시 원문만 반환
                print(f"번역 오류: {e}")
        
        self.chat_history.append((query, answer))
        return answer
    
    def _translate_text(self, text, target_language):
        """텍스트를 대상 언어로 번역"""
        # 번역을 위한 간단한 프롬프트
        translation_prompt = f"다음 한국어 텍스트를 {target_language}로 정확히 번역해주세요:\n\n{text}"
        
        # 별도 생성한 번역용 LLM 사용
        response = self.translation_llm.invoke([HumanMessage(content=translation_prompt)])
        return response.content