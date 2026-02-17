#!/usr/bin/env python3
"""
Climate Disclosure Agent - 端到端测试脚本

测试内容：
1. 分析 Apple 2023 环境报告
2. 生成评分和发现
3. 输出可视化图表

需要：
- OPENAI_API_KEY 环境变量
- test_data/apple_env_2023.pdf
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/climate-disclosure-agent')

def test_basic_analysis():
    """测试基础分析功能"""
    print("=" * 60)
    print("Climate Disclosure Agent - 端到端测试")
    print("=" * 60)
    
    # 检查 API Key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ 错误: 未设置 OPENAI_API_KEY 环境变量")
        print("\n设置方法:")
        print('export OPENAI_API_KEY="sk-sp-8bf3202950a548db91c3e2606499e729"')
        print('export OPENAI_BASE_URL="https://coding.dashscope.aliyuncs.com/v1"')
        return False
    
    print(f"✅ API Key 已设置: {api_key[:20]}...")
    
    # 检查测试文件
    test_file = "test_data/apple_env_2023.pdf"
    if not os.path.exists(test_file):
        print(f"❌ 错误: 测试文件不存在: {test_file}")
        return False
    
    print(f"✅ 测试文件存在: {test_file} ({os.path.getsize(test_file)/1024/1024:.1f}MB)")
    
    # 导入模块
    print("\n📦 导入模块...")
    try:
        from cda.agent import ClimateDisclosureAgent
        from cda.output.visualizer import DisclosureVisualizer
        print("✅ 模块导入成功")
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    
    # 创建 Agent
    print("\n🤖 创建 ClimateDisclosureAgent...")
    try:
        agent = ClimateDisclosureAgent()
        print(f"✅ Agent 创建成功")
        print(f"   - 验证器数量: {len(agent.validators)}")
        print(f"   - 适配器数量: {len(agent.adapters)}")
    except Exception as e:
        print(f"❌ Agent 创建失败: {e}")
        return False
    
    # 分析报告
    print("\n📊 分析 Apple 2023 环境报告...")
    print("   (这可能需要 1-2 分钟，LLM 正在提取数据...)")
    try:
        result = agent.analyze(
            source=test_file,
            company_name="Apple Inc.",
            sector="technology",
            validate_external=False  # 暂不使用外部验证
        )
        print("✅ 分析完成！")
        print(f"   返回类型: {type(result)}")
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 输出结果（处理 dict 或对象）
    print("\n" + "=" * 60)
    print("📈 分析结果")
    print("=" * 60)
    
    # 兼容 dict 和对象
    if isinstance(result, dict):
        company_name = result.get('company_name', 'Unknown')
        overall_score = result.get('overall_score', 0)
        grade = result.get('grade', 'N/A')
        dimension_scores = result.get('dimension_scores', {})
        validation_results = result.get('validation_results', [])
        summary = result.get('summary', 'No summary available')
    else:
        company_name = result.company_name
        overall_score = result.overall_score
        grade = result.grade
        dimension_scores = result.dimension_scores
        validation_results = result.validation_results
        summary = result.summary
    
    print(f"公司: {company_name}")
    print(f"综合评分: {overall_score}/100")
    print(f"等级: {grade}")
    print(f"\n各维度得分:")
    for dimension, score in dimension_scores.items():
        print(f"  - {dimension}: {score}/100")
    
    # 统计发现
    all_findings = []
    for vr in validation_results:
        if isinstance(vr, dict):
            all_findings.extend(vr.get('findings', []))
        else:
            all_findings.extend(vr.findings)
    
    critical = len([f for f in all_findings if (f.get('severity') if isinstance(f, dict) else f.severity.value) == "critical"])
    warning = len([f for f in all_findings if (f.get('severity') if isinstance(f, dict) else f.severity.value) == "warning"])
    info = len([f for f in all_findings if (f.get('severity') if isinstance(f, dict) else f.severity.value) == "info"])
    
    print(f"\n发现的问题:")
    print(f"  - 严重: {critical}")
    print(f"  - 警告: {warning}")
    print(f"  - 信息: {info}")
    
    # 显示部分发现
    if all_findings:
        print(f"\n前 5 个发现:")
        for i, finding in enumerate(all_findings[:5], 1):
            if isinstance(finding, dict):
                severity = finding.get('severity', 'unknown')
                message = finding.get('message', 'No message')
            else:
                severity = finding.severity.value
                message = finding.message
            print(f"  {i}. [{severity.upper()}] {message}")
    
    print(f"\n摘要: {summary}")
    
    # 生成可视化（如果结果是对象）
    if not isinstance(result, dict):
        print("\n📊 生成可视化图表...")
        try:
            viz = DisclosureVisualizer()
            
            # 雷达图
            fig = viz.radar_chart(result)
            fig.write_html("test_output_radar.html")
            print("✅ 雷达图已保存: test_output_radar.html")
            
            # 发现统计图
            fig2 = viz.findings_summary(result)
            fig2.write_html("test_output_findings.html")
            print("✅ 发现统计图已保存: test_output_findings.html")
            
        except Exception as e:
            print(f"⚠️  可视化生成失败: {e}")
    else:
        print("\n⚠️  结果为 dict 类型，跳过可视化生成")
    
    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_basic_analysis()
    sys.exit(0 if success else 1)
