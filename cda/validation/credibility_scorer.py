"""Credibility scorer for the News Consistency Validator."""

from typing import List

from .news_models import Contradiction


class CredibilityScorer:
    """Calculate credibility score based on contradictions found."""

    def score(
        self,
        contradictions: List[Contradiction],
        total_events: int
    ) -> float:
        """
        Calculate credibility score.

        Args:
            contradictions: List of contradictions found
            total_events: Total number of events processed

        Returns:
            Credibility score (0-100)
        """
        base_score = 100.0

        # Deduct points for each contradiction based on severity
        for contradiction in contradictions:
            if contradiction.severity == "critical":
                base_score -= 30
            elif contradiction.severity == "warning":
                base_score -= 15
            elif contradiction.severity == "info":
                base_score -= 5

        # Ensure score doesn't go below 0
        credibility_score = max(0.0, base_score)

        # If no events were found, return full score (assuming no negative news)
        if total_events == 0 and not contradictions:
            credibility_score = 100.0

        return credibility_score

    def get_rating(self, score: float) -> str:
        """
        Get rating based on credibility score.

        Args:
            score: Credibility score (0-100)

        Returns:
            Rating string
        """
        if 90 <= score <= 100:
            return "Excellent"
        elif 70 <= score < 90:
            return "Good"
        elif 50 <= score < 70:
            return "Fair"
        elif 30 <= score < 50:
            return "Poor"
        else:
            return "Very Poor"

    def get_detailed_feedback(self, contradictions: List[Contradiction]) -> str:
        """
        Generate detailed feedback based on contradictions found.

        Args:
            contradictions: List of contradictions found

        Returns:
            Detailed feedback string
        """
        if not contradictions:
            return "No credibility issues detected. The company's disclosures align well with publicly reported environmental events."

        critical_count = sum(1 for c in contradictions if c.severity == "critical")
        warning_count = sum(1 for c in contradictions if c.severity == "warning")
        info_count = sum(1 for c in contradictions if c.severity == "info")

        feedback_parts = []

        if critical_count > 0:
            feedback_parts.append(f"{critical_count} critical issue(s) found that significantly impact credibility.")
        if warning_count > 0:
            feedback_parts.append(f"{warning_count} warning(s) indicating potential credibility concerns.")
        if info_count > 0:
            feedback_parts.append(f"{info_count} informational item(s) noted.")

        # Add specific recommendations
        contradiction_types = [c.contradiction_type.value for c in contradictions]
        if "omission" in contradiction_types:
            feedback_parts.append("Recommendation: Ensure all material environmental events are disclosed in reports.")
        if "misrepresentation" in contradiction_types:
            feedback_parts.append("Recommendation: Align environmental claims with actual performance data.")
        if "magnitude_mismatch" in contradiction_types:
            feedback_parts.append("Recommendation: Provide accurate quantification of environmental impacts.")

        return " ".join(feedback_parts)