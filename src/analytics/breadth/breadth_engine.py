from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from src.analytics.breadth.models import (
    BreadthDivergenceContext,
    ConstituentState,
    DivergenceType,
    HeavyweightLeadershipContext,
    LeadershipBias,
    MarketBreadthContext,
    MarketBreadthSummary,
    SectorParticipationContext,
)
from src.market_data.models.quality_enums import DataQualityStatus


class MarketBreadthEngine:
    """
    Deterministic provider-independent market breadth and constituent engine.
    Derives advances/declines, sector rotation, and heavyweight leadership directly from data.
    """

    DEFAULT_HEAVYWEIGHTS = [
        "HDFCBANK", "RELIANCE", "ICICIBANK", "INFY", "TCS",
        "ITC", "LT", "AXISBANK", "SBIN", "BHARTIARTL"
    ]

    DEFAULT_SECTOR_MAP = {
        "BANK": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "INDUSINDBK"],
        "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM"],
        "AUTO": ["M&M", "MARUTI", "TATAMOTORS", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"],
        "ENERGY": ["RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL", "COALINDIA"],
        "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "APOLLOHOSP", "DIVISLAB"],
        "FMCG": ["ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
        "METALS": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL"],
    }

    @staticmethod
    def analyze(
        constituents: Sequence[ConstituentState],
        index_change_pct: float,
        total_universe_count: int = 50,
    ) -> MarketBreadthContext:
        """Computes comprehensive market breadth, divergence, sector, and leadership analysis."""
        if not constituents:
            return MarketBreadthEngine._empty_context(total_universe_count)

        # 1. Breadth Summary
        summary = MarketBreadthEngine.calculate_breadth(constituents, total_universe_count)

        # 2. Breadth Divergence
        divergence = MarketBreadthEngine.evaluate_divergence(summary, index_change_pct)

        # 3. Sector Participation
        sectors = MarketBreadthEngine.evaluate_sectors(constituents)

        # 4. Heavyweight Leadership
        leadership = MarketBreadthEngine.evaluate_heavyweights(constituents)

        # Quality resolution
        overall_quality = summary.quality
        if leadership.quality == DataQualityStatus.UNAVAILABLE or summary.coverage_pct < 50.0:
            overall_quality = DataQualityStatus.UNAVAILABLE
        elif summary.coverage_pct < 90.0:
            overall_quality = DataQualityStatus.DELAYED

        return MarketBreadthContext(
            breadth_summary=summary,
            divergence=divergence,
            sector_context=sectors,
            leadership=leadership,
            quality=overall_quality,
        )

    @staticmethod
    def calculate_breadth(
        constituents: Sequence[ConstituentState],
        total_universe_count: int = 50,
    ) -> MarketBreadthSummary:
        """Calculates advance/decline stats directly from constituent change percentages."""
        obs_count = len(constituents)
        if obs_count == 0:
            return MarketBreadthSummary(
                total_constituents=total_universe_count,
                observed_constituents=0,
                advances=0,
                declines=0,
                unchanged=0,
                advance_decline_ratio=1.0,
                advance_pct=50.0,
                weighted_breadth_score=0.0,
                coverage_pct=0.0,
                quality=DataQualityStatus.UNAVAILABLE,
            )

        advances = sum(1 for c in constituents if c.change_pct > 0.05)
        declines = sum(1 for c in constituents if c.change_pct < -0.05)
        unchanged = obs_count - advances - declines

        adr = round(advances / declines, 2) if declines > 0 else float(advances)
        adv_pct = round((advances / obs_count) * 100.0, 2)

        # Weighted score: sum(change_pct * weight) / sum(weights)
        total_weight = sum(c.weight for c in constituents)
        weighted_sum = sum(c.change_pct * c.weight for c in constituents)
        raw_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        # Normalize to [-1.0, +1.0] range (capping at +/- 2.0% average change)
        weighted_score = round(max(-1.0, min(1.0, raw_score / 2.0)), 4)

        coverage = round((obs_count / total_universe_count) * 100.0, 2) if total_universe_count > 0 else 100.0
        quality = DataQualityStatus.VALID if coverage >= 90.0 else (DataQualityStatus.DELAYED if coverage >= 50.0 else DataQualityStatus.UNAVAILABLE)

        return MarketBreadthSummary(
            total_constituents=total_universe_count,
            observed_constituents=obs_count,
            advances=advances,
            declines=declines,
            unchanged=unchanged,
            advance_decline_ratio=adr,
            advance_pct=adv_pct,
            weighted_breadth_score=weighted_score,
            coverage_pct=coverage,
            quality=quality,
        )

    @staticmethod
    def evaluate_divergence(
        summary: MarketBreadthSummary,
        index_change_pct: float,
    ) -> BreadthDivergenceContext:
        """Detects divergence between index price movement and underlying market breadth."""
        if summary.quality == DataQualityStatus.UNAVAILABLE:
            return BreadthDivergenceContext(DivergenceType.NONE, index_change_pct, summary.advance_pct, "Insufficient breadth data")

        # Bearish Divergence: Index is up (>= +0.3%) but less than 40% of constituents are advancing
        if index_change_pct >= 0.30 and summary.advance_pct < 40.0:
            return BreadthDivergenceContext(
                divergence=DivergenceType.BEARISH_DIVERGENCE,
                index_change_pct=index_change_pct,
                breadth_advance_pct=summary.advance_pct,
                note=f"Index up {index_change_pct:+.2f}% with only {summary.advance_pct}% advances (Narrow Leadership)",
            )
        # Bullish Divergence: Index is down (<= -0.3%) but more than 60% of constituents are advancing
        elif index_change_pct <= -0.30 and summary.advance_pct > 60.0:
            return BreadthDivergenceContext(
                divergence=DivergenceType.BULLISH_DIVERGENCE,
                index_change_pct=index_change_pct,
                breadth_advance_pct=summary.advance_pct,
                note=f"Index down {index_change_pct:+.2f}% while {summary.advance_pct}% of stocks advance (Broad Accumulation)",
            )

        return BreadthDivergenceContext(
            divergence=DivergenceType.NONE,
            index_change_pct=index_change_pct,
            breadth_advance_pct=summary.advance_pct,
            note="Breadth aligns with index trajectory",
        )

    @staticmethod
    def evaluate_sectors(constituents: Sequence[ConstituentState]) -> SectorParticipationContext:
        """Aggregates sector performance and participation from constituent stocks."""
        by_symbol = {c.symbol.upper(): c for c in constituents}
        sector_changes: Dict[str, float] = {}

        for sec_name, symbols in MarketBreadthEngine.DEFAULT_SECTOR_MAP.items():
            sec_consts = [by_symbol[s] for s in symbols if s in by_symbol]
            if sec_consts:
                avg_chg = sum(c.change_pct for c in sec_consts) / len(sec_consts)
                sector_changes[sec_name] = round(avg_chg, 2)

        if not sector_changes:
            return SectorParticipationContext({}, [], [], 0.0, DataQualityStatus.UNAVAILABLE)

        sorted_sectors = sorted(sector_changes.items(), key=lambda x: x[1], reverse=True)
        leading = [s[0] for s in sorted_sectors if s[1] > 0.1]
        lagging = [s[0] for s in sorted_sectors if s[1] < -0.1]

        # Participation score: ratio of positive sectors
        pos_count = sum(1 for s in sector_changes.values() if s > 0.0)
        neg_count = sum(1 for s in sector_changes.values() if s < 0.0)
        total_sec = len(sector_changes)
        score = round((pos_count - neg_count) / total_sec, 2) if total_sec > 0 else 0.0

        return SectorParticipationContext(
            sector_changes=sector_changes,
            leading_sectors=leading,
            lagging_sectors=lagging,
            participation_score=score,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def evaluate_heavyweights(constituents: Sequence[ConstituentState]) -> HeavyweightLeadershipContext:
        """Evaluates participation among index heavyweight stocks."""
        by_symbol = {c.symbol.upper(): c for c in constituents}
        hw_consts = [by_symbol[s] for s in MarketBreadthEngine.DEFAULT_HEAVYWEIGHTS if s in by_symbol]

        if not hw_consts:
            return HeavyweightLeadershipContext(
                heavyweight_symbols=MarketBreadthEngine.DEFAULT_HEAVYWEIGHTS,
                advances=0,
                declines=0,
                leadership_bias=LeadershipBias.UNAVAILABLE,
                contribution_score=0.0,
                quality=DataQualityStatus.UNAVAILABLE,
            )

        adv = sum(1 for c in hw_consts if c.change_pct > 0.05)
        dec = sum(1 for c in hw_consts if c.change_pct < -0.05)
        total_hw = len(hw_consts)

        score = round((adv - dec) / total_hw, 2) if total_hw > 0 else 0.0

        if score >= 0.3:
            bias = LeadershipBias.BULLISH
        elif score <= -0.3:
            bias = LeadershipBias.BEARISH
        else:
            bias = LeadershipBias.MIXED

        return HeavyweightLeadershipContext(
            heavyweight_symbols=[c.symbol for c in hw_consts],
            advances=adv,
            declines=dec,
            leadership_bias=bias,
            contribution_score=score,
            quality=DataQualityStatus.VALID,
        )

    @staticmethod
    def _empty_context(total_universe_count: int) -> MarketBreadthContext:
        return MarketBreadthContext(
            breadth_summary=MarketBreadthSummary(total_universe_count, 0, 0, 0, 0, 1.0, 50.0, 0.0, 0.0, DataQualityStatus.UNAVAILABLE),
            divergence=BreadthDivergenceContext(DivergenceType.NONE, 0.0, 50.0, "No constituent data"),
            sector_context=SectorParticipationContext({}, [], [], 0.0, DataQualityStatus.UNAVAILABLE),
            leadership=HeavyweightLeadershipContext([], 0, 0, LeadershipBias.UNAVAILABLE, 0.0, DataQualityStatus.UNAVAILABLE),
            quality=DataQualityStatus.UNAVAILABLE,
        )
