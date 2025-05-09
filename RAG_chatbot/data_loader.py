# RAG_chatbot/data_loader.py
import os
import re
import json
import glob
import requests
import subprocess
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

# 여성가족부_결혼이민자 대상 한국어교육기관 정보, 한국건강가정진흥원_전국 다문화가족지원센터 통번역 지원사 배치현황
def load_data_by_api(url: str, page: int = 1, per_page: int = 1000) -> dict:
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

# 여성가족부 해바라기센터 정보 API 의 경우 curl 사용
def load_sunflower_center_data_by_api(url: str, page: int = 1, per_page: int = 100) -> dict:

    service_key = os.getenv("DATA_API_KEY")

    api_request_url = f"{url}?serviceKey={service_key}&pageNo={page}&numOfRows={per_page}&type=json"
    cmd = ["curl", "-s", "-X", "GET", api_request_url, "-H", "accept: */*"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)

    return data

def load_korean_education_data(page: int = 1, per_page: int = 1000) -> list[Document]:
    """여성가족부 결혼이민자 대상 한국어 교육기관 정보 API를 호출하고, VectorDB에 저장한다."""
    # 기관 정보는 data 키 - [{기관정보..}] 형태로 리턴됨.
    korean_education_url = "https://api.odcloud.kr/api/3077037/v1/uddi:de366691-6657-4b87-b324-f1bbbf01c0cb"
    result = load_data_by_api(url=korean_education_url, page=page, per_page=per_page)
    data_list = result.get('data', [])

    return data_list

def load_translator_data(page: int = 1, per_page: int = 1000) -> list[Document]:
    """한국건강가정진흥원_전국 다문화가족지원센터 통번역 지원사 배치현황 정보 API를 호출하고, VectorDB에 저장한다."""
    translator_url = "https://api.odcloud.kr/api/3081602/v1/uddi:3edbb122-3a1c-420d-992a-855bd0a961aa"
    result = load_data_by_api(url=translator_url, page=page, per_page=per_page)
    data_list = result.get('data', [])
    
    return data_list

def load_sunflower_center_data(page: int = 1, per_page: int = 100) -> list[Document]:
    """여성가족부 해바라기센터 정보 API를 호출하고, VectorDB에 저장한다."""
    sunflower_centor_url = "https://apis.data.go.kr/1383000/gmis/sfCnterServiceV2/getSfCnterListV2"
    result = load_sunflower_center_data_by_api(url=sunflower_centor_url, page=page, per_page=per_page)
    data_list = result.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    documents = []

    for item in data_list:
        contact_number = item.get('rprsTelno') or "전화번호 정보 없음"

        if contact_number != "전화번호 정보 없음":
            contact_number = format_korean_phone(contact_number)

        content = "\n".join([
            "여성가족부 해바라기센터 정보 (365일 24시간 성폭력, 가정폭력, 성매매, 교제폭력, 스토킹 피해자에게 통합적인 서비스를 제공하는 기관)",
            f"센터명: {item.get('cnterNm') or '센터명 정보 없음'}",
            f"주소: {item.get('roadNmAddr') or item.get('lotnoAddr') or '주소 정보 없음'}",
            f"연락처: {contact_number}",
            f"운영시간: {item.get('operHrCn') or '운영시간 정보 없음'}",
            f"센터지원안내: {item.get('sprtCnt') or '센터지원 정보 없음'}",
            f"홈페이지: {item.get('hmpgAddr') or '홈페이지 정보 없음'}",
            f"이메일: {item.get('emlAddr') or '이메일 정보 없음'}",
        ])
        documents.append(Document(page_content=content, metadata={
            "source": "여성가족부 해바라기센터 정보 (공공데이터포털 제공)",
            "type": "API to Vector DB",
            "category": "sunflower_center_info"
        }))

    return documents

# 전화번호 포맷 통일 함수 (021234567 -> 02-123-4567)
# 여성가족부 해바라기센터 연락처 포맷에 사용
def format_korean_phone(contact_number):
    # 지역번호가 2자리인 경우 (서울 02)
    if contact_number.startswith("02"):
        return re.sub(r"^(02)(\d{3,4})(\d{4})$", r"\1-\2-\3", contact_number)
    else:
        # 나머지는 지역번호가 3자리
        return re.sub(r"^(\d{3})(\d{3,4})(\d{4})$", r"\1-\2-\3", contact_number)

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

def split_csv(items, data, max_rows=10):
    if not items:
        return []

    header = list(items[0].keys())
    documents = []

    for i in range(0, len(items), max_rows):
        chunk_rows = items[i:i + max_rows]
        lines = [", ".join(header)]  # 헤더
        for row in chunk_rows:
            lines.append(", ".join(str(row.get(col, "")) for col in header))
        chunk_text = "\n".join(lines)

        doc = Document(
            page_content= data + '\n' + chunk_text,
            metadata={
                "source": data + " (공공데이터포털 제공)",
                "type": "API to Vector DB",
                "chunk_index": i // max_rows  # optional: 몇 번째 청크인지 추적 가능
            }
        )
        documents.append(doc)
    return documents