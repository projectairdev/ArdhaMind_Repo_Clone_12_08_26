from __future__ import annotations

import re
from typing import Any, Dict, List

class NewsDeduplicator:
    """
    Stateless deduplication layer.
    Identifies similar articles based on title/content similarity and merges duplicates.
    """

    @staticmethod
    def _normalize_title(title: str) -> str:
        """
        Cleans and normalizes title for fuzzy comparison.
        """
        text = title.lower()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        return " ".join(text.split())

    @staticmethod
    def _similarity_ratio(str1: str, str2: str) -> float:
        """
        Computes word intersection over union (IoU) ratio as a fast stateless similarity metric.
        """
        words1 = set(str1.split())
        words2 = set(str2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @classmethod
    def deduplicate(cls, articles: List[Dict[str, Any]], threshold: float = 0.70) -> List[Dict[str, Any]]:
        """
        Detects similar articles, merges content/metadata, and keeps track of source references.
        """
        if not articles:
            return []

        unique_articles: List[Dict[str, Any]] = []

        for art in articles:
            norm_title = cls._normalize_title(art.get("title", ""))
            found_dup = False

            for unique_art in unique_articles:
                unique_norm = cls._normalize_title(unique_art.get("title", ""))
                
                # Check for exact URL match or high Title similarity
                url_match = (art.get("url") and art.get("url") == unique_art.get("url"))
                title_sim = cls._similarity_ratio(norm_title, unique_norm)

                if url_match or title_sim >= threshold:
                    # Found duplicate! Merge sources and content
                    found_dup = True
                    # Maintain source references
                    sources = unique_art.setdefault("sources", [unique_art.get("source", "Unknown")])
                    new_source = art.get("source", "Unknown")
                    if new_source not in sources:
                        sources.append(new_source)
                    
                    # Update primary source to be a comma-separated list of unique sources
                    unique_art["source"] = ", ".join(sources)

                    # Update content to use the longer/more informative description
                    current_content = unique_art.get("content", "")
                    new_content = art.get("content", "")
                    if len(new_content) > len(current_content):
                        unique_art["content"] = new_content

                    # Keep both URLs if distinct
                    urls = unique_art.setdefault("urls", [unique_art.get("url", "")])
                    new_url = art.get("url", "")
                    if new_url and new_url not in urls:
                        urls.append(new_url)
                    break

            if not found_dup:
                # Add sources list for future merges
                art_copy = dict(art)
                art_copy["sources"] = [art_copy.get("source", "Unknown")]
                art_copy["urls"] = [art_copy.get("url", "")]
                unique_articles.append(art_copy)

        return unique_articles
