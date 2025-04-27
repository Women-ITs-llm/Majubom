from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

def get_db_connection():
    """DB 연결 문자열 생성"""
    load_dotenv(override=True)
    
    db_config = {key: os.getenv(key) for key in [
        "DB_USER", 
        "DB_PASSWORD", 
        "DB_HOST", 
        "DB_PORT", 
        "DB_NAME"
    ]}
    
    connection = f"postgresql+psycopg2://{db_config['DB_USER']}:{db_config['DB_PASSWORD']}@{db_config['DB_HOST']}:{db_config['DB_PORT']}/{db_config['DB_NAME']}"
    return connection

def create_vector_store(documents=None, collection_name="laws_db"):
    """
    벡터 스토어 접속 (이미 존재한다고 가정)
    새 문서가 제공된 경우에만 추가
    """
    connection = get_db_connection()
    
    # 임베딩 모델 (캐싱 사용)
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-small",
        cache_folder="/tmp/hf_cache"  # 캐시 폴더 지정
    )
    
    # 기존 벡터 스토어에 접속
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True
    )
    
    # 새 문서가 있는 경우만 추가
    if documents:
        vector_store.add_documents(documents)
    
    return vector_store

def create_retriever(vector_store, k=5, fetch_k=10):
    """검색기 생성"""
    return vector_store.as_retriever(search_kwargs={
        "k": k,         # 최종 반환할 문서 개수
        "fetch_k": fetch_k,  # 처음 검색할 문서 개수
        "search_type": "mmr"  # MMR 적용
    })