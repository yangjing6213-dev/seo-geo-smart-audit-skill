# SEO/GEO 巡检证据与分级规范

## 1. 证据等级

| 状态 | 可接受证据 | 可作结论 |
|---|---|---|
| `verified` | 当前 HTTP 响应、原始 HTML、渲染 DOM、sitemap、robots、用户提供的数据导出 | 可描述已观察到的事实 |
| `render_required` | 静态抓取无法覆盖的客户端渲染内容 | 只能要求浏览器复核 |
| `external_data_required` | GSC、Bing Webmaster、GA4、CrUX/PageSpeed 字段数据、答案引擎真实查询 | 只能描述数据缺口 |
| `hypothesis` | 间接迹象、抽样或不完整证据 | 只能提出调查方向 |

报告必须写明引擎规则版本、采集时间、目标 URL、抓取上限、User-Agent、语言/地区条件和任何失败请求。

## 2. 严重级别

| 级别 | 使用条件 | 示例 |
|---|---|---|
| Critical | 大范围阻止抓取、索引或访问核心页面 | 全站 5xx、robots 阻止全站、核心页错误 noindex |
| High | 明显压制关键页面收录、规范化或国际化信号 | sitemap 关键 URL 404、canonical 指向其他域、语言版本交叉 canonical |
| Medium | 影响发现、摘要质量、主题理解或部分页面表现 | 重复 title、hreflang 不互惠、内部链接薄弱、关键页无可见作者/日期 |
| Low | 低风险质量改进或待确认策略 | description 长度、少量 alt、可选机器可读资源、AI 爬虫策略确认 |
| Info | 数据缺口、已通过检查或监控建议 | 需要 CrUX 字段数据、静态 schema 需渲染复核 |

不要按问题数量计算“健康分”。若需要评分，必须公开权重，并让阻断级问题拥有否决权。

## 3. 技术 SEO 清单

### 抓取和索引

- 首页和关键模板返回预期 2xx。
- HTTP、HTTPS、www、非 www 的规范跳转一致。
- robots.txt 可读取，未意外阻止公开内容，并声明正确 sitemap。
- sitemap 只包含规范、可索引、成功响应 URL；检查重复 `<loc>`。
- 关键页面没有错误 noindex、软 404、循环或长重定向链。

### Canonical 与重复内容

- 唯一页面使用自引用 canonical。
- canonical 的协议、主机、路径大小写和尾斜杠与最终 URL 一致。
- canonical 指向同语言内容；跨语言 canonical 通常会压制非规范语言页。
- 参数页、筛选页和分页规则有明确策略，不凭静态抽样推断全站。

### 页面与内容

- title、description、H1 与页面意图一致，站内主要模板无明显重复。
- 一个页面原则上有一个清晰 H1；标题层级表达结构而非视觉样式。
- 重要图片有描述性 alt；装饰图片空 alt 不应算缺陷。
- 关键页面在三次左右点击内可达；识别孤立页和断链。
- 内容有真实作者、更新日期、来源、经验或案例等 E-E-A-T 证据。

### 结构化数据

- 静态 HTML 只能证明服务端输出的 JSON-LD。
- 对 JS 注入 schema 使用浏览器 DOM 或 Rich Results Test。
- 类型应匹配页面可见内容；解析成功不等于符合富结果资格。
- 对 Article/Product/Organization/BreadcrumbList 等检查关键字段和 URL 一致性。

### 性能

- LCP、INP、CLS 使用 CrUX、PageSpeed 字段数据或 GSC Core Web Vitals。
- 单次响应时长只能作为网络观测，不作为 Core Web Vitals 结论。
- PageSpeed 调用失败时明确写“未验证”，不要用本地加载速度代替。

## 4. 国际 SEO 清单

- 每个语言页具有唯一 URL，并使用正确 `<html lang>`。
- hreflang 使用有效语言/地区代码，包含自引用和互惠关系。
- 需要兜底时提供 `x-default`。
- hreflang 目标返回 200、可索引并与 canonical 一致。
- 不用包含 `/en` 的简单字符串判断语言；解析 pathname 的完整段。
- 不把只翻译导航、正文仍相同的页面视为高质量本地化。
- 使用 Accept-Language 或 IP 自动切换内容时，检查缓存 `Vary` 和 Googlebot 可发现性。

## 5. GEO 清单

### 可发现

- 按类别记录每个 Bot 的独立策略：搜索/引用 `OAI-SearchBot`、`PerplexityBot`；训练控制 `GPTBot`、`Google-Extended`、`ClaudeBot`；用户触发抓取 `ChatGPT-User`、`Claude-User`。
- 报告必须保留 `search`、`training`、`user_fetch` 类别；不能只输出一个合并后的允许/阻止结论。
- robots 决策需结合站点政策；训练控制与搜索/用户触发访问不能互相替代。
- 验证 Google 与 Bing 的基础索引入口；没有站长平台数据时不声称已收录。

### 可理解

- 品牌名、组织信息、作者、日期、来源和主要实体前后一致。
- 核心产品、服务、价格、限制和联系方式在公开页面可读取。
- 结构化数据与可见内容一致。
- `/llms.txt`、`/pricing.md`、知识包等属于增强项，不是 Google AI 功能的硬性门槛。

### 可引用

- 重点问题有直接、独立成立的答案段。
- 定义、步骤、对比和限制使用适合抽取的结构。
- 数字、统计和判断带原始来源与日期。
- 内容避免关键词堆砌、无来源结论和只面向机器的低价值变体。
- 用真实查询矩阵测量品牌提及和域名引用；没有探测结果时保持未知。

## 6. 报告验收

- 当前规则引擎版本为 `1.4.9`，报告必须在 `meta.engine_version` 中记录该版本。
- 每个 High/Critical 项至少有一条可复现证据和一条验收方法。
- 机器可读资源不接受 HTML 专属检查。
- “未检查”“检查失败”“不存在”分别表达。
- 修复建议指向最小责任边界，不扩展为无关重构。
- 最终报告列出成功请求、失败请求、抓取覆盖率和仍需人工/浏览器/平台数据验证的项目。
- 受管运行取消或超过总时限时必须以明确异常结束，不得把部分抓取结果报告为成功。
- 总时限是完整运行的硬截止时间，不是 socket inactivity timeout；响应体必须分块读取，并在每块读取前后检查取消与剩余总时限，底层读取超时不得以原始 `TimeoutError` 逸出。受管读取每个响应只启动一个 watchdog，不为每个分块创建线程；当 HTTP 或 HTTPS 响应头已到但响应体完全停顿时，取消或总时限到期必须通过 `shutdown` 并强制关闭底层 socket 描述符打断阻塞读取，精确回抛 `AuditCancelledError` 或 `AuditTimeoutError`。`should_cancel` 及其 `check_control` 包装必须快速、非阻塞；watchdog 在正常和异常路径都必须停止，并只做有界 `join`，不得让清理永久阻塞。若有界等待到期，不得覆盖正在传播的原始异常，也不得尝试强杀 Python 线程；回调解除阻塞后 watcher 必须自行退出。`KeyboardInterrupt` 和 `SystemExit` 等 `BaseException` 必须保持原类型、对象和消息传播，不得被并发产生的管理异常替换；未配置取消和总时限时继续遵守单请求 timeout 语义。
- 单请求 `timeout` 的公共合同固定为有限数值且 `0 < timeout <= 604800` 秒（7 天）。必须拒绝零、负数、NaN、正负 Infinity 和超过该上限的有限值，并在任何 DNS resolver 子进程或连接 socket 创建前使用固定脱敏错误结束；不得通过运行时探测或按当前平台动态改变该公共合同。
- `max_redirects` 必须是非 `bool` 的非负整数，并在任何网络请求、DNS resolver 或连接 socket 创建前验证；库和 CLI 均使用固定脱敏错误拒绝负数、非整数和异常类型，不得回显目标 URL。
- 受管运行应在每个网络请求和每轮页面遍历前检查取消与总时限，在每个页面处理后报告进度；页面间延迟必须按剩余总时限封顶并切片检查取消。
- 初始 URL 必须作为候选完成结构、凭据、协议、规范化和 DNS/IP 安全校验，只有解析成功后才可赋给 current/final URL；初始解析失败时 `final_url` 必须保留字段并返回 `None`，序列化结果不得包含未验证候选的 URL、hostname 或私密路径。未验证阶段禁止复制底层 `TimeoutError`、`URLError` 或 `OSError` 文本：初始解析只返回固定的 `Target resolution timed out` 或 `Target resolution failed`。每次收到重定向 `Location` 后，必须把 `urljoin`、结构校验、规范化和 DNS/IP 校验全部放在同一未验证边界内；包括 NFKC 非法 netloc 在内的 `ValueError`、`URLError`、`TimeoutError` 或 `OSError` 都必须映射为固定脱敏消息。只有验证通过后才可写入 redirect history 或更新 current/final URL。重定向候选解析失败只返回固定的 `Redirect target resolution timed out` 或 `Redirect target validation failed`。即使已经达到重定向上限，最后一个候选目标仍必须验证，恶意候选不得进入返回对象或异常；`AuditCancelledError` 和 `AuditTimeoutError` 仍必须精确回抛。
- 公网运行必须拒绝私网、回环、链路本地、云元数据、带凭据 URL、非 HTTP(S) URL，以及公开地址重定向到这些目标的请求；畸形 URL 和凭据 URL 的结构错误必须使用固定脱敏消息，不得回显用户名、密码、路径或完整输入 URL。
- 公网地址采用允许列表语义：只有 `ipaddress.is_global` 为真的地址可以连接，并显式拒绝 `169.254.169.254`、阿里云 ECS `100.100.100.200` 及 `100.64.0.0/10` shared range。
- DNS 校验与实际 TCP 连接必须使用同一组已验证解析结果，禁止连接阶段再次按主机名解析；每次重定向必须重新解析并验证。
- 固定解析结果不得破坏请求身份：HTTP `Host`、HTTPS SNI 和证书主机名校验必须继续使用原始 URL 主机名。
- 连接 socket 的生命周期必须覆盖 `settimeout`、bind、connect 和 TLS 包装阶段；任何 `OSError`、`OverflowError`、`ValueError` 或 TLS 异常都必须关闭原始或已包装 socket，不得留下文件描述符泄漏。
- Windows/Python 标准库不能安全中断进程内的系统 DNS；域名解析必须在 Python isolated mode（`-I`）的独立短生命周期子进程中执行。每次解析同时受单请求 `timeout` 和剩余总时限约束，以两者较小值为硬上限；即使未配置总时限，也不得超过单请求上限。取消或任一时限到期时必须终止并等待回收子进程，禁止用不可取消线程池积压解析任务。仅单请求 DNS 超时应形成受控请求失败，总时限到期仍必须抛出 `AuditTimeoutError`。解析器 stderr、Worker 环境凭据和用户完整 URL 不得进入命令行输出或异常。极短时限可能被进程启动成本消耗；若部署环境无法接受该成本，应替换为具备原生超时和取消能力的受控 DNS resolver 服务，而不是放宽截止时间或地址校验。
- 网络安全验收必须包含真实本地 HTTP/TLS 服务：验证 TCP 只连接已解析 IP，同时 HTTP `Host`、TLS SNI 和证书主机名校验仍使用原始 hostname。

## 7. 主要一方参考

- Google Search Essentials: https://developers.google.com/search/docs/essentials
- Google localized versions: https://developers.google.com/search/docs/specialty/international/localized-versions
- Google canonical guidance: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Google sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Google AI features guidance: https://developers.google.com/search/docs/fundamentals/ai-features
- Google Rich Results Test: https://search.google.com/test/rich-results
- Bing Webmaster Guidelines: https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a
- llms.txt proposal: https://llmstxt.org/
