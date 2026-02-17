import pandas as pd
from typing import Dict, Any, Optional

from cda.adapters.base import BaseAdapter, DataNotAvailableError
from cda.extraction.schema import DisclosureExtract
from cda.validation.base import ValidationResult, ValidationFinding, Severity


class CDPAdapter(BaseAdapter):
    """
    CDP (Carbon Disclosure Project) 数据适配器。

    用途：验证企业的CDP披露和评分情况。
    数据：用户需从CDP网站获取历史问卷回复数据。
    """

    name = "cdp"
    data_source_url = "https://www.cdp.net/en/responses"

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
                f"CDP data not provided. Download from: {self.data_source_url}"
            )

        findings = []
        company = extract.company_name

        # 查找企业记录
        matches = self._fuzzy_match(company)

        if not matches:
            # 企业声称参与CDP但数据库中没有记录
            if "cdp" in [f.lower() for f in extract.framework]:
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="CDP-001",
                    severity=Severity.WARNING,
                    message=f"Company claims CDP participation but not found in CDP database",
                    recommendation="Verify CDP submission status directly with CDP"
                ))
        else:
            # 找到记录，验证细节匹配
            for _, record in matches.iterrows():
                discrepancies = self._compare_disclosure(extract, record)
                findings.extend(discrepancies)

        # 计算分数（基于匹配度）
        critical_findings = len([f for f in findings if f.severity == Severity.CRITICAL])
        score = max(1.0 - (critical_findings * 0.3), 0.0)

        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=score,
            findings=findings,
            metadata={"cdp_records_found": len(matches) if matches is not None else 0}
        )

    def _fuzzy_match(self, company_name: str) -> Optional[pd.DataFrame]:
        """模糊匹配企业名（处理名称不一致问题）"""
        from difflib import get_close_matches
        
        if self._data is None or self._data.empty:
            return None
            
        # 尝试不同的列名来查找公司名称
        possible_columns = ['company_name', 'Company Name', 'Organization', 'Name']
        company_col = None
        for col in possible_columns:
            if col in self._data.columns:
                company_col = col
                break
        
        if company_col is None:
            # 如果找不到标准列名，使用第一个可能包含公司名称的列
            for col in self._data.columns:
                if any(keyword in col.lower() for keyword in ['company', 'org', 'name']):
                    company_col = col
                    break
        
        if company_col is None:
            return None
            
        names = self._data[company_col].dropna().astype(str).tolist()
        matches = get_close_matches(company_name, names, n=3, cutoff=0.7)
        
        if matches:
            mask = self._data[company_col].isin(matches)
            return self._data[mask]
        return None

    def _compare_disclosure(self, extract: DisclosureExtract, cdp_record) -> list[ValidationFinding]:
        """对比披露内容与CDP记录"""
        findings = []

        # 验证披露年份
        if hasattr(cdp_record, 'year') and extract.report_year != cdp_record['year']:
            findings.append(ValidationFinding(
                validator=self.name,
                code="CDP-002",
                severity=Severity.WARNING,
                message=f"Report year mismatch: disclosed {extract.report_year}, "
                        f"CDP records {cdp_record['year']}"
            ))

        # 验证披露得分（如果可用）
        if 'score' in cdp_record or 'grade' in cdp_record:
            score_field = 'score' if 'score' in cdp_record else 'grade'
            cdp_score = cdp_record[score_field]
            
            # 这里可以添加更复杂的评分对比逻辑
            if pd.notna(cdp_score):
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="CDP-003",
                    severity=Severity.INFO,
                    message=f"Company CDP {score_field}: {cdp_score}"
                ))

        # 验证行业分类
        if 'sector' in cdp_record and extract.sector:
            cdp_sector = str(cdp_record['sector']).lower()
            disc_sector = extract.sector.lower()
            if cdp_sector != disc_sector:
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="CDP-004",
                    severity=Severity.INFO,
                    message=f"Sector difference: disclosed {extract.sector}, CDP records {cdp_record['sector']}"
                ))

        return findings

    def get_benchmark(self, sector: str) -> Dict[str, Any]:
        if self._data is None:
            return {}
        
        # 尝试找到行业列
        sector_col = None
        possible_sector_cols = ['sector', 'Sector', 'Industry', 'industry']
        for col in possible_sector_cols:
            if col in self._data.columns:
                sector_col = col
                break
        
        if sector_col is None:
            return {}
            
        sector_data = self._data[
            self._data[sector_col].str.contains(sector, case=False, na=False, regex=False)
        ]
        
        # 获取平均得分等基准信息
        score_col = None
        possible_score_cols = ['score', 'Score', 'grade', 'Grade', 'rating', 'Rating']
        for col in possible_score_cols:
            if col in sector_data.columns:
                score_col = col
                break
                
        benchmark = {
            "total_companies": len(sector_data),
        }
        
        if score_col:
            numeric_scores = pd.to_numeric(sector_data[score_col], errors='coerce')
            avg_score = numeric_scores.mean()
            if not pd.isna(avg_score):
                benchmark["average_score"] = avg_score
                
        return benchmark

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