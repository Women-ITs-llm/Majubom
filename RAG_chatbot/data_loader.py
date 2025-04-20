from langchain_community.document_loaders import PyMuPDFLoader
import glob
from langchain.text_splitter import CharacterTextSplitter

def load_pdfs(data_dir="data/"):
    """PDF 파일들을 로드하여 Document 객체 리스트 반환"""
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
    
    # 메타데이터 추가
    for doc in center_docs:
        doc.metadata["type"] = "center"
        doc.metadata["category"] = "multicultural_center"
    
    return center_docs

def create_text_splitter(chunk_size=1000, chunk_overlap=100):
    """텍스트 분할기 생성"""
    return CharacterTextSplitter(
        separator = '',
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
        length_function = len,
    )

def split_documents(docs, text_splitter=None):
    """문서를 청크로 분할"""
    if text_splitter is None:
        text_splitter = create_text_splitter()
    
    return text_splitter.split_documents(docs)