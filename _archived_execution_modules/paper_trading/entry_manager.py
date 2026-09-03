from __future__ import annotations

from typing import List, Dict, Optional
from src.models import DecisionReport, ConfidenceReport, RiskReport, PaperTrade


class PaperEntryManager:
    """
    Stateless manager responsible for generating paper trades from BUY or SELL decisions.
    """

    @staticmethod
    def evaluate_entries(
        decision_report: DecisionReport,
        confidence_report: Optional[ConfidenceReport] = None,
        risk_report: Optional[RiskReport] = None,
        market_prices: Optional[Dict[str, float]] = None,
    ) -> List[PaperTrade]:
        """
        Generates paper trades ONLY from BUY or SELL decisions in a decision report.
        """
        if market_prices is None:
            market_prices = {}

        trades: List[PaperTrade] = []
        for decision in decision_report.candidate_decisions:
            if decision.decision not in ("BUY", "SELL"):
                continue

            # Resolve confidence
            confidence_score = 75.0
            if confidence_report:
                for cc in confidence_report.candidate_confidences:
                    if cc.candidate_id == decision.candidate_id:
                        confidence_score = cc.confidence_score
                        break

            # Resolve risk
            risk_grade = "LOW_RISK"
            if risk_report:
                for cr in risk_report.candidate_risks:
                    if cr.candidate_id == decision.candidate_id:
                        risk_grade = cr.risk_grade
                        break

            # Resolve premium (fallback to a sensible default like 100.0 or derived from capital)
            premium = market_prices.get(decision.tradingsymbol) or market_prices.get(decision.candidate_id)
            if premium is None:
                if decision.allocated_capital > 0 and decision.allocated_lots > 0:
                    premium = decision.allocated_capital / (decision.allocated_lots * 50.0)
                else:
                    premium = 100.0

            lots = decision.allocated_lots if decision.allocated_lots > 0 else 2
            capital = decision.allocated_capital if decision.allocated_capital > 0 else (lots * 50.0 * premium)

            trade = PaperTrade(
                trade_id=f"T_{decision_report.report_id}_{decision.candidate_id}",
                decision_id=decision_report.report_id,
                candidate_id=decision.candidate_id,
                tradingsymbol=decision.tradingsymbol,
                entry_time=decision_report.timestamp or "2026-07-10T12:00:00",
                premium=premium,
                lots=lots,
                capital=capital,
                strategy_name=decision.strategy_name,
                confidence_score=confidence_score,
                risk_grade=risk_grade,
                action=decision.decision,
            )
            trades.append(trade)

        return trades
