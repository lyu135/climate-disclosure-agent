# 测试数据获取指南

## 📥 公开 ESG 报告下载链接

### 推荐测试报告（都是公开可下载的）：

#### 1. Microsoft Environmental Sustainability Report
- **URL**: https://query.prod.cms.rt.microsoft.com/cms/api/am/binary/RW15mgm
- **年份**: 2023
- **大小**: ~5MB
- **特点**: 数据完整，TCFD框架对齐，适合测试

#### 2. Unilever Annual Report and Accounts
- **URL**: https://www.unilever.com/files/92ui5egz/production/16cb778e4d31b81509b8e3c4f7d3e1c8b5e8c5e0.pdf
- **年份**: 2023
- **特点**: 包含详细的气候披露

#### 3. Nestlé Creating Shared Value Report
- **URL**: https://www.nestle.com/sites/default/files/2024-03/creating-shared-value-report-2023-en.pdf
- **年份**: 2023
- **特点**: 完整的 Scope 1/2/3 排放数据

#### 4. Apple Environmental Progress Report
- **URL**: https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2023.pdf
- **年份**: 2023
- **特点**: 科学减排目标，SBTi 认证

#### 5. IKEA Sustainability Report
- **URL**: https://www.ikea.com/global/en/images/ikea-sustainability-report-fy23_8c9e0e0e.pdf
- **年份**: 2023
- **特点**: 供应链气候风险披露

---

## 🚀 快速下载命令

```bash
cd /root/.openclaw/workspace/climate-disclosure-agent
mkdir -p test_data

# 下载 Microsoft 报告
wget -O test_data/microsoft_esg_2023.pdf "https://query.prod.cms.rt.microsoft.com/cms/api/am/binary/RW15mgm"

# 下载 Apple 报告
wget -O test_data/apple_env_2023.pdf "https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2023.pdf"

# 下载 IKEA 报告
wget -O test_data/ikea_sustainability_2023.pdf "https://www.ikea.com/global/en/images/ikea-sustainability-report-fy23_8c9e0e0e.pdf"
```

---

## 📊 外部验证数据（可选）

### SBTi 数据
- **下载页面**: https://sciencebasedtargets.org/companies-taking-action
- **格式**: CSV
- **包含**: 2000+ 家企业的科学减排目标承诺

### CDP 数据
- **下载页面**: https://www.cdp.net/en/data
- **格式**: CSV/Excel
- **需要**: 免费注册账号

---

## 🧪 测试建议

### 最小测试集（推荐）
1. Microsoft 报告（数据完整）
2. Apple 报告（有 SBTi 认证，可测试交叉验证）

### 完整测试集
1. Microsoft
2. Apple
3. IKEA
（3 份报告可以做多公司对比，生成漂亮的雷达图）

---

## ⚠️ 注意事项

1. **PDF 大小**: 建议选择 5-20MB 的报告（太大会影响 LLM 提取速度）
2. **语言**: ���先选择英文报告（LLM 提取效果更好）
3. **年份**: 2022-2024 的报告最佳（框架更新）
4. **框架**: 优先选择明确标注 TCFD/SASB 的报告

---

生成时间: 2026-02-17
