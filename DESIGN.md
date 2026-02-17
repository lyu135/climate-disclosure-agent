# Climate Disclosure Validation Agent — 完整设计方案

> A modular, extensible agent framework for automated climate disclosure analysis with pluggable validation modules and external data adapters.

---

## 1. 项目定位与核心理念

### 1.1 What It Is

**ClimateDisclosureAgent (CDA)** 是一个面向ESG气候披露的轻量级分析Agent框架。它不是一个数据产品，而是一套**方法论的代码化实现**——将"如何评估一份气候报告的质量"这个问题拆解为可编程、可组合、可扩展的模块。

### 1.2 设计哲学

| 原则 | 含义 |
|------|------|
| **Framework over Product** | 提供骨架和接口，不绑定特定数据源或行业 |
| **Convention over Configuration** | 零配置即可运行基础分析，高级功能按需插入 |
| **Composable Validation** | 每个验证器独立运行，也可以组合形成pipeline |
| **Graceful Degradation** | 没有外部数据时做内部一致性分析，有则做交叉验证 |

### 1.3 差异化定位

与市面上的ESG工具相比，CDA不做"大而全"的平台，而是聚焦于：

- **可编程性**：分析逻辑透明可审计，不是黑箱评分
- **学术可引用**：评估框架有明确的方法论依据（TCFD/SASB/GRI）
- **低门槛**：`pip install` 后5行代码即可出结果
- **高天花板**：支持自定义Validator/Adapter无限扩展

---

## 2. 系统架构

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────┐
│                    ClimateDisclosureAgent                 │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │   Ingestion  │───▶│  Extraction  │───▶│  Validation │  │
│  │    Layer     │    │    Engine    │    │   Pipeline  │  │
│  └─────────────┘    └──────────────┘    └──────┬──────┘  │
│        ▲                   ▲                   │         │
│        │                   │                   ▼         │
│  ┌─────┴─────┐    ┌───────┴──────┐    ┌──────────────┐  │
│  │  Input     │    │   LLM        │    │   Scoring    │  │
│  │  Adapters  │    │   Provider   │    │   Engine     │  │
│  │  (PDF/JSON │    │   Interface  │    │              │  │
│  │   /Text)   │    │  (OpenAI/    │    │  ┌────────┐  │  │
│  └───────────┘    │   Claude/    │    │  │Consist.│  │  │
│                    │   Local)     │    │  │Quantif.│  │  │
│                    └──────────────┘    │  │Complet.│  │  │
│                                       │  │Risk    │  │  │
│  ┌────────────────────────────────┐   │  └────────┘  │  │
│  │     External Data Adapters     │───┤              │  │
│  │  (SBTi / CDP / TRACE / Custom) │   └──────────────┘  │
│  └────────────────────────────────┘          │           │
│                                              ▼           │
│                                     ┌──────────────┐     │
│                                     │    Output     │     │
│                                     │  (JSON/DF/   │     │
│                                     │   Viz/Report) │     │
│                                     └──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### 2.2 项目目录结构

```
climate-disclosure-agent/
├── README.md
├── pyproject.toml
├── setup.py
│
├── cda/                              # 核心包
│   ├── __init__.py
│   ├── agent.py                      # Agent主入口
│   ├── config.py                     # 全局配置
│   │
│   ├── ingestion/                    # 输入层
│   │   ├── __init__.py
│   │   ├── base.py                   # InputHandler抽象基类
│   │   ├── pdf_handler.py            # PDF解析
│   │   ├── json_handler.py           # 结构化JSON输入
│   │   └── text_handler.py           # 纯文本输入
│   │
│   ├── extraction/                   # 提取层
│   │   ├── __init__.py
│   │   ├── base.py                   # Extractor抽象基类
│   │   ├── llm_extractor.py          # LLM结构化提取
│   │   ├── rule_extractor.py         # 规则/正则提取
│   │   └── schema.py                 # 提取输出的数据模型 (Pydantic)
│   │
│   ├── validation/                   # 验证层（核心价值）
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseValidator抽象基类
│   │   ├── consistency.py            # 结构一致性验证
│   │   ├── quantification.py         # 量化充分性验证
│   │   ├── completeness.py           # 披露完整性验证
│   │   ├── risk_coverage.py          # 风险覆盖度验证
│   │   └── pipeline.py               # 验证Pipeline编排
│   │
│   ├── adapters/                     # 外部数据适配层
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseAdapter抽象基类
│   │   ├── sbti_adapter.py           # SBTi示例适配器
│   │   ├── cdp_adapter.py            # CDP示例适配器
│   │   └── climatetrace_adapter.py   # Climate TRACE示例适配器
│   │
│   ├── scoring/                      # 评分引擎
│   │   ├── __init__.py
│   │   ├── scorer.py                 # 综合评分器
│   │   └── weights.py                # 评分权重配置
│   │
│   └── output/                       # 输出层
│       ├── __init__.py
│       ├── base.py                   # OutputRenderer基类
│       ├── json_output.py
│       ├── dataframe_output.py
│       ├── visualizer.py             # 图表生成
│       └── report.py                 # Markdown/PDF报告
│
├── examples/                         # 使用示例（关键展示）
│   ├── 01_basic_analysis.py          # 最简用法
│   ├── 02_with_external_data.py      # 接入外部验证
│   ├── 03_custom_validator.py        # 自定义验证规则
│   ├── 04_batch_comparison.py        # 多公司对比
│   └── 05_custom_adapter.py          # 自定义数据源
│
├── tests/
│   ├── test_extraction.py
│   ├── test_validators.py
│   ├── test_adapters.py
│   └── fixtures/                     # 测试数据
│       └── sample_disclosure.json
│
└── docs/
    ├── methodology.md                # 评估方法论说明
    ├── extending.md                  # 扩展指南
    └── api_reference.md              # API文档
```

---

## 3. 核心数据模型 (Schema)

这是整个框架的数据枢纽——所有模块的输入输出都围绕这套统一的数据结构运转。

### 3.1 提取结果模型

```python
# cda/extraction/schema.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class EmissionScope(str, Enum):
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"

class EmissionData(BaseModel):
    """单一排放数据项"""
    scope: EmissionScope
    value: Optional[float] = None              # tCO2e
    unit: str = "tCO2e"
    year: Optional[int] = None
    baseline_year: Optional[int] = None
    intensity_value: Optional[float] = None    # 强度指标
    intensity_unit: Optional[str] = None       # e.g., "tCO2e/revenue_million"
    methodology: Optional[str] = None          # 核算方法
    assurance_level: Optional[str] = None      # 第三方审计级别

class TargetData(BaseModel):
    """减排目标数据"""
    description: str
    target_year: Optional[int] = None
    base_year: Optional[int] = None
    reduction_pct: Optional[float] = None      # 减排百分比
    scopes_covered: list[EmissionScope] = []
    is_science_based: Optional[bool] = None
    sbti_status: Optional[str] = None          # committed/approved/none
    interim_targets: list[dict] = []           # 中期里程碑

class RiskItem(BaseModel):
    """气候风险披露项"""
    risk_type: str                             # physical/transition
    category: str                              # e.g., "acute_physical", "policy_legal"
    description: str
    time_horizon: Optional[str] = None         # short/medium/long
    financial_impact: Optional[str] = None     # 量化影响描述
    financial_impact_value: Optional[float] = None
    mitigation_strategy: Optional[str] = None
    likelihood: Optional[str] = None

class GovernanceData(BaseModel):
    """治理结构数据"""
    board_oversight: Optional[bool] = None
    board_climate_committee: Optional[bool] = None
    executive_incentive_linked: Optional[bool] = None
    reporting_frequency: Optional[str] = None

class DisclosureExtract(BaseModel):
    """
    结构化提取结果 —— 整个框架的核心数据模型。
    所有Validator和Adapter的输入都基于此结构。
    """
    company_name: str
    report_year: int
    report_type: str = "sustainability"        # sustainability/annual/cdp
    framework: list[str] = []                  # ["TCFD", "GRI", "SASB"]
    sector: Optional[str] = None
    
    # 排放数据
    emissions: list[EmissionData] = []
    
    # 目标承诺
    targets: list[TargetData] = []
    
    # 风险披露
    risks: list[RiskItem] = []
    
    # 治理结构
    governance: GovernanceData = GovernanceData()
    
    # 原始文本片段索引（用于溯源）
    source_references: dict[str, str] = Field(
        default_factory=dict,
        description="字段到原文的映射，用于审计溯源"
    )
    
    # 元数据
    extraction_confidence: float = 0.0
    extraction_method: str = "llm"
```

### 3.2 验证结果模型

```python
# cda/validation/base.py
from pydantic import BaseModel
from enum import Enum

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ValidationFinding(BaseModel):
    """单条验证发现"""
    validator: str                # 来源验证器名
    code: str                     # 问题编码，e.g., "CONSIST-001"
    severity: Severity
    message: str                  # 人类可读描述
    field: Optional[str] = None   # 涉及字段
    evidence: Optional[str] = None  # 原文证据
    recommendation: Optional[str] = None

class ValidationResult(BaseModel):
    """单个验证器的输出"""
    validator_name: str
    score: float                  # 0.0 - 1.0
    max_score: float = 1.0
    findings: list[ValidationFinding] = []
    metadata: dict = {}

class AggregatedResult(BaseModel):
    """Pipeline聚合结果"""
    company_name: str
    overall_score: float
    grade: str                    # A/B/C/D/F
    dimension_scores: dict[str, float]  # 各维度得分
    validation_results: list[ValidationResult]
    cross_validation: Optional[dict] = None  # 外部交叉验证结果
    summary: str                  # LLM生成的一句话总结
```

---

## 4. 核心模块设计

### 4.1 Agent主入口

```python
# cda/agent.py
class ClimateDisclosureAgent:
    """
    主入口类，编排整个分析流程。
    
    设计要点：
    - 零配置即可运行（所有依赖都有默认实现）
    - 通过构造函数注入自定义组件
    - 支持链式调用
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",           # "openai" | "claude" | "local"
        llm_config: dict = None,
        validators: list[str] = None,            # None = 全部启用
        adapters: list[BaseAdapter] = None,      # None = 仅内部分析
        scoring_weights: dict = None,            # 自定义评分权重
        language: str = "en"                     # 输出语言
    ):
        self.extractor = self._init_extractor(llm_provider, llm_config)
        self.validators = self._init_validators(validators)
        self.adapters = adapters or []
        self.scorer = Scorer(weights=scoring_weights)
        self.pipeline = ValidationPipeline(
            validators=self.validators,
            adapters=self.adapters
        )
    
    def analyze(
        self,
        source: str | dict,                      # PDF路径、JSON路径或dict
        company_name: str = None,
        sector: str = None,
        validate_external: bool = True,
        output_format: str = "json"              # "json" | "dataframe" | "report"
    ) -> AggregatedResult:
        """
        核心分析方法。
        
        流程：
        1. Ingestion: 解析输入 → 原始文本
        2. Extraction: LLM提取 → DisclosureExtract
        3. Validation: Pipeline验证 → ValidationResult[]
        4. Cross-validation: 外部数据校验（可选）
        5. Scoring: 综合评分 → AggregatedResult
        """
        # Step 1: 输入解析
        raw_text = self._ingest(source)
        
        # Step 2: 结构化提取
        extract = self.extractor.extract(
            raw_text, 
            company_name=company_name,
            sector=sector
        )
        
        # Step 3 & 4: 验证Pipeline
        validation_results = self.pipeline.run(
            extract, 
            cross_validate=validate_external
        )
        
        # Step 5: 综合评分
        result = self.scorer.aggregate(extract, validation_results)
        
        return self._format_output(result, output_format)
    
    def compare(
        self,
        sources: list[str | dict],
        company_names: list[str] = None,
        **kwargs
    ) -> ComparisonResult:
        """批量分析并对比多家公司"""
        results = [
            self.analyze(src, name, **kwargs)
            for src, name in zip(sources, company_names or [None]*len(sources))
        ]
        return ComparisonResult(results=results)
    
    def _init_validators(self, names):
        """按名称加载验证器，None则全部加载"""
        registry = {
            "consistency": ConsistencyValidator(),
            "quantification": QuantificationValidator(),
            "completeness": CompletenessValidator(),
            "risk_coverage": RiskCoverageValidator(),
        }
        if names is None:
            return list(registry.values())
        return [registry[n] for n in names if n in registry]
```

### 4.2 验证器设计（核心价值所在）

#### 4.2.1 验证器基类

```python
# cda/validation/base.py
from abc import ABC, abstractmethod

class BaseValidator(ABC):
    """
    验证器抽象基类。
    
    扩展方式：
    1. 继承BaseValidator
    2. 实现validate()方法
    3. 注册到Agent或Pipeline
    """
    
    name: str = "base"
    version: str = "1.0"
    description: str = ""
    
    @abstractmethod
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        """
        执行验证，返回结果。
        
        Args:
            extract: 结构化提取结果
        Returns:
            ValidationResult: 包含得分和发现
        """
        pass
    
    def _finding(self, code, severity, message, **kwargs) -> ValidationFinding:
        """工厂方法，简化Finding创建"""
        return ValidationFinding(
            validator=self.name,
            code=code,
            severity=severity,
            message=message,
            **kwargs
        )
```

#### 4.2.2 结构一致性验证器

```python
# cda/validation/consistency.py
class ConsistencyValidator(BaseValidator):
    """
    检查报告内部是否自洽。
    
    核心逻辑：
    - 承诺与行动的匹配（说了Net Zero，有没有路径？）
    - 数据与叙事的匹配（提到Scope 3占比大，有没有管理措施？）
    - 时间线的逻辑性（2030中期目标 < 2050长期目标）
    """
    
    name = "consistency"
    
    # 一致性检查规则集
    RULES = [
        {
            "code": "CONSIST-001",
            "name": "net_zero_pathway",
            "condition": lambda e: any("net zero" in t.description.lower() for t in e.targets),
            "check": lambda e: any(t.interim_targets for t in e.targets),
            "message": "Net Zero target declared but no interim milestones found",
            "severity": Severity.CRITICAL
        },
        {
            "code": "CONSIST-002",
            "name": "scope3_materiality",
            "condition": lambda e: _scope3_material(e),
            "check": lambda e: any(
                r.category in ["supply_chain", "value_chain"] for r in e.risks
            ),
            "message": "Scope 3 appears material (>40% of total) but no supply chain risk disclosed",
            "severity": Severity.WARNING
        },
        {
            "code": "CONSIST-003",
            "name": "target_timeline_logic",
            "condition": lambda e: len(e.targets) > 1,
            "check": lambda e: _check_timeline_monotonicity(e.targets),
            "message": "Target timeline inconsistency: interim target more aggressive than long-term",
            "severity": Severity.WARNING
        },
        {
            "code": "CONSIST-004",
            "name": "investment_specificity",
            "condition": lambda e: _mentions_climate_investment(e),
            "check": lambda e: _has_specific_projects(e),
            "message": "Climate investment amount mentioned without specific project breakdown",
            "severity": Severity.INFO
        },
        {
            "code": "CONSIST-005",
            "name": "governance_action_gap",
            "condition": lambda e: e.governance.board_oversight,
            "check": lambda e: e.governance.executive_incentive_linked is not None,
            "message": "Board oversight claimed but executive incentive linkage not specified",
            "severity": Severity.WARNING
        },
    ]
    
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        passed = 0
        applicable = 0
        
        for rule in self.RULES:
            if rule["condition"](extract):
                applicable += 1
                if rule["check"](extract):
                    passed += 1
                else:
                    findings.append(self._finding(
                        code=rule["code"],
                        severity=rule["severity"],
                        message=rule["message"]
                    ))
        
        score = passed / applicable if applicable > 0 else 1.0
        
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={"rules_applicable": applicable, "rules_passed": passed}
        )
```

#### 4.2.3 量化充分性验证器

```python
# cda/validation/quantification.py
class QuantificationValidator(BaseValidator):
    """
    评估披露的"数据密度"——是否有足够的量化指标支撑叙述。
    
    评分维度：
    1. 排放数据完整度（绝对值/强度/基准年/方法论/审计）
    2. 目标量化程度（百分比/时间表/里程碑）
    3. 风险量化程度（财务影响/概率/时间范围）
    """
    
    name = "quantification"
    
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        sub_scores = {}
        
        # --- 排放数据完整度 ---
        emission_checks = {
            "has_scope1_absolute": any(
                e.scope == EmissionScope.SCOPE_1 and e.value is not None 
                for e in extract.emissions
            ),
            "has_scope2_absolute": any(
                e.scope == EmissionScope.SCOPE_2 and e.value is not None 
                for e in extract.emissions
            ),
            "has_scope3_absolute": any(
                e.scope == EmissionScope.SCOPE_3 and e.value is not None 
                for e in extract.emissions
            ),
            "has_baseline_year": any(
                e.baseline_year is not None for e in extract.emissions
            ),
            "has_intensity_metric": any(
                e.intensity_value is not None for e in extract.emissions
            ),
            "has_methodology": any(
                e.methodology is not None for e in extract.emissions
            ),
            "has_third_party_assurance": any(
                e.assurance_level is not None for e in extract.emissions
            ),
        }
        sub_scores["emissions"] = sum(emission_checks.values()) / len(emission_checks)
        
        # --- 目标量化程度 ---
        target_checks = {
            "has_reduction_percentage": any(
                t.reduction_pct is not None for t in extract.targets
            ),
            "has_target_year": any(
                t.target_year is not None for t in extract.targets
            ),
            "has_base_year": any(
                t.base_year is not None for t in extract.targets
            ),
            "has_interim_milestones": any(
                len(t.interim_targets) > 0 for t in extract.targets
            ),
            "has_scope_coverage": any(
                len(t.scopes_covered) > 0 for t in extract.targets
            ),
        }
        sub_scores["targets"] = sum(target_checks.values()) / max(len(target_checks), 1)
        
        # --- 风险量化程度 ---
        risk_checks = {
            "has_financial_impact": any(
                r.financial_impact_value is not None for r in extract.risks
            ),
            "has_time_horizon": any(
                r.time_horizon is not None for r in extract.risks
            ),
            "has_likelihood": any(
                r.likelihood is not None for r in extract.risks
            ),
            "has_mitigation": any(
                r.mitigation_strategy is not None for r in extract.risks
            ),
        }
        sub_scores["risks"] = sum(risk_checks.values()) / max(len(risk_checks), 1)
        
        # 生成findings
        for check_name, passed in {**emission_checks, **target_checks, **risk_checks}.items():
            if not passed:
                findings.append(self._finding(
                    code=f"QUANT-{check_name.upper()}",
                    severity=Severity.WARNING,
                    message=f"Missing quantification: {check_name.replace('_', ' ')}",
                    field=check_name
                ))
        
        # 加权总分
        weights = {"emissions": 0.4, "targets": 0.35, "risks": 0.25}
        overall = sum(sub_scores[k] * weights[k] for k in weights)
        
        return ValidationResult(
            validator_name=self.name,
            score=overall,
            findings=findings,
            metadata={"sub_scores": sub_scores}
        )
```

#### 4.2.4 披露完整性验证器

```python
# cda/validation/completeness.py
class CompletenessValidator(BaseValidator):
    """
    基于TCFD/SASB/GRI框架检查披露覆盖率。
    
    核心思路：根据企业所在行业，检查是否覆盖了标准要求的所有披露维度。
    """
    
    name = "completeness"
    
    # TCFD四大支柱的检查清单
    TCFD_CHECKLIST = {
        "governance": {
            "board_oversight": "Board-level oversight of climate risks",
            "management_role": "Management's role in climate assessment",
        },
        "strategy": {
            "climate_risks_identified": "Climate-related risks identified",
            "climate_opportunities": "Climate-related opportunities described",
            "scenario_analysis": "Scenario analysis conducted",
            "strategy_resilience": "Strategy resilience assessment",
        },
        "risk_management": {
            "risk_identification_process": "Process for identifying climate risks",
            "risk_management_process": "Process for managing climate risks",
            "integration_with_erm": "Integration with overall risk management",
        },
        "metrics_targets": {
            "ghg_emissions": "GHG emissions disclosed (Scope 1, 2, 3)",
            "climate_targets": "Climate-related targets set",
            "progress_tracking": "Progress against targets tracked",
        }
    }
    
    # SASB行业特定指标（示例：食品/农业）
    SASB_SECTOR_METRICS = {
        "food_agriculture": [
            "ghg_emissions", "energy_management", "water_management",
            "land_use", "biodiversity_impact", "supply_chain_environmental",
            "food_safety", "packaging_waste"
        ],
        "oil_gas": [
            "ghg_emissions", "air_quality", "water_management",
            "biodiversity", "reserves_valuation", "community_impact"
        ],
        "financials": [
            "financed_emissions", "climate_risk_exposure",
            "sustainable_finance_products", "engagement_policy"
        ],
        # 可扩展更多行业...
    }
    
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        
        # TCFD完整性检查
        tcfd_results = self._check_tcfd(extract)
        
        # SASB行业检查（如果提供了sector）
        sasb_results = {}
        if extract.sector:
            sasb_results = self._check_sasb(extract)
        
        # 汇总
        total_items = sum(len(v) for v in self.TCFD_CHECKLIST.values())
        covered_items = sum(1 for v in tcfd_results.values() if v)
        
        score = covered_items / total_items
        
        for item, covered in tcfd_results.items():
            if not covered:
                findings.append(self._finding(
                    code=f"COMPL-TCFD-{item.upper()}",
                    severity=Severity.WARNING,
                    message=f"TCFD recommended disclosure missing: {item}",
                    field=item
                ))
        
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "tcfd_coverage": tcfd_results,
                "sasb_coverage": sasb_results,
                "tcfd_score": score,
            }
        )
    
    def _check_tcfd(self, extract: DisclosureExtract) -> dict[str, bool]:
        """逐项检查TCFD覆盖情况"""
        results = {}
        
        # Governance
        results["board_oversight"] = extract.governance.board_oversight is not None
        results["management_role"] = extract.governance.reporting_frequency is not None
        
        # Strategy
        results["climate_risks_identified"] = len(extract.risks) > 0
        results["climate_opportunities"] = any(
            "opportunity" in r.description.lower() for r in extract.risks
        )
        results["scenario_analysis"] = "scenario" in str(extract.source_references).lower()
        
        # Risk Management
        results["risk_identification_process"] = any(
            r.category is not None for r in extract.risks
        )
        results["risk_management_process"] = any(
            r.mitigation_strategy is not None for r in extract.risks
        )
        
        # Metrics & Targets
        results["ghg_emissions"] = len(extract.emissions) > 0
        results["climate_targets"] = len(extract.targets) > 0
        results["progress_tracking"] = any(
            e.baseline_year is not None for e in extract.emissions
        )
        
        return results
```

#### 4.2.5 风险覆盖度验证器

```python
# cda/validation/risk_coverage.py
class RiskCoverageValidator(BaseValidator):
    """
    评估气候风险披露的广度和深度。
    
    基于TCFD框架将风险分为物理风险和转型风险两大类，
    检查各子类别的覆盖情况。
    """
    
    name = "risk_coverage"
    
    RISK_TAXONOMY = {
        "physical": {
            "acute": ["extreme_weather", "flooding", "wildfire", "drought"],
            "chronic": ["sea_level_rise", "temperature_change", "precipitation_change"],
        },
        "transition": {
            "policy_legal": ["carbon_pricing", "regulation", "litigation"],
            "technology": ["substitution", "disruption", "efficiency"],
            "market": ["demand_shift", "commodity_price", "stranded_assets"],
            "reputation": ["stigmatization", "stakeholder_concern"],
        }
    }
    
    def validate(self, extract: DisclosureExtract) -> ValidationResult:
        findings = []
        
        # 统计风险类型覆盖
        covered_types = set()
        for risk in extract.risks:
            covered_types.add(risk.risk_type)
            covered_types.add(risk.category)
        
        # 检查大类覆盖
        has_physical = any(r.risk_type == "physical" for r in extract.risks)
        has_transition = any(r.risk_type == "transition" for r in extract.risks)
        
        if not has_physical:
            findings.append(self._finding(
                code="RISK-001",
                severity=Severity.CRITICAL,
                message="No physical climate risks disclosed"
            ))
        
        if not has_transition:
            findings.append(self._finding(
                code="RISK-002",
                severity=Severity.CRITICAL,
                message="No transition climate risks disclosed"
            ))
        
        # 检查深度（是否有量化）
        quantified_risks = [r for r in extract.risks if r.financial_impact_value is not None]
        quantification_rate = len(quantified_risks) / max(len(extract.risks), 1)
        
        if quantification_rate < 0.3:
            findings.append(self._finding(
                code="RISK-003",
                severity=Severity.WARNING,
                message=f"Only {quantification_rate:.0%} of risks have quantified financial impact"
            ))
        
        # 评分
        breadth = (int(has_physical) + int(has_transition)) / 2
        depth = quantification_rate
        score = breadth * 0.5 + depth * 0.5
        
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings,
            metadata={
                "risk_types_covered": list(covered_types),
                "physical_covered": has_physical,
                "transition_covered": has_transition,
                "quantification_rate": quantification_rate
            }
        )
```

### 4.3 验证Pipeline

```python
# cda/validation/pipeline.py
class ValidationPipeline:
    """
    验证流水线——编排多个Validator和Adapter的执行顺序。
    
    Pipeline支持：
    - 顺序执行所有内部验证器
    - 可选执行外部数据交叉验证
    - 结果聚合和冲突解决
    """
    
    def __init__(self, validators: list[BaseValidator], adapters: list[BaseAdapter] = None):
        self.validators = validators
        self.adapters = adapters or []
    
    def run(
        self, 
        extract: DisclosureExtract,
        cross_validate: bool = True
    ) -> list[ValidationResult]:
        results = []
        
        # Phase 1: 内部验证
        for validator in self.validators:
            result = validator.validate(extract)
            results.append(result)
        
        # Phase 2: 外部交叉验证（可选）
        if cross_validate and self.adapters:
            for adapter in self.adapters:
                try:
                    xv_result = adapter.cross_validate(extract)
                    results.append(xv_result)
                except DataNotAvailableError:
                    # 优雅降级：无数据时跳过，不影响其他验证
                    results.append(ValidationResult(
                        validator_name=f"adapter:{adapter.name}",
                        score=None,
                        findings=[ValidationFinding(
                            validator=adapter.name,
                            code="ADAPTER-NO-DATA",
                            severity=Severity.INFO,
                            message=f"External data not available from {adapter.name}, skipped."
                        )]
                    ))
        
        return results
```

---

## 5. Adapter设计（可插拔外部数据）

### 5.1 Adapter基类

```python
# cda/adapters/base.py
from abc import ABC, abstractmethod

class DataNotAvailableError(Exception):
    """数据不可用时抛出"""
    pass

class BaseAdapter(ABC):
    """
    外部数据源适配器基类。
    
    设计原则：
    - 数据源由用户自行提供（CSV/API key/DataFrame）
    - Adapter只负责"对接逻辑"，不负责"数据获取"
    - 无数据时返回明确提示而非报错
    """
    
    name: str = "base"
    data_source_url: str = ""       # 数据获取地址提示
    requires_auth: bool = False
    
    @abstractmethod
    def cross_validate(self, extract: DisclosureExtract) -> ValidationResult:
        """
        用外部数据交叉验证提取结果。
        
        Returns:
            ValidationResult: 交叉验证发现
        Raises:
            DataNotAvailableError: 用户未提供数据时
        """
        pass
    
    @abstractmethod
    def get_benchmark(self, sector: str) -> dict:
        """获取行业基准数据"""
        pass
    
    def status(self) -> dict:
        """检查Adapter状态"""
        return {
            "name": self.name,
            "data_loaded": self._has_data(),
            "source_url": self.data_source_url,
        }
    
    @abstractmethod
    def _has_data(self) -> bool:
        pass
```

### 5.2 SBTi Adapter 示例实现

```python
# cda/adapters/sbti_adapter.py
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
    
    def _fuzzy_match(self, company_name: str):
        """模糊匹配企业名（处理名称不一致问题）"""
        from difflib import get_close_matches
        names = self._data["Company Name"].tolist()
        matches = get_close_matches(company_name, names, n=1, cutoff=0.7)
        if matches:
            return self._data[self._data["Company Name"] == matches[0]].iloc[0]
        return None
    
    def _compare_target(self, disclosed_target, sbti_record) -> list[ValidationFinding]:
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
    
    def get_benchmark(self, sector: str) -> dict:
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
```

### 5.3 自定义Adapter模板

```python
# cda/adapters/template.py
class CustomAdapter(BaseAdapter):
    """
    用户自定义数据源模板。
    
    使用方式：
        adapter = CustomAdapter(
            name="my_source",
            data_source="my_data.csv",
            column_mapping={
                "company": "Company Name",
                "emissions": "Total GHG",
                "target_year": "Net Zero Year"
            },
            validation_logic=my_validation_func  # 可选
        )
    """
    
    def __init__(
        self,
        name: str,
        data_source,
        column_mapping: dict,
        validation_logic: callable = None
    ):
        self.name = name
        self._data = pd.read_csv(data_source) if isinstance(data_source, str) else data_source
        self._mapping = column_mapping
        self._custom_logic = validation_logic
    
    def cross_validate(self, extract: DisclosureExtract) -> ValidationResult:
        if self._custom_logic:
            return self._custom_logic(extract, self._data, self._mapping)
        
        # 默认：简单存在性检查
        company_col = self._mapping.get("company", "company")
        match = self._data[self._data[company_col].str.contains(
            extract.company_name, case=False, na=False
        )]
        
        findings = []
        if match.empty:
            findings.append(ValidationFinding(
                validator=self.name,
                code="CUSTOM-001",
                severity=Severity.INFO,
                message=f"Company not found in {self.name} dataset"
            ))
        
        return ValidationResult(
            validator_name=f"adapter:{self.name}",
            score=1.0 if not match.empty else None,
            findings=findings
        )
    
    def get_benchmark(self, sector: str) -> dict:
        return {"source": self.name, "data_available": not self._data.empty}
    
    def _has_data(self) -> bool:
        return self._data is not None and not self._data.empty
```

---

## 6. 评分引擎

```python
# cda/scoring/scorer.py
class Scorer:
    """
    将多维度验证结果聚合为综合评分。
    
    评分体系：
    - 总分 0-100，映射为A/B/C/D/F等级
    - 各维度可配置权重
    - 外部交叉验证作为"加分/扣分"而非基础分
    """
    
    DEFAULT_WEIGHTS = {
        "consistency": 0.25,
        "quantification": 0.30,
        "completeness": 0.25,
        "risk_coverage": 0.20,
    }
    
    GRADE_MAP = [
        (90, "A"),
        (80, "B"),
        (70, "C"),
        (60, "D"),
        (0,  "F"),
    ]
    
    def __init__(self, weights: dict = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def aggregate(
        self, 
        extract: DisclosureExtract, 
        results: list[ValidationResult]
    ) -> AggregatedResult:
        
        dimension_scores = {}
        
        # 内部验证器得分
        for result in results:
            if result.score is not None and not result.validator_name.startswith("adapter:"):
                dimension_scores[result.validator_name] = result.score
        
        # 加权总分
        overall = sum(
            dimension_scores.get(dim, 0) * weight
            for dim, weight in self.weights.items()
        ) * 100  # 转为百分制
        
        # 外部交叉验证调整
        adapter_results = [r for r in results if r.validator_name.startswith("adapter:")]
        cross_validation_penalty = sum(
            len([f for f in r.findings if f.severity == Severity.CRITICAL]) * 5
            for r in adapter_results
        )
        overall = max(overall - cross_validation_penalty, 0)
        
        # 等级映射
        grade = "F"
        for threshold, g in self.GRADE_MAP:
            if overall >= threshold:
                grade = g
                break
        
        return AggregatedResult(
            company_name=extract.company_name,
            overall_score=round(overall, 1),
            grade=grade,
            dimension_scores={k: round(v * 100, 1) for k, v in dimension_scores.items()},
            validation_results=results,
            cross_validation={
                "adapters_used": [r.validator_name for r in adapter_results],
                "penalty_applied": cross_validation_penalty
            },
            summary=self._generate_summary(extract, overall, grade, dimension_scores)
        )
    
    def _generate_summary(self, extract, score, grade, dims) -> str:
        weakest = min(dims, key=dims.get) if dims else "N/A"
        return (
            f"{extract.company_name} ({extract.report_year}) scores {score:.0f}/100 "
            f"(Grade {grade}). Weakest dimension: {weakest}."
        )
```

---

## 7. 可视化输出

```python
# cda/output/visualizer.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DisclosureVisualizer:
    """生成分析结果的交互式可视化图表"""
    
    @staticmethod
    def radar_chart(result: AggregatedResult) -> go.Figure:
        """多维度雷达图"""
        dims = result.dimension_scores
        categories = list(dims.keys())
        values = list(dims.values())
        
        fig = go.Figure(data=go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill='toself',
            name=result.company_name
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=f"Disclosure Quality - {result.company_name}"
        )
        return fig
    
    @staticmethod
    def comparison_radar(results: list[AggregatedResult]) -> go.Figure:
        """多公司对比雷达图"""
        fig = go.Figure()
        for result in results:
            dims = result.dimension_scores
            categories = list(dims.keys())
            values = list(dims.values())
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=result.company_name,
                opacity=0.6
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Cross-Company Disclosure Comparison"
        )
        return fig
    
    @staticmethod
    def completeness_heatmap(results: list[AggregatedResult]) -> go.Figure:
        """披露完整性热力图"""
        companies = [r.company_name for r in results]
        dimensions = list(results[0].dimension_scores.keys()) if results else []
        
        z = [[r.dimension_scores.get(d, 0) for d in dimensions] for r in results]
        
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=dimensions,
            y=companies,
            colorscale="RdYlGn",
            zmin=0, zmax=100,
            text=[[f"{v:.0f}" for v in row] for row in z],
            texttemplate="%{text}",
        ))
        fig.update_layout(title="Disclosure Completeness Matrix")
        return fig
    
    @staticmethod
    def findings_summary(result: AggregatedResult) -> go.Figure:
        """验证发现按严重程度统计"""
        all_findings = []
        for vr in result.validation_results:
            all_findings.extend(vr.findings)
        
        severity_counts = {"critical": 0, "warning": 0, "info": 0}
        for f in all_findings:
            severity_counts[f.severity.value] += 1
        
        colors = {"critical": "#e74c3c", "warning": "#f39c12", "info": "#3498db"}
        
        fig = go.Figure(data=[go.Bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            marker_color=[colors[k] for k in severity_counts.keys()]
        )])
        fig.update_layout(
            title=f"Validation Findings - {result.company_name}",
            yaxis_title="Count"
        )
        return fig
```

---

## 8. 使用示例

### 8.1 最简用法（5行代码）

```python
from cda import ClimateDisclosureAgent

agent = ClimateDisclosureAgent()
result = agent.analyze("cargill_esg_2024.pdf", company_name="Cargill")

print(f"Score: {result.overall_score}/100 ({result.grade})")
print(f"Issues: {len([f for vr in result.validation_results for f in vr.findings])}")
```

### 8.2 接入外部验证

```python
from cda import ClimateDisclosureAgent
from cda.adapters import SBTiAdapter, CDPAdapter

agent = ClimateDisclosureAgent(
    adapters=[
        SBTiAdapter("sbti_companies.csv"),
        CDPAdapter("cdp_scores.csv"),
    ]
)

result = agent.analyze(
    "cargill_esg_2024.pdf",
    company_name="Cargill",
    sector="food_agriculture",
    validate_external=True
)

# 查看交叉验证结果
for vr in result.validation_results:
    if vr.validator_name.startswith("adapter:"):
        print(f"[{vr.validator_name}] Score: {vr.score}")
        for f in vr.findings:
            print(f"  - [{f.severity}] {f.message}")
```

### 8.3 多公司对比

```python
from cda import ClimateDisclosureAgent
from cda.output import DisclosureVisualizer

agent = ClimateDisclosureAgent()

companies = {
    "Cargill": "reports/cargill_2024.pdf",
    "ADM": "reports/adm_2024.pdf",
    "Bunge": "reports/bunge_2024.pdf",
    "Deere": "reports/deere_2024.pdf",
}

results = [
    agent.analyze(path, company_name=name, sector="food_agriculture")
    for name, path in companies.items()
]

# 生成对比图表
viz = DisclosureVisualizer()
viz.comparison_radar(results).show()
viz.completeness_heatmap(results).show()
```

### 8.4 自定义验证器

```python
from cda.validation import BaseValidator, ValidationResult, Severity

class GreenwashingDetector(BaseValidator):
    """检测潜在洗绿信号"""
    
    name = "greenwashing"
    
    VAGUE_TERMS = [
        "carbon neutral", "green", "eco-friendly", "sustainable",
        "net positive", "climate leader"
    ]
    
    def validate(self, extract):
        findings = []
        
        # 检查模糊表述与量化数据的比例
        vague_count = sum(
            1 for ref in extract.source_references.values()
            if any(term in ref.lower() for term in self.VAGUE_TERMS)
        )
        
        quantified_count = len([
            e for e in extract.emissions if e.value is not None
        ])
        
        if vague_count > quantified_count * 2:
            findings.append(self._finding(
                code="GREENWASH-001",
                severity=Severity.WARNING,
                message=f"High ratio of vague claims ({vague_count}) "
                        f"vs quantified data ({quantified_count})"
            ))
        
        score = 1.0 - min(vague_count / max(quantified_count * 3, 1), 1.0)
        
        return ValidationResult(
            validator_name=self.name,
            score=score,
            findings=findings
        )

# 注册到Agent
agent = ClimateDisclosureAgent()
agent.validators.append(GreenwashingDetector())
result = agent.analyze("report.pdf")
```

---

## 9. CV / LinkedIn 展示建议

### 9.1 项目描述

```
Climate Disclosure Validation Agent (CDA)

Designed and implemented a modular AI agent framework for automated 
evaluation of corporate climate disclosures. The system features 
pluggable validation modules (consistency, quantification, completeness, 
risk coverage), standardized external data adapters (SBTi, CDP), and 
a composable pipeline architecture enabling extensible analysis workflows.

Tech: Python, Pydantic, LangChain, Plotly | Patterns: Strategy, Adapter, Pipeline
```

### 9.2 关键亮点 Bullet Points

- Architected a **plugin-based validation engine** with 4 core validators and extensible `BaseValidator` interface, enabling custom rule injection without framework modification
- Implemented **cross-source verification system** via adapter pattern, supporting SBTi, CDP, and Climate TRACE integration with graceful degradation when data is unavailable
- Built **TCFD/SASB-aligned scoring methodology** producing structured assessments across governance, strategy, risk management, and metrics dimensions
- Designed **standardized data schema** (Pydantic models) bridging unstructured PDF extraction and structured validation pipeline, achieving type-safe data flow throughout

### 9.3 技术关键词（简历/ATS优化）

`Python` · `LLM/AI Agent` · `LangChain` · `Pydantic` · `ESG/Climate` · `TCFD` · `SASB` · `Design Patterns (Strategy, Adapter, Pipeline)` · `Data Validation` · `Plotly` · `API Design` · `Modular Architecture`

---

## 10. 两周落地计划

### Week 1: 核心骨架

| Day | 任务 | 产出 |
|-----|------|------|
| 1 | Schema定义（Pydantic模型） + 项目脚手架 | `schema.py`, `pyproject.toml` |
| 2 | LLM提取模块（用OpenAI/Claude做结构化提取） | `llm_extractor.py` |
| 3 | ConsistencyValidator + QuantificationValidator | 2个验证器 |
| 4 | CompletenessValidator + RiskCoverageValidator | 2个验证器 |
| 5 | ValidationPipeline + Scorer | pipeline编排 + 评分逻辑 |
| 6-7 | Agent主入口 + 基础测试 | `agent.py` + tests |

### Week 2: 接口 + 展示

| Day | 任务 | 产出 |
|-----|------|------|
| 1 | BaseAdapter + SBTi Adapter示例 | adapter层 |
| 2 | 可视化模块（雷达图/热力图/柱状图） | `visualizer.py` |
| 3 | 跑2-3家公司的完整分析 | 真实结果数据 |
| 4 | README + 方法论文档 + examples/ | 文档 |
| 5 | 代码整理 + 截图 + LinkedIn发布 | 最终交付 |

---

## 11. 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 数据模型 | **Pydantic v2** | 类型安全 + 自动验证 + JSON Schema导出 |
| LLM集成 | **LangChain** (或直接API) | 灵活切换模型，结构化输出支持好 |
| 可视化 | **Plotly** | 交互式图表，截图效果好 |
| PDF解析 | **PyMuPDF + pdfplumber** | 互补：前者速度快，后者表格提取强 |
| 测试 | **pytest** | 标准选择 |
| 包管理 | **pyproject.toml** | 现代Python标准 |
| 文档 | **MkDocs** (可选) | 轻量静态文档 |

---

## 12. 扩展路线（如果继续发展）

### Phase 2 — 增强能力
- 更多行业的SASB指标库（金融/能源/制造）
- 支持时间序列分析（同一公司多年对比）
- LLM-as-Judge模式（用LLM评估披露叙述质量）

### Phase 3 — 产品化方向
- Streamlit/Gradio前端
- REST API封装
- 支持批量PDF处理
- Webhook通知（新报告发布时自动分析）
