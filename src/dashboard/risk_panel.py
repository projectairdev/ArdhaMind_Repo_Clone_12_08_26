from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import RiskReport

class RiskPanel:
    """
    Stateless Risk Panel.
    Displays Risk report details, exposures, capital allocation, and warnings.
    """

    def __init__(self, risk_report: Optional[RiskReport] = None) -> None:
        self.risk_report = risk_report

    def to_dict(self) -> Dict[str, Any]:
        """
        Extracts structured presentation data for portfolio risk.
        """
        if not self.risk_report:
            return {}

        rr = self.risk_report
        cand_risks = []
        for cr in rr.candidate_risks:
            cand_risks.append({
                "candidate_id": cr.candidate_id,
                "tradingsymbol": cr.tradingsymbol,
                "strategy_name": cr.strategy_name,
                "risk_grade": cr.risk_grade,
                "allocated_capital": cr.capital_allocation.allocated_capital,
                "allocated_lots": cr.capital_allocation.allocated_lots,
                "risk_amount": cr.capital_allocation.risk_amount,
                "is_approved": cr.is_approved,
                "warnings": [w if isinstance(w, str) else getattr(w, "message", str(w)) for w in cr.warnings],
            })

        sector_exposures = []
        if rr.exposure_summary and rr.exposure_summary.sector_exposures:
            for s in rr.exposure_summary.sector_exposures:
                sector_exposures.append({
                    "sector": s.sector,
                    "allocated_capital": s.allocated_capital,
                    "exposure_pct": s.exposure_pct,
                })

        directional_exposures = []
        if rr.exposure_summary and rr.exposure_summary.directional_exposures:
            for d in rr.exposure_summary.directional_exposures:
                directional_exposures.append({
                    "direction": d.direction,
                    "allocated_capital": d.allocated_capital,
                    "exposure_pct": d.exposure_pct,
                })

        expiry_exposures = []
        if rr.exposure_summary and rr.exposure_summary.expiry_exposures:
            for e in rr.exposure_summary.expiry_exposures:
                expiry_exposures.append({
                    "expiry": e.expiry,
                    "allocated_capital": e.allocated_capital,
                    "exposure_pct": e.exposure_pct,
                })

        return {
            "report_id": rr.report_id,
            "summary": {
                "highest_risk_candidate_id": rr.summary.highest_risk_candidate_id,
                "lowest_risk_candidate_id": rr.summary.lowest_risk_candidate_id,
                "portfolio_risk_grade": rr.summary.portfolio_risk_grade,
                "total_warnings": rr.summary.total_warnings,
                "conclusions": rr.summary.conclusions,
            },
            "exposure_summary": {
                "total_capital_allocated": rr.exposure_summary.total_capital_allocated if rr.exposure_summary else 0.0,
                "portfolio_utilization_pct": rr.exposure_summary.portfolio_utilization_pct if rr.exposure_summary else 0.0,
                "sector_exposures": sector_exposures,
                "directional_exposures": directional_exposures,
                "expiry_exposures": expiry_exposures,
            },
            "candidate_risks": cand_risks,
        }

    def render_cli(self) -> str:
        """
        Renders an ASCII text-based representation of the Risk Panel.
        """
        data = self.to_dict()
        lines = []
        lines.append("+- RISK WATCHLIST & PORTFOLIO EXPOSURE ----------------------------------------+")

        if not data:
            lines.append("| Risk Report: NOT AVAILABLE                                                   |")
            lines.append("+------------------------------------------------------------------------------+")
            return "\n".join(lines)

        sum_data = data["summary"]
        exp_data = data["exposure_summary"]

        lines.append(f"| PORTFOLIO RISK GRADE: {sum_data['portfolio_risk_grade']:<18} | Capital Utilized: {exp_data['portfolio_utilization_pct']:>5.1f}% |")
        lines.append(f"| Total Allocated     : INR {exp_data['total_capital_allocated']:<14.2f} | Risk Warnings   : {sum_data['total_warnings']:<3} |")
        lines.append("| " + "-"*76 + " |")

        # Exposures
        lines.append("| Directional Exposures:                                                       |")
        if exp_data["directional_exposures"]:
            for d in exp_data["directional_exposures"]:
                lines.append(f"|   * {d['direction']:<15}: INR {d['allocated_capital']:<12.1f} ({d['exposure_pct']:.1f}%)                                |")
        else:
            lines.append("|   No directional exposures registered.                                       |")

        lines.append("| " + "-"*76 + " |")

        # Candidate details table
        lines.append("| CANDIDATE ID                       | RISK GRADE | LOTS | ALLOCATED CAP | APPROVED |")
        lines.append("| " + "-"*34 + "+" + "-"*12 + "+" + "-"*6 + "+" + "-"*15 + "+" + "-"*10 + " |")
        
        for c in data["candidate_risks"][:5]:  # top 5
            lines.append(
                f"| {c['candidate_id'][:34]:<34} | {c['risk_grade']:<10} | {c['allocated_lots']:>4} | INR {c['allocated_capital']:>11.1f} | {str(c['is_approved']):<8} |"
            )
            # Show individual candidate warnings if any
            if c["warnings"]:
                for w in c["warnings"][:1]:
                    lines.append(f"|   Warning: {w[:70]:<70} |")

        if len(data["candidate_risks"]) > 5:
            lines.append(f"| ... and {len(data['candidate_risks']) - 5} other candidates risk-profileed                             |")

        # Conclusions
        if sum_data["conclusions"]:
            lines.append("| " + "-"*76 + " |")
            lines.append("| Risk Engine Conclusions:                                                     |")
            for conc in sum_data["conclusions"][:3]:
                lines.append(f"|   * {conc[:70]:<70} |")

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
