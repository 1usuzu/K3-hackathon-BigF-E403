from enum import Enum
from typing import Optional
from dataclasses import dataclass
from backend.app.schemas.enums import DeploymentMode

class ModelTier(str, Enum):
    FAST_MODEL = "FAST_MODEL"  # Simple tasks (flashcards, quick summary)
    PRO_MODEL = "PRO_MODEL"    # Complex tasks (mindmap generation, deep RAG synthesis)

@dataclass
class GatewayConfig:
    deployment_mode: DeploymentMode = DeploymentMode.CLOUD_ENTERPRISE
    zero_data_retention: bool = True
    fast_model_name: str = "gpt-4o-mini"
    pro_model_name: str = "gpt-4o"
    embedding_model_name: str = "text-embedding-3-small"
    default_timeout_sec: float = 30.0
    max_token_limit: int = 4096
    rate_limit_max_retries: int = 3
    retry_backoff_base_sec: float = 0.5
