"""Visualization module for climate disclosure analysis results."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any
from cda.validation.base import AggregatedResult, ValidationFinding, ValidationResult


class DisclosureVisualizer:
    """Generate interactive visualizations for climate disclosure analysis results."""

    @staticmethod
    def radar_chart(result: AggregatedResult) -> go.Figure:
        """Generate a radar chart showing multi-dimensional scores for a single company.
        
        Args:
            result: Aggregated analysis result for a single company
            
        Returns:
            Plotly figure object containing the radar chart
        """
        dims = result.dimension_scores
        categories = list(dims.keys())
        values = list(dims.values())

        # Handle empty dimension scores
        if not categories or not values:
            fig = go.Figure()
            fig.add_annotation(text="No dimensional data available", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title=f"Disclosure Quality - {result.company_name}")
            return fig

        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],  # Close the radar chart
            theta=categories + [categories[0]],  # Close the radar chart
            fill='toself',
            name=result.company_name,
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 100],
                    tickmode='linear',
                    dtick=20,
                    gridcolor='lightgray'
                ),
                angularaxis=dict(gridcolor='lightgray')
            ),
            title=f"Disclosure Quality - {result.company_name}",
            template='plotly_white',
            font=dict(size=12),
            hovermode='closest'
        )
        
        return fig

    @staticmethod
    def comparison_radar(results: List[AggregatedResult]) -> go.Figure:
        """Generate a comparative radar chart showing multi-dimensional scores across multiple companies.
        
        Args:
            results: List of aggregated analysis results for multiple companies
            
        Returns:
            Plotly figure object containing the comparison radar chart
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="No results to compare", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title="Cross-Company Disclosure Comparison")
            return fig

        # Check if all results have the same dimensions
        first_dims = results[0].dimension_scores
        categories = list(first_dims.keys())
        
        # Verify all results have the same dimensions
        for result in results[1:]:
            if list(result.dimension_scores.keys()) != categories:
                # Handle different dimensions gracefully
                fig = go.Figure()
                fig.add_annotation(text="Cannot compare: Different dimensions across companies", 
                                   xref="paper", yref="paper",
                                   x=0.5, y=0.5, showarrow=False)
                fig.update_layout(title="Cross-Company Disclosure Comparison")
                return fig

        fig = go.Figure()
        
        # Add trace for each company
        for result in results:
            dims = result.dimension_scores
            values = list(dims.values())
            
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],  # Close the radar chart
                theta=categories + [categories[0]],  # Close the radar chart
                fill='toself',
                name=result.company_name,
                line=dict(width=2),
                marker=dict(size=6),
                opacity=0.7
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 100],
                    tickmode='linear',
                    dtick=20,
                    gridcolor='lightgray'
                ),
                angularaxis=dict(gridcolor='lightgray')
            ),
            title="Cross-Company Disclosure Comparison",
            template='plotly_white',
            font=dict(size=12),
            hovermode='closest'
        )
        
        return fig

    @staticmethod
    def completeness_heatmap(results: List[AggregatedResult]) -> go.Figure:
        """Generate a heatmap showing disclosure completeness across companies and dimensions.
        
        Args:
            results: List of aggregated analysis results for multiple companies
            
        Returns:
            Plotly figure object containing the completeness heatmap
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="No results for heatmap", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title="Disclosure Completeness Matrix")
            return fig

        # Extract company names and dimensions
        companies = [r.company_name for r in results]
        
        # Get all unique dimensions across all results
        all_dimensions = set()
        for result in results:
            all_dimensions.update(result.dimension_scores.keys())
        dimensions = sorted(list(all_dimensions))
        
        if not dimensions:
            fig = go.Figure()
            fig.add_annotation(text="No dimensional data for heatmap", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title="Disclosure Completeness Matrix")
            return fig

        # Create the matrix of scores
        z = []
        for result in results:
            row = []
            for dim in dimensions:
                row.append(result.dimension_scores.get(dim, 0))
            z.append(row)

        # Create hover text with actual values
        text = [[f"{val:.1f}" for val in row] for row in z]

        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dimensions,
            y=companies,
            colorscale="RdYlGn",  # Red-Yellow-Green scale
            zmin=0, 
            zmax=100,
            text=text,
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>" +
                         "<b>%{x}</b>: %{z}<extra></extra>",
        ))
        
        fig.update_layout(
            title="Disclosure Completeness Matrix",
            xaxis_title="Disclosure Dimensions",
            yaxis_title="Companies",
            template='plotly_white',
            font=dict(size=12)
        )
        
        # Rotate x-axis labels for better readability
        fig.update_xaxes(tickangle=-45)
        
        return fig

    @staticmethod
    def findings_summary(result: AggregatedResult) -> go.Figure:
        """Generate a bar chart showing validation findings by severity level.
        
        Args:
            result: Aggregated analysis result for a single company
            
        Returns:
            Plotly figure object containing the findings summary chart
        """
        # Collect all findings from all validation results
        all_findings = []
        for vr in result.validation_results:
            all_findings.extend(vr.findings)

        # Count findings by severity
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        for finding in all_findings:
            severity_key = finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity).lower()
            # Map possible variations to our keys
            if 'critical' in severity_key:
                severity_counts["critical"] += 1
            elif 'warning' in severity_key:
                severity_counts["warning"] += 1
            elif 'info' in severity_key or 'information' in severity_key:
                severity_counts["info"] += 1
            else:
                # Default to info for any other severity types
                severity_counts["info"] += 1

        # Define colors for each severity level
        colors = {
            "critical": "#e74c3c",  # Red for critical
            "warning": "#f39c12",  # Orange for warning
            "info": "#3498db"      # Blue for info
        }

        # Create the bar chart
        fig = go.Figure(data=[go.Bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            marker_color=[colors[k] for k in severity_counts.keys()],
            text=list(severity_counts.values()),  # Show count on bars
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>' +
                         'Count: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            title=f"Validation Findings - {result.company_name}",
            xaxis_title="Severity Level",
            yaxis_title="Number of Findings",
            template='plotly_white',
            font=dict(size=12)
        )
        
        # Add a note if no findings
        if sum(severity_counts.values()) == 0:
            fig.add_annotation(
                text="No validation findings detected",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        return fig

    @staticmethod
    def score_trend(results: List[AggregatedResult]) -> go.Figure:
        """Generate a trend chart showing score changes over time for one or more companies.
        
        Note: This assumes that results are ordered chronologically and represent the same company over time.
        
        Args:
            results: List of aggregated analysis results ordered chronologically
            
        Returns:
            Plotly figure object containing the score trend chart
        """
        if not results:
            fig = go.Figure()
            fig.add_annotation(text="No results for trend analysis", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title="Score Trend Analysis")
            return fig

        # Group results by company
        company_results = {}
        for result in results:
            if result.company_name not in company_results:
                company_results[result.company_name] = []
            company_results[result.company_name].append(result)

        fig = go.Figure()

        # Add a line for each company
        for company, company_data in company_results.items():
            years = [result.report_year if hasattr(result, 'report_year') else i for i, result in enumerate(company_data)]
            scores = [result.overall_score for result in company_data]
            
            fig.add_trace(go.Scatter(
                x=years,
                y=scores,
                mode='lines+markers',
                name=company,
                line=dict(width=3),
                marker=dict(size=8)
            ))

        fig.update_layout(
            title="Overall Score Trend Over Time",
            xaxis_title="Year / Report Period",
            yaxis_title="Overall Score",
            template='plotly_white',
            font=dict(size=12),
            hovermode='x unified'
        )
        
        return fig

    @staticmethod
    def detailed_findings_table(result: AggregatedResult) -> go.Figure:
        """Generate an interactive table showing detailed validation findings.
        
        Args:
            result: Aggregated analysis result for a single company
            
        Returns:
            Plotly figure object containing the detailed findings table
        """
        # Collect all findings from all validation results
        all_findings = []
        for vr in result.validation_results:
            for finding in vr.findings:
                all_findings.append({
                    'Validator': vr.validator_name,
                    'Code': finding.code,
                    'Severity': finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity),
                    'Message': finding.message[:100] + "..." if len(finding.message) > 100 else finding.message,  # Truncate long messages
                    'Field': finding.field if finding.field else 'N/A',
                    'Recommendation': finding.recommendation[:100] + "..." if finding.recommendation and len(finding.recommendation) > 100 else (finding.recommendation or 'N/A')
                })

        if not all_findings:
            fig = go.Figure()
            fig.add_annotation(text="No validation findings to display", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
            fig.update_layout(title=f"Detailed Findings Table - {result.company_name}")
            return fig

        # Create the table
        header_values = ['Validator', 'Code', 'Severity', 'Message', 'Field', 'Recommendation']
        cell_values = [[row[col] for row in all_findings] for col in header_values]

        # Color rows based on severity
        row_colors = []
        for finding in all_findings:
            severity = finding['Severity'].lower()
            if 'critical' in severity:
                row_colors.append('#ffebee')  # Light red for critical
            elif 'warning' in severity:
                row_colors.append('#fff3e0')  # Light orange for warning
            else:
                row_colors.append('#e3f2fd')  # Light blue for info

        fig = go.Figure(data=[go.Table(
            header=dict(
                values=[f"<b>{col}</b>" for col in header_values],
                fill_color='paleturquoise',
                align='left',
                font=dict(size=12, color='black'),
                height=30
            ),
            cells=dict(
                values=cell_values,
                fill_color=[row_colors],  # Apply row colors
                align='left',
                font=dict(size=11),
                height=25
            )
        )])

        fig.update_layout(
            title=f"Detailed Validation Findings - {result.company_name}",
            font=dict(size=11)
        )

        return fig