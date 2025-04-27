import os
import sys
import asyncio
import json
from datetime import date
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from browser_use import Agent, Controller

# 경로 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

load_dotenv()

# ✅ Pydantic 모델 정의
class KoreanProgram(BaseModel):
    title: str
    summary: str
    location: str
    dates: str

class KoreanPrograms(BaseModel):
    programs: List[KoreanProgram]

# ✅ Controller 선언
controller = Controller(output_model=KoreanPrograms)

# ✅ 실행 함수
async def fetch_hanultari_data():
    agent = Agent(
        task="""
        Visit https://mcfamily.or.kr/programs/family?page=2.
        Extract all multicultural family support programs.
        Each object should include: "title", "summary", "location", and "dates".
        Return only a valid JSON object with the key "programs".
        """,
        controller=controller,
        llm=ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    )

    # Agent 실행
    history = await agent.run()
    result = history.final_result()

    if not result:
        raise ValueError("❌ Agent 결과 없음")

    try:
        parsed: KoreanPrograms = KoreanPrograms.model_validate_json(result)
    except Exception as e:
        print("❌ Pydantic 파싱 실패:", e)
        print("🔍 원본 결과:", result[:300])
        raise

    # JSON 저장
    os.makedirs("RAG_chatbot/data", exist_ok=True)
    save_path = f"RAG_chatbot/data/hanultari_{date.today()}.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(parsed.dict(), f, ensure_ascii=False, indent=2)

    print(f"✅ 총 {len(parsed.programs)}개의 프로그램 정보를 저장했습니다.")
    print(f"📁 저장 경로: {save_path}")

if __name__ == "__main__":
    asyncio.run(fetch_hanultari_data())
