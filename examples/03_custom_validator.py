#!/usr/bin/env python3
"""
自定义验证器示例 - Climate Disclosure Agent (CDA)

本示例演示了如何创建和使用自定义验证器：
- 定义GreenwashingDetector验证器
- 注册到分析代理
- 运行分析并查看自定义验证结果
"""

from cda import ClimateDisclosureAgent
from cda.validation import BaseValidator, ValidationResult, ValidationFinding, Severity

class GreenwashingDetector(BaseValidator):
    """
    检测潜在洗绿信号的自定义验证器
    
    该验证器检查气候披露报告中模糊表述与量化数据的比例，
    当模糊表述过多而缺乏具体量化数据时发出警告。
    """
    
    name = "greenwashing_detector"
    description = "检测气候披露中的潜在洗绿行为"

    VAGUE_TERMS = [
        "carbon neutral", "green", "eco-friendly", "sustainable",
        "net positive", "climate leader", "environmentally friendly",
        "eco-conscious", "green initiative", "eco-solution"
    ]

    def validate(self, extract):
        """
        执行验证
        
        Args:
            extract: 从报告中提取的结构化数据
            
        Returns:
            ValidationResult: 包含验证结果的对象
        """
        findings = []

        # 检查模糊表述与量化数据的比例
        vague_count = 0
        for ref in extract.source_references.values():
            for term in self.VAGUE_TERMS:
                if term.lower() in ref.lower():
                    vague_count += 1

        # 计算量化数据的数量（以有数值的排放数据为例）
        quantified_count = len([
            e for e in extract.emissions 
            if e.value is not None or e.intensity_value is not None
        ])
        
        # 还可以考虑目标和风险的量化情况
        quantified_targets = len([
            t for t in extract.targets 
            if t.reduction_pct is not None or t.target_year is not None
        ])
        quantified_risks = len([
            r for r in extract.risks 
            if r.financial_impact_value is not None
        ])
        
        quantified_count += quantified_targets + quantified_risks

        if vague_count > quantified_count * 2:
            findings.append(self._finding(
                code="GREENWASH-001",
                severity=Severity.WARNING,
                message=f"模糊声明比例过高 ({vague_count}个模糊词) "
                        f"vs 量化数据 ({quantified_count}个量化项)"
            ))

        # 计算分数（量化数据越多，分数越高；模糊表述越多，分数越低）
        if quantified_count > 0:
            score = min(1.0, quantified_count / (vague_count + quantified_count) * 1.5)
            score = max(0.0, min(1.0, score))  # 限制在0-1之间
        else:
            score = 0.0 if vague_count > 0 else 0.5  # 没有量化数据但也没有模糊词则中等分

        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "vague_terms_count": vague_count,
                "quantified_items_count": quantified_count
            }
        )

def main():
    print("=== Climate Disclosure Agent - 自定义验证器示例 ===\n")
    
    # 创建分析代理实例
    agent = ClimateDisclosureAgent()
    
    # 添加自定义验证器到代理
    agent.validators.append(GreenwashingDetector())
    
    print(f"已注册验证器: {[v.name for v in agent.validators]}")
    print(f"包含自定义验证器: {'greenwashing_detector' in [v.name for v in agent.validators]}\n")
    
    # 分析气候披露报告
    try:
        result = agent.analyze(
            source="sample_report.pdf",  # 替换为实际报告路径
            company_name="Sample Company",
            sector="technology"
        )
        
        print(f"公司: {result.company_name}")
        print(f"综合评分: {result.overall_score}/100 (等级: {result.grade})")
        
        # 查找自定义验证器的结果
        greenwash_results = [
            vr for vr in result.validation_results 
            if vr.validator_name == "greenwashing_detector"
        ]
        
        if greenwash_results:
            print("\n自定义验证器结果 (洗绿检测):")
            gr = greenwash_results[0]
            print(f"  评分: {gr.score if gr.score is not None else 'N/A'}")
            print(f"  元数据: {gr.metadata}")
            
            if gr.findings:
                print("  发现:")
                for finding in gr.findings:
                    print(f"    - [{finding.severity}] {finding.message}")
                    if finding.recommendation:
                        print(f"        建议: {finding.recommendation}")
            else:
                print("  - 未发现洗绿风险")
        else:
            print("未找到自定义验证器结果")
        
        # 显示总体统计
        total_findings = len([f for vr in result.validation_results for f in vr.findings])
        print(f"\n总体发现数量: {total_findings}")
        
        # 显示各维度得分
        print("\n各维度得分:")
        for dimension, score in result.dimension_scores.items():
            print(f"  - {dimension}: {score}/100")
            
        print(f"\n分析摘要: {result.summary}")
        
    except FileNotFoundError:
        print("错误: 未找到示例PDF文件。请确保提供了有效的气候披露报告路径。")
        print("注意: 此示例需要一个真实的PDF文件路径来运行。")
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        print("请确保已正确安装所有依赖项，并配置了适当的LLM提供商。")

if __name__ == "__main__":
    main()