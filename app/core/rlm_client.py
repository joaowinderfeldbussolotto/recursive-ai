from rlm import RLM
from rlm.logger import RLMLogger
from app.core.config import settings

rlm = RLM(
    backend="litellm",
    backend_kwargs={
        "model_name": settings.mistral_model,
        "api_key": settings.mistral_api_key,
        "base_url": "https://api.mistral.ai/v1",
        "rpm": settings.mistral_rpm,
    },
    environment="local",
    logger=RLMLogger(log_dir="./logs"),
    verbose=True,
)
