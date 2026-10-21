"""C4 next-stage prediction models and baseline interfaces."""
from .frequency import FrequencyBaseline
from .markov import MarkovModel
from .predictor import predict_next

__all__ = ["MarkovModel", "FrequencyBaseline", "predict_next"]
