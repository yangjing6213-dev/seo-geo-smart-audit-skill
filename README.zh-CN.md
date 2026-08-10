# SearchScope｜独立站 SEO/GEO 智能巡检

[English](README.en.md) | 简体中文

SearchScope 是一个面向公开独立站的只读 SEO/GEO 巡检 Skill。它检查抓取与收录信号、元数据、canonical、hreflang、结构化数据、AI 爬虫可访问性和内容可引用性，并生成带证据、优先级和验收方法的修复清单。

- 产品名：SearchScope
- Skill 标识：`independent-site-seo-geo-auditor`
- Skill 版本：`1.4.1`
- 规则引擎：`1.4.9`
- 创作者：[ENHE AI工作室](https://www.enhe-tech.com.cn)

## 核心能力

- 检查 `robots.txt`、sitemap、HTTP 状态、noindex 和重定向。
- 按最终 URL 和 canonical 归一化页面，减少重复元数据和 hreflang 误判。
- 检查 title、description、H1/H2、图片 alt 和内部链接。
- 分开静态证据、需渲染验证项和外部数据项。
- 评估 AI 爬虫访问、品牌实体信号、机器可读资源和内容可引用性。
- 输出 JSON、Markdown 和自包含 HTML 报告。
- 附带可部署的双语网页入口，仅对公开 URL 执行只读巡检。

## 运行要求

- Python 3.10 或更高版本。
- 运行时仅使用 Python 标准库。
- Node.js 仅用于前端 JavaScript 语法检查，不是运行依赖。

## 安装为 Codex Skill

```bash
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git ~/.codex/skills/independent-site-seo-geo-auditor
```

重启 Codex 或重新加载 Skills 后，调用 `independent-site-seo-geo-auditor` 即可。

## 命令行巡检

```bash
python scripts/site_audit.py https://example.com \
  --max-pages 25 \
  --json-out audit.json \
  --markdown-out audit.md \
  --html-out audit.html
```

默认阻止私网、回环、保留地址和带凭据的 URL，并仅抓取同源公开页面。

## 网页入口

```bash
python app.py
```

打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。可通过 `PORT` 环境变量修改端口。

公开只读巡检接口：`POST /api/audit`。请求体为 `{"url":"https://example.com","max_pages":25}`，最多巡检 300 个同源页面。`GET /api/health` 返回只读模式和巡检能力状态。

## 验证

```bash
python -m unittest discover -s tests -v
python scripts/test_site_audit.py
python -m compileall -q app.py scripts tests
node --check web/app.js
```

## 项目结构

```text
SKILL.md                 Codex/Agent Skill 入口
agents/                  智能体展示配置
scripts/                 巡检引擎、HTML 渲染器和引擎测试
references/              评分与证据规则
assets/                  Markdown 报告模板
app.py                   本地只读网页服务
web/                     双语用户界面
tests/                   网页入口测试
```

## 安全与结果边界

SearchScope 不登录目标站、不提交表单、不修改生产数据。它不会使用响应时间伪装 Core Web Vitals，也不保证收录、排名或 AI 引用。漏洞请按 [SECURITY.md](SECURITY.md) 私密报告。

## 贡献与支持

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。使用问题和支持边界见 [SUPPORT.md](SUPPORT.md)。

## 许可证

本项目使用 [Apache License 2.0](LICENSE)。
