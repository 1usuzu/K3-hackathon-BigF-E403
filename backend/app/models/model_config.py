from typing import Optional
from sqlalchemy import String, Boolean, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.schemas.enums import DeploymentMode

class ModelConfiguration(Base):
    __tablename__ = "model_configurations"

    course_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    deployment_mode: Mapped[str] = mapped_column(String(50), default=DeploymentMode.CLOUD_ENTERPRISE.value, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., OpenAI, Anthropic, Ollama, vLLM
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)     # e.g., gpt-4o, claude-3-5-sonnet, llama-3.1
    
    # Store ONLY environment variable name for security (Rule 12: No secrets in DB)
    api_key_env_var_name: Mapped[Optional[str]] = mapped_column(String(100), default="OPENAI_API_KEY", nullable=True)
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # For Local Ollama/vLLM endpoints
    
    zero_data_retention: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("ix_model_config_course_active", "course_id", "is_active"),
    )
