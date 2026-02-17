"""JSON output module for climate disclosure analysis results."""
import json
from typing import Union, Dict, Any, List
from pathlib import Path
from cda.validation.base import AggregatedResult
from datetime import datetime


class JSONOutputRenderer:
    """Render analysis results to JSON format."""
    
    def __init__(self, indent: int = 2, sort_keys: bool = True):
        """
        Initialize the JSON renderer.
        
        Args:
            indent: Number of spaces for indentation in JSON output
            sort_keys: Whether to sort keys alphabetically in output
        """
        self.indent = indent
        self.sort_keys = sort_keys
    
    def render(self, result: AggregatedResult) -> str:
        """
        Convert an AggregatedResult to a JSON string.
        
        Args:
            result: The aggregated analysis result to convert
            
        Returns:
            JSON string representation of the result
        """
        data = self._convert_to_dict(result)
        return json.dumps(data, indent=self.indent, sort_keys=self.sort_keys, default=str)
    
    def render_list(self, results: List[AggregatedResult]) -> str:
        """
        Convert a list of AggregatedResults to a JSON string.
        
        Args:
            results: List of aggregated analysis results to convert
            
        Returns:
            JSON string representation of the results
        """
        data_list = [self._convert_to_dict(result) for result in results]
        return json.dumps(data_list, indent=self.indent, sort_keys=self.sort_keys, default=str)
    
    def save(self, result: AggregatedResult, filepath: Union[str, Path]) -> None:
        """
        Save an AggregatedResult to a JSON file.
        
        Args:
            result: The aggregated analysis result to save
            filepath: Path to the output JSON file
        """
        data = self._convert_to_dict(result)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=self.indent, sort_keys=self.sort_keys, default=str)
    
    def save_list(self, results: List[AggregatedResult], filepath: Union[str, Path]) -> None:
        """
        Save a list of AggregatedResults to a JSON file.
        
        Args:
            results: List of aggregated analysis results to save
            filepath: Path to the output JSON file
        """
        data_list = [self._convert_to_dict(result) for result in results]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=self.indent, sort_keys=self.sort_keys, default=str)
    
    def _convert_to_dict(self, result: AggregatedResult) -> Dict[str, Any]:
        """
        Convert an AggregatedResult to a dictionary suitable for JSON serialization.
        
        Args:
            result: The aggregated analysis result to convert
            
        Returns:
            Dictionary representation of the result
        """
        # Convert the main result fields to a dictionary
        result_dict = {
            "company_name": result.company_name,
            "overall_score": result.overall_score,
            "grade": result.grade,
            "dimension_scores": result.dimension_scores,
            "summary": result.summary,
            "timestamp": datetime.now().isoformat(),
            "validation_results": []
        }
        
        # Add cross-validation data if present
        if result.cross_validation is not None:
            result_dict["cross_validation"] = result.cross_validation
        
        # Process each validation result
        for vr in result.validation_results:
            vr_dict = {
                "validator_name": vr.validator_name,
                "score": vr.score,
                "max_score": getattr(vr, 'max_score', 1.0),  # Handle cases where max_score might not exist
                "metadata": vr.metadata,
                "findings": []
            }
            
            # Process each finding
            for finding in vr.findings:
                finding_dict = {
                    "validator": finding.validator,
                    "code": finding.code,
                    "severity": str(finding.severity) if hasattr(finding.severity, 'value') else finding.severity,
                    "message": finding.message,
                    "field": finding.field,
                    "evidence": finding.evidence,
                    "recommendation": finding.recommendation
                }
                vr_dict["findings"].append(finding_dict)
            
            result_dict["validation_results"].append(vr_dict)
        
        return result_dict


def render_json(result: AggregatedResult, indent: int = 2, sort_keys: bool = True) -> str:
    """
    Convenience function to render an AggregatedResult to JSON string.
    
    Args:
        result: The aggregated analysis result to convert
        indent: Number of spaces for indentation in JSON output
        sort_keys: Whether to sort keys alphabetically in output
        
    Returns:
        JSON string representation of the result
    """
    renderer = JSONOutputRenderer(indent=indent, sort_keys=sort_keys)
    return renderer.render(result)


def save_json(result: AggregatedResult, filepath: Union[str, Path], indent: int = 2, sort_keys: bool = True) -> None:
    """
    Convenience function to save an AggregatedResult to a JSON file.
    
    Args:
        result: The aggregated analysis result to save
        filepath: Path to the output JSON file
        indent: Number of spaces for indentation in JSON output
        sort_keys: Whether to sort keys alphabetically in output
    """
    renderer = JSONOutputRenderer(indent=indent, sort_keys=sort_keys)
    renderer.save(result, filepath)