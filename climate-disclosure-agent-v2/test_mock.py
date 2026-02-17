#!/usr/bin/env python3
"""
Climate Disclosure Agent - Mock 数据测试

不需要真实 API Key，用假数据展示完整功能
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/climate-disclosure-agent')

from cda.extraction.schema import (
    DisclosureExtract, EmissionData, EmissionScope, 
    TargetData, RiskItem, GovernanceData
)
from cda.validation.consistency import ConsistencyValidator
from cda.validation.quantification import QuantificationValidator
from cda.validation.completeness import CompletenessValidator
from cda.validation.risk_coverage import RiskCoverageValidator
from cda.validation.pipeline import ValidationPipeline
from cda.scoring.scorer import Scorer
from cda.output.visualizer import DisclosureVisualizer

def create_mock_apple_data():
    """创建 Apple 的 Mock 数据"""
    return DisclosureExtract(
        company_name="Apple Inc.",
        report_year=2023,
        report_type="sustainability",
        framework=["TCFD", "GRI"],
        sector="technology",
        
        # 排放数据
        emissions=[
            EmissionData(
                scope=EmissionScope.SCOPE_1,
                value=48100.0,
                unit="tCO2e",
                year=2023,
                baseline_year=2015,
                methodology="GHG Protocol",
                assurance_level="Limited"
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_2,
                value=0.0,  # Apple 声称 100% 可再生能源
                unit="tCO2e",
                year=2023,
                baseline_year=2015,
                intensity_value=0.0,
                intensity_unit="tCO2e/revenue_million"
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_3,
                value=14100000.0,
                unit="tCO2e",
                year=2023,
                baseline_year=2015,
                methodology="GHG Protocol"
            ),
        ],
        
        # 减排目标
        targets=[
            TargetData(
                description="Carbon neutral across entire business by 2030",
                target_year=2030,
                base_year=2015,
                reduction_pct=75.0,
                scopes_covered=[EmissionScope.SCOPE_1, EmissionScope.SCOPE_2, EmissionScope.SCOPE_3],
                is_science_based=True,
                sbti_status="approved",
                interim_targets=[
                    {"year": 2025, "reduction": 40},
                    {"year": 2027, "reduction": 60}
                ]
            ),
        ],
        
        # 气候风险
        risks=[
            RiskItem(
                risk_type="physical",
                category="acute_physical",
                description="Extreme weather events disrupting supply chain",
                time_horizon="short",
                financial_impact="Potential supply disruption",
                financial_impact_value=50000000.0,
                mitigation_strategy="Diversify supplier base",
                likelihood="medium"
            ),
            RiskItem(
                risk_type="transition",
                category="policy_legal",
                description="Carbon pricing regulations",
                time_horizon="medium",
                financial_impact="Increased operational costs",
                financial_impact_value=100000000.0,
                mitigation_strategy="Invest in renewable energy",
                likelihood="high"
            ),
            RiskItem(
                risk_type="transition",
                category="market",
                description="Shift in consumer preferences toward sustainable products",
                time_horizon="medium",
                financial_impact="Market share impact",
                mitigation_strategy="Accelerate product sustainability initiatives"
            ),
        ],
        
        # 治理结构
        governance=GovernanceData(
            board_oversight=True,
            board_climate_committee=True,
            executive_incentive_linked=True,
            reporting_frequency="annual"
        ),
        
        extraction_confidence=0.95,
        extraction_method="mock"
    )

def create_mock_microsoft_data():
    """创建 Microsoft 的 Mock 数据"""
    return DisclosureExtract(
        company_name="Microsoft",
        report_year=2023,
        report_type="sustainability",
        framework=["TCFD", "SASB"],
        sector="technology",
        
        emissions=[
            EmissionData(
                scope=EmissionScope.SCOPE_1,
                value=120000.0,
                year=2023,
                baseline_year=2020
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_2,
                value=0.0,
                year=2023,
                baseline_year=2020
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_3,
                value=13000000.0,
                year=2023,
                baseline_year=2020
            ),
        ],
        
        targets=[
            TargetData(
                description="Carbon negative by 2030",
                target_year=2030,
                base_year=2020,
                reduction_pct=100.0,
                scopes_covered=[EmissionScope.SCOPE_1, EmissionScope.SCOPE_2, EmissionScope.SCOPE_3],
                is_science_based=True,
                sbti_status="committed"
            ),
        ],
        
        risks=[
            RiskItem(
                risk_type="physical",
                category="chronic",
                description="Rising temperatures affecting data center cooling",
                time_horizon="long",
                financial_impact_value=200000000.0
            ),
            RiskItem(
                risk_type="transition",
                category="technology",
                description="Transition to low-carbon cloud infrastructure",
                time_horizon="short",
                financial_impact_value=500000000.0
            ),
        ],
        
        governance=GovernanceData(
            board_oversight=True,
            board_climate_committee=True,
            executive_incentive_linked=True,
            reporting_frequency="annual"
        ),
        
        extraction_confidence=0.90,
        extraction_method="mock"
    )

def test_mock_analysis():
    """使用 Mock 数据测试完整流程"""
    print("=" * 60)
    print("Climate Disclosure Agent - Mock 数据测试")
    print("=" * 60)
    
    # 创建 Mock 数据
    print("\n📦 创建 Mock 数据...")
    apple_data = create_mock_apple_data()
    microsoft_data = create_mock_microsoft_data()
    print(f"✅ Apple 数据: {len(apple_data.emissions)} 排放项, {len(apple_data.targets)} 目标, {len(apple_data.risks)} 风险")
    print(f"✅ Microsoft 数据: {len(microsoft_data.emissions)} 排放项, {len(microsoft_data.targets)} 目标, {len(microsoft_data.risks)} 风险")
    
    # 创建验证器
    print("\n🔍 创建验证器...")
    validators = [
        ConsistencyValidator(),
        QuantificationValidator(),
        CompletenessValidator(),
        RiskCoverageValidator(),
    ]
    print(f"✅ 加载了 {len(validators)} 个验证器")
    
    # 创建 Pipeline
    print("\n⚙️  创建验证 Pipeline...")
    pipeline = ValidationPipeline(validators=validators)
    print("✅ Pipeline 就绪")
    
    # 分析 Apple
    print("\n" + "=" * 60)
    print("📊 分析 Apple Inc.")
    print("=" * 60)
    
    apple_results = pipeline.run(apple_data, cross_validate=False)
    scorer = Scorer()
    apple_final = scorer.aggregate(apple_data, apple_results)
    
    print(f"\n公司: {apple_final.company_name}")
    print(f"综合评分: {apple_final.overall_score}/100")
    print(f"等级: {apple_final.grade}")
    print(f"\n各维度得分:")
    for dim, score in apple_final.dimension_scores.items():
        print(f"  - {dim}: {score}/100")
    
    all_findings = [f for vr in apple_final.validation_results for f in vr.findings]
    print(f"\n发现的问题: {len(all_findings)} 个")
    if all_findings:
        print("前 3 个:")
        for i, f in enumerate(all_findings[:3], 1):
            print(f"  {i}. [{f.severity.value.upper()}] {f.message}")
    
    print(f"\n摘要: {apple_final.summary}")
    
    # 分析 Microsoft
    print("\n" + "=" * 60)
    print("📊 分析 Microsoft")
    print("=" * 60)
    
    microsoft_results = pipeline.run(microsoft_data, cross_validate=False)
    microsoft_final = scorer.aggregate(microsoft_data, microsoft_results)
    
    print(f"\n公司: {microsoft_final.company_name}")
    print(f"综合评分: {microsoft_final.overall_score}/100")
    print(f"等级: {microsoft_final.grade}")
    print(f"\n各维度得分:")
    for dim, score in microsoft_final.dimension_scores.items():
        print(f"  - {dim}: {score}/100")
    
    # 生成对比可视化
    print("\n" + "=" * 60)
    print("📊 生成对比可视化")
    print("=" * 60)
    
    try:
        viz = DisclosureVisualizer()
        
        # 对比雷达图
        fig = viz.comparison_radar([apple_final, microsoft_final])
        fig.write_html("mock_comparison_radar.html")
        print("✅ 对比雷达图: mock_comparison_radar.html")
        
        # 完整性热力图
        fig2 = viz.completeness_heatmap([apple_final, microsoft_final])
        fig2.write_html("mock_completeness_heatmap.html")
        print("✅ 完整性热力图: mock_completeness_heatmap.html")
        
        # Apple 单独雷达图
        fig3 = viz.radar_chart(apple_final)
        fig3.write_html("mock_apple_radar.html")
        print("✅ Apple 雷达图: mock_apple_radar.html")
        
        # 发现统计
        fig4 = viz.findings_summary(apple_final)
        fig4.write_html("mock_apple_findings.html")
        print("✅ Apple 发现统计: mock_apple_findings.html")
        
    except Exception as e:
        print(f"❌ 可视化失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎉 Mock 测试完成！")
    print("=" * 60)
    print("\n生成的文件:")
    print("  - mock_comparison_radar.html (对比雷达图)")
    print("  - mock_completeness_heatmap.html (完整性热力图)")
    print("  - mock_apple_radar.html (Apple 单独雷达图)")
    print("  - mock_apple_findings.html (发现统计)")
    print("\n用浏览器打开这些 HTML 文件查看可视化效果！")

if __name__ == "__main__":
    test_mock_analysis()
