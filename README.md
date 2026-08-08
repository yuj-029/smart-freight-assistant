# 智能货代助手 · Smart Freight Assistant

> AI 驱动的国际物流助手 — 运价查询、船期追踪、汇率换算、术语百科，支持四通道推送

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

---

## 这是什么 / What is this?

智能货代助手是一个 **AI Agent Skill**，可在支持 Skill 框架的 AI 助手中安装使用。它让 AI 助手获得国际物流领域的专业能力：

- **运价查询**：24 家主流船公司 + 54 个全球港口，USD+RMB 双币种报价
- **船期追踪**：提单号 / 柜号直查，AIS 船位查询
- **汇率换算**：接入中国银行外汇牌价，实时汇率
- **术语百科**：Incoterms 2020 标准术语解释
- **四通道推送**：企业微信 / 钉钉 / QQ邮箱 / Bark

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
| 运价查询 | "上海到洛杉矶 40HQ 最新运价" |
| 船期追踪 | "查提单号 MSCU123456789" |
| 汇率换算 | "1万美元等于多少人民币" |
| 术语查询 | "解释 FOB 和 CIF 的区别" |
| 定时推送 | "每天早上 9 点推送上海出口运价简报" |
| 换通道 | "把推送通道切成钉钉" |

---

## 触发关键词 / Triggers

船公司、港口、航线、船名、运价、海运费、船期、提单、柜号、货代、订舱、询价、汇率 等 350+ 关键词。

完整列表见 [SKILL.md](SKILL.md)。

---

## 架构 / Architecture

```
public/ (本仓库)            private/ (本地，不入库)
├── SKILL.md                 ├── notify.py
├── LICENSE                  ├── config.yaml
├── package.json             ├── .env
├── README.md                └── scrapers/
└── .gitignore                   ├── rates.py
                                 └── tracking.py
```

- **公开层**：Skill 指令模板、输出格式、触发关键词、交互流程
- **私有层**：推送代码、API 密钥、数据聚合爬虫、反爬策略

---

## 许可证 / License

[GNU AGPL v3](LICENSE)

© 2026 [yuj-029](https://github.com/yuj-029)
