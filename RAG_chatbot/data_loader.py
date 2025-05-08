# RAG_chatbot/data_loader.py
import os
import json
import glob
import requests
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain.text_splitter import CharacterTextSplitter

def load_pdfs(data_dir="data/"):
    """법률정보 PDF 파일들을 로드하여 Document 객체 리스트 반환"""
    pdf_files = glob.glob(f"{data_dir}/*.pdf")
    all_docs = []

    for file in pdf_files:
        loader = PyMuPDFLoader(file)
        docs = loader.load()
        all_docs.extend(docs)
    
    return all_docs

def load_center_data(center_pdf):
    """다문화가족지원센터 데이터 로딩 및 메타데이터 추가"""
    loader = PyMuPDFLoader(center_pdf)
    center_docs = loader.load()
    
    for doc in center_docs:
        doc.metadata["type"] = "center"
        doc.metadata["category"] = "multicultural_center"
    
    return center_docs

import glob

def load_hanultari_json(json_path: str) -> list[Document]:
    """JSON 파일을 Document 리스트로 변환"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    programs = data.get("programs") or data.get("multicultural_family_support_programs") or []
    documents = []

    for item in programs:
        content = "\n".join([
            f"Title: {item.get('title')}",
            f"Summary: {item.get('summary') or '정보 없음'}",
            f"Location: {item.get('location')}",
            f"Date: {item.get('dates') or item.get('date') or item.get('end_date') or '날짜 정보 없음'}"
        ])
        documents.append(Document(page_content=content, metadata={
            "source": os.path.basename(json_path),
            "type": "program",
            "category": "multicultural_policy"
        }))

    return documents

def load_all_hanultari_jsons(folder_path: str) -> list[Document]:
    """폴더 내 모든 한울타리 JSON 파일을 Document 리스트로 로딩"""
    """폴더 내 모든 JSON 파일을 Document 리스트로 로딩하므로 다누리(danuri_2025-04-26-program.json) 도 로딩"""
    json_files = glob.glob(f"{folder_path}/*.json")
    all_docs = []

    for path in json_files:
        docs = load_hanultari_json(path)
        all_docs.extend(docs)

    return all_docs

def load_korean_education_data_by_api(page: int = 1, per_page: int = 1000) -> dict:
    """여성가족부 결혼이민자 대상 한국어 교육기관 정보를 API로 가져온다."""
    
    # 여성가족부_결혼이민자 대상 한국어교육 운영기관 현황 (2024년)
    # https://www.data.go.kr/iim/api/selectAPIAcountView.do#layer-api-guide
    url = "https://api.odcloud.kr/api/3077037/v1/uddi:de366691-6657-4b87-b324-f1bbbf01c0cb"
    service_key = os.getenv("DATA_API_KEY")
    
    params = {
        "page": page,
        "perPage": per_page,
        "serviceKey": service_key
    }

    headers = {
        "accept": "*/*"
    }
    
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # 실패하면 예외 발생

    return response.json()

def load_korean_education_data(page: int = 1, per_page: int = 1000) -> list[Document]:
    """여성가족부 결혼이민자 대상 한국어 교육기관 정보 API를 호출하고, VectorDB에 저장한다."""
    # 기관 정보는 data 키 - [{기관정보..}] 형태로 리턴됨.
    result = load_korean_education_data_by_api(page=page, per_page=per_page)
    data_list = result.get('data', [])
    documents = []

    for item in data_list:
        contact_numbers = [item.get(f"연락처{i}") for i in range(1, 5) if item.get(f"연락처{i}")]
        contact_numbers.extend([item.get("연락처")])
        content = "\n".join([
            "결혼이민자 대상 한국어 교육기관 정보",
            f"시도: {item.get('시도') or '시도 정보 없음'}",
            f"운영기관명: {item.get('운영기관명')}",
            f"주소: {item.get('주소') or '주소 정보 없음'}",
            f"연락처: {', '.join(contact_numbers) or '연락처 정보 없음'}"
        ])
        documents.append(Document(page_content=content, metadata={
            "source": "여성가족부 결혼이민자 대상 한국어교육 운영기관 현황 (공공데이터포털 제공)",
            "type": "API to Vector DB",
            "category": "korean_language_education"
        }))

    return documents

def create_text_splitter(chunk_size=1000, chunk_overlap=100):
    """텍스트 분할기 생성"""
    return CharacterTextSplitter(
        separator='',
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

def split_documents(docs, text_splitter=None):
    """문서를 청크로 분할"""
    if text_splitter is None:
        text_splitter = create_text_splitter()
    
    return text_splitter.split_documents(docs)
