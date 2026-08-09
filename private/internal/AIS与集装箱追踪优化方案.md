---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 5cb1b25772f6b0aafa9bcb1a8e5ab88d_f785ce4193cc11f1bafa525400287e28
    ReservedCode1: xvFpq3ZahudjkstY8trTng07CBhohmToNaZChUR5sgnNFULZvq9F+ZJvy2rtBSzi5jCsnBcj/t2Jmrd0mGulOj+QuVcY0DNJubY99r2k0gfxBmJa+2H0Xp6fjE0Zoduxf0XKvGzXNAv2I3YNmHidW8zzHf9PfUSH6Qk52YtBtx4VjnN4SCQvpz5kFAk=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 5cb1b25772f6b0aafa9bcb1a8e5ab88d_f785ce4193cc11f1bafa525400287e28
    ReservedCode2: xvFpq3ZahudjkstY8trTng07CBhohmToNaZChUR5sgnNFULZvq9F+ZJvy2rtBSzi5jCsnBcj/t2Jmrd0mGulOj+QuVcY0DNJubY99r2k0gfxBmJa+2H0Xp6fjE0Zoduxf0XKvGzXNAv2I3YNmHidW8zzHf9PfUSH6Qk52YtBtx4VjnN4SCQvpz5kFAk=
---



# AIS 船位追踪 & 集装箱追踪 — 优化方案

> 撰于 2026-08-09 | 版本 v1.0  
> 覆盖模块: scrapers/tracking.py / poller.py

---

## 一、当前方案一览

| 维度 | AIS 船位追踪 | 集装箱追踪 |
|------|-------------|-----------|
| **数据源** | web_search（MarineTraffic / VesselFinder / 船讯网 公开页面） | web_search（51tracking / 百运网 / 船公司官网 公开页面） |
| **查询流程** | build_vessel_search_queries → Agent web_search → parse_web_search_result → cache_vessel_position | build_container_search_queries → Agent web_search → parse_container_search_result → cache_container_status |
| **刷新机制** | poller.py 定时触发，缓存命中直接使用，miss 输出 search_required 指令 | 同上 |
| **延迟** | 通常落后实际 4–24h（取决于公开页面更新频率） | 通常落后实际 2–12h |
| **成本** | ¥0（纯 web_search） | ¥0（纯 web_search） |
| **覆盖** | 依赖搜索命中率，IMO 号未知时召回质量下降 | 依赖 51tracking/百运网收录范围，非热门线路可能查不到 |

---

## 二、AIS 船位追踪 — 升级路线

### 2.1 当前方案（web_search）

**优点**
- 零成本，无 API Key 管理负担
- 船名 + IMO 双关键词覆盖主流船舶

**缺点**
- 延时不可控：公开页更新频率不统一，高峰时段可能 24h+
- 结构化提取依赖正则脆弱性：MarineTraffic/VesselFinder 页面改版导致字段提取失败
- 无历史轨迹，无法回溯航程
- 无批量查询能力，一个船名一次搜索

### 2.2 升级候选

| 方案 | 价格 | 延迟 | 船位精度 | 轨迹回放 | 批量查询 | 适用阶段 |
|------|------|------|----------|----------|----------|----------|
| **Datalastic** | €99/月 (2000 API calls) | ≤ 1h | < 0.1 海里 | ✔ | ✔ | 小型货代 / 单点试用 |
| **船讯网 (shipxy.com)** | ¥300–800/月 | ≤ 30min | < 0.05 海里 | ✔ | ✔ | 国内货代首选，中文友好 |
| **Kpler** | $2000+/月 | ≤ 5min | < 0.01 海里 | ✔（全球 14 天） | ✔ | 中大型货代 / 多船队 |
| **VesselFinder API** | $99–299/月 | ≤ 3h | < 0.5 海里 | 有限 | ✔ | 对标 Datalastic 中价位 |
| **Spire Maritime (卫星 AIS)** | $500+/月 | ≤ 1h | < 0.01 海里 | ✔（全球） | ✔ | 远洋盲区覆盖最强 |

**建议升级路径**：web_search → **船讯网 ¥300/月**（国内货代最优性价比）→ Kpler（业务量 >50 船时）

---

## 三、集装箱追踪 — 升级路线

### 3.1 当前方案（web_search 渠道）

**优点**
- 零成本，无接入门槛
- 多渠道兜底：51tracking + 百运网 + 船公司官网 + 聚合站

**缺点**
- 搜索命中不稳定：小众船公司 / 冷门航线搜不到
- 事件时间线解析依赖页面格式，51tracking 页面改版即失效
- 无推送/回调，依赖定时轮询
- 无批量：一个 B/L 号一次搜索

### 3.2 升级候选

| 方案 | 价格 | 免费额度 | 延迟 | 推送回调 | 批量查询 | 适用阶段 |
|------|------|----------|------|----------|----------|----------|
| **51Tracking API** | ¥239/月 (5000单) | 200单/月 | ≤ 30min | ✔ webhook | ✔ | 月度 200–5000 单 |
| **Ship24** | €49/月 (500单) | 10单/月 | ≤ 1h | ✔ webhook | ✔ | 月度 10–500 单 |
| **Traqo** | $150/月 (无限) | 无 | ≤ 15min | ✔ webhook + Slack/Teams | ✔ | 中型货代 1000+ 单/月 |
| **Terminal49** | $200+/月 | 视合同 | ≤ 10min | ✔ webhook | ✔ | 北美线路专精 |
| **Project44** | $1000+/月 | 无 | ≤ 5min | ✔ 企业级 | ✔ | 大型货代 / 多式联运 |

**建议升级路径**：web_search → **51Tracking ¥239/月**（月查询量 200–5000 单的甜蜜点）→ Traqo（月超 5000 单或需要 Slack 集成时）

---

## 四、决策矩阵：量 / 成本 / 延迟

### AIS 船位

| 月查询次数 | 推荐方案 | 月成本 | 单次成本 | 延迟 |
|-----------|---------|--------|---------|------|
| ≤ 10 次 | web_search（当前） | ¥0 | ¥0 | 4–24h |
| 10–50 次 | 船讯网 ¥300/月 | ¥300 | ¥6–30 | ≤ 30min |
| 50–200 次 | Datalastic €99/月 | ≈ ¥800 | ¥4–16 | ≤ 1h |
| 200+ 次 | Kpler | ¥16000+ | ¥80+ | ≤ 5min |

### 集装箱追踪

| 月查询次数 | 推荐方案 | 月成本 | 单次成本 | 延迟 |
|-----------|---------|--------|---------|------|
| ≤ 10 次 | web_search（当前） | ¥0 | ¥0 | 2–12h |
| 10–200 次 | Ship24 €49/月 | ≈ ¥400 | ¥2–40 | ≤ 1h |
| 200–5000 次 | **51Tracking ¥239/月** | ¥239 | ¥0.05–1.2 | ≤ 30min |
| 5000+ 次 | Traqo $150/月 | ≈ ¥1200 | ¥0.24 | ≤ 15min |

---

## 五、建议切换阈值

| 场景 | 切换条件 | 目标方案 |
|------|---------|---------|
| **AIS** — 用户主动查询频率 > 10 次/周 | 切换 → 船讯网 ¥300/月 | AIS 延迟从 24h → 30min |
| **AIS** — 月活跃监控船舶 ≥ 5 艘 | 切换 → Datalastic | 支持批量轮询 + 历史轨迹 |
| **集装箱** — 月查询量突破 200 单 | 切换 → 51Tracking ¥239/月 | 延迟 30min + webhook 主动推送 |
| **集装箱** — 用户抱怨搜索命中率低 | 立即切换 → Ship24 / 51Tracking | 消除"搜不到"体验问题 |
| **双链路** — 商业用户接入 ≥ 3 家 | 整体切 Kpler + 51Tracking | 月成本 ¥3000 内，全链路 ≤ 30min |

---

## 六、实施计划

| 阶段 | 时间 | 动作 | 产出 |
|------|------|------|------|
| **Phase 0**（当前） | 已完成 | web_search 管道全链路打通 | build/parse/get 三函数就绪 |
| **Phase 1** — 容器化 | 2026.09 | 接入 Ship24 免费层（10单/月）验证 API 调用链路 | tracking.py 新增 `source="ship24"` 分支 |
| **Phase 2** — 付费切换 | 2026.10 | 用户量突破阈值后切 51Tracking + 船讯网 | API Key 配置 → .env，poller.py 全自动闭环 |
| **Phase 3** — 企业级 | 2027.Q1 | Kpler + Traqo / Project44 | 多船队 + 多式联运 + 实时看板 |

---

## 七、代码影响评估

| 涉及文件 | 改动内容 | 风险 |
|---------|---------|------|
| `scrapers/tracking.py` | 新增 `source` 参数分支（ship24 / 51tracking / datalastic 等） | 低：纯增量，不改现有接口 |
| `poller.py` | `poll_all()` 中 `source` 切换逻辑 + API 调用 | 低：仅改数据获取路径 |
| `.env.template` | 新增 `SHIP24_API_KEY` / `TRACKING51_API_KEY` / `SHIPXY_API_KEY` | 低：模板只增不删 |
| `usage_counter.py` | 可能需要区分 API 调用次数/免费额度 | 中：涉及计费逻辑 |

---

*文档结束。后续各阶段改造按 SKILL.md §7 盯箱/追踪模块定义的触发词与回复模板对齐。*
*（内容由AI生成，仅供参考）*

---

## 八、独立部署与多端推送方案

### 背景

当前盯箱提醒依赖 Marvis 的 web_search 工具和 create_scheduled_task。独立部署后，Marvis 仅需替换为：Windows 任务计划器（调度）+ requests 库（搜索）+ notify.py（推送）。

### 独立架构

```
Windows 任务计划器（免费，每天 9:00 / 每 N 小时）
    │
    ▼
poller.py → tracking.py → alert_dispatcher → notify.py
    │           │               │                 │
    │      _execute_search()   7 种告警         四通道
    │      替换 web_search      类型            推送
    ▼
本地 JSON 缓存
```

### 唯一改动点

`tracking.py` 新增 `_execute_search(query)` 函数，替换 Marvis 的 web_search：

- 方案A：`requests` + Google Custom Search API（免费 100 次/天）
- 方案B：`requests` 直接抓船公司官网 tracking 页 + AIS 公开站
- 方案C：51Tracking API（¥239/月，10000 额度）

其余代码零改动。

### 推送通道对比

| 通道 | 手机端 | 电脑端 | 费用 | 配置难度 |
|------|:---:|:---:|------|:---:|
| 企业微信 Webhook | ✅ | ✅ | 免费 | 低 |
| 钉钉机器人 | ✅ | ✅ | 免费 | 低 |
| Bark | iOS | — | 免费 | 低 |
| QQ邮箱 | ✅ | ✅ | 免费 | 低 |
| WxPusher | ✅ 微信 | — | 免费 | 中 |
| Telegram Bot | ✅ | ✅ | 免费 | 低 |
| ntfy | ✅ | ✅ | 免费/自建 | 低 |

### 推荐组合

| 方案 | 调度 | 数据 | 推送 | 月费 | 适用 |
|------|------|------|------|:---:|------|
| 极简 | 任务计划器 | requests 公开页 | 企微 Webhook | ¥0 | 当前阶段首选 |
| 强提醒 | 任务计划器 | 同上 | Bark + 企微 | ¥0 | iOS 用户 |
| 专业 | 任务计划器/cron | 51Tracking API | 钉钉 + Bark | ¥239 | 量大了切 |

### 落地步骤

1. 获取推送通道凭据（企微机器人 Webhook URL / Bark Key）
2. 配置 notify.py 环境变量
3. 在 tracking.py 实现 `_execute_search`
4. 创建 Windows 任务计划器条目，定时执行 `python poller.py`
5. 跑一次验证全链路
*（内容由AI生成，仅供参考）*
