#!/usr/bin/env python3
"""
自定义数据源示例 - Climate Disclosure Agent (CDA)

本示例演示了如何创建和使用自定义数据适配器：
- 定义CustomClimateDataAdapter
- 集成到分析流程中
- 执行交叉验证
"""

from cda import ClimateDisclosureAgent
from cda.adapters import BaseAdapter
from cda.adapters.base import DataNotAvailableError
from cda.validation import ValidationResult, ValidationFinding, Severity
from cda.extraction.schema import DisclosureExtract

import pandas as pd
from typing import Dict, Any

class CustomClimateDataAdapter(BaseAdapter):
    """
    自定义气候数据适配器示例
    
    该适配器演示如何集成自定义外部数据源进行交叉验证。
    它可以验证公司披露的排放数据与外部数据库的一致性。
    """
    
    name = "custom_climate_data"
    data_source_url = "https://your-climate-data-source.com"  # 替换为实际数据源URL
    requires_auth = False  # 根据实际情况设置是否需要认证

    def __init__(self, data_source=None, column_mapping: Dict[str, str] = None):
        """
        初始化自定义数据适配器
        
        Args:
            data_source: 数据源，支持以下格式：
                - str: CSV/Excel文件路径
                - pd.DataFrame: 已加载的数据框
                - None: 无数据模式
            column_mapping: 列名映射，指定如何将外部数据映射到内部字段
        """
        self._data = self._load_data(data_source)
        self._column_mapping = column_mapping or {
            "company": "company_name",
            "emissions_scope1": "scope1_emissions_tco2e",
            "emissions_scope2": "scope2_emissions_tco2e",
            "emissions_scope3": "scope3_emissions_tco2e",
            "target_year": "net_zero_target_year",
            "verification": "third_party_verification"
        }

    def cross_validate(self, extract: DisclosureExtract) -> ValidationResult:
        """
        使用外部数据交叉验证提取结果
        
        Args:
            extract: 从报告中提取的结构化数据
            
        Returns:
            ValidationResult: 交叉验证结果
        """
        if self._data is None:
            raise DataNotAvailableError(
                f"自定义气候数据未提供。请从 {self.data_source_url} 获取数据。"
            )

        findings = []
        company_name = extract.company_name
        
        # 通过公司名查找匹配记录
        match = self._find_company_match(company_name)
        
        if match is None:
            # 公司在外部数据中找不到
            findings.append(ValidationFinding(
                validator=self.name,
                code="CUSTOM-001",
                severity=Severity.INFO,
                message=f"公司在外部数据源中未找到: {company_name}",
                recommendation="确认公司是否应出现在此数据源中"
            ))
        else:
            # 找到匹配，验证数据一致性
            inconsistencies = self._validate_consistency(extract, match)
            findings.extend(inconsistencies)

        # 计算分数（基于发现的问题严重性）
        critical_issues = len([f for f in findings if f.severity == Severity.CRITICAL])
        warning_issues = len([f for f in findings if f.severity == Severity.WARNING])
        
        # 基础分数减去问题惩罚
        score = 1.0 - (critical_issues * 0.3 + warning_issues * 0.1)
        score = max(0.0, min(1.0, score))  # 限制在0-1之间

        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=score,
            findings=findings,
            metadata={
                "record_found": match is not None,
                "data_source_size": len(self._data) if self._data is not None else 0
            }
        )

    def get_benchmark(self, sector: str = None) -> Dict[str, Any]:
        """
        获取行业基准数据
        
        Args:
            sector: 行业名称
            
        Returns:
            Dict: 基准数据
        """
        if self._data is None:
            return {}
        
        # 如果提供了行业，则筛选该行业的数据
        if sector and 'sector' in self._data.columns:
            sector_data = self._data[
                self._data['sector'].str.contains(sector, case=False, na=False, regex=False)
            ]
        else:
            sector_data = self._data
            
        return {
            "total_companies": len(sector_data),
            "coverage_rate": len(sector_data.dropna()) / len(sector_data) if len(self._data) > 0 else 0,
            "data_source": self.name,
            "last_updated": getattr(self, '_last_updated', 'unknown')
        }

    def status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "name": self.name,
            "data_loaded": self._has_data(),
            "data_source_url": self.data_source_url,
            "requires_auth": self.requires_auth,
            "data_size": len(self._data) if self._data is not None else 0
        }

    def _load_data(self, source):
        """加载数据源"""
        if source is None:
            return None
        if isinstance(source, pd.DataFrame):
            return source
        if isinstance(source, str):
            if source.endswith('.csv'):
                return pd.read_csv(source)
            elif source.endswith(('.xlsx', '.xls')):
                return pd.read_excel(source)
        raise ValueError(f"不支持的数据源格式: {type(source)}")

    def _has_data(self) -> bool:
        """检查是否有可用数据"""
        return self._data is not None and not self._data.empty

    def _find_company_match(self, company_name: str):
        """
        在外部数据中查找公司匹配
        
        Args:
            company_name: 公司名称
            
        Returns:
            匹配的记录或None
        """
        if self._data is None:
            return None
            
        company_col = self._column_mapping.get("company", "company")
        
        # 尝试精确匹配
        matches = self._data[
            self._data[company_col].str.contains(company_name, case=False, na=False, regex=False)
        ]
        
        if len(matches) > 0:
            return matches.iloc[0]  # 返回第一个匹配项
        
        # 如果没有精确匹配，可以尝试更宽松的匹配逻辑
        # （这里可以根据需要添加更复杂的匹配算法）
        return None

    def _validate_consistency(self, extract: DisclosureExtract, external_record) -> list:
        """
        验证提取数据与外部记录的一致性
        
        Args:
            extract: 提取的披露数据
            external_record: 外部数据记录
            
        Returns:
            list: 发现的不一致性列表
        """
        findings = []
        
        # 验证排放数据一致性
        for emission in extract.emissions:
            scope_col = self._column_mapping.get(f"emissions_{emission.scope.value}", f"emissions_{emission.scope.value}")
            
            if scope_col in external_record and emission.value is not None:
                external_value = external_record[scope_col]
                
                if pd.notna(external_value):
                    # 检查数值差异（允许5%的误差）
                    difference = abs(emission.value - external_value) / max(external_value, 1)
                    
                    if difference > 0.05:  # 5%阈值
                        findings.append(ValidationFinding(
                            validator=self.name,
                            code=f"CUSTOM-EMISSION-{emission.scope.value.upper()}-MISMATCH",
                            severity=Severity.WARNING,
                            message=f"{emission.scope.value} 排放数据不一致: "
                                    f"披露 {emission.value}, 外部记录 {external_value}",
                            field=f"emissions.{emission.scope.value}",
                            evidence=f"差异率: {difference:.2%}"
                        ))
        
        # 验证目标年份一致性
        target_year_col = self._column_mapping.get("target_year", "net_zero_target_year")
        if target_year_col in external_record:
            external_target_year = external_record[target_year_col]
            
            for target in extract.targets:
                if target.target_year and pd.notna(external_target_year):
                    if target.target_year != external_target_year:
                        findings.append(ValidationFinding(
                            validator=self.name,
                            code="CUSTOM-TARGET-YEAR-MISMATCH",
                            severity=Severity.WARNING,
                            message=f"净零目标年份不一致: "
                                    f"披露 {target.target_year}, 外部记录 {external_target_year}",
                            field="targets.net_zero_year"
                        ))
        
        # 验证第三方验证状态
        verification_col = self._column_mapping.get("verification", "third_party_verification")
        if verification_col in external_record:
            external_verified = external_record[verification_col]
            
            # 检查披露中是否有相应的验证声明
            has_verification_claim = any(
                e.assurance_level for e in extract.emissions
            ) or any(
                "verified" in t.description.lower() or "assured" in t.description.lower()
                for t in extract.targets
            )
            
            if pd.notna(external_verified) and external_verified and not has_verification_claim:
                findings.append(ValidationFinding(
                    validator=self.name,
                    code="CUSTOM-VERIFICATION-MISMATCH",
                    severity=Severity.INFO,
                    message=f"外部数据显示已验证，但披露中未明确提及验证",
                    field="verification.claims"
                ))
        
        return findings


def main():
    print("=== Climate Disclosure Agent - 自定义数据源示例 ===\n")
    
    # 创建自定义数据适配器实例
    # 注意：在实际使用中，您需要提供真实的CSV或DataFrame数据
    try:
        custom_adapter = CustomClimateDataAdapter(
            data_source="climate_data.csv",  # 替换为实际数据路径
            column_mapping={
                "company": "Company_Name",
                "emissions_scope1": "Scope1_Emissions",
                "emissions_scope2": "Scope2_Emissions", 
                "emissions_scope3": "Scope3_Emissions",
                "target_year": "NetZero_Target_Year",
                "verification": "Third_Party_Verified"
            }
        )
        
        print("自定义数据适配器初始化成功")
        print(f"适配器状态: {custom_adapter.status()}")
        
        # 创建分析代理并集成自定义适配器
        agent = ClimateDisclosureAgent(
            adapters=[custom_adapter]
        )
        
        print(f"已配置适配器: {[adapter.name for adapter in agent.adapters]}")
        
        # 分析气候披露报告
        result = agent.analyze(
            source="sample_report.pdf",  # 替换为实际报告路径
            company_name="Sample Company",
            sector="technology",
            validate_external=True
        )
        
        print(f"\n分析完成 - 公司: {result.company_name}")
        print(f"综合评分: {result.overall_score}/100 (等级: {result.grade})")
        
        # 查看自定义适配器的交叉验证结果
        custom_results = [
            vr for vr in result.validation_results 
            if vr.validator_name == f"adapter:{custom_adapter.name}"
        ]
        
        if custom_results:
            print(f"\n自定义适配器交叉验证结果:")
            cr = custom_results[0]
            print(f"  评分: {cr.score if cr.score is not None else 'N/A'}")
            print(f"  元数据: {cr.metadata}")
            
            if cr.findings:
                print("  发现:")
                for finding in cr.findings:
                    print(f"    - [{finding.severity}] {finding.message}")
                    if hasattr(finding, 'field') and finding.field:
                        print(f"        字段: {finding.field}")
                    if finding.recommendation:
                        print(f"        建议: {finding.recommendation}")
            else:
                print("  - 未发现交叉验证问题")
        else:
            print("\n未找到自定义适配器的交叉验证结果")
        
        # 显示总体统计
        total_findings = len([f for vr in result.validation_results for f in vr.findings])
        print(f"\n总体发现数量: {total_findings}")
        
        # 显示各维度得分
        print("\n各维度得分:")
        for dimension, score in result.dimension_scores.items():
            print(f"  - {dimension}: {score}/100")
            
        print(f"\n分析摘要: {result.summary}")
        
    except FileNotFoundError:
        print("错误: 未找到示例数据文件或报告。请确保提供了有效的数据文件和气候披露报告路径。")
        print("注意: 此示例需要真实的CSV数据文件和PDF报告来运行。")
    except DataNotAvailableError as e:
        print(f"数据不可用错误: {str(e)}")
        print("请确保提供了有效的外部数据源。")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        print("请确保已正确安装所有依赖项，并配置了适当的LLM提供商。")


if __name__ == "__main__":
    main()