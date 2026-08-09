---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 5cb1b25772f6b0aafa9bcb1a8e5ab88d_a7c75b4a928211f18e22525400f8a581
    ReservedCode1: YRgqtiEIOTPAY89qVQ2dEkHooGgd+YSzpVd7TKC6YxDWfhchP36j26F9ZdZdCQu+mtrUxEUf+VI9TrjyTfcSCIWYk4Up3vazX8is7Uw3DqoUV3GEJOfqlUF4lHTb9UuGv6Qe+jEo/lrFwWXxJG3UUmsrOqiUAJQkNphA+Jdihb15S8nbuWTN1AlndTs=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 5cb1b25772f6b0aafa9bcb1a8e5ab88d_a7c75b4a928211f18e22525400f8a581
    ReservedCode2: YRgqtiEIOTPAY89qVQ2dEkHooGgd+YSzpVd7TKC6YxDWfhchP36j26F9ZdZdCQu+mtrUxEUf+VI9TrjyTfcSCIWYk4Up3vazX8is7Uw3DqoUV3GEJOfqlUF4lHTb9UuGv6Qe+jEo/lrFwWXxJG3UUmsrOqiUAJQkNphA+Jdihb15S8nbuWTN1AlndTs=
---





# 智能货代助手 Skill 技术方案

> 版本：v1.1 | 日期：2026-08-08 | 作者：Marvis
> 更新：运价新增可订状态列、推送通道四选一、目的港政策六大区域覆盖、定正二期完成度

---

## 一、产品定位

### 一句话定义
货代操作员的 **AI 副驾驶**——桌面端零部署的自然语言货代助手，服务中国 6 万+ 小微货代企业的个人提效需求。

### 核心差异
| 维度 | 市场竞品（运小沓/5U AI 等） | 智能货代助手 Skill |
|------|---------------------------|-------------------|
| 形态 | SaaS 平台 / 企业级部署 | Marvis 桌面端内置 Skill |
| 门槛 | 年费数万~数十万 | 零部署，零费用 |
| 用户 | 中大型货代企业 | 个人操作员 / 小微团队 |
| 定位 | 替代/耦合 TMS/ERP | 作为现有工具的外挂和增强层 |
| 交互 | 企微/网页/API | 自然语言对话 |

---

## 二、核心功能模块

### 模块 A：智能查询（一期交付）

| 功能 | 描述 | 示例指令 | 依赖能力 |
|------|------|----------|----------|
| 运价查询 | 聚合主流船公司/平台公开运价，按起运港-目的港-柜型-时间查询，含可订状态推断（基于有效期+市场趋势+航线数） | 「上海到洛杉矶 40HQ 下周海运费多少」 | web_search + web_fetch |
| 船期追踪 | 按船名/IMO号/提单号/柜号实时查询货物位置与状态 | 「查一下提单号 COSU12345678 现在到哪了」 | web_fetch（船公司公开页面） |
| 汇率查询 | 实时多币种汇率，叠加运价自动换算本币 | 「今天美元汇率多少，帮我把这批运费折成人民币」 | web_search |
| 目的港政策 | 全球六大区域单证适配表（Americas/Europe/Asia-Pacific/Middle East/Africa/CIS），含关税、VAT、免堆期/免箱期、强制单证、特殊要求等结构化字段 | 「出口拉各斯港有什么特殊要求」 | web_search + 结构化输出 |
| 术语百科 | 货代行业术语即时解释，含实操案例 | 「DDP和DAP有什么区别，实操要注意什么」 | 内置知识 + web_search |

### 模块 B：主动监控（二期交付）

监控功能按实现方式分为两种执行模式：

- **纯提醒类**：基于确定时间点的提醒（到港提醒、免费期预警），由 `create_scheduled_task` 云端调度，到期时 Marvis 双端（PC/手机）均可收到推送，无需额外部署。
- **轮询监控类**：需要持续抓取外部数据并对比状态（定时盯箱、运价波动提醒），由 GitHub Actions 定时脚本 + `notify.py` 四通道推送（企微/钉钉/邮箱/Bark），脱离 PC 全自动运行，无需本地常驻。

| 功能 | 描述 | 示例指令 | 执行模式 | 实现方案 |
|------|------|----------|----------|----------|
| 到港提醒 | 船舶预计到港前主动推送提醒 | 「MSC DIANA 号到洛杉矶前24小时提醒我通知客户」 | 纯提醒类 | create_scheduled_task 云端定时 → Marvis 双端推送 |
| 免费期预警 | 目的港免堆期/免箱期到期前告警 | 「这批货免堆期到8月15号，提前3天提醒我」 | 纯提醒类 | create_scheduled_task 云端定时 → Marvis 双端推送 |
| 定时盯箱 | 设置提单号，定时轮询状态，有变化主动通知 | 「每隔2小时帮我盯一下 COSU12345678，有状态变化马上告诉我」 | 轮询监控类 | GitHub Actions cron定时 → curl 抓取船公司页面 → 对比缓存 → notify.py 四通道推送 |
| 运价波动提醒 | 设置关注航线，运价波动超阈值主动通知 | 「上海到汉堡运价波动超过10%提醒我」 | 轮询监控类 | GitHub Actions cron定时 → curl 抓取运价 → 对比历史 → notify.py 四通道推送 |
| 异常天气/航线告警 | 台风路径/港口罢工等异常事件圈出受影响提单 | 「最近有没有影响华东到东南亚航线的台风」 | 事件触发 | web_search 主动检索 + LLM 判断影响范围 |

### 模块 C：文档处理（三期交付）

| 功能 | 描述 | 示例指令 | 依赖能力 |
|------|------|----------|----------|
| 托书OCR录单 | 拍照/截图托书，自动提取发货人/收货人/品名/件重尺/船名航次 | 用户上传托书截图 → 结构化输出 | analyze_image + LLM |
| 提单草稿比对 | 船公司草稿单 vs 客户确认单，自动标出差 | 「帮我比对这两份提单，看看有没有不一样的地方」 | analyze_image + text diff |
| 单证模板生成 | 输入关键信息，自动生成报关单/装箱单/发票模板 | 「生成一份出口报关单模板，品名玩具，HS 950300」 | LLM 生成 + write_file |
| HS编码推荐 | 描述货物，推荐 HS 编码 + 监管条件 + 所需单证 | 「塑料玩具出口美国HS编码是什么，要什么单证」 | web_search + LLM |

### 模块 D：知识库（贯穿全程）

| 功能 | 描述 | 依赖能力 |
|------|------|----------|
| 内部SOP问答 | 读取公司内部操作手册/规章制度，即时问答 | file-agent 读取 + RAG |
| 历史案例检索 | 记录典型操作，新人可查询历史处理方式 | 本地文件索引 |
| 货代考试题库 | 货代从业资格考试题目练习与解析 | 预置题库 + LLM 讲解 |

---

## 三、技术架构

```
用户自然语言输入
        │
        ▼
┌───────────────────────────────────┐
│         Marvis Main Agent         │
│  ┌─────────────────────────────┐  │
│  │   智能货代助手 Skill        │  │
│  │                             │  │
│  │  ┌──────────┐ ┌──────────┐ │  │
│  │  │意图路由层│ │上下文管理│ │  │
│  │  │ 查询/监控│ │ 提单号   │ │  │
│  │  │ /文档/知 │ │ 航线偏好 │ │  │
│  │  │ 识库分发 │ │ 监控列表 │ │  │
│  │  └────┬─────┘ └──────────┘ │  │
│  └───────┼────────────────────┘  │
└──────────┼───────────────────────┘
           │
    ┌──────┼──────────────────┐
    ▼      ▼                  ▼
┌──────┐ ┌────────┐    ┌───────────┐
│web_  │ │file-   │    │create_    │
│search│ │agent   │    │scheduled_ │
│+fetch│ │analyze │    │task       │
│      │ │_image  │    │           │
└──────┘ └────────┘    └───────────┘
  实时      文档+       定时任务
  信息      OCR        引擎
```

### 能力依赖清单

| 层级 | 组件 | 用途 |
|------|------|------|
| Skill 层 | SKILL.md | 触发规则 + 核心指令 + 输出格式协议 |
| Main Agent | web_search / web_fetch | 运价/船期/汇率/政策实时检索 |
| Main Agent | create_scheduled_task | 盯箱/到港提醒/免费期预警 |
| Sub Agent | file-agent | 内部文档读取/单证生成/格式转换 |
| Main Agent | analyze_image | 托书OCR/提单比对 |
| Main Agent | python_executor | 数据处理/运价对比计算 |
| 缓存层 | 本地文件存储 | 用户偏好（常用航线/港口/船公司）、监控任务清单 |

### 二期监控架构

二期监控功能采用双通道架构，按任务性质分流到不同的执行引擎：

**通道一：纯提醒类（云端定时）**

```
用户对话 → create_scheduled_task（云端）
                │
                ▼
         Marvis 调度引擎
                │
        ┌───────┴───────┐
        ▼               ▼
    PC 端推送      手机端推送
```

适用场景：到港提醒、免费期预警。优势：零外部依赖，Marvis 原生支持，双端可达。

**通道二：轮询监控类（GitHub Actions + notify.py）**

```
GitHub Actions（cron 定时触发）
        │
        ▼
curl 抓取船公司 / 运价平台公开页面
        │
        ▼
对比本地缓存文件（上次抓取结果）
        │
   ┌────┴────┐
   ▼         ▼
 无变化     有变化
   │         │
 结束    调用 notify.py → 推送至用户所选通道（企微/钉钉/邮箱/Bark）
```

适用场景：定时盯箱、运价波动提醒。优势：完全脱离 PC，GitHub Actions 免费额度（每月 2000 分钟）远超需求。

**推送通道设计**

轮询监控类任务检测到状态变化后，通过统一的 `notify.py` 调度器推送通知。用户可根据偏好自主选择推送通道：

| 通道 | 注册门槛 | 配置步骤 | 费用 | 适用场景 |
|------|---------|----------|------|----------|
| 企业微信机器人 | 需有企业微信 | 群聊→添加机器人→获取 Webhook URL | 免费 | 已有企业微信的团队 |
| 钉钉机器人 | 需有钉钉 | 群聊→智能群助手→添加机器人→获取 Webhook URL | 免费 | 已有钉钉的团队 |
| QQ邮箱 SMTP | 无门槛 | 开启 SMTP 服务→获取授权码 | 免费（每日额度充足） | 个人用户，无企业IM |
| Bark（iOS） | 安装 Bark App | App Store 下载→获取推送 Key | 免费 | iOS 用户，轻量级推送 |

**统一推送调度代码（notify.py）**

```python
# notify.py — 统一推送调度，通过 NOTIFY_CHANNEL 环境变量切换通道
import os, requests, smtplib, json
from email.mime.text import MIMEText
from datetime import datetime

CHANNEL = os.environ.get("NOTIFY_CHANNEL", "wecom")  # wecom / dingtalk / email / bark

def notify(title, content):
    if CHANNEL == "wecom":
        _notify_wecom(title, content)
    elif CHANNEL == "dingtalk":
        _notify_dingtalk(title, content)
    elif CHANNEL == "email":
        _notify_email(title, content)
    elif CHANNEL == "bark":
        _notify_bark(title, content)
    else:
        raise ValueError(f"不支持的推送通道: {CHANNEL}")

def _notify_wecom(title, content):
    webhook = os.environ["WECOM_WEBHOOK"]
    requests.post(webhook, json={
        "msgtype": "markdown",
        "markdown": {"content": f"## {title}\n{content}"}
    })

def _notify_dingtalk(title, content):
    webhook = os.environ["DINGTALK_WEBHOOK"]
    requests.post(webhook, json={
        "msgtype": "markdown",
        "markdown": {"title": title, "text": f"### {title}\n{content}"}
    })

def _notify_email(title, content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = f"[盯箱] {title}"
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]
    with smtplib.SMTP_SSL(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 465))) as s:
        s.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASSWORD"])
        s.send_message(msg)

def _notify_bark(title, content):
    key = os.environ["BARK_KEY"]
    requests.get(f"https://api.day.app/{key}/{title}/{content}")

# CLI 入口供 GitHub Actions 调用
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python notify.py <标题> <内容>")
        sys.exit(1)
    notify(sys.argv[1], sys.argv[2])
```

**配置方式**：用户在 GitHub 仓库的 Settings → Secrets and variables → Actions 中设置以下环境变量：

- `NOTIFY_CHANNEL`：选择 `wecom` / `dingtalk` / `email` / `bark`
- 按所选通道配置对应的 Secret（如 `WECOM_WEBHOOK`、`DINGTALK_WEBHOOK`、`EMAIL_FROM` / `EMAIL_TO` / `EMAIL_PASSWORD` / `SMTP_HOST`、`BARK_KEY`）

| 依赖 | 用途 | 费用 |
|------|------|------|
| GitHub Actions | 定时触发抓取脚本（cron 表达式） | 免费（公开仓库无限、私有仓库 2000 分钟/月） |
| 推送通道（四选一） | 状态变化通知 | 全部免费（个人额度内） |
| curl / jq | 抓取页面、解析 JSON | 开源工具，GitHub Actions runner 内置 |

---

## 四、用户交互设计

### 对话示例

**场景1：运价查询**
```
用户：上海到汉堡 40HQ 8月中旬海运费多少
Marvis：已查询到以下运价（8月11日-17日，上海→汉堡）：

| 船公司 | 船名航次 | ETD | 40HQ运价(USD) | 折算(RMB) | 有效期 | 可订状态 |
|--------|---------|-----|-------------|----------|--------|----------|
| 马士基 | MAERSK HANOI 2432E | 8.13 | 2,850 | ≈20,805 | 8/1~8/15 | ✅ 可订 |
| MSC | MSC DIANA SZ432A | 8.15 | 2,720 | ≈19,856 | 8/5~8/20 | ✅ 可订 |
| 达飞 | CMA CGM TITAN 0PG25E | 8.12 | 2,950 | ≈21,535 | 8/1~8/15 | ⚠️ 即将截止 |
| ONE | ONE HAMBURG 045W | 8.16 | 2,680 | ≈19,564 | 8/1~8/10 | ⚠️ 即将截止 |

> 汇率：1 USD ≈ 7.30 RMB（2026-08-08）。可订状态基于有效期+市场趋势推断，以实际订舱确认为准。

来源：各船公司官网公开运价，实际以订舱确认为准
```

**场景2：定时盯箱**
```
用户：帮我盯一下 SZ12345678，每4小时查一次，有变化叫我
Marvis：已设置定时任务「盯箱 SZ12345678」，每4小时自动查询状态。

当前状态：2026-08-07 14:30 — 已装船，预计8月15日抵达汉堡港

有变化会第一时间通知你。
```

**场景3：OCR录单**
```
用户：[上传托书截图]
Marvis：已识别托书内容：

| 字段 | 内容 |
|------|------|
| 发货人 | ABC TRADING CO., LTD |
| 收货人 | XYZ IMPORT INC. |
| 起运港 | 上海 |
| 目的港 | 洛杉矶 |
| 品名 | PLASTIC TOYS |
| 件数 | 500 CTNS |
| 毛重 | 8,500 KGS |
| 体积 | 35 CBM |
| 船名航次 | EVER FORWARD 0456E |

如需生成装箱单或报关单模板请告诉我。
```

---

## 五、开发路线图

### 一期（MVP，2-3天）— 立即可做

| 功能 | 说明 |
|------|------|
| 运价查询 | web_search + web_fetch 聚合公开运价 |
| 船期追踪 | 提单号查询船公司公开页面 |
| 汇率查询 | web_search 实时汇率 |
| 术语百科 | 内置货代术语知识 + web_search 补充 |
| SKILL.md | 编写触发规则 + 核心指令 |

### 二期（1-2周）

| 功能 | 说明 | 状态 | 技术路线 |
|------|------|------|----------|
| 到港提醒 | 基于ETA的定时提醒 | ✅ 已完成 | 纯提醒类，create_scheduled_task 云端定时 |
| 免费期预警 | 基于日期的定时提醒 | ✅ 已完成 | 纯提醒类，create_scheduled_task 云端定时 |
| 定时盯箱 | GitHub Actions + notify.py 自动轮询 | ⚠️ 模板化 | 轮询监控类，GitHub Actions 模板已就绪（cron + notify.py），未实际部署 |
| 运价波动提醒 | 定时对比历史运价 | ⏳ 待实施 | 轮询监控类，GitHub Actions cron + notify.py |

### 三期（2-4周）

| 功能 | 说明 |
|------|------|
| 托书OCR录单 | analyze_image + LLM 结构化 |
| 提单比对 | 双图对比 |
| 单证模板生成 | LLM 按模板生成 |
| HS编码推荐 | web_search + LLM |
| 内部SOP问答 | file-agent + 本地文档读取 |

---

## 六、竞品对比总结

| 能力 | 运小沓 | 5U AI | GetTransport | 集运MaaS | **本Skill** |
|------|--------|-------|-------------|----------|------------|
| 询报价 | ★★★ | ★★★ | ★★★ | ★ | ★★（聚合公开价） |
| 接单/OCR | ★★★ | ★★ | ★★ | — | ★★（托书OCR） |
| 追踪/盯箱 | ★★ | ★★★ | ★★★ | ★★★ | ★★（定时轮询） |
| 知识问答 | ★ | ★ | — | ★ | ★★★ |
| 定时提醒 | — | — | — | — | ★★★ |
| 零部署 | — | — | — | — | ★★★ |
| 个人免费 | — | — | — | ★ | ★★★ |

> 结论：竞品强在 **交易自动化**（接单-报价-订舱闭环），本 Skill 强在 **信息赋能 + 个人提效**，二者可互补而非直接竞争。

---

## 七、商业模式设想（可选）

| 阶段 | 模式 | 说明 |
|------|------|------|
| 免费期 | 完全免费 | 个人操作员零门槛使用，积累种子用户 |
| 增值期 | 基础免费 + 高级付费 | 基础查询免费；高级功能（定时盯箱数量、OCR次数、知识库上传）按量或订阅 |
| B端 | 团队版/企业版 | 共享监控列表、团队SOP知识库、多账户管理 |

---

## 附录：SKILL.md（v1.1 当前版本）

> 完整文件：`output\smart-freight-assistant\SKILL.md`（321行，双语）

### 核心结构

| 章节 | 内容 |
|------|------|
| 触发时机 | 业务关键词（货代/运价/船期/单证/目的港/术语）+ 26家船公司 + 54个港口 + 航运联盟 + 航线方向（中英双语） |
| 运价查询 | 7列表格输出（船公司/船名航次/ETD/运价USD/运价RMB/可订状态/备注），可订状态基于有效期+市场趋势+航线数推断 |
| 货物追踪 | 公开AIS数据追踪 + 未来API直连会员路线图，输出9列结构化表格 |
| 汇率查询 | 多币种双向换算，实时抓取中国银行外汇牌价 |
| 术语百科 | 定义+适用场景+风险划分+费用划分+实操注意事项 |
| 目的港政策 | 全球六大区域单证适配表（Americas/Europe/Asia-Pacific/Middle East/Africa/CIS），按基础清关/特殊单证/货物限制/检疫熏蒸/港口操作五维输出 |
| 推送通道 | 四选一（企微/钉钉/邮箱/Bark）交互式配置，含切换对话示例 |

### 与 v1.0 草案的关键差异

1. 完全双语（中/英）
2. 关键词覆盖从 ~10 个扩展至 26 船公司 + 54 港口 + 贸易术语 + 航运联盟 + 航线方向
3. 运价输出从 5 列扩展至 7 列，新增「运价(RMB)」和「可订状态」
4. 目的港政策从单维度扩展至五维结构，六大区域差异覆盖
5. 推送通道从「Server酱」改为四通道可切换（企微/钉钉/邮箱/Bark），含完整配置引导

*（内容由AI生成，仅供参考）*

---

## 附录B：GitHub Actions 盯箱脚本模板

以下为定时盯箱的完整 GitHub Actions 工作流模板，用户只需替换占位符中的提单号，并在 GitHub Secrets 中配置所选推送通道的凭据即可使用。

### 文件路径

`.github/workflows/monitor.yml`

### 工作流代码

```yaml
name: Container Monitor

on:
  schedule:
    # 每2小时执行一次（UTC 时间）
    - cron: '0 */2 * * *'
  workflow_dispatch:  # 支持手动触发

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Fetch container status
        id: fetch
        run: |
          # ====== 用户需替换以下内容 ======
          # BILL_NO: 提单号，例如 COSU12345678
          BILL_NO="<YOUR_BILL_NO>"

          # 抓取船公司公开查询页面（示例为 COSCO Skypace）
          RESPONSE=$(curl -s "https://skypace.coscoshipping.com/container/track?billNo=${BILL_NO}")
          echo "response=${RESPONSE}" >> $GITHUB_OUTPUT

          # 提取关键状态（根据实际页面结构调整解析逻辑）
          STATUS=$(echo "$RESPONSE" | grep -oP '"status":"\K[^"]+' | head -1)
          echo "status=${STATUS}" >> $GITHUB_OUTPUT
          echo "bill_no=${BILL_NO}" >> $GITHUB_OUTPUT

      - name: Compare with cache
        id: compare
        run: |
          CURRENT_STATUS="${{ steps.fetch.outputs.status }}"
          BILL_NO="${{ steps.fetch.outputs.bill_no }}"
          CACHE_FILE="cache_${BILL_NO}.txt"

          if [ -f "$CACHE_FILE" ]; then
            PREVIOUS_STATUS=$(cat "$CACHE_FILE")
            if [ "$CURRENT_STATUS" != "$PREVIOUS_STATUS" ]; then
              echo "changed=true" >> $GITHUB_OUTPUT
              echo "previous=${PREVIOUS_STATUS}" >> $GITHUB_OUTPUT
            else
              echo "changed=false" >> $GITHUB_OUTPUT
            fi
          else
            echo "changed=true" >> $GITHUB_OUTPUT
            echo "previous=（首次检测）" >> $GITHUB_OUTPUT
          fi

          # 更新缓存
          echo "$CURRENT_STATUS" > "$CACHE_FILE"
          echo "current=${CURRENT_STATUS}" >> $GITHUB_OUTPUT

      - name: Push notification via notify.py
        if: steps.compare.outputs.changed == 'true'
        env:
          NOTIFY_CHANNEL: ${{ secrets.NOTIFY_CHANNEL }}
          WECOM_WEBHOOK: ${{ secrets.WECOM_WEBHOOK }}
          DINGTALK_WEBHOOK: ${{ secrets.DINGTALK_WEBHOOK }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          BARK_KEY: ${{ secrets.BARK_KEY }}
        run: |
          BILL_NO="${{ steps.fetch.outputs.bill_no }}"
          PREVIOUS="${{ steps.compare.outputs.previous }}"
          CURRENT="${{ steps.compare.outputs.current }}"

          pip install requests -q
          python notify.py \
            "盯箱提醒：${BILL_NO} 状态变化" \
            "提单号：${BILL_NO}

          原状态：${PREVIOUS}
          新状态：${CURRENT}"

      - name: Commit cache update
        if: steps.compare.outputs.changed == 'true'
        run: |
          git config user.name "GitHub Actions Bot"
          git config user.email "actions@github.com"
          git add cache_*.txt
          git commit -m "Update cache for ${{ steps.fetch.outputs.bill_no }}" || true
          git push || true
```

### 部署步骤

1. 在 GitHub 创建仓库（建议私有），将上述 `.yml` 放入 `.github/workflows/` 目录，将 `notify.py`（见推送通道设计章节）放入仓库根目录
2. 替换 `<YOUR_BILL_NO>` 为实际提单号
3. 在仓库 Settings → Secrets and variables → Actions 中配置 Secrets：
   - `NOTIFY_CHANNEL`：选择推送通道（`wecom` / `dingtalk` / `email` / `bark`）
   - 按所选通道填入对应的 Secret（如 WECOM_WEBHOOK / DINGTALK_WEBHOOK 等）
   - 若选择邮箱通道，需额外配置 `EMAIL_FROM`、`EMAIL_TO`、`EMAIL_PASSWORD`、`SMTP_HOST`
4. 推送至 GitHub，Actions 将自动按 cron 表达式定时运行
5. 在仓库 Settings → Actions → General → Workflow permissions 中确保勾选 "Read and write permissions"

### 扩展说明

- **多提单号**：复制 jobs 中的 steps 块，修改 BILL_NO 即可同时监控多个提单
- **其他船公司**：修改 fetch 步骤中的 curl URL 和解析逻辑适配目标平台
- **运价监控**：将 fetch 步骤改为抓取运价平台页面，对比价格变化即可复用同一架构
- **切换推送通道**：修改 `NOTIFY_CHANNEL` Secret 的值即可在四通道间切换，无需改动代码
- **多通道通知**：如需同时使用多个通道（如企业微信 + Bark 双保险），可在 workflow 中添加多个 notify 步骤，分别指定不同的 NOTIFY_CHANNEL

*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
