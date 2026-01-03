"""
Epistemic Assessor - Calculate know/uncertainty vectors.

Applies Empirica's epistemic principles to documentation assessment.
"""

from dataclasses import dataclass
from typing import Any

from .coverage import CoverageResult


@dataclass
class EpistemicAssessment:
    """Epistemic assessment result."""
    know: float
    uncertainty: float
    overall_coverage: float
    total_features: int
    documented_features: int
    assessment: str
    recommendations: list[str]
    moon: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "know": round(self.know, 2),
            "uncertainty": round(self.uncertainty, 2),
            "overall_coverage": round(self.overall_coverage * 100, 1),
            "total_features": self.total_features,
            "documented_features": self.documented_features,
            "assessment": self.assessment,
            "recommendations": self.recommendations,
            "moon": self.moon
        }


class EpistemicAssessor:
    """
    Calculate epistemic vectors for documentation coverage.

    Philosophy:
    - know = what the docs explain
    - uncertainty = what's hidden from users
    - Higher coverage = higher know, lower uncertainty
    """

    def __init__(self):
        self.results: list[CoverageResult] = []

    def add_result(self, result: CoverageResult):
        """Add a coverage result."""
        if result.total > 0:  # Only add if there are items
            self.results.append(result)

    def assess(self) -> EpistemicAssessment:
        """Calculate epistemic assessment."""
        if not self.results:
            return EpistemicAssessment(
                know=0.0,
                uncertainty=1.0,
                overall_coverage=0.0,
                total_features=0,
                documented_features=0,
                assessment="No features discovered",
                recommendations=["Add discoverable features to your project"],
                moon="🌑"
            )

        # Calculate totals
        total = sum(r.total for r in self.results)
        documented = sum(r.documented for r in self.results)
        coverage = documented / total if total > 0 else 0.0

        # Calculate epistemic vectors
        # know scales with coverage but caps at 0.95 (never perfect knowledge)
        know = min(0.95, coverage * 1.1)  # Slight boost for good coverage

        # uncertainty is inverse but with a floor (always some uncertainty)
        uncertainty = max(0.05, 1.0 - coverage)

        # Generate assessment text
        if coverage >= 0.80:
            assessment = "Documentation is comprehensive"
        elif coverage >= 0.60:
            assessment = "Documentation has notable gaps"
        elif coverage >= 0.40:
            assessment = "Significant features undocumented"
        elif coverage >= 0.20:
            assessment = "Major documentation debt"
        else:
            assessment = "Critical: Most features undocumented"

        # Generate recommendations
        recommendations = self._generate_recommendations()

        # Moon phase
        moon = self._score_to_moon(coverage)

        return EpistemicAssessment(
            know=know,
            uncertainty=uncertainty,
            overall_coverage=coverage,
            total_features=total,
            documented_features=documented,
            assessment=assessment,
            recommendations=recommendations,
            moon=moon
        )

    def _generate_recommendations(self) -> list[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Sort by coverage (worst first)
        sorted_results = sorted(self.results, key=lambda r: r.coverage)

        for result in sorted_results[:5]:  # Top 5 worst categories
            if result.coverage < 0.70 and result.undocumented:
                undoc_preview = result.undocumented[:3]
                if len(result.undocumented) > 3:
                    undoc_preview.append(f"...and {len(result.undocumented) - 3} more")
                recommendations.append(
                    f"Document {result.category}: {', '.join(undoc_preview)}"
                )

        return recommendations[:5]

    def _score_to_moon(self, score: float) -> str:
        """Convert score to moon phase."""
        if score >= 0.85:
            return "🌕"
        elif score >= 0.70:
            return "🌔"
        elif score >= 0.50:
            return "🌓"
        elif score >= 0.30:
            return "🌒"
        else:
            return "🌑"
