from rlm import RLM
from app.core.config import settings

rlm = RLM(
    model=settings.mistral_model,
    api_key=settings.mistral_api_key,
)
