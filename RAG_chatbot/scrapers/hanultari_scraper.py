from browser_use import Agent
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
llm = ChatOpenAI(base_url='https://openrouter.ai/api/v1', model='openai/o4-mini', api_key=api_key)
print(api_key)

async def fetch_hanultari_documents() -> list[Document]:
    agent = Agent(
        task="""
        Visit https://www.mcfamily.or.kr/programs/family
        and extract multicultural family support programs in Korean.
        If there are multiple programs pages, move to the next page and extract the information.
        Provide titles and summaries suitable for immigrants.
        """,
        llm = llm
        # llm=ChatOpenAI(
        #     model="deepseek-chat",  # or "deepseek-v3-base"
        #     openai_api_base="https://openrouter.ai/api/v1",
        #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        # ),
    )
    result = await agent.run()

    if isinstance(result, str):
        return [Document(page_content=block.strip()) for block in result.split("\n\n") if block.strip()]
    else:
        return []

# CLI 실행 시 테스트
if __name__ == "__main__":
    documents = asyncio.run(fetch_hanultari_documents())
    print(f"📄 총 {len(documents)}개의 문서 수집 완료")
    for doc in documents:
        print("🧾", doc.page_content[:100], "...")