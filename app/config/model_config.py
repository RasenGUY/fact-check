from enum import Enum
from dataclasses import dataclass
from .supported_models import X_AI_GROK_4_FAST, OPEN_AI_GPT_5_2_CHAT, OPEN_AI_GPT_5_2

class ModelUseCase(str, Enum):
    """Use cases for model selection - allows easy prompt/model switching."""

    FACT_CHECK_WEBSEARCH = "fact_check_websearch"  # Web search step
    FACT_CHECK_EVALUATION = "fact_check_evaluation"  # Evaluation step

@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    model_name: str


# Simple use case → model mapping (no tiers)
MODEL_MAPPING: dict[ModelUseCase, ModelConfig] = {
    ModelUseCase.FACT_CHECK_WEBSEARCH: ModelConfig(model_name=OPEN_AI_GPT_5_2_CHAT),
    ModelUseCase.FACT_CHECK_EVALUATION: ModelConfig(model_name=OPEN_AI_GPT_5_2),
}


class ModelSelector:
    """Select model based on use case."""

    @staticmethod
    def get_model_name(use_case: ModelUseCase) -> str:
        """Get model name for a use case."""
        if use_case not in MODEL_MAPPING:
            raise ValueError(f"Unknown use case: {use_case}")
        return MODEL_MAPPING[use_case].model_name

    @staticmethod
    def get_websearch_model(use_case: ModelUseCase) -> str:
        """Get model name with :online suffix for websearch."""
        return f"{ModelSelector.get_model_name(use_case)}:online"
