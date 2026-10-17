# SearchScope｜独立站 SEO/GEO 智能巡检

<p align="center">
  <img src="assets/logo.png" alt="SearchScope 标志" width="180">
</p>

> 帮助独立站经营者和 AI 创作者检查公开网站的 SEO 与 GEO 基础，并整理出带证据的改进清单。

网站能打开，不代表搜索引擎和 AI 工具都能正确读取它。SearchScope 会按公开页面上的证据逐项检查，并把“已经确认的问题”和“还需要更多资料才能判断的部分”分开说明。它只做巡检，不会替你修改网站，也不保证排名或 AI 引用结果。

[简体中文](README.md) | [English](README.en.md)

[![CI](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/ci.yml) [![CodeQL](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/codeql.yml/badge.svg)](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/actions/workflows/codeql.yml)

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-used-F7DF1E?logo=javascript&logoColor=222) ![HTML5](https://img.shields.io/badge/HTML5-used-E34F26?logo=html5&logoColor=white) ![CSS](https://img.shields.io/badge/CSS-used-663399?logo=css3&logoColor=white) [![Apache-2.0](https://img.shields.io/github/license/yangjing6213-dev/seo-geo-smart-audit-skill)](https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill/blob/main/LICENSE)

![SearchScope 项目封面](assets/project-cover.png)

> 图片是项目封面示意，不是实际巡检页面。图中分数、趋势和数据均为视觉示例，不代表真实网站的审计结果。

## 目录

- [一、这个项目是什么？](#what-is-searchscope)
- [二、先看效果](#see-results)
- [三、适合谁用？](#who-is-it-for)
- [四、你会得到什么？](#deliverables)
- [五、它能帮你解决什么问题？](#problems-solved)
- [六、安装与快速开始](#install-and-start)
- [七、如何使用？](#how-to-use)
- [八、项目工作流程](#workflow)
- [九、项目目录结构](#project-structure)
- [十、注意事项与常见问题](#notes-and-faq)
- [十一、版本说明](#version)
- [十二、相关项目](#related-projects)
- [十三、关于作者](#author)
- [十四、继续探索](#explore)

<a id="what-is-searchscope"></a>
## 一、这个项目是什么？

SearchScope 是一个面向公开独立网站的只读巡检工具，包含三部分：

- **AI Skill**：Skill 是一套让 AI 按特定方法完成任务的操作指南，需要配合支持加载 Skill 的 AI 工具使用。SearchScope 的 Skill 标识是 **independent-site-seo-geo-auditor**。
- **本地网页入口**：在自己的电脑上打开双语页面，输入网址并查看报告。
- **命令行工具**：适合熟悉终端操作的人，或希望把巡检接入自己工作流程的人。

这里的 SEO 是搜索引擎优化；GEO 指让网站内容更容易被 AI 答案工具发现、理解和引用。SearchScope 会检查网页上能直接看到的线索，例如抓取规则、页面标题、描述、标题层级、语言页面关系、结构化数据，以及 AI 爬虫访问设置。

你通常只需提供网站首页网址。站点类型、目标语言、重点页面和页面数量等信息可以帮助 AI 给出更贴合业务的解释。SearchScope 会读取公开页面，整理证据、问题优先级、修复建议和验收方法。它不登录网站后台、不提交表单，也不修改网站。

<a id="see-results"></a>
## 二、先看效果

![SearchScope 项目封面](assets/project-cover.png)

这是项目封面，不是程序运行截图。图中的评分、流量趋势和问题数量都是示意内容，不能作为 SearchScope 的真实测试结果或效果承诺。

仓库目前没有附上某个真实网站的完整巡检报告，因此这里不展示虚构的评分或案例。你可以先查看[报告模板](assets/audit-report-template.md)，了解正式报告会怎样记录范围、证据、问题等级和验收方法。模板本身不是已经运行完成的报告。

<a id="who-is-it-for"></a>
## 三、适合谁用？

### 特别适合

- 经营品牌站、内容站、电商网站或 SaaS 官网，想先了解公开页面有哪些 SEO 基础问题的人。
- AI 创作者或小团队，想把重复的网站检查整理成一份可复核、可继续执行的清单。
- 管理多语言网站，需要检查不同语言页面之间的对应关系的人。
- 使用支持 Skill 的 AI 工具，希望让 AI 按固定证据标准检查网站的人。

### 暂时不适合

- 想要工具自动改网站、持续监控排名，或保证流量、排名和 AI 引用的人。
- 想直接审计内网、个人电脑上的测试网站或需要登录才能访问的网站。默认只接受公开的 HTTP 或 HTTPS 页面。
- 想在没有 Search Console、分析平台或真实 AI 答案样本的情况下，得到准确流量、排名或引用率结论的人。SearchScope 不会猜测这些数据。
- 没有 Python 3.10 或更高版本、又希望在自己电脑上运行 Skill、网页或命令行版本的人。无需安装的在线入口是否可用，以该页面当前状态为准。

<a id="deliverables"></a>
## 四、你会得到什么？

一次巡检会按所选入口提供相应结果：

- **问题与证据**：网站已具备的基础、发现的问题、问题等级、页面证据和可执行的修复与验收建议。
- **评分与范围**：Skill 和报告包含基于已核实问题的 100 分制评估、覆盖页面和证据范围。需要浏览器或外部数据才能判断的事项会单独标出，不会直接当作已确认问题扣分。
- **本地网页入口**：在浏览器页面中查看结果，并下载 Markdown 报告、JSON 数据和智能体提示词。下载文件会进入浏览器设置的下载位置。
- **命令行工具**：可按你指定的位置生成 JSON、Markdown 和单文件 HTML 报告。HTML 报告不需要另外启动服务即可在浏览器打开。
- **AI Skill**：在支持 Skill 的工具里获得巡检分析和后续建议；是否同时生成文件，取决于所用 AI 工具是否能创建文件以及你提出的要求。

结果不是搜索排名、流量或 AI 引用的预测。

<a id="problems-solved"></a>
## 五、它能帮你解决什么问题？

手动巡检时，常见困难是需要逐页找线索，还容易把“尚未查到”误当成“确定有问题”。SearchScope 会先按页面证据整理发现，再把需要浏览器复核、需要外部数据和证据不足的事项标出来。

这样你可以先处理有明确证据、影响较大的问题，再决定是否补充浏览器结果或平台数据。实际修复仍由你或你的开发者完成；修复后可以再次巡检，检查公开页面是否发生变化。

<a id="install-and-start"></a>
## 六、安装与快速开始

### 使用前需要准备什么

| 使用方式 | 必要条件 |
|---|---|
| 在线入口 | 可上网的浏览器和公开网站网址。在线入口由仓库之外单独部署；账号、费用、数据处理方式和当前可用性以页面说明为准，本仓库没有公布这些服务细节。 |
| 本地网页或命令行 | Python 3.10 或更高版本，以及可访问目标公开网站的网络。默认巡检使用 Python 自带功能，无需安装额外运行包。 |
| AI Skill | 支持加载 Skill 的 AI 工具。若使用 Codex，可按下方步骤安装。运行巡检脚本的环境同样需要 Python 3.10 或更高版本。 |
| 可选浏览器复核 | 只有在需要检查 JavaScript 加载后的页面信息时才需要；须额外安装 Playwright 1.59.0 或更高版本及 Chromium。 |

Node.js 不是日常使用所需的软件。无需提供网站登录密码或站长平台账号。在线 AI 服务、AI 工具和独立托管服务的收费由各服务提供方决定；项目仓库没有对它们作免费承诺。

### 推荐先试：在线入口

仓库记录的独立在线入口：[打开 SearchScope 在线页面](https://enheai-seo-geo.coze.site/)。

此路径不需要在本机安装项目；账号、费用和数据处理规则仍以在线服务页面当前说明为准。

如果页面可访问，按页面当前说明输入一个公开网站网址并开始巡检。入口由仓库之外单独维护，功能、账号要求、费用、数据处理方式和可用性可能与本地版本不同；请先阅读页面说明。若页面无法打开，或你希望自己控制运行环境，请使用下面的本地网页入口。

### 在自己的电脑上打开网页

在 GitHub 项目页面点击 Code → Download ZIP 并解压；也可以在你希望保存项目的目录打开终端，运行以下命令。命令会下载整个项目；不要只复制 SKILL.md，否则巡检脚本和规则文件会缺失。

**Windows PowerShell**（需先安装 Python 3.10 或更高版本和 Git）：

~~~powershell
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git
cd seo-geo-smart-audit-skill
python app.py
~~~

**macOS 或 Linux 终端**：

~~~bash
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git
cd seo-geo-smart-audit-skill
python3 app.py
~~~

当终端显示服务已启动后，在同一台电脑的浏览器打开：

[http://127.0.0.1:8000](http://127.0.0.1:8000)

输入公开网站网址，首次可选 10 页快速巡检，然后点击开始。结果会显示在网页中；点击“下载 Markdown”或“下载 JSON”后，文件会保存到浏览器的下载位置。网页服务只监听当前电脑，不会自动对局域网或互联网开放。要停止服务，在启动它的终端按 Ctrl+C。

如果下载的是 ZIP，请先完整解压，再在解压后的项目文件夹中打开终端并运行命令。

### 安装为 Codex Skill

如果你希望在 Codex 对话中调用这个 Skill，可把整个仓库放到 Codex 的 Skill 文件夹。以下命令仅适用于首次安装；如果目标文件夹已经存在，不要重复克隆。

**Windows PowerShell：**

~~~powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git "$env:USERPROFILE\.codex\skills\independent-site-seo-geo-auditor"
~~~

**macOS 或 Linux：**

~~~bash
mkdir -p ~/.codex/skills
git clone https://github.com/yangjing6213-dev/seo-geo-smart-audit-skill.git ~/.codex/skills/independent-site-seo-geo-auditor
~~~

安装后重新加载 Skill 或重启 Codex。其他 AI 工具的安装位置和方法可能不同，请以该工具的 Skill 使用说明为准。若没有 Git，也可以从 GitHub 下载 ZIP，把完整项目解压到对应的 Skill 文件夹。

### 可选：检查 JavaScript 加载后的页面

默认巡检读取公开网页的静态内容。如果目标页面依赖 JavaScript 才显示标题、摘要或结构化数据，可以在项目文件夹中额外安装浏览器组件：

~~~bash
python -m pip install -r requirements-renderer.txt
python -m playwright install chromium
~~~

macOS 或 Linux 若使用 python3，请把命令中的 python 换成 python3。浏览器复核默认关闭，最多检查 10 个页面；它不测量页面速度、视觉布局或交互体验。详细限制见[浏览器复核说明](docs/browser-rendering.md)。

<a id="how-to-use"></a>
## 七、如何使用？

### 在 AI 对话中使用 Skill

安装后开始一个新对话，输入网站网址和你关心的范围。可以复制下面这段，再把示例网址换成你自己管理的公开网站：

~~~text
请调用 independent-site-seo-geo-auditor，对 https://example.com 做一次最多 10 页的只读 SEO/GEO 基线巡检。只检查公开页面，不登录、不修改网站。请列出页面证据、问题优先级、最小修复建议和验收方法，并区分已经核实、需要浏览器复核、需要外部数据和证据不足的事项。没有搜索平台数据或真实 AI 答案样本时，不要推测实际流量、排名或引用率。
~~~

这里的 example.com 只是演示输入，并未在本次文档更新中实际巡检。若想生成某种报告或文件，可在指令中明确提出；AI 会根据当前工具是否支持创建文件说明产物位置。

### 在本地网页中使用

1. 启动 app.py 并打开上面的本机地址。
2. 输入公开网站网址，选择要检查的页面数；首次使用可选 10 页。
3. 如有自己导出的数据，可选填符合格式的 JSON 文件；不需要此项也能开始。
4. 点击开始并在页面查看评分、问题、证据和建议。
5. 通过页面按钮下载 Markdown 报告或 JSON 数据；文件位置由浏览器的下载设置决定。

### 给进阶用户：本地接口

如果你希望其他本地工具调用巡检功能，本地只读巡检接口：`POST /api/audit`。请用 JSON 发送公开网站网址和页面数；每次最多巡检 300 个同源页面。进度可通过 `GET /api/audit/status` 查看，接口说明见[网页入口说明](docs/WEB_ENTRY.md)。

### 用命令行生成文件

在项目文件夹中运行以下示例。它会检查最多 25 个页面，并在当前文件夹生成三份文件：

~~~powershell
python scripts/site_audit.py https://example.com --max-pages 25 --json-out audit.json --markdown-out audit.md --html-out audit.html
~~~

三个文件分别是完整 JSON 数据、Markdown 报告和可单独打开的 HTML 报告。把 audit.json 等文件名改成你希望保存的位置即可。macOS 或 Linux 终端中将 python 改为 python3。

要调整结果，可以补充站点类型、目标语言、重点页面或缩小检查范围。继续处理同一个网站时，可以在同一 AI 对话里补充资料或要求重新整理；准备检查另一个网站时，建议另开一个巡检任务，避免不同网站的证据混在一起。修复网站后需要再次运行巡检，工具不会自动跟踪变化。

<a id="workflow"></a>
## 八、项目工作流程

**提供公开网站网址与检查范围 → 读取站点公开页面 → 按证据标记发现 → 查看报告和验收建议 → 由你决定是否修复并再次巡检**

本地网页和命令行负责抓取页面并生成规则检查结果；AI Skill 根据项目规则整理分析、解释和后续行动。AI Skill、本地工具和在线入口并非同一套托管服务。你需要检查证据是否符合自己的网站情况，并自行或请开发者实施修改。

<a id="project-structure"></a>
## 九、项目目录结构

| 文件或目录 | 用途 |
|---|---|
| SKILL.md | AI Skill 的使用规则和证据标准。 |
| scripts/site_audit.py | 核心网页巡检脚本。 |
| app.py、web/ | 本地网页服务和中英文界面。 |
| references/audit-rubric.md | 问题分级与评分规则。 |
| assets/audit-report-template.md | 报告模板，不是实际运行结果。 |
| assets/logo.png、assets/project-cover.png | 项目标志和封面图。 |
| assets/ASSET_PROVENANCE.md | 项目图片素材的来源与使用记录。 |
| docs/browser-rendering.md | 可选浏览器复核的安装方法和限制。 |
| docs/external-evidence.md | 搜索平台和 AI 答案抽样数据的 JSON 格式。 |
| docs/WEB_ENTRY.md | 本地与在线入口的补充说明。 |
| LICENSE、CHANGELOG.md | 许可文本与项目变更记录。 |

正常使用时不需要编辑这些核心文件。命令行的输出文件保存到你传入的路径；网页下载的报告保存到浏览器下载位置。

<a id="notes-and-faq"></a>
## 十、注意事项与常见问题

### 它能告诉我 Google 排名或 AI 引用率吗？

不能只靠公开网页抓取得出这些真实数据。SearchScope 不会自动登录 Google Search Console、Bing Webmaster、GA4 或答案引擎。你可以按[外部数据导入说明](docs/external-evidence.md)提供符合格式的汇总数据；报告只代表你提供的日期和抽样范围，不是排名预测或完整的 AI 可见性结论。

### 为什么有些结论显示还要复核？

有些信息只有浏览器加载 JavaScript 后才能检查；另外一些结论需要搜索平台数据或真实答案引擎样本。报告会标记这些情况，而不是把它们当作已确认缺陷。

### 它会修改我的网站吗？

不会。工具只读取公开页面，不登录、不提交表单、不更改网站。修复步骤由你自己或你授权的开发者执行。

### 在线版和本地版一样吗？需要付费吗？

在线入口由仓库之外单独部署，仓库无法确认它现在提供的功能、账号要求、收费或数据处理细节。请以在线页面和所用 AI 工具的当前说明为准。代码许可见仓库中的 [Apache License 2.0](LICENSE)；项目图片素材的来源与使用记录见 [素材说明](assets/ASSET_PROVENANCE.md)。这些文件不代表所有第三方托管服务免费，也不表示所有目标网站内容都能自由再利用。

### 报告可以直接分享吗？

分享前请检查报告内容。报告可能包含目标网址、页面地址、标题和问题证据。你在本地网页或命令行导入的外部数据会在当前进程中汇总；报告只保留汇总数字，不保存原始页面行、查询文本或账号凭据。在线入口的数据处理方式应另行查看其页面说明。只导入你有权处理的资料；项目不会要求你提交网站登录凭据。

### 本地网页打不开怎么办？

确认 Python 3.10 或更高版本已安装，并且程序仍在启动它的终端中运行。若端口 8000 已被占用，可按照[网页入口说明](docs/WEB_ENTRY.md)更换本机端口。默认本地网页只允许检查公开网站；内网、回环和保留地址不会作为普通目标放行。

<a id="version"></a>
## 十一、版本说明

仓库文件标注的版本为：

- Skill 包：1.4.1
- 巡检规则引擎：1.4.9

CHANGELOG.md 当前记录在 Unreleased 栏目下，没有在该文件中标注正式发布版本或发布日期。版本号不代表结果准确率、排名或 AI 引用保证。后续变更请查看[变更记录](CHANGELOG.md)。

<a id="related-projects"></a>
## 十二、相关项目

无。

<a id="author"></a>
## 十三、关于作者

**Enhe（恩禾）｜产品设计师 · 一人公司实践者 · AI Builder**

用 AI 打造一人公司。

- GitHub：[yangjing6213-dev](https://github.com/yangjing6213-dev)
- X / Twitter：[Amenenhe_ai](https://x.com/Amenenhe_ai)
- 网站：[恩禾 ENHE AI](https://www.enhe-tech.com.cn/)
- 微信：Hu-Amen
- 邮箱：[amen.enhe@gmail.com](mailto:amen.enhe@gmail.com)

<a id="explore"></a>
## 十四、继续探索

我把一套重复的网站检查流程整理成了 SearchScope，希望它能成为别人也能使用、核对和继续修改的工具。如果你也在用 AI 整理内容、工作流程，或把想法做成可复用的小工具，欢迎继续了解我的个人创作与工作实践：

[访问恩禾 ENHE AI](https://www.enhe-tech.com.cn/)
