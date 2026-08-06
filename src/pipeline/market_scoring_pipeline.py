from __future__ import annotations

from src.models import TradeContext, MarketScore
from src.scoring_engine import MarketScoreBuilder
from src.utils import setup_logger

logger = setup_logger("MarketScoringPipeline")


class MarketScoringPipeline:
    """
    Stateless, modular pipeline that consumes a complete TradeContext and produces
    the single, unified, immutable MarketScore representing the objective quality of the trading environment.
    """

    def __init__(self) -> None:
        pass

    def run(self, context: TradeContext) -> MarketScore:
        logger.info("Initializing NIFTY Market Scoring Pipeline...")
        score = MarketScoreBuilder.build(context)
        logger.info(
            f"NIFTY MarketScore computed successfully: Score={score.overall_score:.2f}, "
            f"Grade={score.letter_grade}, Classification={score.classification}"
        )
        return score
