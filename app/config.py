import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "300"))
    max_brief_length: int = int(os.getenv("MAX_BRIEF_LENGTH", "12000"))
    max_request_bytes: int = int(os.getenv("MAX_REQUEST_BYTES", "30000"))

    def __post_init__(self) -> None:
        if self.request_timeout <= 0:
            raise ValueError("REQUEST_TIMEOUT must be greater than zero")
        if not 1 <= self.max_brief_length <= 20000:
            raise ValueError("MAX_BRIEF_LENGTH must be between 1 and 20000")
        if self.max_request_bytes < self.max_brief_length:
            raise ValueError("MAX_REQUEST_BYTES must be at least MAX_BRIEF_LENGTH")
        if not self.ollama_model.strip():
            raise ValueError("OLLAMA_MODEL cannot be empty")


settings = Settings()
