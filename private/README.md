# ============================================
# 智能货代助手 — 私有层 / Private Layer
# ============================================
# 本目录包含所有不应出现在公开 GitHub 仓库中的实现代码和配置。
# .gitignore 已配置排除 private/ 和 .env，确保不会误提交。
#
# 目录结构 / Structure:
#   .env                     API 密钥与凭证（严禁提交）
#   config.yaml              推送通道配置
#   notify.py                四通道通知调度
#   scrapers/rates.py        运价数据聚合爬虫
#   scrapers/tracking.py     船期 AIS / 提单追踪爬虫
#   scraper-keys/            爬虫专用密钥（可选）
# ============================================
