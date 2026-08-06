from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from email.utils import parsedate_to_datetime

class TimeDecayCalculator:
    """
    Stateless decayer that decreases news/event impact based on time elapsed since publication.
    """

    @staticmethod
    def parse_time(time_str: str) -> datetime:
        """
        Parses various string datetime representations safely into a UTC datetime.
        """
        if not time_str:
            return datetime.utcnow()
        
        # Try standard ISO/JSON format
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(time_str[:19], fmt)
                return dt
            except Exception:
                pass

        # Try RFC 2822 / RSS pubDate format
        try:
            dt = parsedate_to_datetime(time_str)
            # Convert to naive UTC
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            pass

        return datetime.utcnow()

    @classmethod
    def calculate_multiplier(cls, published_at: str, current_time: str = None) -> float:
        """
        Calculates a decay factor between 1.0 and 0.0.
        Decay profile:
        - 0 to 4 hours: 1.0 (No decay)
        - 4 to 12 hours: Linear decay from 1.0 to 0.8
        - 12 to 24 hours: Linear decay from 0.8 to 0.5
        - 24 to 48 hours: Linear decay from 0.5 to 0.10
        - > 48 hours: 0.0
        """
        pub_dt = cls.parse_time(published_at)
        curr_dt = cls.parse_time(current_time) if current_time else datetime.utcnow()

        delta = curr_dt - pub_dt
        hours_elapsed = max(0.0, delta.total_seconds() / 3600.0)

        if hours_elapsed <= 4.0:
            return 1.0
        elif hours_elapsed <= 12.0:
            # 1.0 -> 0.8
            return 1.0 - ((hours_elapsed - 4.0) / 8.0) * 0.2
        elif hours_elapsed <= 24.0:
            # 0.8 -> 0.5
            return 0.8 - ((hours_elapsed - 12.0) / 12.0) * 0.3
        elif hours_elapsed <= 48.0:
            # 0.5 -> 0.1
            return 0.5 - ((hours_elapsed - 24.0) / 24.0) * 0.4
        else:
            return 0.0

    @classmethod
    def decay_article_impact(cls, article: Dict[str, Any], current_time: str = None) -> float:
        """
        Returns decayed impact score based on the article's published timestamp.
        """
        pub_time = article.get("published_at", "")
        impact_obj = article.get("impact")
        impact_score = 0.0
        if impact_obj:
            if hasattr(impact_obj, 'impact_score'):
                impact_score = impact_obj.impact_score
            elif isinstance(impact_obj, dict):
                impact_score = impact_obj.get("impact_score", 0.0)

        multiplier = cls.calculate_multiplier(pub_time, current_time)
        return round(impact_score * multiplier, 2)
