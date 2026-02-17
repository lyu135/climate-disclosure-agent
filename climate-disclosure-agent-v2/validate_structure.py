#!/usr/bin/env python3
"""
Quick validation script for Climate Disclosure Agent project structure
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, min_size=0):
    """Check if file exists and has minimum size"""
    path = Path(filepath)
    if not path.exists():
        return False, "Missing"
    size = path.stat().st_size
    if size < min_size:
        return False, f"Empty ({size}B)"
    return True, f"OK ({size}B)"

def main():
    print("=" * 60)
    print("Climate Disclosure Agent - Project Structure Validation")
    print("=" * 60)
    
    # Core modules to check
    core_files = {
        "Core Schema": [
            ("cda/extraction/schema.py", 1000),
            ("cda/validation/base.py", 500),
        ],
        "Validators": [
            ("cda/validation/consistency.py", 1000),
            ("cda/validation/quantification.py", 1000),
            ("cda/validation/completeness.py", 1000),
            ("cda/validation/risk_coverage.py", 1000),
            ("cda/validation/pipeline.py", 1000),
        ],
        "Agent & Extraction": [
            ("cda/agent.py", 2000),
            ("cda/extraction/llm_extractor.py", 2000),
            ("cda/ingestion/pdf_handler.py", 1000),
        ],
        "Adapters": [
            ("cda/adapters/base.py", 500),
            ("cda/adapters/sbti_adapter.py", 1000),
            ("cda/adapters/cdp_adapter.py", 1000),
        ],
        "Scoring & Output": [
            ("cda/scoring/scorer.py", 1000),
            ("cda/output/visualizer.py", 2000),
            ("cda/output/json_output.py", 500),
            ("cda/output/dataframe_output.py", 500),
        ],
        "Examples": [
            ("examples/01_basic_analysis.py", 500),
            ("examples/02_with_external_data.py", 500),
            ("examples/03_custom_validator.py", 500),
            ("examples/04_batch_comparison.py", 500),
            ("examples/05_custom_adapter.py", 500),
        ],
        "Documentation": [
            ("README.md", 5000),
            ("docs/methodology.md", 1000),
            ("docs/extending.md", 5000),
            ("pyproject.toml", 500),
        ],
    }
    
    total_files = 0
    passed_files = 0
    
    for category, files in core_files.items():
        print(f"\n{category}:")
        print("-" * 60)
        for filepath, min_size in files:
            total_files += 1
            exists, status = check_file_exists(filepath, min_size)
            symbol = "✅" if exists else "❌"
            print(f"  {symbol} {filepath:<45} {status}")
            if exists:
                passed_files += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {passed_files}/{total_files} files validated")
    print(f"Completion: {passed_files/total_files*100:.1f}%")
    print("=" * 60)
    
    if passed_files == total_files:
        print("\n🎉 All core modules are present and non-empty!")
        return 0
    else:
        print(f"\n⚠️  {total_files - passed_files} files need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
