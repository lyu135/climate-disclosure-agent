import pandas as pd
from typing import Dict, Any, Optional

from cda.adapters.base import BaseAdapter, DataNotAvailableError
from cda.extraction.schema import DisclosureExtract, TargetData
from cda.validation.base import ValidationResult, ValidationFinding, Severity


class SBTiAdapter(BaseAdapter):
    """
    SBTi (Science Based Targets initiative) 数据适配器。

    用途：验证企业是否真实持有SBTi认证目标。
    数据：用户需从 https://sciencebasedtargets.org 下载CSV。
    """

    name = "sbti"
    data_source_url = "https://sciencebasedtargets.org/companies-taking-action"

    def __init__(self, data_source=None):
        """
        Args:
            data_source: 支持多种输入格式
                - str: CSV/Excel文件路径
                - pd.DataFrame: 已加载的数据
                - None: 无数据模式（会在cross_validate时提示）
        """
        self._data = self._load(data_source)

    def cross_validate(self, extract: DisclosureExtract) -> ValidationResult:
        if self._data is None:
            raise DataNotAvailableError(
                f"SBTi data not provided. Download from: {self.data_source_url}"
            )

        findings = []
        company = extract.company_name

        # 查找企业记录
        match = self._fuzzy_match(company)

        if match is None:
            # 企业声称有SBTi但数据库中没有
            if any(t.is_science_based for t in extract.targets):
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="SBTI-001",
                    severity=Severity.CRITICAL,
                    message=f"Company claims SBTi target but not found in SBTi database",
                    recommendation="Verify SBTi status directly with the initiative"
                ))
        else:
            # 找到记录，验证细节匹配
            for target in extract.targets:
                if target.is_science_based:
                    discrepancies = self._compare_target(target, match)
                    findings.extend(discrepancies)

        score = 1.0 - (len([f for f in findings if f.severity == Severity.CRITICAL]) * 0.3)

        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=max(score, 0.0),
            findings=findings,
            metadata={"sbti_record_found": match is not None}
        )

    def _fuzzy_match(self, company_name: str) -> Optional[pd.Series]:
        """模糊匹配企业名（处理名称不一致问题）"""
        from difflib import get_close_matches
        
        if self._data is None or self._data.empty:
            return None
            
        names = self._data["Company Name"].tolist()
        matches = get_close_matches(company_name, names, n=1, cutoff=0.7)
        
        if matches:
            return self._data[self._data["Company Name"] == matches[0]].iloc[0]
        return None

    def _compare_target(self, disclosed_target: TargetData, sbti_record) -> list[ValidationFinding]:
        """对比披露目标与SBTi记录"""
        findings = []

        # 验证目标年份
        if disclosed_target.target_year and "Target Year" in sbti_record:
            if disclosed_target.target_year != sbti_record["Target Year"]:
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="SBTI-002",
                    severity=Severity.WARNING,
                    message=f"Target year mismatch: disclosed {disclosed_target.target_year}, "
                            f"SBTi records {sbti_record['Target Year']}"
                ))

        return findings

    def get_benchmark(self, sector: str) -> Dict[str, Any]:
        if self._data is None:
            return {}
        sector_data = self._data[self._data["Sector"].str.contains(sector, case=False, na=False)]
        return {
            "total_companies": len(sector_data),
            "committed_pct": len(sector_data[sector_data["Status"] == "Targets Set"]) / max(len(sector_data), 1),
        }

    def _load(self, source):
        if source is None:
            return None
        if isinstance(source, pd.DataFrame):
            return source
        if isinstance(source, str):
            if source.endswith(".csv"):
                return pd.read_csv(source)
            elif source.endswith((".xlsx", ".xls")):
                return pd.read_excel(source)
        return None

    def _has_data(self) -> bool:
        return self._data is not None