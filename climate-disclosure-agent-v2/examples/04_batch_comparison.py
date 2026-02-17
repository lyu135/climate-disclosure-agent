#!/usr/bin/env python3
"""
多公司对比示例 - Climate Disclosure Agent (CDA)

本示例演示了如何批量分析多家公司的气候披露报告并进行对比：
- 批量分析多个报告
- 生成对比可视化图表
- 输出对比结果
"""

from cda import ClimateDisclosureAgent
from cda.output import DisclosureVisualizer

def main():
    print("=== Climate Disclosure Agent - 多公司对比示例 ===\n")
    
    # 创建分析代理实例
    agent = ClimateDisclosureAgent()
    
    # 定义要分析的公司及其报告路径
    # 注意：在实际使用中，您需要替换为真实的PDF路径
    companies = {
        "Cargill": "reports/cargill_2024.pdf",      # 替换为实际路径
        "ADM": "reports/adm_2024.pdf",              # 替换为实际路径
        "Bunge": "reports/bunge_2024.pdf",          # 替换为实际路径
        "Deere": "reports/deere_2024.pdf",          # 替换为实际路径
    }
    
    print("开始批量分析...")
    
    # 批量分析各公司报告
    results = []
    failed_analyses = []
    
    for company_name, report_path in companies.items():
        try:
            print(f"  分析 {company_name} 的报告...")
            result = agent.analyze(
                source=report_path,
                company_name=company_name,
                sector="food_agriculture"  # 假设这些公司都在食品农业领域
            )
            results.append(result)
            print(f"    ✓ 完成 - 评分: {result.overall_score}/100")
        except FileNotFoundError:
            print(f"    ✗ 失败 - 文件不存在: {report_path}")
            failed_analyses.append((company_name, report_path))
        except Exception as e:
            print(f"    ✗ 失败 - 错误: {str(e)}")
            failed_analyses.append((company_name, str(e)))
    
    print(f"\n分析完成！成功: {len(results)}, 失败: {len(failed_analyses)}")
    
    if not results:
        print("没有成功分析任何公司报告。请检查文件路径。")
        return
    
    # 显示各公司结果摘要
    print("\n各公司分析结果:")
    print("-" * 60)
    for result in results:
        print(f"{result.company_name:15} | 评分: {result.overall_score:5.1f} | 等级: {result.grade:2} | "
              f"发现: {len([f for vr in result.validation_results for f in vr.findings]):2}")
    
    # 生成对比可视化（如果输出模块可用）
    try:
        print("\n生成可视化图表...")
        viz = DisclosureVisualizer()
        
        # 生成对比雷达图
        try:
            radar_fig = viz.comparison_radar(results)
            print("  ✓ 对比雷达图生成成功")
            # 注意：在实际环境中，您可能需要保存图表或显示它
            # radar_fig.show()  # 取消注释以在支持的环境中显示图表
        except Exception as e:
            print(f"  ✗ 雷达图生成失败: {str(e)}")
        
        # 生成完整性热力图
        try:
            heatmap_fig = viz.completeness_heatmap(results)
            print("  ✓ 完整性热力图生成成功")
            # heatmap_fig.show()  # 取消注释以在支持的环境中显示图表
        except Exception as e:
            print(f"  ✗ 热力图生成失败: {str(e)}")
            
    except ImportError:
        print("  - 可视化模块不可用，跳过图表生成")
    except Exception as e:
        print(f"  - 可视化过程中出现错误: {str(e)}")
    
    # 输出详细对比分析
    print("\n详细对比分析:")
    print("-" * 60)
    
    # 按维度比较
    dimensions = set()
    for result in results:
        dimensions.update(result.dimension_scores.keys())
    
    print(f"{'维度':<20}", end="")
    for result in results:
        print(f"{result.company_name:<15}", end="")
    print()
    
    for dim in sorted(dimensions):
        print(f"{dim:<20}", end="")
        for result in results:
            score = result.dimension_scores.get(dim, 0)
            print(f"{score:<15.1f}", end="")
        print()
    
    # 找出最佳和最差表现
    print("\n表现分析:")
    best_company = max(results, key=lambda r: r.overall_score)
    worst_company = min(results, key=lambda r: r.overall_score)
    print(f"  最佳表现: {best_company.company_name} ({best_company.overall_score}/100)")
    print(f"  待改进: {worst_company.company_name} ({worst_company.overall_score}/100)")

if __name__ == "__main__":
    main()