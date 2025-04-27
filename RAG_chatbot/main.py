from data_loader import (
    load_pdfs,
    load_center_data,
    load_all_hanultari_jsons,
    create_text_splitter,
    split_documents,
)
from vector_store import create_vector_store, create_retriever
from model import create_qa_chain

def main():
    # 텍스트 분할기 생성
    text_splitter = create_text_splitter()
    
    # 법률 PDF 로드 및 분할
    print("법률 PDF 파일 로딩 중...")
    docs = load_pdfs("data/")
    print(docs)
    texts = split_documents(docs, text_splitter)
    
    # 벡터 스토어 생성 및 법률 데이터 추가
    print("벡터 스토어 생성 및 법률 데이터 추가 중...")
    vector_store = create_vector_store(texts)
    
    # 다문화가족지원센터 데이터 로드
    print("다문화가족지원센터 데이터 로딩 중...")
    center_pdf = "data/다문화가족지원센터현황(공공데이터).pdf"
    center_docs = load_center_data(center_pdf)

    # 한울타리 JSON 데이터 로드
    print("한울타리 정책 프로그램 데이터 로딩 중...")
    hanultari_docs = load_all_hanultari_jsons("data/")
    hanultari_chunks = split_documents(hanultari_docs, text_splitter)
    vector_store.add_documents(hanultari_chunks)
    print(f"한울타리 프로그램 데이터 {len(hanultari_chunks)}개 청크가 추가되었습니다.")
    
    # 다문화가족지원센터 데이터 분할 및 추가
    center_chunks = split_documents(center_docs, text_splitter)
    vector_store.add_documents(center_chunks)
    print(f"다문화가족지원센터 데이터 {len(center_chunks)}개 청크가 추가되었습니다.")
    
    # 리트리버 생성
    retriever = create_retriever(vector_store)
    
    # QA 체인 생성
    qa_chain = create_qa_chain(retriever)
    
    # 테스트 쿼리
    query = "10개월 된 아이가 있는 베트남 출신 결혼이민자로서 받을 수 있는 지원 정책과 이용할 수 있는 시설이 알고 싶어요."
    print("\n테스트 쿼리:", query)
    response = qa_chain.invoke(query)
    print("\n응답:", response["result"])

if __name__ == "__main__":
    main()