# 可选浏览器复核 / Optional Browser Rendering

## 中文说明

浏览器复核默认关闭。勾选本地网页中的复核选项，或在命令行加上 `--render-browser` 后，程序会用 Chromium 检查最多 10 个已抓取页面的实际加载结果，并把标题、摘要、规范网址、页面语言、抓取指令、一级标题和结构化数据变化列入报告。这些观察是补充证据，不改变基础评分。

这项功能需要额外安装一次可选组件。请在项目文件夹中运行：

```bash
python -m pip install -r requirements-renderer.txt
python -m playwright install chromium
```

安装后，可在网页入口勾选“用浏览器检查页面实际加载后的内容”，或运行：

```bash
python scripts/site_audit.py https://example.com --max-pages 25 --render-browser
```

命令行和网页入口都只检查公开网站。浏览器不直接访问网站：程序会接管每个网页请求，并通过现有的安全抓取器加载同一网站的公开内容。私网、回环、保留地址和跨站资源会被阻止；只允许读取请求，不允许提交表单、发送写入请求或建立 WebSocket 连接。浏览器不使用你的登录账号或已有 Cookie，也不会保存完整的渲染后网页。

为控制运行时间和数据量，最多检查 10 页；每页最多处理 40 个浏览器请求、单个资源最多 1 MB、每页总量最多 5 MB。图片、字体、媒体、第三方资源和后台服务工作线程会被拦截，因此少数依赖这些内容的页面可能无法完整渲染。它不会测量页面速度、视觉布局或交互体验；这些仍需单独检查。

## English

Browser rendering is off by default. After you select the option in the local web app or pass `--render-browser` on the command line, Chromium checks the loaded DOM of up to 10 crawled pages. The report includes changes to titles, descriptions, canonical URLs, page language, crawl directives, H1 headings, and structured-data counts. These are supplemental observations and do not change the base score.

Install the optional components once from the project folder:

```bash
python -m pip install -r requirements-renderer.txt
python -m playwright install chromium
```

Then select the browser option in the web app or run:

```bash
python scripts/site_audit.py https://example.com --max-pages 25 --render-browser
```

Only public sites are checked. Chromium does not connect to the site directly: the application intercepts browser requests and serves eligible same-origin public content through the existing safe fetcher. Private, loopback, reserved, and cross-origin resources are blocked. Only read requests are allowed; form submission, write requests, and WebSockets are blocked. The browser does not use your login account or existing cookies, and the rendered page HTML is not retained.

To limit time and data use, rendering is capped at 10 pages, 40 browser requests per page, 1 MB per resource, and 5 MB per page. Images, fonts, media, third-party resources, and service workers are blocked, so some sites may not render completely. This feature does not measure page speed, visual layout, or interaction quality; those need separate checks.
