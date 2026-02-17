"""Cross validator for the News Consistency Validator."""

import re
from typing import List, Optional
from datetime import datetime

from ..extraction.schema import DisclosureExtract
from .news_models import (
    EnvironmentalEvent, 
    Contradiction, 
    ContradictionType,
    EventType
)


def determine_severity(event: EnvironmentalEvent) -> str:
    """Determine severity level of an event."""
    if event.event_type in [EventType.FINE, EventType.LAWSUIT, EventType.VIOLATION]:
        if event.financial_impact and event.financial_impact > 10_000_000:
            return "critical"
        return "warning"
    elif event.event_type in [EventType.INVESTIGATION, EventType.REGULATION]:
        return "warning"
    else:
        return "info"


class CrossValidator:
    """Cross-validate disclosure reports with news events."""

    def validate(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """
        Cross-validate disclosure data with news events.

        Args:
            disclosure: Disclosure data
            events: List of news events

        Returns:
            List of contradictions
        """
        contradictions = []
        
        # Check for omissions (events not mentioned in the report)
        contradictions.extend(self._check_omissions(disclosure, events))
        
        # Check for misrepresentations (conflicting claims)
        contradictions.extend(self._check_misrepresentations(disclosure, events))
        
        # Check for timing mismatches
        contradictions.extend(self._check_timing_mismatches(disclosure, events))
        
        # Check for magnitude mismatches
        contradictions.extend(self._check_magnitude_mismatches(disclosure, events))
        
        return contradictions

    def _check_omissions(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """Check for omissions (events not disclosed in the report)."""
        contradictions = []
        
        for event in events:
            # Check if critical events were omitted from risks section
            if event.event_type in [EventType.FINE, EventType.LAWSUIT, EventType.VIOLATION]:
                # Look for mentions of the event in the disclosure
                risks_text = " ".join([risk.description for risk in disclosure.risks])
                targets_text = " ".join([target.description for target in disclosure.targets])
                emissions_text = " ".join([f"{e.scope.value} {e.value}" for e in disclosure.emissions])
                
                disclosure_text = " ".join([
                    risks_text,
                    targets_text,
                    emissions_text
                ]).lower()
                
                # Create keywords to search for
                event_keywords = [kw.lower() for kw in event.keywords]
                event_description_lower = event.description.lower()
                
                # Check if any event-related keywords appear in the disclosure
                found_mention = False
                for keyword in event_keywords + [event_description_lower]:
                    if keyword in disclosure_text:
                        found_mention = True
                        break
                
                if not found_mention:
                    # Determine impact on credibility based on event type and severity
                    impact = -30 if event.severity == "critical" else -15 if event.severity == "warning" else -5
                    
                    contradiction = Contradiction(
                        contradiction_type=ContradictionType.OMISSION,
                        severity=event.severity,
                        claim_in_report=None,
                        evidence_from_news=event.description,
                        event=event,
                        impact_on_credibility=impact,
                        recommendation="Disclose all material environmental penalties and legal proceedings in the Risks section"
                    )
                    contradictions.append(contradiction)
        
        return contradictions

    def _check_misrepresentations(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """Check for misrepresentations (claims that contradict news)."""
        contradictions = []
        
        # Convert disclosure text to lowercase for searching
        risks_text = " ".join([risk.description for risk in disclosure.risks])
        targets_text = " ".join([target.description for target in disclosure.targets])
        emissions_text = " ".join([f"{e.scope.value} {e.value}" for e in disclosure.emissions])
        
        disclosure_text = " ".join([
            risks_text,
            targets_text,
            emissions_text
        ]).lower()
        
        for event in events:
            # Check if company claimed positive environmental stance but news shows negative events
            positive_claims_patterns = [
                r"carbon.*neutral", 
                r"zero.*emission", 
                r"climate.*positive", 
                r"sustainable.*practice",
                r"environmentally.*friendly",
                r"green.*initiative",
                r"clean.*energy"
            ]
            
            negative_event_indicators = []
            if event.event_type == EventType.FINE:
                negative_event_indicators.extend(["fine", "penalty", "violation"])
            elif event.event_type == EventType.LAWSUIT:
                negative_event_indicators.extend(["lawsuit", "legal", "court"])
            elif event.event_type == EventType.VIOLATION:
                negative_event_indicators.extend(["violation", "breach", "non-compliance"])
            elif event.event_type == EventType.ACCIDENT:
                negative_event_indicators.extend(["accident", "spill", "leak", "incident"])
            
            # Check for contradictory claims
            for pattern in positive_claims_patterns:
                if re.search(pattern, disclosure_text):
                    for indicator in negative_event_indicators:
                        if indicator in event.description.lower():
                            # Found contradiction
                            impact = -30 if event.severity == "critical" else -15 if event.severity == "warning" else -5
                            
                            contradiction = Contradiction(
                                contradiction_type=ContradictionType.MISREPRESENTATION,
                                severity=event.severity,
                                claim_in_report=f"Company claims '{pattern}' but news reports {event.event_type.value}: {event.description}",
                                evidence_from_news=event.description,
                                event=event,
                                impact_on_credibility=impact,
                                recommendation="Align environmental claims with actual performance and disclose any discrepancies"
                            )
                            contradictions.append(contradiction)
                            break  # Break inner loop once contradiction is found
    
        return contradictions

    def _check_timing_mismatches(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """Check for timing mismatches between events and reporting."""
        contradictions = []
        
        # Get report year to compare with event dates
        report_year = disclosure.report_year
        
        for event in events:
            try:
                event_year = int(event.date.split('-')[0])
                
                # Check if event occurred in the report year but wasn't disclosed
                if event_year == report_year:
                    # Check if there's no mention of the event in the disclosure
                    risks_text = " ".join([risk.description for risk in disclosure.risks])
                    targets_text = " ".join([target.description for target in disclosure.targets])
                    emissions_text = " ".join([f"{e.scope.value} {e.value}" for e in disclosure.emissions])
                    
                    disclosure_text = " ".join([
                        risks_text,
                        targets_text,
                        emissions_text
                    ]).lower()
                    
                    event_keywords = [kw.lower() for kw in event.keywords]
                    event_description_lower = event.description.lower()
                    
                    found_mention = False
                    for keyword in event_keywords + [event_description_lower]:
                        if keyword in disclosure_text:
                            found_mention = True
                            break
                    
                    if not found_mention:
                        impact = -15 if event.severity in ["critical", "warning"] else -5
                        
                        contradiction = Contradiction(
                            contradiction_type=ContradictionType.TIMING_MISMATCH,
                            severity=event.severity,
                            claim_in_report=f"Event occurred in {event_year} but was not disclosed",
                            evidence_from_news=f"Event reported in {event.date}: {event.description}",
                            event=event,
                            impact_on_credibility=impact,
                            recommendation="Ensure timely disclosure of all material environmental events"
                        )
                        contradictions.append(contradiction)
            except (ValueError, IndexError):
                # If date parsing fails, skip this check
                continue
        
        return contradictions

    def _check_magnitude_mismatches(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """Check for magnitude mismatches between reported and actual impacts."""
        contradictions = []
        
        for event in events:
            if event.financial_impact:
                # Look for financial disclosures in the report
                risks_text = " ".join([risk.description for risk in disclosure.risks])
                targets_text = " ".join([target.description for target in disclosure.targets])
                
                disclosure_text = " ".join([
                    risks_text,
                    targets_text
                ])
                
                # Try to find any financial figures in the disclosure
                # This is a simplified approach - in practice, you'd need more sophisticated parsing
                financial_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|bn|billion)?', disclosure_text, re.IGNORECASE)
                
                for match in financial_matches:
                    try:
                        reported_amount = float(match.replace(',', ''))
                        
                        # Apply multiplier based on context
                        if 'million' in disclosure_text.lower():
                            reported_amount *= 1_000_000
                        elif 'billion' in disclosure_text.lower() or 'bn' in disclosure_text.lower():
                            reported_amount *= 1_000_000_000
                        
                        # Check if there's a significant discrepancy (more than 5x difference)
                        if reported_amount > 0 and abs(event.financial_impact - reported_amount) / max(event.financial_impact, reported_amount) > 0.5:
                            impact = -20 if event.severity in ["critical", "warning"] else -10
                            
                            contradiction = Contradiction(
                                contradiction_type=ContradictionType.MAGNITUDE_MISMATCH,
                                severity=event.severity,
                                claim_in_report=f"Reported financial impact: ${reported_amount:,.2f}, Actual: ${event.financial_impact:,.2f}",
                                evidence_from_news=f"Financial penalty of ${event.financial_impact:,.2f} reported in news",
                                event=event,
                                impact_on_credibility=impact,
                                recommendation="Provide accurate quantification of financial impacts from environmental events"
                            )
                            contradictions.append(contradiction)
                    except ValueError:
                        continue
        
        return contradictions