"""
DataFrame output renderer for the Climate Disclosure Agent framework.
"""
from typing import List
import pandas as pd
from cda.validation.base import AggregatedResult


class DataFrameOutput:
    """Render results as pandas DataFrame."""

    def render(self, result: AggregatedResult):
        """
        Render the aggregated result as a DataFrame.
        
        Args:
            result: The aggregated result to render
            
        Returns:
            pandas DataFrame with the results
        """
        # Create a summary DataFrame
        data = {
            'Company': [result.company_name],
            'Overall Score': [result.overall_score],
            'Grade': [result.grade],
            'Summary': [result.summary]
        }
        
        # Add dimension scores as columns
        for dim, score in result.dimension_scores.items():
            data[f'{dim.title()} Score'] = [score]
        
        df = pd.DataFrame(data)
        return df


class ComparisonResult:
    """Results from comparing multiple companies."""
    
    def __init__(self, results: List[AggregatedResult]):
        """
        Initialize with a list of results to compare.
        
        Args:
            results: List of aggregated results to compare
        """
        self.results = results
    
    def to_dataframe(self):
        """
        Convert comparison results to DataFrame.
        
        Returns:
            pandas DataFrame with comparison data
        """
        rows = []
        for result in self.results:
            row = {
                'Company': result.company_name,
                'Overall Score': result.overall_score,
                'Grade': result.grade,
                'Summary': result.summary
            }
            
            # Add dimension scores
            for dim, score in result.dimension_scores.items():
                row[f'{dim.title()} Score'] = score
            
            rows.append(row)
        
        return pd.DataFrame(rows)