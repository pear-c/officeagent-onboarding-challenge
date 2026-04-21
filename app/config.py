"""앱 설정 — pydantic-settings로 환경변수 로드."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """환경변수 기반 설정. .env 파일 자동 로드."""

    # 서버
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    chroma_collection: str = "documents"
    chroma_cache_collection: str = "cache_questions"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl_seconds: int = 3600  # 1시간

    # 임베딩
    embedding_model: str = "BAAI/bge-m3"
    embedding_device: str = "cpu"

    # 청킹
    chunk_size: int = 400
    chunk_overlap: int = 80

    # LLM
    llm_answer_provider: str = "claude"  # claude | codex | ollama
    llm_auxiliary_provider: str = "codex"  # claude | codex | ollama
    llm_max_tokens: int = 1024

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"

    # 파일 업로드
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_filename_length: int = 255

    # 검색
    search_top_k: int = 5
    cache_similarity_threshold: float = 0.95

    # Reranker
    reranker_enabled: bool = True
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    reranker_top_k: int = 5        # rerank 후 최종 전달할 청크 수
    reranker_candidates: int = 15   # 벡터 검색에서 reranker로 넘길 후보 수

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
