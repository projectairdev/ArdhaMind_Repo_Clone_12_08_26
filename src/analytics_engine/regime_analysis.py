from __future__ import annotations

import re
from typing import List, Dict
from src.models import (
    MarketPerformance,
    AnalyticsRegimePerformance,
    OpportunityPerformance,
    GradePerformance,
    BiasPerformance,
    TradeJournalEntry,
)

class RegimeAnalyser:
    """
    Stateless evaluator for market regime and opportunity characteristics.
    """

    @staticmethod
    def extract_opportunity(e: TradeJournalEntry) -> str:
        notes = (e.notes or "").upper()
        if "CLASSIFICATION:" in notes:
            for word in ["EXCELLENT", "GOOD", "WATCHLIST", "WAIT", "POOR", "AVOID"]:
                if word in notes:
                    return word

        exp = (e.explanation_summary or "").upper()
        for word in ["EXCELLENT", "GOOD", "WATCHLIST", "WAIT", "POOR", "AVOID"]:
            if word in exp:
                return word

        dec = (e.decision_summary or "").upper()
        for word in ["EXCELLENT", "GOOD", "WATCHLIST", "WAIT", "POOR", "AVOID"]:
            if word in dec:
                return word

        return "GOOD"  # Default fallback

    @staticmethod
    def extract_directional_bias(e: TradeJournalEntry) -> str:
        notes = (e.notes or "").upper()
        if "BIAS:" in notes:
            for word in ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]:
                if word in notes:
                    return word

        exp = ((e.explanation_summary or "") + " " + (e.decision_summary or "")).upper()
        for word in ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]:
            if word in exp:
                return word

        symbol = (e.tradingsymbol or "").upper()
        if "CE" in symbol:
            return "BULLISH"
        elif "PE" in symbol:
            return "BEARISH"

        return "NEUTRAL"

    @classmethod
    def analyze(cls, entries: List[TradeJournalEntry]) -> MarketPerformance:
        if not entries:
            return MarketPerformance()

        # 1. Group by Regime
        by_regime: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            reg = e.market_regime or "VOLATILE"
            by_regime.setdefault(reg, []).append(e)

        regime_list: List[AnalyticsRegimePerformance] = []
        for reg, reg_entries in by_regime.items():
            total = len(reg_entries)
            wins = [x for x in reg_entries if x.pnl > 0]
            losses = [x for x in reg_entries if x.pnl < 0]
            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in reg_entries) / total if total > 0 else 0.0

            gross_p = sum(x.pnl for x in wins)
            gross_l = abs(sum(x.pnl for x in losses))
            pf = gross_p / gross_l if gross_l > 0 else (gross_p if gross_p > 0 else 1.0)

            avg_win = sum(x.pnl for x in wins) / len(wins) if wins else 0.0
            avg_loss = sum(x.pnl for x in losses) / len(losses) if losses else 0.0
            exp = ((win_rate / 100.0) * avg_win) + (((total - len(wins)) / total) * avg_loss)

            regime_list.append(
                AnalyticsRegimePerformance(
                    market_regime=reg,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    profit_factor=pf,
                    expectancy=exp,
                )
            )

        # 2. Group by Opportunity Classification
        by_opp: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            opp = cls.extract_opportunity(e)
            by_opp.setdefault(opp, []).append(e)

        opp_list: List[OpportunityPerformance] = []
        for opp, opp_entries in by_opp.items():
            total = len(opp_entries)
            wins = [x for x in opp_entries if x.pnl > 0]
            losses = [x for x in opp_entries if x.pnl < 0]
            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in opp_entries) / total if total > 0 else 0.0

            gross_p = sum(x.pnl for x in wins)
            gross_l = abs(sum(x.pnl for x in losses))
            pf = gross_p / gross_l if gross_l > 0 else (gross_p if gross_p > 0 else 1.0)

            avg_win = sum(x.pnl for x in wins) / len(wins) if wins else 0.0
            avg_loss = sum(x.pnl for x in losses) / len(losses) if losses else 0.0
            exp = ((win_rate / 100.0) * avg_win) + (((total - len(wins)) / total) * avg_loss)

            opp_list.append(
                OpportunityPerformance(
                    opportunity_classification=opp,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    profit_factor=pf,
                    expectancy=exp,
                )
            )

        # 3. Group by Market Score Grade
        by_grade: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            grade = e.market_score_grade or "B"
            by_grade.setdefault(grade, []).append(e)

        grade_list: List[GradePerformance] = []
        for grade, grade_entries in by_grade.items():
            total = len(grade_entries)
            wins = [x for x in grade_entries if x.pnl > 0]
            losses = [x for x in grade_entries if x.pnl < 0]
            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in grade_entries) / total if total > 0 else 0.0

            gross_p = sum(x.pnl for x in wins)
            gross_l = abs(sum(x.pnl for x in losses))
            pf = gross_p / gross_l if gross_l > 0 else (gross_p if gross_p > 0 else 1.0)

            avg_win = sum(x.pnl for x in wins) / len(wins) if wins else 0.0
            avg_loss = sum(x.pnl for x in losses) / len(losses) if losses else 0.0
            exp = ((win_rate / 100.0) * avg_win) + (((total - len(wins)) / total) * avg_loss)

            grade_list.append(
                GradePerformance(
                    market_score_grade=grade,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    profit_factor=pf,
                    expectancy=exp,
                )
            )

        # 4. Group by Directional Bias
        by_bias: Dict[str, List[TradeJournalEntry]] = {}
        for e in entries:
            bias = cls.extract_directional_bias(e)
            by_bias.setdefault(bias, []).append(e)

        bias_list: List[BiasPerformance] = []
        for bias, bias_entries in by_bias.items():
            total = len(bias_entries)
            wins = [x for x in bias_entries if x.pnl > 0]
            losses = [x for x in bias_entries if x.pnl < 0]
            win_rate = (len(wins) / total) * 100.0 if total > 0 else 0.0
            average_return = sum(x.pnl for x in bias_entries) / total if total > 0 else 0.0

            gross_p = sum(x.pnl for x in wins)
            gross_l = abs(sum(x.pnl for x in losses))
            pf = gross_p / gross_l if gross_l > 0 else (gross_p if gross_p > 0 else 1.0)

            avg_win = sum(x.pnl for x in wins) / len(wins) if wins else 0.0
            avg_loss = sum(x.pnl for x in losses) / len(losses) if losses else 0.0
            exp = ((win_rate / 100.0) * avg_win) + (((total - len(wins)) / total) * avg_loss)

            bias_list.append(
                BiasPerformance(
                    directional_bias=bias,
                    total_trades=total,
                    win_rate=win_rate,
                    average_return=average_return,
                    profit_factor=pf,
                    expectancy=exp,
                )
            )

        return MarketPerformance(
            by_regime=sorted(regime_list, key=lambda x: x.total_trades, reverse=True),
            by_opportunity=sorted(opp_list, key=lambda x: x.total_trades, reverse=True),
            by_grade=sorted(grade_list, key=lambda x: x.total_trades, reverse=True),
            by_bias=sorted(bias_list, key=lambda x: x.total_trades, reverse=True),
        )
