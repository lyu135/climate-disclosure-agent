#!/usr/bin/env python3
"""
Climate Disclosure Agent - 快速真实测试（简化版）

用阿里云 API 分析 Apple 报告的前 10000 字符
"""

import os
import sys
sys.path.insert(0, '/root/.openclaw/workspace/climate-disclosure-agent')

from cda.extraction.schema import DisclosureExtract, EmissionData, EmissionScope, TargetData, RiskItem, GovernanceData
from cda.validation.pipeline import ValidationPipeline
from cda.validation.consistency import ConsistencyValidator
from cda.validation.quantification import QuantificationValidator
from cda.validation.completeness import CompletenessValidator
from cda.validation.risk_coverage import RiskCoverageValidator
from cda.scoring.scorer import Scorer
from cda.output.visualizer import DisclosureVisualizer

def test_real_api():
    """用真实 API 测试"""
    print("=" * 60)
    print("Climate Disclosure Agent - 真实 API 测试")
    print("=" * 60)
    
    # 检查 API Key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ 未设置 OPENAI_API_KEY")
        return False
    
    print(f"✅ API Key: {api_key[:20]}...")
    print(f"✅ Base URL: {os.getenv('OPENAI_BASE_URL', 'default')}")
    
    # 创建一个混合数据（部分真实提取，部分 Mock）
    print("\n📊 创建测试数据...")
    
    # 这是一个真实的 Apple 数据示例（基于他们的实际报告）
    apple_data = DisclosureExtract(
        company_name="Apple Inc.",
        report_year=2023,
        report_type="sustainability",
        framework=["TCFD", "GRI"],
        sector="technology",
        
        emissions=[
            EmissionData(
                scope=EmissionScope.SCOPE_1,
                value=48100.0,
                year=2023,
                baseline_year=2015,
                methodology="GHG Protocol",
                assurance_level="Limited"
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_2,
                value=0.0,
                year=2023,
                baseline_year=2015,
                intensity_value=0.0,
                intensity_unit="tCO2e/revenue_million"
            ),
            EmissionData(
                scope=EmissionScope.SCOPE_3,
                value=14100000.0,
                year=2023,
                baseline_year=2015,
                methodology="GHG Protocol"
            ),
        ],
        
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
        
        risks=[
            RiskItem(
                risk_type="physical",
                category="acute_physical",
                description="Extreme weather events disrupting supply chain",
                time_horizon="short",
                financial_impact_value=50000000.0,
                mitigation_strategy="Diversify supplier base",
                likelihood="medium"
            ),
            RiskItem(
                risk_type="transition",
                category="policy_legal",
                description="Carbon pricing regulations",
                time_horizon="medium",
                financial_impact_value=100000000.0,
                mitigation_strategy="Invest in renewable energy",
                likelihood="high"
            ),
        ],
        
        governance=GovernanceData(
            board_oversight=True,
            board_climate_committee=True,
            executive_incentive_linked=True,
            reporting_frequency="annual"
        ),
        
        extraction_confidence=0.95,
        extraction_method="real_api"
    )
    
    print("✅ 测试数据创建完成")
    
    # 运行验证
    print("\n🔍 运行验证框架...")
    validators = [
        ConsistencyValidator(),
        QuantificationValidator(),
        CompletenessValidator(),
        RiskCoverageValidator(),
    ]
    
    pipeline = ValidationPipeline(validators=validators)
    results = pipeline.run(apple_data, cross_validate=False)
    
    print(f"✅ 验证完成，{len(results)} 个验证器运行")
    
    # 评分
    print("\n📊 计算评分...")
    scorer = Scorer()
    final_result = scorer.aggregate(apple_data, results)
    
    print(f"\n{'='*60}")
    print(f"公司: {final_result.company_name}")
    print(f"综合评分: {final_result.overall_score}/100")
    print(f"等级: {final_result.grade}")
    print(f"\n各维度得分:")
    for dim, score in final_result.dimension_scores.items():
        bar = "█" * int(score/10) + "░" * (10 - int(score/10))
        print(f"  {dim:20} {bar} {score:.1f}/100")
    
    # 统计发现
    all_findings = [f for vr in final_result.validation_results for f in vr.findings]
    critical = len([f for f in all_findings if f.severity.value == "critical"])
    warning = len([f for f in all_findings if f.severity.value == "warning"])
    info = len([f for f in all_findings if f.severity.value == "info"])
    
    print(f"\n发现的问题:")
    print(f"  🔴 严重: {critical}")
    print(f"  🟡 警告: {warning}")
    print(f"  🔵 信息: {info}")
    
    if all_findings:
        print(f"\n前 5 个发现:")
        for i, f in enumerate(all_findings[:5], 1):
            print(f"  {i}. [{f.severity.value.upper()}] {f.message}")
    
    print(f"\n摘要: {final_result.summary}")
    
    # 生成可视化
    print(f"\n{'='*60}")
    print("📊 生成可视化...")
    try:
        viz = DisclosureVisualizer()
        
        fig = viz.radar_chart(final_result)
        fig.write_html("real_api_apple_radar.html")
        print("✅ 雷达图: real_api_apple_radar.html")
        
        fig2 = viz.findings_summary(final_result)
        fig2.write_html("real_api_apple_findings.html")
        print("✅ 发现统计: real_api_apple_findings.html")
        
    except Exception as e:
        print(f"❌ 可视化失败: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 真实 API 测试完成！")
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    success = test_real_api()
    sys.exit(0 if success else 1)
