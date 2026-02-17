#!/usr/bin/env python3
"""
最简用法示例 - Climate Disclosure Agent (CDA)

本示例演示了CDA框架的基本使用方法：
- 初始化ClimateDisclosureAgent
- 分析单个气候披露报告
- 输出分析结果（评分和问题数量）
"""

from cda import ClimateDisclosureAgent

def main():
    print("=== Climate Disclosure Agent - 最简用法示例 ===\n")
    
    # 创建分析代理实例（使用默认配置）
    agent = ClimateDisclosureAgent()
    
    # 分析气候披露报告
    # 注意：在实际使用中，您需要替换为真实的PDF路径
    try:
        # 这里使用一个虚拟的PDF路径作为示例
        # 在实际部署时，请替换为真实的气候披露报告PDF路径
        result = agent.analyze(
            source="sample_report.pdf",  # 替换为实际报告路径
            company_name="Sample Company",
            sector="technology"
        )
        
        print(f"公司: {result.company_name}")
        print(f"报告年份: {getattr(result, 'report_year', 'N/A')}")  # 如果结果对象包含年份信息
        print(f"综合评分: {result.overall_score}/100 (等级: {result.grade})")
        print(f"发现的问题数量: {len([f for vr in result.validation_results for f in vr.findings])}")
        
        # 显示各维度得分
        print("\n各维度得分:")
        for dimension, score in result.dimension_scores.items():
            print(f"  - {dimension}: {score}/100")
            
        # 显示摘要信息
        print(f"\n分析摘要: {result.summary}")
        
    except FileNotFoundError:
        print("错误: 未找到示例PDF文件。请确保提供了有效的气候披露报告路径。")
        print("注意: 此示例需要一个真实的PDF文件路径来运行。")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        print("请确保已正确安装所有依赖项，并配置了适当的LLM提供商。")

if __name__ == "__main__":
    main()