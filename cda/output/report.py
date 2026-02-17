"""
Report renderer for the Climate Disclosure Agent framework.
"""
from cda.validation.base import AggregatedResult


class ReportRenderer:
    """Render results as formatted report."""

    def render(self, result: AggregatedResult) -> str:
        """
        Render the aggregated result as a formatted report.
        
        Args:
            result: The aggregated result to render
            
        Returns:
            Formatted report string
        """
        report = f"# Climate Disclosure Analysis Report\n\n"
        report += f"**Company**: {result.company_name}\n"
        report += f"**Report Year**: {result.report_year if hasattr(result, 'report_year') else 'N/A'}\n\n"
        
        report += f"## Overall Assessment\n"
        report += f"- **Score**: {result.overall_score}/100\n"
        report += f"- **Grade**: {result.grade}\n"
        report += f"- **Summary**: {result.summary}\n\n"
        
        report += f"## Dimension Scores\n"
        for dim, score in result.dimension_scores.items():
            report += f"- **{dim.replace('_', ' ').title()}**: {score:.1f}/100\n"
        report += "\n"
        
        report += f"## Validation Findings\n"
        critical_findings = []
        warning_findings = []
        info_findings = []
        
        for vr in result.validation_results:
            for finding in vr.findings:
                if finding.severity == 'critical':
                    critical_findings.append(finding)
                elif finding.severity == 'warning':
                    warning_findings.append(finding)
                else:
                    info_findings.append(finding)
        
        if critical_findings:
            report += f"### Critical Issues ({len(critical_findings)})\n"
            for finding in critical_findings:
                report += f"- [{finding.code}] {finding.message}\n"
            report += "\n"
        
        if warning_findings:
            report += f"### Warnings ({len(warning_findings)})\n"
            for finding in warning_findings:
                report += f"- [{finding.code}] {finding.message}\n"
            report += "\n"
        
        if info_findings:
            report += f"### Informational ({len(info_findings)})\n"
            for finding in info_findings:
                report += f"- [{finding.code}] {finding.message}\n"
            report += "\n"
        
        if result.cross_validation:
            report += f"## Cross-Validation\n"
            report += f"- Adapters used: {', '.join(result.cross_validation.get('adapters_used', []))}\n"
            report += f"- Penalty applied: {result.cross_validation.get('penalty_applied', 0)}\n"
            report += "\n"
        
        return report