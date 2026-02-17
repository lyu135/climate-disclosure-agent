# News Consistency Validator - 完整设计规范

## 1. 功能概述

**目标**：通过搜集报告期内的环境/气候相关新闻，交叉验证企业披露的真实性，识别漂绿行为和选择性披露。

**核心逻辑**：
```
报告说的（What they claim） vs 新闻报道的（What actually happened）
→ 矛盾 = 可信度问题
```

---

## 2. 模块架构

```
NewsConsistencyValidator
├── NewsDataSource (新闻数据源)
│   ├── GoogleNewsAPI
│   ├── BingNewsAPI
│   └── BraveSearchAPI (备选)
├── EventExtractor (事件提取器)
│   ├── LLM-based extraction
│   └── Event classification
├── CrossValidator (交叉验证器)
│   ├── Contradiction detection
│   └── Omission detection
└── CredibilityScorer (可信度评分器)
```

---

## 3. 数据结构设计

### 3.1 NewsArticle (新闻文章)
```python
class NewsArticle(BaseModel):
    """新闻文章数据模型"""
    title: str                          # 标题
    url: str                            # 链接
    source: str                         # 来源（Reuters/Bloomberg/etc）
    published_date: str                 # 发布日期 (YYYY-MM-DD)
    snippet: str                        # 摘要
    full_text: Optional[str] = None     # 全文（可选）
    relevance_score: float = 0.0        # 相关性得分 (0.0-1.0)
```

### 3.2 EnvironmentalEvent (环境事件)
```python
class EventType(str, Enum):
    """事件类型"""
    FINE = "fine"                       # 罚款
    LAWSUIT = "lawsuit"                 # 诉讼
    ACCIDENT = "accident"               # 事故
    REGULATION = "regulation"           # 监管
    VIOLATION = "violation"             # 违规
    INVESTIGATION = "investigation"     # 调查
    NGO_REPORT = "ngo_report"          # NGO 报告
    OTHER = "other"

class EnvironmentalEvent(BaseModel):
    """环境事件数据模型"""
    event_type: EventType               # 事件类型
    description: str                    # 事件描述
    date: str                           # 事件日期 (YYYY-MM-DD)
    severity: str                       # 严重程度 (critical/high/medium/low)
    financial_impact: Optional[float] = None  # 财务影响（美元）
    source_article: NewsArticle         # 来源新��
    keywords: List[str] = []            # 关键词
    confidence: float = 0.0             # 提取置信度 (0.0-1.0)
```

### 3.3 Contradiction (矛盾)
```python
class ContradictionType(str, Enum):
    """矛盾类型"""
    OMISSION = "omission"               # 遗漏（报告未提及）
    MISREPRESENTATION = "misrepresentation"  # 误导（报告说法与事实不符）
    TIMING_MISMATCH = "timing_mismatch" # 时间不匹配
    MAGNITUDE_MISMATCH = "magnitude_mismatch"  # 数量级不匹配

class Contradiction(BaseModel):
    """矛盾数据模型"""
    contradiction_type: ContradictionType
    severity: str                       # critical/warning/info
    claim_in_report: Optional[str] = None  # 报告中的说法
    evidence_from_news: str             # 新闻中的证据
    event: EnvironmentalEvent           # 相关事件
    impact_on_credibility: float        # 对可信度的影响 (-50 to 0)
    recommendation: str                 # 改进建议
```

### 3.4 NewsValidationResult (新闻验证结果)
```python
class NewsValidationResult(BaseModel):
    """新闻验证结果"""
    company_name: str
    report_period_start: str            # 报告期开始 (YYYY-MM-DD)
    report_period_end: str              # 报告期结束 (YYYY-MM-DD)
    
    # 搜集的数据
    news_articles_found: int            # 找到的新闻数量
    events_extracted: List[EnvironmentalEvent]  # 提取的事件
    
    # 验证结果
    contradictions: List[Contradiction] # 发现的矛盾
    credibility_score: float            # 可信度得分 (0-100)
    
    # 统计
    critical_issues: int                # 严重问题数量
    warnings: int                       # 警告数量
    info_items: int                     # 信息数量
    
    # 元数据
    validation_date: str                # 验证日期
    data_sources: List[str]             # 数据来源
```

---

## 4. 核心功能实现规范

### 4.1 NewsDataSource (新闻数据源)

**文件位置**：`cda/validation/news_data_source.py`

**类定义**：
```python
class NewsDataSource:
    """新闻数据源基类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化数据源"""
        pass
    
    def search_news(
        self,
        company_name: str,
        start_date: str,
        end_date: str,
        keywords: List[str] = None,
        max_results: int = 50
    ) -> List[NewsArticle]:
        """
        搜索新闻
        
        Args:
            company_name: 公司名称
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            keywords: 额外关键词（默认：["environment", "climate", "pollution", "fine", "lawsuit"]）
            max_results: 最大结果数
            
        Returns:
            新闻文章列表
        """
        pass
```

**实现要求**：
1. 支持多个 API（Google News、Bing News、Brave Search）
2. 自动构建搜索查询：`"{company_name}" AND ({keyword1} OR {keyword2} OR ...)`
3. 按相关性排序
4. 去重（相同标题/URL）
5. 错误处理（API 限额、网络错误）

**默认关键词列表**：
```python
DEFAULT_KEYWORDS = [
    "environment", "climate", "pollution", "emission",
    "fine", "penalty", "lawsuit", "violation",
    "regulation", "EPA", "investigation",
    "carbon", "greenhouse gas", "sustainability"
]
```

---

### 4.2 EventExtractor (事件提取器)

**文件位置**：`cda/validation/event_extractor.py`

**类定义**：
```python
class EventExtractor:
    """从新闻中提取环境事件"""
    
    def __init__(self, llm_provider: str = "openai", llm_config: Dict = None):
        """初始化 LLM"""
        pass
    
    def extract_events(
        self,
        news_articles: List[NewsArticle],
        company_name: str
    ) -> List[EnvironmentalEvent]:
        """
        从新闻列表中提取环境事件
        
        Args:
            news_articles: 新闻文章列表
            company_name: 公司名称
            
        Returns:
            环境事件列表
        """
        pass
    
    def _extract_single_event(
        self,
        article: NewsArticle,
        company_name: str
    ) -> Optional[EnvironmentalEvent]:
        """从单篇新闻提取事件"""
        pass
```

**LLM Prompt 设计**：
```
You are an environmental compliance analyst. Extract structured information about environmental/climate events from the following news article.

Company: {company_name}
Article Title: {title}
Article Date: {date}
Article Content: {snippet}

Extract the following information (return JSON only):
{
  "event_type": "fine|lawsuit|accident|regulation|violation|investigation|ngo_report|other",
  "description": "Brief description of the event",
  "date": "YYYY-MM-DD (event date, not article date)",
  "severity": "critical|high|medium|low",
  "financial_impact": 1000000.0 (in USD, null if not mentioned),
  "keywords": ["keyword1", "keyword2"],
  "confidence": 0.9 (0.0-1.0, your confidence in this extraction)
}

If the article is not about an environmental/climate event related to {company_name}, return null.
```

**实现要求**：
1. 批量处理（每次最多 10 篇，避免 token 超限）
2. 过滤无关新闻（confidence < 0.5）
3. 日期解析（支持多种格式）
4. 财务影响提取（识别 "$500M", "500 million dollars" 等）
5. 错误处理（LLM 失败时返回空列表）

---

### 4.3 CrossValidator (交叉验证器)

**文件位置**：`cda/validation/cross_validator.py`

**类定义**：
```python
class CrossValidator:
    """交叉验证报告与新闻"""
    
    def validate(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """
        交叉验证披露数据与新闻事件
        
        Args:
            disclosure: 披露数据
            events: 新闻事件列表
            
        Returns:
            矛盾列表
        """
        pass
    
    def _check_omissions(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """检查遗漏（报告未提及的事件）"""
        pass
    
    def _check_misrepresentations(
        self,
        disclosure: DisclosureExtract,
        events: List[EnvironmentalEvent]
    ) -> List[Contradiction]:
        """检查误导（报告说法与事实不符）"""
        pass
```

**验证逻辑**：

1. **遗漏检查（Omission Detection）**
   - 如果新闻中有 `fine/lawsuit/violation` 事件
   - 但 `disclosure.risks` 中没有对应的风险披露
   - → 生成 `OMISSION` 类型矛盾

2. **误导检查（Misrepresentation Detection）**
   - 如果报告声称 "zero emissions" 或 "carbon neutral"
   - 但新闻报道排放超标或使用化石燃料
   - → 生成 `MISREPRESENTATION` 类型矛盾

3. **数量级检查（Magnitude Mismatch）**
   - 如果新闻报道罚款 $500M
   - 但报告中财务影响只提及 $50M
   - → 生成 `MAGNITUDE_MISMATCH` 类型矛盾

**严重程度判定**：
```python
def determine_severity(event: EnvironmentalEvent) -> str:
    if event.event_type in ["fine", "lawsuit", "violation"]:
        if event.financial_impact and event.financial_impact > 10_000_000:
            return "critical"
        return "warning"
    elif event.event_type in ["investigation", "regulation"]:
        return "warning"
    else:
        return "info"
```

---

### 4.4 CredibilityScorer (���信度评分器)

**文件位置**：`cda/validation/credibility_scorer.py`

**类定义**：
```python
class CredibilityScorer:
    """计算可信度得分"""
    
    def score(
        self,
        contradictions: List[Contradiction],
        total_events: int
    ) -> float:
        """
        计算可信度得分
        
        Args:
            contradictions: 矛盾列表
            total_events: 总事件数
            
        Returns:
            可信度得分 (0-100)
        """
        pass
```

**评分公式**：
```python
base_score = 100

for contradiction in contradictions:
    if contradiction.severity == "critical":
        base_score -= 30
    elif contradiction.severity == "warning":
        base_score -= 15
    elif contradiction.severity == "info":
        base_score -= 5

# 确保不低于 0
credibility_score = max(0, base_score)

# 如果没有负面新闻，满分
if total_events == 0:
    credibility_score = 100
```

**评级标准**：
- 90-100: Excellent (无矛盾或仅有轻微信息)
- 70-89: Good (少量警告)
- 50-69: Fair (多个警告或少量严重问题)
- 30-49: Poor (多个严重问题)
- 0-29: Very Poor (大量严重矛盾，疑似漂绿)

---

### 4.5 NewsConsistencyValidator (主验证器)

**文件位置**：`cda/validation/news_consistency.py`

**类定义**：
```python
class NewsConsistencyValidator(BaseValidator):
    """新闻一致性验证器"""
    
    def __init__(
        self,
        news_api_key: Optional[str] = None,
        llm_provider: str = "openai",
        llm_config: Optional[Dict] = None
    ):
        """初始化验证器"""
        self.data_source = NewsDataSource(api_key=news_api_key)
        self.event_extractor = EventExtractor(llm_provider, llm_config)
        self.cross_validator = CrossValidator()
        self.credibility_scorer = CredibilityScorer()
    
    def validate(self, data: DisclosureExtract) -> ValidationResult:
        """
        执行新闻一致性验证
        
        Args:
            data: 披露数据
            
        Returns:
            验证结果
        """
        # 1. 确定报告期
        report_start = f"{data.report_year}-01-01"
        report_end = f"{data.report_year}-12-31"
        
        # 2. 搜索新闻
        news_articles = self.data_source.search_news(
            company_name=data.company_name,
            start_date=report_start,
            end_date=report_end
        )
        
        # 3. 提取事件
        events = self.event_extractor.extract_events(
            news_articles=news_articles,
            company_name=data.company_name
        )
        
        # 4. 交叉验证
        contradictions = self.cross_validator.validate(
            disclosure=data,
            events=events
        )
        
        # 5. 计算可信度得分
        credibility_score = self.credibility_scorer.score(
            contradictions=contradictions,
            total_events=len(events)
        )
        
        # 6. 生成 ValidationResult
        findings = []
        for contradiction in contradictions:
            finding = Finding(
                severity=Severity(contradiction.severity),
                message=f"{contradiction.contradiction_type.value}: {contradiction.evidence_from_news}",
                field="credibility",
                recommendation=contradiction.recommendation,
                metadata={
                    "event_type": contradiction.event.event_type.value,
                    "event_date": contradiction.event.date,
                    "source_url": contradiction.event.source_article.url
                }
            )
            findings.append(finding)
        
        return ValidationResult(
            validator_name="news_consistency",
            dimension="credibility",
            score=credibility_score,
            findings=findings,
            metadata={
                "news_articles_found": len(news_articles),
                "events_extracted": len(events),
                "contradictions_found": len(contradictions),
                "report_period": f"{report_start} to {report_end}"
            }
        )
```

---

## 5. 集成到现有框架

### 5.1 修改 ValidationPipeline

**文件**：`cda/validation/pipeline.py`

**修改点**：
```python
# 在 __init__ 中添加 news_consistency 验证器
def __init__(self, validators: Optional[List[BaseValidator]] = None):
    if validators is None:
        validators = [
            ConsistencyValidator(),
            QuantificationValidator(),
            CompletenessValidator(),
            RiskCoverageValidator(),
            NewsConsistencyValidator()  # 新增
        ]
    self.validators = validators
```

### 5.2 修改 Scorer

**文件**：`cda/scoring/scorer.py`

**修改点**：
```python
# 添加 credibility 维度权重
DEFAULT_WEIGHTS = {
    "consistency": 0.20,      # 从 0.25 降到 0.20
    "quantification": 0.20,   # 从 0.25 降到 0.20
    "completeness": 0.20,     # 从 0.25 降到 0.20
    "risk_coverage": 0.20,    # 从 0.25 降到 0.20
    "credibility": 0.20       # 新增
}
```

### 5.3 修改 Visualizer

**文件**：`cda/output/visualizer.py`

**新增方法**：
```python
def news_timeline_chart(self, result: ScoredResult) -> go.Figure:
    """
    生成新闻事件时间线图
    
    显示：
    - 报告期内的环境事件
    - 事件类型（罚款/诉讼/事故）
    - 严重程度（颜色编码）
    """
    pass
```

---

## 6. 配置文件

**文件**：`cda/config.py`

**新增配置**：
```python
# News Validator Configuration
NEWS_VALIDATOR_CONFIG = {
    "enabled": True,
    "api_provider": "brave",  # "google" | "bing" | "brave"
    "api_key": os.getenv("NEWS_API_KEY"),
    "max_articles": 50,
    "llm_provider": "openai",
    "llm_model": "qwen-plus",
    "default_keywords": [
        "environment", "climate", "pollution", "emission",
        "fine", "penalty", "lawsuit", "violation",
        "regulation", "investigation"
    ]
}
```

---

## 7. 测试要求

### 7.1 单元测试

**文件**：`tests/test_news_validator.py`

**测试用例**：
1. `test_news_data_source_search()` - 测试新闻搜索
2. `test_event_extractor_single_article()` - 测试单篇新闻提取
3. `test_event_extractor_batch()` - 测试批量提取
4. `test_cross_validator_omission()` - 测试遗漏检测
5. `test_cross_validator_misrepresentation()` - 测试误导检测
6. `test_credibility_scorer()` - 测试评分逻辑
7. `test_news_consistency_validator_integration()` - 测试完整流程

### 7.2 集成测试

**文件**：`examples/example_news_validation.py`

**测试场景**：
```python
# 场景 1：无负面新闻（满分）
# 场景 2：有负面但已披露（高分）
# 场景 3：有负面未披露（低分）
# 场景 4：严重矛盾（极低分）
```

---

## 8. 文档要求

### 8.1 更新 README.md

**新增章节**：
```markdown
### News Consistency Validation

CDA can cross-validate disclosure reports with real-world news to detect greenwashing:

- Searches environmental/climate news during the report period
- Extracts events (fines, lawsuits, violations, regulations)
- Identifies contradictions and omissions
- Calculates credibility score (0-100)

Example:
```python
from cda.validation.news_consistency import NewsConsistencyValidator

validator = NewsConsistencyValidator(news_api_key="your_key")
result = validator.validate(disclosure_data)

print(f"Credibility Score: {result.score}/100")
for finding in result.findings:
    print(f"- {finding.message}")
```
```

### 8.2 新增文档

**文件**：`docs/news_validation.md`

**内容**：
- 功能介绍
- 数据源配置
- API Key 获取方法
- 评分逻辑详解
- 常见问题

---

## 9. 依赖更新

**文件**：`pyproject.toml`

**新增依赖**：
```toml
[tool.poetry.dependencies]
# 现有依赖...
requests = "^2.31.0"           # HTTP 请求
beautifulsoup4 = "^4.12.0"     # HTML 解析（可选）
python-dateutil = "^2.8.2"     # 日期解析
```

---

## 10. 验收标准

### 10.1 功能验收
- [ ] 能够搜索指定时间范围的新闻（至少支持 1 个 API）
- [ ] 能够从新闻中提取环境事件（准确率 >70%）
- [ ] 能够识别遗漏和误导（至少 2 种矛盾类型）
- [ ] 能够计算可信度得分（0-100）
- [ ] 能够生成 ValidationResult 对象
- [ ] 能够集成到现有 ValidationPipeline

### 10.2 性能验收
- [ ] 单份报告分析时间 <3 分钟（含新闻搜索和 LLM 提取）
- [ ] 支持批量处理（10 份报告 <30 分钟）
- [ ] API 错误时能够优雅降级（返回空结果而非崩溃）

### 10.3 代码质量验收
- [ ] 所有函数有类型注解
- [ ] 所有类有 docstring
- [ ] 单元测试覆盖率 >80%
- [ ] 通过 mypy 类型检查
- [ ] 通过 black 格式化

### 10.4 文档验收
- [ ] README.md 更新
- [ ] 新增 docs/news_validation.md
- [ ] 新增 example_news_validation.py
- [ ] 所有 API 有注释

---

## 11. 实现优先级

### Phase 1: 核心功能（必须）
1. NewsDataSource (Brave Search API)
2. EventExtractor (LLM-based)
3. CrossValidator (omission detection)
4. CredibilityScorer
5. NewsConsistencyValidator
6. 集成到 ValidationPipeline

### Phase 2: 增强功能（重要）
7. 支持多个新闻 API（Google/Bing）
8. Misrepresentation detection
9. 新闻时间线可视化
10. 单元测试

### Phase 3: 优化功能（可选）
11. 缓存机制（避免重复搜索）
12. 多语言支持
13. 自定义关键词
14. 批量处理优化

---

## 12. API Key 获取指南

### Brave Search API (推荐)
- 免费额度：2000 次/月
- 注册：https://brave.com/search/api/
- 环境变量：`BRAVE_API_KEY`

### Google News API
- 免费额度：100 次/天
- 注册：https://newsapi.org/
- 环境变量：`GOOGLE_NEWS_API_KEY`

### Bing News API
- 免费额度：1000 次/月
- 注册：https://www.microsoft.com/en-us/bing/apis/bing-news-search-api
- 环境变量：`BING_NEWS_API_KEY`

---

## 13. 示例输出

```json
{
  "validator_name": "news_consistency",
  "dimension": "credibility",
  "score": 45.0,
  "findings": [
    {
      "severity": "critical",
      "message": "omission: Company fined $5M for air pollution violations in June 2023, not mentioned in report",
      "field": "credibility",
      "recommendation": "Disclose all material environmental penalties in the Risks section",
      "metadata": {
        "event_type": "fine",
        "event_date": "2023-06-15",
        "source_url": "https://reuters.com/..."
      }
    },
    {
      "severity": "warning",
      "message": "misrepresentation: Report claims 'carbon neutral operations' but news reports coal-powered data centers",
      "field": "credibility",
      "recommendation": "Clarify scope of carbon neutrality claims and disclose Scope 2 emissions sources",
      "metadata": {
        "event_type": "investigation",
        "event_date": "2023-09-20",
        "source_url": "https://bloomberg.com/..."
      }
    }
  ],
  "metadata": {
    "news_articles_found": 23,
    "events_extracted": 5,
    "contradictions_found": 2,
    "report_period": "2023-01-01 to 2023-12-31"
  }
}
```

---

## 14. 交付清单

**代码文件**：
- [ ] `cda/validation/news_data_source.py`
- [ ] `cda/validation/event_extractor.py`
- [ ] `cda/validation/cross_validator.py`
- [ ] `cda/validation/credibility_scorer.py`
- [ ] `cda/validation/news_consistency.py`

**测试文件**：
- [ ] `tests/test_news_validator.py`
- [ ] `examples/example_news_validation.py`

**文档文件**：
- [ ] `docs/news_validation.md`
- [ ] 更新 `README.md`
- [ ] 更新 `TECHNICAL_DOCUMENTATION.md`

**配置文件**：
- [ ] 更新 `cda/config.py`
- [ ] 更新 `pyproject.toml`

---

**设计完成时间**：2026-02-17  
**预计实现时间**：5-7 天  
**设计者**：小夏  
**实现者**：Qwen Code
