import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from RAG_chatbot.data_loader import load_all_hanultari_jsons, split_documents
from RAG_chatbot.vector_store import create_vector_store

def main():
    # ✅ 한울타리 JSON 여러 개 로드
    docs = load_all_hanultari_jsons("RAG_chatbot/data")

    # ✅ 텍스트 청크로 분할
    chunks = split_documents(docs)

    # ✅ 벡터 DB에 저장
    vector_store = create_vector_store(documents=chunks)
    print(f"✅ {len(chunks)}개의 JSON 청크가 벡터 DB에 저장되었습니다.")

if __name__ == "__main__":
    main()
