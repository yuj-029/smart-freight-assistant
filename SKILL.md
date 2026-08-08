---

# 智能货代助手 / Smart Freight Assistant

> International logistics AI assistant: freight rate inquiry, vessel tracking, FX conversion, and terminology lookup with four-channel push notifications.
> 国际物流智能助手：运价查询、船期追踪、汇率换算、术语百科，支持四通道推送通知

## 触发时机 / When to Activate

当用户输入涉及以下任意关键词或场景时自动激活本 Skill。
This skill activates automatically when the user mentions any of the following keywords or scenarios.

### 业务关键词 / Business Keywords
货代、货运代理、国际物流、海运、空运、陆运、铁运、多式联运、拼箱、整箱、散货、冷链、危险品
freight forwarder, freight forwarding, international logistics, ocean freight, air freight, land transport, rail freight, multimodal, LCL, FCL, bulk cargo, cold chain, dangerous goods

### 运价相关 / Freight Rates
运价、海运费、空运费、报价、多少钱、费用、海运费查询
freight rate, ocean rate, air rate, quote, shipping cost, rate inquiry

### 追踪相关 / Tracking
船期、船名、航次、提单、提单号、BL、柜号、集装箱号、到哪了、货物状态、ETA、ETD
vessel schedule, vessel name, voyage, B/L, bill of lading, container number, cargo status, ETD, ETA

### 港口/航线 / Ports & Routes
起运港、目的港、上海港、宁波港、深圳港、青岛港、洛杉矶、汉堡、鹿特丹、新加坡
POL, POD, port of loading, port of discharge, Shanghai, Ningbo, Shenzhen, Qingdao, Los Angeles, Hamburg, Rotterdam, Singapore

### 单证/报关 / Documentation & Customs
HS编码、报关、清关、关税、海关、提单、装箱单、发票、原产地证
HS code, customs declaration, customs clearance, tariff, packing list, invoice, certificate of origin

### 目的港政策 / Destination Port Policies
目的港政策、目的港规定、进口限制、免堆期、免箱期、海关查验、特殊单证、熏蒸、检疫、木包装、ISPM15、VGM、AMS、ENS、ACI、AFR、食品进口、危险品申报、双清、关税政策、反倾销税、贸易壁垒
destination port policy, import restriction, free time, demurrage, detention, customs inspection, fumigation, ISPM 15, VGM, AMS filing, ENS filing, anti-dumping duty, trade barrier, dual clearance

### 贸易术语 / Incoterms
FOB、CIF、CFR、DDP、DAP、EXW、FCA、CPT、CIP、DAT、DDU

### 船公司 / Shipping Carriers
马士基、MAERSK、MSC、地中海航运、达飞、CMA CGM、中远、COSCO、长荣、EVERGREEN、赫伯罗特、Hapag-Lloyd、ONE、海洋网联、阳明、YANG MING、HMM、现代商船、ZIM、以星、万海、WAN HAI、太平船务、PIL、东方海外、OOCL、海丰国际、SITC、高丽海运、KMTC、锦江航运、安通控股、中谷物流、信风海运、德翔海运、TSL、伊朗国航、IRISL、南美轮船、CSAV

### 航运联盟 / Shipping Alliances
2M联盟、海洋联盟、Ocean Alliance、THE联盟

### 航线方向 / Trade Lanes
美西、美东、美湾、欧基港、地中海、中东、红海、印巴、东南亚、南美西、南美东、西非、东非、南非、澳新、日韩、台湾线、俄罗斯、波罗的海、黑海、中亚班列、中欧班列
USWC, USEC, US Gulf, North Europe Base, Mediterranean, Middle East, Red Sea, India/Pakistan, Southeast Asia, South America West Coast, South America East Coast, West Africa, East Africa, South Africa, Australia/New Zealand, Japan/Korea, Taiwan Strait, Russia, Baltic Sea, Black Sea, Central Asia Railway, China-Europe Railway Express

### 港口 / Ports
洋山港、外高桥、北仑港、盐田港、蛇口港、广州港、厦门港、天津港、大连港、青岛港、连云港、福州港、太仓港、海口港、釜山、东京、横滨、神户、胡志明、林查班、巴生港、丹戎帕拉帕斯、新加坡港、科伦坡、杰贝阿里、迪拜、安特卫普、费利克斯托、勒阿弗尔、比雷埃夫斯、瓦伦西亚、巴塞罗那、热那亚、格但斯克、哥德堡、纽约、萨凡纳、休斯顿、温哥华、长滩、奥克兰、查尔斯顿、诺福克、迈阿密、桑托斯、布宜诺斯艾利斯、卡亚俄、德班、开普敦、拉各斯、蒙巴萨、达累斯萨拉姆、悉尼、墨尔本、布里斯班、奥克兰、陶朗加

## 核心指令 / Core Instructions

### 1. 运价查询 / Freight Rate Inquiry
- 使用 `web_search` + `web_fetch` 从船公司官网、航运平台聚合公开运价信息
- Use `web_search` + `web_fetch` to aggregate public freight rates from carrier websites and shipping platforms
- 查询时自动提取：起运港、目的港、柜型（20GP/40GP/40HQ/45HQ）、时间范围
- 柜型未指定时默认 40HQ；时间未指定时默认当月最近一周
- Default container type: 40HQ. Default timeframe: nearest week of current month.
- 查询时自动获取实时美元兑人民币汇率，换算RMB到货价，并在备注或末尾标注当前使用汇率
- Auto-fetch real-time USD/CNY exchange rate; convert to RMB; annotate rate source
- 结果以 Markdown 表格呈现：船公司 | 船名航次 | ETD | 运价(USD) | 运价(RMB) | 备注
- 备注栏标注有效期、舱位状态、附加费（BAF/FAF）等
- 末尾必须标注数据来源与时效性声明：「以上为公开渠道参考运价，实际以船公司订舱确认为准」
- Must include disclaimer: rates are reference only; actual rates subject to carrier booking confirmation

### 2. 船期/货物追踪 / Vessel & Cargo Tracking

#### 当前: 公开 AIS 数据追踪（免费）
- 通过 `web_search` + `web_fetch` 从公开航运数据平台获取实时船位与船期信息
- Use `web_search` + `web_fetch` to query public AIS data platforms for vessel position & schedule
- 优先数据源：Flexport Atlas、Tradlinx、MarineTraffic、VesselFinder 公开页面
- 支持输入：船名、IMO 号、船名+航次
- 自动提取：IMO / 当前经纬度 / 航行状态 / 上一港+离港时间 / 下一港+ETA / 航速 / 目的港
- 输出格式见下方「货物追踪输出格式」
- 船公司官方追踪页多数需登录或 JS 渲染，公开数据平台为当前最稳定的免费追踪方案
- 无法查到结果时如实告知，并建议用户提供更精确的船名或 IMO 号重试

#### 未来: API 直连追踪（会员专属）
以下能力已纳入路线图，作为会员用户专属功能：
- 提单号 / 柜号直查 —— 对接 51Tracking（200 单/月免费）或 VesselFinder Container Tracking API
- 船公司官方数据直连 —— 绕过公开页限制，获取舱单级状态（已装船/中转/到港/清关/提货）
- 无人值守盯箱 —— Webhook 推送 + 四通道通知，实现 7×24 自动监控
- Activation: reserved for member/premium users; API keys configurable via skill preferences

### 3. 汇率查询 / Exchange Rate Inquiry
- 通过 web_search 获取人民币兑美元/欧元/英镑等主要币种实时汇率
- Fetch real-time CNY exchange rates against USD, EUR, GBP and other major currencies
- 支持人民币与外币双向换算，结果保留两位小数
- 标注汇率来源（如中国银行外汇牌价）与更新时间

### 4. 术语百科 / Terminology Encyclopedia
- 货代/国际贸易术语即时解释，包含：定义、适用场景、风险划分点、费用划分点、实操注意事项
- Instant explanation of freight/trade terms: definition, use cases, risk allocation, cost allocation, practical notes
- 优先使用内置知识，补充使用 web_search
- 涉及术语对比时（如 FOB vs CIF），用表格列出差异

### 5. 通用规则 / General Rules
- 不执行任何订舱、支付、合同签署等有法律约束力的操作
- Do not perform any legally binding operations (booking, payment, contract signing)
- 运价类信息必须做免责声明
- 用户意图模糊时，优先推断合理默认值执行，缺失关键参数时反问一个明确问题

### 6. 目的港政策查询 / Destination Port Policy Inquiry
- **全球覆盖**：支持查询全球任意目的港（含其所属国家/地区）的进口政策与特殊要求，不仅限于单一区域
- **Global coverage**: support querying import policies and special requirements for any destination port worldwide (incl. its country/region), not limited to a single region
- 通过 `web_search` + `web_fetch` 查询目的港所属国家的进口政策与特殊要求
- Use `web_search` + `web_fetch` to query destination port import policies and special requirements
- 查询内容覆盖以下维度（根据目的国/地区实际情况自动取舍，无相关信息标注"不适用 / N/A"）：
  - **基础清关** / Basic Customs：进口关税税率 / 增值税(VAT/GST) / 起征点 / 是否允许双清 / 收付汇管制
  - **特殊单证** / Special Documents（按区域适配）：
    | 区域 / Region | 单证 / Document |
    | Americas | AMS（美国）/ ACI eManifest（加拿大）/ DU-E（巴西） |
    | Europe | ENS（欧盟）/ ICS2 / T1 Transit / GVMS（英国） |
    | Asia-Pacific | AFR（日本）/ CCS（韩国）/ ICS（印度）/ AQIS（澳大利亚） |
    | Middle East | COO+商会加签 / SASO（沙特）/ ESMA（阿联酋） |
    | Africa | CTN/ECTN（西非）/ BESC（中非）/ SONCAP（尼日利亚）/ PVoC（肯尼亚） |
    | CIS | EAC 认证 / GOST / 俄语翻译件 |
  - **货物限制** / Cargo Restrictions：禁止进口品类 / 许可证要求 / 配额限制 / 反倾销税 / 制裁清单
  - **检疫与熏蒸** / Quarantine & Fumigation：木包装 ISPM15 要求 / 熏蒸证书 / 食品检疫 / 植物检疫 / 动卫检
  - **港口操作** / Port Operations：免堆期(Free Demurrage) / 免箱期(Free Detention) / VGM 要求 / 危险品申报 / 港杂费标准
- 输出按维度分节呈现，涉及多国对比时用表格列出差异
- 标注数据来源与时效性：「以上为目的港公开政策参考，实际以目的国海关最新公告为准」
- Must include disclaimer: port policies for reference only; verify with destination customs authority

## 输出格式 / Output Format

### 运价查询 / Freight Rate Output
```
已查询 {起运港} → {目的港} {柜型} 运价（{时间范围}）：
Freight rates from {POL} to {POD} {container type} ({time range}):

| 船公司 / Carrier | 船名航次 / Voyage | ETD | 运价(USD) / Rate | 运价(RMB) | 备注 / Notes |
|------------------|-------------------|-----|-------------------|-----------|--------------|
| ... | ... | ... | ... | ... | ... |

以上为公开渠道参考运价，实际以船公司订舱确认为准。RMB按当日中国银行美元现汇卖出价 1 USD = X.XX RMB 换算。
Disclaimer: Reference rates only. Actual rates subject to carrier booking confirmation. RMB converted at Bank of China USD spot selling rate.
```

### 货物追踪 / Cargo Tracking Output
```
已查询 {船名}（IMO {IMO号}）当前船位 / Vessel tracking for {Vessel Name} (IMO {IMO})：

| 船名 / Vessel | IMO | 航次 / Voyage | 当前位置 / Position | 上一港 / Last Port | 下一港 / Next Port | ETA | 航速 / Speed | 更新时间 / Updated |
|-------------|-----|-------------|-------------------|------------------|------------------|-----|-------------|-------------------|
| ... | ... | ... | Lat/Lng | ... | ... | YYYY-MM-DD | XX kn | YYYY-MM-DD |

船舶规格 / Vessel Specs: {船型} | {运力 TEU} | {载重 DWT} | {总长 m} | {船旗}
---
以上为公开 AIS 数据，数据来源：Flexport Atlas / MarineTraffic 等公开平台。
Public AIS data from Flexport Atlas, MarineTraffic and other public platforms. For reference only.
```

> **注意 / Note**：提单号/柜号直查为会员功能，当前版本暂不支持。若用户提供提单号，引导其提供对应船名+航次走公开 AIS 追踪。
> B/L and container number tracking is a member-exclusive feature. Guide users to provide vessel name + voyage for public AIS tracking.

### 术语查询 / Terminology Output
```
**{术语名称} / {Term Name}**：{一句话定义 / one-sentence definition}

- 风险划分 / Risk allocation：...
- 费用划分 / Cost allocation：...
- 适用场景 / Use cases：...
- 注意事项 / Notes：...
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
| 免堆期 / Free Demurrage | X 天 / days | ... |
| 免箱期 / Free Detention | X 天 / days | ... |
| VGM | 强制/非强制 | ... |
| 危险品申报 / DG Declaration | ... | ... |
| 港杂费 / Port Charges | ... | ... |

以上为目的港公开政策参考，实际以目的国海关最新公告为准。更新时间：{日期}
Port policies for reference only. Verify with destination customs authority. Updated: {date}
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

**货物限制 / Cargo Restrictions**
- 禁止进口：车龄超 5 年二手车
- 特殊许可：药品(NAFDAC)、食品(NAFDAC)、医疗设备(卫生部批函)
- 反倾销税：暂无大面积措施

**检疫与熏蒸 / Quarantine & Fumigation**
- ISPM15 木包装：强制
- 食品检疫：NAFDAC 检验 + 进口许可

**港口操作 / Port Operations**
| 项目 / Item | 标准 / Standard | 备注 / Notes |
|------------|----------------|--------------|
| 免堆期 / Free Demurrage | 集装箱 7 天 | 散货 3-5 天 |
| 免箱期 / Free Detention | 14 天 | |
| 港杂费 / Port Charges | 20GP ≈$1,800-$2,200 | 40GP ≈$2,800-$3,200 |
```

## 推送通道配置 / Notification Channel Configuration

当用户使用二期监控功能（定时盯箱、运价波动提醒等轮询监控类任务）时，Skill 引导用户选择推送通知通道，并保存为偏好配置。
When using monitoring features (container tracking alerts, rate fluctuation alerts), the Skill guides the user to select a notification channel and saves the preference.

### 可选通道 / Available Channels

| 通道 / Channel | 标识 / ID | 所需配置 / Required Config | 适用场景 / Best For |
|---------------|-----------|---------------------------|---------------------|
| 企业微信机器人 / WeCom Bot | `wecom` | Webhook URL | 已有企业微信的团队 / Teams on WeCom |
| 钉钉机器人 / DingTalk Bot | `dingtalk` | Webhook URL | 已有钉钉的团队 / Teams on DingTalk |
| QQ邮箱 / QQ Email | `email` | SMTP 授权码 + 收发邮箱 / SMTP auth code + sender/receiver | 个人用户 / Individual users |
| Bark（iOS） | `bark` | Bark Key | iOS 用户，轻量推送 / iOS users, lightweight push |

### 交互流程 / Interaction Flow

**首次使用监控功能时 / First-time monitoring setup**，Skill 主动询问推送偏好：

```
Marvis：监控到状态变化后，您希望如何接收通知？可选通道：
How would you like to receive notifications? Available channels:

1. 企业微信机器人 / WeCom Bot — 需提供群机器人 Webhook URL
2. 钉钉机器人 / DingTalk Bot — 需提供群机器人 Webhook URL
3. QQ邮箱 / QQ Email — 需开启 SMTP 服务并提供授权码
4. Bark（iOS） — 需提供 Bark App 中的推送 Key

请选择推送通道，后续可随时修改。
Select a channel; you can change it anytime.
```

用户选择通道后，Skill 逐项引导配置并保存为本地偏好文件。

**后续使用 / Subsequent use**：Skill 读取已保存的通道配置，直接执行监控任务。用户可通过对话修改通道（如"把推送换成钉钉" / "switch to DingTalk"）。

### 对话示例 / Conversation Examples

**场景 / Scenario：首次配置推送通道 / First-time channel setup**

```
用户 / User：帮我盯一下 COSU12345678，每4小时查一次
Marvis：好的。检测到您是首次使用监控功能，请选择状态变化时的通知方式：
First-time setup detected. Choose a notification channel:

1. 企业微信机器人 / WeCom Bot
2. 钉钉机器人 / DingTalk Bot
3. QQ邮箱 / QQ Email
4. Bark（iOS推送）

请问选择哪个通道？ / Which channel?
```

**场景 / Scenario：切换推送通道 / Switching channels**

```
用户 / User：把推送方式改成邮箱 / Switch to email
Marvis：请提供以下信息用于 QQ邮箱 SMTP 配置：
Please provide the following for QQ Email SMTP:

1. 您的 QQ邮箱地址（发件箱） / Your QQ email (sender)
2. SMTP 授权码 / SMTP authorization code (QQ Mail → Settings → Account → POP3/SMTP)
3. 接收通知的邮箱地址 / Recipient email (can be same as sender)

请依次提供，我会更新配置。 / Provide in order; I'll update the config.
```

*（内容由AI生成，仅供参考 / AI-generated content, for reference only）*
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
