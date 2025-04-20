# RAG_chatbot/scripts/update_hanultari.py

import os
import sys
import re
import asyncio
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from browser_use import Agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from RAG_chatbot.vector_store import create_vector_store

# 경로 및 환경 변수 설정
load_dotenv()

def parse_markdown_result(result: str) -> list[Document]:
    """Agent가 반환한 markdown 문자열에서 프로그램 정보를 파싱해 Document 리스트로 변환"""
    program_blocks = re.split(r"\n\d+\.\s+\*\*Title\*\*:", result.strip())
    documents = []

    for block in program_blocks[1:]:  # 첫 번째는 빈 문자열일 수 있음
        title_match = re.search(r"^(.*?)\n", block)
        summary_match = re.search(r"\*\*Summary\*\*: (.*?)\n", block)
        location_match = re.search(r"\*\*Location\*\*: (.*?)\n", block)
        date_match = re.search(r"\*\*Date\*\*: (.*)", block)

        parts = []
        if title_match:
            parts.append("Title: " + title_match.group(1).strip())
        if summary_match:
            parts.append("Summary: " + summary_match.group(1).strip())
        if location_match:
            parts.append("Location: " + location_match.group(1).strip())
        if date_match:
            parts.append("Date: " + date_match.group(1).strip())

        if parts:
            doc = Document(page_content="\n".join(parts), metadata={"source": "hanultari"})
            documents.append(doc)

    return documents


async def fetch_hanultari_documents() -> tuple[list[Document], str]:
    """한울타리 사이트에서 다문화가족 지원 프로그램을 추출해 Document 리스트로 반환"""
    agent = Agent(
        task="""
        Visit https://mcfamily.or.kr/ko/programs/family?page=1
        Extract only the first 10 multicultural family support programs in Korean.
        Include: title, summary, location, and date.
        Do not include HTML or unrelated information.
        """,
        llm=ChatOpenAI(
            model="deepseek/deepseek-chat:free",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            max_tokens=2048
        ),
    )

    result = await agent.run()

    if isinstance(result, str):
        documents = parse_markdown_result(result)
    else:
        documents = []

    return documents, result


def main():
    print("\n🌐 한울타리 정책 크롤링 중...")
    documents, raw_result = asyncio.run(fetch_hanultari_documents())

    if not documents:
        print("\u274c 크롤링된 문서가 없습니다. 응답 미리보기 ↓")
        print(raw_result)
        return

    print(f"\ud83d\udcc4 \ubb38서 수: {len(documents)}개")

    print("\n\ud83d\udcca 기존 벡터 스토어에 연결 중...")
    vector_store = create_vector_store()

    print("\ud83e\udde0 \ubb38서들을 벡터 스토어에 추가 중...")
    vector_store.add_documents(documents)

    print("\u2705 한울타리 정책 정보가 벡터 DB에 성공적으로 업데이트되었습니다!")


if __name__ == "__main__":
    main()