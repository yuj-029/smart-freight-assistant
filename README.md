# 智能货代助手 · Smart Freight Assistant

> AI 驱动的国际物流助手 — 运价查询、船期追踪、汇率换算、目的港政策、术语百科，支持四通道推送
>
> **版本 / Version**: v1.3.3 | **更新 / Updated**: 2026-08-09

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## 这是什么 / What is this?

智能货代助手是一个 **AI Agent Skill**，可在支持 Skill 框架的 AI 助手中安装使用。它让 AI 助手获得国际物流领域的专业能力：

| 功能 | 状态 | 说明 |
|------|------|------|
| 运价查询 | ✅ 可用 | 26 家船公司 + 54 港口，USD+RMB 双币种，过期自动过滤，双源口径标注 |
| 船期追踪 | ✅ 可用 | 船名/IMO 公开 AIS 追踪，四级时效分级，提单号直查（二期） |
| 汇率换算 | ✅ 可用 | 中国银行每日牌价，双向报价（买入/卖出），周末自动警告 |
| 目的港政策 | ✅ 可用 | 全球六大区域覆盖，免堆期/关税/单证/检疫/港口操作 |
| 术语百科 | ✅ 可用 | Incoterms 2020 标准，多义词消歧，费用测算示例 |
| 推送通知 | 🔧 模板就绪 | 四通道（企微/钉钉/邮箱/Bark），API 对接二期 |

---

## 安装 / Installation

在 AI 助手中安装本 Skill：

```
请帮我安装 smart-freight-assistant skill
```

或者通过 ClawdHub 市场搜索 "货代"。

---

## 使用 / Usage

安装后，直接在对话中使用自然语言触发：

| 场景 | 示例 |
|------|------|
| 运价查询 | "上海到汉堡 40HQ 最新运价" |
| 船期追踪 | "追踪 COSCO SURABAYA 当前船位" |
| 汇率换算 | "1万美元等于多少人民币" |
| 目的港政策 | "杰贝阿里港进口政策" |
| 术语查询 | "解释 FOB 和 CIF 的区别" |

---

## 触发关键词 / Triggers

船公司、港口、航线、船名、运价、海运费、船期、提单、柜号、货代、订舱、询价、汇率、目的港政策、免堆期、关税、ISPM15、Incoterms 等 350+ 关键词。

完整列表见 [SKILL.md](SKILL.md)。

---

## 版本历史 / Changelog

| 版本 | 日期 | 要点 |
|------|------|------|
| v1.3.3 | 2026-08-09 | 运价过期过滤 5 级强制规则 + AIS 严重滞后港序兜底 |
| v1.3.2 | 2026-08-08 | AGPL v3 版权水印 |
| v1.3.1 | 2026-08-08 | 港序 vs AIS 区分 + 船名航次缺失处理 + 口径不明标注 |
| v1.3 | 2026-08-08 | 过期过滤 + 双源口径 + AIS 时效四级分级 |
| v1.2 | 2026-08-07 | 22 缺陷修复（数据完整度分级/柜型标准化/Incoterms 2020 等） |
| v1.1 | 2026-08-06 | 可订状态列 + 二期功能 |
| v1.0 | 2026-08-05 | 首版：五大功能模块 |

完整日志见 [SKILL.md](SKILL.md) 版本日志章节。

---

## 架构 / Architecture

```
public/ (本仓库)            private/ (本地，不入库)
├── SKILL.md                 ├── notify.py
├── LICENSE                  ├── config.template.yaml
├── package.json             ├── .env.template
├── README.md                └── internal/
└── .gitignore                   ├── 数据源操作手册.md
                                 └── scrapers/
```

- **公开层**：Skill 指令模板、输出格式、触发关键词、交互流程
- **私有层**：推送代码、API 密钥、数据聚合爬虫、12 份内部文档

---

## 许可证 / License

[GNU AGPL v3](LICENSE)

© 2026 [yuj-029](https://github.com/yuj-029)
