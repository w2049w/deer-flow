---
name: smart-web-fetch
description: 智能网页抓取技能 - 替代内置 web_fetch，自动使用 Jina Reader / markdown.new / defuddle.md 清洗服务获取干净 Markdown。支持多级降级策略，大幅降低 Token 消耗。当 Agent 需要获取网页内容时使用本技能。
---

# Smart Web Fetch

智能网页内容获取技能，完全替代 web_fetch，自动通过清洗服务获取干净 Markdown。

## 核心功能

- **完全替代 web_fetch**: 获取的已经是清洗后的 Markdown，而非原始 HTML。
- **四级降级策略**: Jina → markdown.new → defuddle.md → 原始内容。
- **Token 优化**: 清洗后的内容比原始 HTML 节省 50-80% Token，极大提升后续处理效率。

## 使用方式

### 命令行获取网页内容

```bash
# 获取清洗后的 Markdown（文本输出）
python3 ./scripts/fetch.py "https://example.com/article"

# 获取 JSON 格式（包含元信息）
python3 ./scripts/fetch.py "https://example.com/article" --json
```

### 在 Agent 中的思维链路

当用户提供一个网页链接或要求“查一下这个网站的内容”时，你应该优先使用此技能：

1. **识别需求**: 用户需要了解某个网页的具体内容。
2. **执行指令**: 运行 `python3 ./scripts/fetch.py "[URL]"`。
3. **处理结果**: 获取清洗后的纯净 Markdown，进行摘要、分析或回答。

## JSON 输出格式

```json
{
  "success": true,
  "url": "https://r.jina.ai/http://example.com/article",
  "content": "# Article Title\n\nClean markdown content here...",
  "source": "jina",
  "error": null
}
```

## 降级策略说明

本技能会自动按以下顺序尝试，直到成功：

1. **Jina Reader**: 首选，中文兼容性极佳。
2. **markdown.new**: 第一备选。
3. **defuddle.md**: 第二备选。
4. **原始内容**: 最终兜底。

## 优势

- 🚀 **Token 节省 50-80%**: 去除广告、导航栏等噪音。
- 🔄 **自动容错**: 多级服务降级，确保 99% 的网页都能成功获取。
- 🆓 **零成本**: 默认使用无需 API Key 的免费服务接口。
- 📝 **干净输出**: 直接供 LLM 阅读的纯 Markdown 格式。
