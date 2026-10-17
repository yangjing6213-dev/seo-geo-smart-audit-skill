---
name: independent-site-seo-geo-auditor
description: 对公开独立站执行只读、证据化的 SEO/GEO AI 审计并输出优化方案。用于技术 SEO 审计、索引与收录诊断、robots.txt 和 sitemap 检查、canonical/hreflang/元数据/结构化数据排查、多语言站点检查、AI 爬虫可访问性、llms.txt 等机器可读资源检查，以及 ChatGPT、Perplexity、Claude、Gemini、Copilot 等答案引擎的内容可引用性评估。适用于 SaaS、电商、内容站、品牌站和多语言独立站。
---

# SearchScope｜独立站 SEO/GEO 智能巡检

对目标站点执行公开、只读、可复现的巡检，输出带证据、优先级、修复建议和验收方法的报告。默认不登录、不修改网站、不提交站长平台，也不声称已取得无法验证的数据。

## 输入

至少取得目标首页 URL。尽量复用用户已经提供的信息，并在缺失会改变结论时再询问：

- 站点类型与核心转化目标
- 重点国家、语言与 URL 结构
- 重点页面、主题和查询词
- 是否提供 GSC、Bing Webmaster、GA4 或真实用户性能数据
- 巡检上限；默认最多抓取 300 个同源 HTML 页面

## 证据边界

严格区分四种结论：

- `verified`：当前请求或文件直接证明。
- `render_required`：需要浏览器渲染后才能证明，例如客户端注入的 JSON-LD。
- `external_data_required`：需要 GSC、GA4、Bing Webmaster、CrUX/PageSpeed 字段数据或 AI 平台真实探测。
- `hypothesis`：有迹象但证据不足，只能作为调查方向。

遵守以下约束：

1. 只访问公开 URL；不要提交表单、登录后台或修改生产数据。
2. 不把 `/llms.txt`、`/pricing.md`、`/okf/` 等机器可读资源按 HTML 的 title、H1、schema 规则检查。
3. 静态抓取未发现 JSON-LD 时，只标记 `render_required`，不要直接断言“没有结构化数据”。
4. 判断语言路径时解析 URL pathname 边界，不要用 `url.includes('/en')` 一类子串判断。
5. 抽样响应时间不等于 LCP、INP、CLS；没有字段数据时把 Core Web Vitals 标记为未知。
6. 没有真实答案引擎结果时，不要捏造品牌提及、引用率、竞争对手或排名。
7. AI 爬虫被阻止可能是站点的隐私或训练策略；将其写成需确认的策略决定，不自动判定为错误。
8. 所有高优先级问题必须附当前证据和可执行的验收方法。

## 工作流

### 1. 明确范围

记录目标 URL、站点类型、语言、页面上限、时间戳、可用数据源和明确排除项。若用户只给 URL，先做公开站点基线巡检，不因缺少后台数据停止。

### 2. 运行确定性基线

优先运行随包脚本：

```bash
python scripts/site_audit.py https://example.com \
  --max-pages 300 \
  --json-out audit.json \
  --markdown-out audit.md \
  --html-out audit.html
```

脚本仅使用 Python 标准库，默认阻止私网、回环和保留地址，遵守 robots.txt，限制同源抓取、响应大小和页面数量。需要审计本机测试站时，只有在用户明确授权后才使用 `--allow-private`。

如需检查 JavaScript 加载后的页面元数据，且可选 Playwright/Chromium 已安装，可在命令中追加 `--render-browser`。浏览器复核不能与 `--allow-private` 同时使用；没有安装时不要自动安装，也不要把待渲染项说成已验证。安装方式和限制见 `docs/browser-rendering.md`。

脚本覆盖：

- robots.txt、sitemap 发现与 sitemap 重复 URL
- HTTP 状态、最终 URL、content-type、noindex
- title、description、canonical、H1/H2、图片 alt、内部链接
- 静态 HTML 中的 JSON-LD 计数与 JSON 解析
- hreflang 自引用和已抓取页面间的互惠关系
- AI/搜索爬虫 robots 可访问性
- `/llms.txt`、`/pricing.md`、`/okf/index.md` 可用性

### 3. 补充浏览器渲染检查

命令行 `--render-browser` 或本地网页复核选项会自动检查最多 10 个已抓取页面的实际 DOM，提取标题、摘要、canonical、robots、语言、H1 和结构化数据变化。它只允许同站公开读取请求，结果不改变基础评分。

这项检查不覆盖视觉布局、移动端效果、交互可达性、页面速度和核心网页指标。需要这些结论时，再另行用浏览器人工复核：

- 读取渲染后的 `<title>`、meta description、canonical、robots、hreflang。
- 执行 `document.querySelectorAll('script[type="application/ld+json"]')` 并解析结果。
- 检查主内容、H1/H2、导航和正文是否在渲染后真实可见。
- 检查移动端布局、交互可达性和懒加载内容；不要用截图代替 DOM 证据。

若可选浏览器组件未安装或复核失败，将相关项目保留为 `render_required`，并说明尚未取得浏览器证据。浏览器渲染的具体资源限制见 `docs/browser-rendering.md`。

### 4. 审计 SEO 基础

按阻断顺序检查：

1. 抓取与索引：robots、noindex、状态码、重定向、sitemap。
2. 规范化：canonical、协议/主机/尾斜杠一致性、重复 URL。
3. 多语言：语言 URL、html lang、hreflang 自引用与互惠、x-default、跨语言 canonical。
4. 页面元素：唯一 title/description、单一 H1、标题层级、正文深度、图片 alt、内部链接。
5. 结构化数据：静态与渲染证据分开，按页面类型核验字段和可见内容一致性。
6. 性能与体验：只有存在 CrUX、PageSpeed 字段数据或 GSC 证据时才判断 Core Web Vitals。

### 5. 审计 GEO 与答案引擎可见性

评估三个层面：

- 可发现：搜索与答案引擎爬虫策略、可索引公开页面、Bing/Google 基础索引入口。
- 可理解：品牌实体、作者、更新时间、来源、结构化数据、公开价格/功能/联系信息和机器可读资源。
- 可引用：直接答案段、定义、步骤、对比表、带日期和来源的数据、清晰主题集群与自然内链。

`llms.txt`、定价 Markdown 或知识包只能作为非 Google 答案引擎和代理可读性的增强项。不要把它们描述为 Google 排名或 AI Overview 收录的必要条件。

只有用户授权并实际执行查询时，才建立答案引擎探测矩阵。逐条记录查询、平台、时间、地区/语言、品牌是否被提及、域名是否被引用、引用 URL 与竞争来源。

### 6. 形成报告

读取 [references/audit-rubric.md](references/audit-rubric.md) 进行分级，并使用 [assets/audit-report-template.md](assets/audit-report-template.md) 输出报告。

每个问题必须包含：

- ID 与类别
- 结论状态和置信度
- 严重级别
- 当前证据
- 业务/搜索影响
- 最小修复建议
- 验收方法

先列阻止抓取、索引和错误 canonical 的问题，再列结构、内容和 GEO 增强项。把“缺少数据”和“确有缺陷”分开。

## 输出要求

交付以下内容：

1. 执行摘要与覆盖范围。
2. 数据源和证据边界。
3. 按 Critical、High、Medium、Low 排序的问题。
4. SEO、GEO、多语言和渲染检查矩阵。
5. 30/60/90 天行动计划；每项含负责人类型、工作量和验收方法。
6. 未验证项与下一步取证清单。
7. 原始 JSON、Markdown 与网页版 HTML 报告路径（运行脚本时）。

完整报告必须同时包含：

- 基于已验证问题计算的 100 分制结果评估、证据覆盖率和逐项扣分依据；`render_required`、`external_data_required`、`hypothesis` 不得作为已确认缺陷扣分。
- 页面级 title、description、Schema 和 hreflang 检查必须先按 `final_url` 与 canonical 建立页面身份；重定向别名、noindex 页面和 canonical-away 页面不进入重复或多语言分组。noindex 只有在同时进入 sitemap 时才作为索引冲突报告。
- 已经具备的 SEO/GEO 内容、当前证据及其价值。
- 存在的问题、严重级别、证据状态和证据。
- 针对每个问题的解决方案与可执行验收方法。
- 面向 Codex、OpenClaw、Hermes Agent、Claude Code 的执行提示词；提示词必须保留已具备能力，并区分可直接修复、需渲染复核和需外部数据的项目。
- 基于本次结果形成的后续优化建议，不把一次性巡检描述为持续监控。

网页版报告要求：

- 使用 `--html-out` 输出单文件、自包含、可直接在浏览器打开的 HTML；不得依赖 CDN、构建步骤或后端服务。
- 报告页必须展示创作者 `ENHE AI工作室` 与官网 `https://www.enhe-tech.com.cn`，并保留目标站点、评分、证据覆盖、问题、优势、行动计划、页面覆盖和限制说明。
- HTML 中的审计数据必须转义；动效只能增强展示，不得隐藏静态报告内容，并支持 `prefers-reduced-motion: reduce`。

不要在用户只要求审计时修改网站。用户明确要求修复后，才在目标项目中进行最小改动，并逐项验证。

## 网页应用入口

此 Skill 同时提供可部署的网页应用入口。仓库根目录执行：

```bash
python app.py
```

在浏览器打开 `http://127.0.0.1:8000`，输入公开站点 URL 后即可发起同一套只读巡检、查看证据化报告，并下载 JSON 或 Markdown。命令行通过 `--html-out` 生成自包含 HTML 报告。

网页 API 固定禁用 `--allow-private`，每次最多巡检 300 个同源页面，且同一实例同时只执行一项巡检。网页报告仍必须遵守本文件的证据边界；它不会伪造 Core Web Vitals 或真实答案引擎引用结果。

## 版本

Skill 包版本：`1.4.1`
规则引擎版本：`1.4.9`
