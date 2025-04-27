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
    load_dotenv(dotenv_path="./.env")
    
    return ChatOpenAI(
        model_name="gpt-4.1-mini",
        temperature=0,
        # openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

def create_qa_prompt(user_info=None):
    """QA 프롬프트 템플릿 생성 (사용자 정보 포함)"""

    # 1️⃣ 사용자 정보 문자열 생성
    user_context = ""
    if user_info:
        parts = []
        if user_info.get("residence_area"):
            parts.append(f"거주 지역: {user_info['residence_area']}")
        if user_info.get("visa_status"):
            parts.append(f"체류 자격: {user_info['visa_status']}")
        if user_info.get("family_members"):
            parts.append(f"가족 구성: {', '.join(user_info['family_members'])}")
        if user_info.get("interests"):
            parts.append(f"관심 분야: {', '.join(user_info['interests'])}")
        
        if parts:
            user_context = "\n\n[사용자 정보]\n" + "\n".join(parts)

    # 2️⃣ System Prompt에 사용자 정보 포함
    system_template = f"""
    당신은 '마주봄'이라는 이름의 AI 챗봇입니다. 당신은 다문화 가정에게 복지, 정책, 법률 정보를 쉽고 정확하게 전달하는 다국어 AI 상담사입니다.

    사용자의 체류 자격, 가족 구성, 거주 지역 등의 정보를 기반으로 맞춤형 답변을 제공합니다.
    사용자의 질문에 대한 답변을 최우선으로 합니다.
    사용자의 질문이 애매하다면 사용자의 정보와 관련된 프로그램을 추천해즙니다.
    질문 이외의 사항을 답변할 경우 추가 제공된 답변임을 알려줍니다.

    {user_context}

    당신이 제공할 수 있는 카테고리는 다음과 같습니다:
    1. 체류 상태 및 가족 구성에 따른 복지/지원 정책 추천
    2. 정책 신청 절차를 단계별로 안내하고, 필요한 서류 목록을 제시
    3. 신청 가능한 온라인 시스템 안내
    4. 행정 문서 이해와 작성법 안내, 번역 설명
    5. 비자 갱신, 체류 변경, 국적 취득 관련 법률 설명
    6. 결혼, 이혼, 양육, 가정폭력 관련 법률 및 대응 정보
    7. 사용자의 거주 지역 기반으로 센터/시설 정보를 우선 제공
    8. 다문화 가정 지원 프로그램 정보를 제공

    답변은 친절하고 쉽게 이해되도록 작성하며, 사용자의 언어 수준을 고려해 간결하게 안내합니다.
    다문화 가정 지원 프로그램은 거주 지역이 아니더라도 제공하면서, 다른 지역임을 알려주세요.
    다만 다문화 가정 지원 프로그램은 신청 기간이 지났을 경우 제공하지 않습니다.
    사용자에게 친절하고 공감하는 말투를 사용하세요.
    사용자의 상황을 고려해 추가로 궁금할 만한 것을 되물어보세요.
    단정 짓기보단 제안을 하듯 부드럽게 전달하세요. 예) "혹시 이런 정보도 필요하실까요?", "다른 지역에 사시는 경우도 알려주시면 더 도와드릴 수 있어요."
    정확한 정보가 없는 경우에는 모른다고 정중히 답변합니다.

    ----------------
    {{context}}
    """

    human_template = "{question}"

    messages = [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template),
    ]

    return ChatPromptTemplate.from_messages(messages)


def create_qa_chain(retriever, user_info=None):
    llm = create_llm()
    qa_prompt = create_qa_prompt(user_info=user_info)
    
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
            model_name="gpt-4.1-mini",
            temperature=0,
            # openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
            
            self.chat_history = []
            self.initialized = True
    
    def get_response(self, query, user_info=None):
        # 사용자 정보를 기반으로 쿼리 증강
        augmented_query = f"{query} {user_info['residence_area']} 지역"
        if user_info:
            parts = []
            if user_info.get("residence_area"):
                parts.append(f"{user_info['residence_area']} 지역에 거주")
            if user_info.get("visa_status"):
                parts.append(f"{user_info['visa_status']} 체류자격")
            if user_info.get("family_members"):
                parts.append(f"가족 구성: {', '.join(user_info['family_members'])}")
            if parts:
                augmented_query = f"{', '.join(parts)}인 사용자가 질문: {query}"
            
            if user_info.get('interests'):
                interests_str = ", ".join(user_info['interests'])
                augmented_query += f" (관심 분야: {interests_str})"
        
        # 응답 생성
        response = self.qa_chain.invoke(augmented_query)
        answer = response["result"]

        # 🔽 사용된 문서 제목 추출
        sources = response.get("source_documents", [])
        titles = []
        for doc in sources:
            title = doc.metadata.get("title") or doc.metadata.get("source")
            if title and title not in titles:
                titles.append(title)
        if titles:
            source_text = "\n\n📚 참고한 문서:\n" + "\n".join(f"- {t}" for t in titles)
            answer += source_text
        
        self.chat_history.append((query, answer))
        return answer
    
    def _translate_text(self, text, target_language):
        """텍스트를 대상 언어로 번역"""
        # 번역을 위한 간단한 프롬프트
        translation_prompt = f"다음 한국어 텍스트를 {target_language}로 정확히 번역해주세요:\n\n{text}"
        
        # 별도 생성한 번역용 LLM 사용
        response = self.translation_llm.invoke([HumanMessage(content=translation_prompt)])
        return response.content