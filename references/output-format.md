# 输出格式 / Output Format

> 本文件为 `SKILL.md`「输出格式」的外置模板，供输出时按对应模块规则选用。占位符 `{...}` 按实际查询结果填充；模板未覆盖字段按「通用规则」留空标注，禁止编造。


### 运价查询 / Freight Rate Output
```
已查询 {起运港} → {目的港} {柜型} 运价（{时间范围}） [数据完整度：⭐⭐⭐/⭐⭐/⭐]：
Freight rates from {POL} to {POD} {container type} ({time range}) [Data completeness: ⭐⭐⭐/⭐⭐/⭐]:

| 船公司 / Carrier | 船名航次 / Voyage | ETD | 运价(USD) / Rate | 运价(RMB) | 可订状态 / Availability | 备注 / Notes |
|------------------|-------------------|-----|-------------------|-----------|------------------------|--------------|
| ... | ... | ... | ... | ... | 可订/紧张 / Available/Tight | 有效期至{日期}，费用口径：{说明} |

RMB换算：付汇用卖出价 1 USD = X.XX RMB，收汇用买入价 1 USD = X.XX RMB
汇率数据截至 {YYYY-MM-DD}（{周X}）{若周末/节假日加：⚠ 周末不更新}
费用口径：{含基础海运费，不含 BAF/FAF/OTHC / 费用口径未明确}
以上为公开渠道参考运价，实际以船公司订舱确认为准。
Disclaimer: Reference rates only. Actual rates subject to carrier booking confirmation.
```

### 货物追踪 / Cargo Tracking Output
```
已查询 {船名}（IMO {IMO号}）当前船位 / Vessel tracking for {Vessel Name} (IMO {IMO})：

| 船名 / Vessel | IMO | 当前位置 / Position | 上一港 / Last Port | 下一港 / Next Port | ETA (UTC / 当地) | 航速 / Speed | AIS更新 / Updated | 时效 / Freshness |
|-------------|-----|-------------------|------------------|------------------|-------------------|-------------|------------------|------------------|
| ... | ... | ... | ... | ... | YYYY-MM-DD HH:MM UTC（当地时间 HH:MM） | XX kn | X分钟/小时前 | [实时]/[稍旧]/[滞后]/[严重滞后] |

船舶规格 / Vessel Specs: {船型} | {运力 TEU} | {载重 DWT} | {总长 m} | {船旗}
***
数据来源 / Source: {VesselFinder / MarineTraffic / MyShipTracking}
{若AIS超过6小时未更新：⚠ AIS数据已X小时未更新，船位可能有偏差}
以上为公开 AIS 数据，仅供参考。
Public AIS data, for reference only.
```

### 术语查询 / Terminology Output
```
**{术语名称} / {Term Name}**：{一句话定义 / one-sentence definition}
适用 Incoterms 版本 / Applicable Incoterms: Incoterms 2020
{若为多义词：
海运含义 / Maritime: ...
空运含义 / Air freight: ...
报关含义 / Customs: ...}

- 风险划分 / Risk allocation：...
- 费用划分 / Cost allocation：...
- 适用场景 / Use cases：...
- 注意事项 / Notes：...
- {若为术语对比} 费用测算示例 / Cost example：...

⚠ {若引用旧版本}/部分资料仍用 Incoterms 2010 表述，注意区分。
```
*（内容由AI生成，仅供参考 / AI-generated content, for reference only）*

### 目的港政策查询 / Destination Port Policy Output
```
已查询 {目的港}（{目的国/地区}）进口政策 / Import policies for {Port of Discharge} ({Country/Region})：

**基础清关 / Basic Customs**
| 项目 / Item | 详情 / Details |
|------------|---------------|
| 进口关税 / Import Duty | ... |
| 增值税(VAT/GST) | ... |
| 起征点 / De Minimis | ... |
| 双清 / Dual Clearance | 支持/不支持 / Yes/No |
| 收付汇管制 / FX Control | ... |

**特殊单证 / Special Documents**（{区域}适用 / applicable to {Region}）
| 单证 / Document | 要求 / Requirement | 说明 / Notes |
|----------------|-------------------|--------------|
| ... | ... | ... |
_其他区域单证标注"不适用 / N/A"_

**货物限制 / Cargo Restrictions**
- 禁止进口 / Prohibited：...
- 许可证要求 / License Required：...
- 反倾销税 / Anti-dumping：...
- 制裁清单 / Sanctions：...

**检疫与熏蒸 / Quarantine & Fumigation**
- ISPM15 木包装：是/否 / Required: Yes/No
- 熏蒸证书 / Fumigation Cert：...
- 食品检疫 / Food Inspection：...
- 动卫检 / Animal & Plant Quarantine：...

**港口操作 / Port Operations**
| 项目 / Item | 标准 / Standard | 备注 / Notes |
|------------|----------------|--------------|
| 免堆期 / Free Demurrage | X 天 / days | {若多源冲突：来源A称X天，来源B称Y天} |
| 免箱期 / Free Detention | X 天 / days | {船公司可能提供差异化政策} |

**超期费率阶梯 / Demurrage Tiered Rates**
| 时段 / Period | 费率 / Rate | 单位 / Unit |
|--------------|------------|-------------|
| D1–D{X}（免费期 / Free） | $0 | — |
| D{X+1}–D{Y} | ${A} | /TEU/天 |
| D{Y+1} 起 | ${B} | /TEU/天 |

以上为目的港公开政策参考（数据收录于 {YYYY-MM-DD}），实际以目的国海关最新公告为准。部分船公司可能提供差异化免堆/免箱期。
Port policies for reference only (data collected on {YYYY-MM-DD}). Verify with destination customs authority. Some carriers may offer differentiated free time.
```

*示例 / Example — 拉各斯港（尼日利亚）：*
```
已查询 拉各斯港 / Lagos Port（尼日利亚）进口政策：

**基础清关 / Basic Customs**
| 项目 / Item | 详情 / Details |
|------------|---------------|
| 进口关税 / Import Duty | 工业品 5%-20%，农产品 10%-50%，按 CIF 完税价格计征 |
| 增值税(VAT) | 7.5%，按 CIF + 关税 + 杂费复合计税 |
| 起征点 / De Minimis | 无统一起征点 |
| 双清 / Dual Clearance | 支持，须持牌清关代理 |
| 收付汇管制 / FX Control | 严格外汇管制，授权经销商购汇，建议提前 30 天申请 |

**特殊单证 / Special Documents**（非洲区域适用）
| 单证 / Document | 要求 / Requirement | 说明 / Notes |
|----------------|-------------------|--------------|
| SONCAP | 强制，装运前取得 | PC 产品证书 + SC 清关证书，SC 单批次有效 |
| FORM M | 强制，装运前 | 进口商通过授权银行申请，所有 SONCAP 前置文件 |

**港口操作 / Port Operations**
| 项目 / Item | 标准 / Standard | 备注 / Notes |
|------------|----------------|--------------|
| 免堆期 / Free Demurrage | 集装箱 7 天 | 散货 3-5 天 |
| 免箱期 / Free Detention | 14 天 | |

**超期费率阶梯 / Demurrage Tiered Rates**
| 时段 / Period | 费率 / Rate | 单位 / Unit |
|--------------|------------|-------------|
| D1–D7（免费期 / Free） | $0 | — |
| D8–D14 | 按船公司约定 | 需具体确认 |
| D15+ | 按船公司约定 | 需具体确认 |

以上为目的港公开政策参考（数据收录于 2026-08-08），实际以目的国海关最新公告为准。部分船公司可能提供差异化免堆/免箱期。
```
