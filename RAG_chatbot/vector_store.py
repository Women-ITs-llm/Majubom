from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
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

def validate_documents(docs, embeddings_model):
    """유효한 page_content와 정상 임베딩이 생성되는 문서만 필터링"""
    docs = [doc for doc in docs if doc.page_content and doc.page_content.strip()]
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    embeddings = embeddings_model.embed_documents(texts)

    valid_docs = []
    for text, meta, emb in zip(texts, metadatas, embeddings):
        if (
            emb and
            isinstance(emb, list) and
            len(emb) > 0 and
            all(isinstance(x, float) for x in emb)
        ):
            valid_docs.append(Document(page_content=text, metadata=meta))
        else:
            print("❌ 임베딩 실패 - 제거된 문서:", text[:50].replace("\n", " "))

    return valid_docs


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
    
    # 문서가 존재할 경우에만 추가
    if documents:
        valid_docs = validate_documents(documents, embeddings)

        if valid_docs:
            vector_store.add_documents(valid_docs)
    
    return vector_store

def create_retriever(vector_store, k=5, fetch_k=10):
    """검색기 생성"""
    return vector_store.as_retriever(search_kwargs={
        "k": k,         # 최종 반환할 문서 개수
        "fetch_k": fetch_k,  # 처음 검색할 문서 개수
        "search_type": "mmr"  # MMR 적용
    })