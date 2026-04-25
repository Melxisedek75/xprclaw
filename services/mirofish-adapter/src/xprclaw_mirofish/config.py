"""Adapter configuration from environment variables."""

from pydantic_settings import BaseSettings


class AdapterConfig(BaseSettings):
    """Configuration loaded from environment."""

    # FastAPI
    log_level: str = "info"

    # MiroFish backend
    mirofish_base_url: str = "http://localhost:5001"
    mirofish_timeout_seconds: int = 300

    # LLM provider
    llm_provider: str = "anthropic"
    llm_api_key: str
    llm_model: str = "claude-3-sonnet-20240229"

    # Zep Cloud (optional, for agent memory)
    zep_api_key: str = ""
    zep_project_id: str = ""

    # Cloudflare D1
    cf_account_id: str
    cf_api_token: str
    d1_database_id: str
    d1_cache_table: str = "mirofish_simulations"

    # Persona delivery
    persona_delivery: str = "hardcoded"
    persona_yaml_path: str = ""

    # Cache eviction
    cache_eviction_mode: str = "lru"
    cache_max_age_seconds: int = 3600

    # Simulation
    sim_timeout_seconds: int = 300
    sim_max_agents: int = 50

    # Environment
    env: str = "development"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False

    def to_dict(self) -> dict[str, str]:
        """Export config as dict (for logging)."""
        return self.model_dump()
