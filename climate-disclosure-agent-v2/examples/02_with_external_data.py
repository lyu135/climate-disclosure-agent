#!/usr/bin/env python3
"""
接入外部验证示例 - Climate Disclosure Agent (CDA)

本示例演示了如何使用外部数据源进行交叉验证：
- 配置SBTi和CDP适配器
- 启用外部数据验证
- 查看交叉验证结果
"""

from cda import ClimateDisclosureAgent
from cda.adapters import SBTiAdapter, CDPAdapter

def main():
    print("=== Climate Disclosure Agent - 接入外部验证示例 ===\n")
    
    # 创建带有外部数据适配器的分析代理
    # 注意：在实际使用中，您需要提供真实的CSV数据文件路径
    try:
        agent = ClimateDisclosureAgent(
            adapters=[
                SBTiAdapter("sbti_companies.csv"),  # 替换为实际SBTi数据路径
                CDPAdapter("cdp_scores.csv"),      # 替换为实际CDP数据路径
            ]
        )
        
        # 分析气候披露报告，启用外部验证
        result = agent.analyze(
            source="sample_report.pdf",           # 替换为实际报告路径
            company_name="Sample Company",
            sector="technology",
            validate_external=True
        )
        
        print(f"公司: {result.company_name}")
        print(f"综合评分: {result.overall_score}/100 (等级: {result.grade})")
        
        # 查看交叉验证结果
        print("\n交叉验证结果:")
        adapter_results = [vr for vr in result.validation_results if vr.validator_name.startswith("adapter:")]
        
        if adapter_results:
            for vr in adapter_results:
                print(f"\n[{vr.validator_name}] 评分: {vr.score if vr.score is not None else 'N/A'}")
                
                if vr.findings:
                    print("  发现:")
                    for finding in vr.findings:
                        print(f"    - [{finding.severity}] {finding.message}")
                        if finding.recommendation:
                            print(f"        建议: {finding.recommendation}")
                else:
                    print("  - 未发现问题")
        else:
            print("  - 未执行任何外部验证（可能缺少数据源）")
        
        # 显示整体分析结果
        print(f"\n总体发现数量: {len([f for vr in result.validation_results for f in vr.findings])}")
        
        # 显示各维度得分
        print("\n各维度得分:")
        for dimension, score in result.dimension_scores.items():
            print(f"  - {dimension}: {score}/100")
            
        print(f"\n分析摘要: {result.summary}")
        
    except FileNotFoundError as e:
        print(f"错误: 找不到所需的数据文件 - {str(e)}")
        print("请确保提供了有效的SBTi/CDP数据文件路径和气候披露报告路径。")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        print("请确保已正确安装所有依赖项，并配置了适当的LLM提供商。")

if __name__ == "__main__":
    main()