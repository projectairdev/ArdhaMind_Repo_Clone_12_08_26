from __future__ import annotations

import math
import statistics as stats_lib
from typing import List
from src.models.validation_report import (
    ConfidenceStatistics,
    RiskStatistics,
    SummaryStatistics,
)
from src.validation_engine.historical_runner import DailyPipelineResult


class StatisticsCalculator:
    """
    Calculates summary, confidence, and risk statistics over historical replay results.
    """

    @staticmethod
    def calculate_confidence_stats(results: List[DailyPipelineResult]) -> ConfidenceStatistics:
        """
        Computes average, max, min, and standard deviation of confidence scores.
        """
        all_confidences = []
        for res in results:
            for conf in res.confidence_report.candidate_confidences:
                all_confidences.append(conf.confidence_score)

        if not all_confidences:
            return ConfidenceStatistics(0.0, 0.0, 0.0, 0.0)

        avg_conf = sum(all_confidences) / len(all_confidences)
        max_conf = max(all_confidences)
        min_conf = min(all_confidences)
        std_conf = stats_lib.stdev(all_confidences) if len(all_confidences) > 1 else 0.0

        return ConfidenceStatistics(
            avg_confidence=round(avg_conf, 2),
            max_confidence=round(max_conf, 2),
            min_confidence=round(min_conf, 2),
            std_confidence=round(std_conf, 2),
        )

    @staticmethod
    def calculate_risk_stats(results: List[DailyPipelineResult]) -> RiskStatistics:
        """
        Computes risk-related statistics including allocated capital and approval rates.
        """
        allocated_capitals = []
        approved_count = 0
        rejected_count = 0

        for res in results:
            allocated_capitals.append(res.risk_report.exposure_summary.total_capital_allocated)
            for cand in res.risk_report.candidate_risks:
                if cand.is_approved:
                    approved_count += 1
                else:
                    rejected_count += 1

        if not allocated_capitals:
            return RiskStatistics(0.0, 0.0, 0.0, 0, 0)

        total_allocated = sum(allocated_capitals)
        avg_allocated = total_allocated / len(allocated_capitals)
        max_allocated = max(allocated_capitals)

        return RiskStatistics(
            avg_allocated_capital=round(avg_allocated, 2),
            total_allocated_capital=round(total_allocated, 2),
            max_allocated_capital=round(max_allocated, 2),
            approved_count=approved_count,
            rejected_count=rejected_count,
        )

    @staticmethod
    def calculate_summary_stats(results: List[DailyPipelineResult]) -> SummaryStatistics:
        """
        Computes high-level summary statistics across all replay sessions.
        """
        total_days = len(results)
        total_candidates = 0
        buy_count = 0
        sell_count = 0
        watch_count = 0
        reject_count = 0
        no_trade_count = 0
        market_scores = []

        for res in results:
            total_candidates += res.decision_report.stats.total_candidates_evaluated
            buy_count += res.decision_report.stats.buy_count
            sell_count += res.decision_report.stats.sell_count
            watch_count += res.decision_report.stats.watch_count
            reject_count += res.decision_report.stats.reject_count
            no_trade_count += res.decision_report.stats.no_trade_count
            market_scores.append(res.market_score.overall_score)

        avg_m_score = (sum(market_scores) / len(market_scores)) if market_scores else 0.0
        decision_freq = ((buy_count + sell_count) / total_candidates * 100.0) if total_candidates > 0 else 0.0

        return SummaryStatistics(
            total_days_evaluated=total_days,
            total_candidates_evaluated=total_candidates,
            overall_buy_count=buy_count,
            overall_sell_count=sell_count,
            overall_watch_count=watch_count,
            overall_reject_count=reject_count,
            overall_no_trade_count=no_trade_count,
            decision_frequency_pct=round(decision_freq, 2),
            avg_market_score=round(avg_m_score, 2),
        )
