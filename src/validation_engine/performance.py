from __future__ import annotations

from typing import Dict, List
from src.models.validation_report import StrategyPerformance, DecisionPerformance
from src.validation_engine.historical_runner import DailyPipelineResult


class PerformanceAnalyzer:
    """
    Analyzes trading and strategy performances across replayed historical trading days.
    """

    @staticmethod
    def analyze_strategy_performance(results: List[DailyPipelineResult]) -> List[StrategyPerformance]:
        """
        Groups metrics by strategy name and calculates performance breakdown.
        """
        # Store temporary stats for each strategy
        # strategy_name -> dict
        data: Dict[str, Dict[str, Any]] = {}

        for res in results:
            # We want to match decisions with their confidence scores.
            # We can use candidate_id to link them.
            conf_map = {
                c.candidate_id: c.confidence_score
                for c in res.confidence_report.candidate_confidences
            }

            for decision in res.decision_report.candidate_decisions:
                strat = decision.strategy_name
                if strat not in data:
                    data[strat] = {
                        "total": 0,
                        "buy": 0,
                        "sell": 0,
                        "watch": 0,
                        "reject": 0,
                        "no_trade": 0,
                        "conf_sum": 0.0,
                        "conf_count": 0,
                    }

                data[strat]["total"] += 1
                dec_type = decision.decision
                if dec_type == "BUY":
                    data[strat]["buy"] += 1
                elif dec_type == "SELL":
                    data[strat]["sell"] += 1
                elif dec_type == "WATCH":
                    data[strat]["watch"] += 1
                elif dec_type == "REJECT":
                    data[strat]["reject"] += 1
                else:
                    data[strat]["no_trade"] += 1

                conf = conf_map.get(decision.candidate_id)
                if conf is not None:
                    data[strat]["conf_sum"] += conf
                    data[strat]["conf_count"] += 1

        performances = []
        for strat, stats in data.items():
            avg_conf = (
                (stats["conf_sum"] / stats["conf_count"]) if stats["conf_count"] > 0 else 0.0
            )
            performances.append(
                StrategyPerformance(
                    strategy_name=strat,
                    total_candidates=stats["total"],
                    buy_count=stats["buy"],
                    sell_count=stats["sell"],
                    watch_count=stats["watch"],
                    reject_count=stats["reject"],
                    no_trade_count=stats["no_trade"],
                    avg_confidence_score=round(avg_conf, 2),
                )
            )

        # Sort alphabetically by strategy name for deterministic output
        return sorted(performances, key=lambda p: p.strategy_name)

    @staticmethod
    def analyze_decision_performance(results: List[DailyPipelineResult]) -> List[DecisionPerformance]:
        """
        Calculates performance summary grouped by decision type.
        """
        total_count = 0
        dec_stats = {
            "BUY": {"count": 0, "conf_sum": 0.0, "cap_sum": 0.0},
            "SELL": {"count": 0, "conf_sum": 0.0, "cap_sum": 0.0},
            "WATCH": {"count": 0, "conf_sum": 0.0, "cap_sum": 0.0},
            "REJECT": {"count": 0, "conf_sum": 0.0, "cap_sum": 0.0},
            "NO TRADE": {"count": 0, "conf_sum": 0.0, "cap_sum": 0.0},
        }

        for res in results:
            conf_map = {
                c.candidate_id: c.confidence_score
                for c in res.confidence_report.candidate_confidences
            }

            for decision in res.decision_report.candidate_decisions:
                dec_type = decision.decision
                if dec_type not in dec_stats:
                    # Normalize unexpected types to NO TRADE
                    dec_type = "NO TRADE"

                dec_stats[dec_type]["count"] += 1
                total_count += 1

                conf = conf_map.get(decision.candidate_id)
                if conf is not None:
                    dec_stats[dec_type]["conf_sum"] += conf

                dec_stats[dec_type]["cap_sum"] += decision.allocated_capital

        performances = []
        for dec_type, stats in dec_stats.items():
            count = stats["count"]
            pct = (count / total_count * 100.0) if total_count > 0 else 0.0
            avg_conf = (stats["conf_sum"] / count) if count > 0 else 0.0
            avg_cap = (stats["cap_sum"] / count) if count > 0 else 0.0

            performances.append(
                DecisionPerformance(
                    decision_type=dec_type,
                    count=count,
                    percentage=round(pct, 2),
                    avg_confidence=round(avg_conf, 2),
                    avg_allocated_capital=round(avg_cap, 2),
                )
            )

        return performances
