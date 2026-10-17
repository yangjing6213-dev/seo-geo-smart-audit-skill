# 外部数据导入 / External Evidence Import

网页工具和命令行可以附加用户自行导出的搜索数据或 AI 答案抽样结果。导入只在当前进程中处理；报告只保留汇总数字，不保存原始页面行、查询内容或账号凭据，也不改变 SEO/GEO 基础评分。

The web app and CLI can attach user-exported search metrics or manually collected AI answer samples. Data is processed in memory; reports keep aggregate figures only. Raw page rows, query text, and account credentials are not stored, and imported figures do not change the base SEO/GEO score.

## 文件要求 / File Requirements

- 使用 UTF-8 编码的 JSON 文件，大小不超过 256 KiB。
- `schema_version` 必须为 `1`。
- 至少包含 `search_console` 或 `answer_engine_samples` 中的一项。
- Search Console 页面 URL 必须与本次巡检的协议、主机名和端口一致。
- 每条答案引擎样本代表一个问题；只填写引用 URL，不填写问题原文。
- 汇总结果只表示你提供的时间段和抽样范围，不代表排名预测或完整的 AI 可见性。

- Use a UTF-8 JSON file no larger than 256 KiB.
- `schema_version` must be `1`.
- Include at least `search_console` or `answer_engine_samples`.
- Search Console page URLs must match the audited target's scheme, hostname, and port.
- Click and impression counts must be nonnegative integers within the signed 64-bit range; average position must be finite and at most 1,000,000.
- Each answer-engine sample represents one query. Include cited URLs only; do not include the query text.
- The summary describes only the supplied period and sample. It is not a ranking forecast or a complete measure of AI visibility.

## 示例 / Example

```json
{
  "schema_version": 1,
  "search_console": {
    "period_start": "2026-10-01",
    "period_end": "2026-10-14",
    "rows": [
      {
        "url": "https://example.com/guide",
        "clicks": 24,
        "impressions": 600,
        "position": 6.2
      }
    ]
  },
  "answer_engine_samples": [
    {
      "engine": "ChatGPT Search",
      "checked_at": "2026-10-17",
      "samples": [
        { "cited_urls": ["https://example.com/guide"] },
        { "cited_urls": [] },
        { "cited_urls": ["https://another-site.example/page"] }
      ]
    }
  ]
}
```

Search Console 的点击率由总点击数除以总展示数计算；平均排名按展示次数加权。答案引擎引用率是“至少有一个引用 URL 属于目标站点的样本数 ÷ 样本总数”。工具不会检查这些外部 URL。

Search Console CTR is calculated as total clicks divided by total impressions; average position is weighted by impressions. The answer-engine citation rate is the share of samples with at least one URL on the target site. The tool does not fetch any of these supplied URLs.

点击数和展示数范围为 `0` 到 `9,223,372,036,854,775,807`；平均排名必须是 `0` 到 `1,000,000` 之间的有限数字。超出范围的数据会被拒绝，避免异常数字让报告无法生成。

## 使用方式 / How to Use

在网页工具中选择 JSON 文件后，照常输入站点并开始巡检。文件会随本次请求发送给本地应用，不会写入项目目录。

In the web app, choose the JSON file, enter the site, and start the audit. The file is sent with that request and is not written into the project directory.

命令行可选用同一文件：

The CLI accepts the same file:

```bash
python scripts/site_audit.py https://example.com --external-evidence evidence.json --json-out audit.json --markdown-out audit.md
```

目前不自动连接 Search Console、答案引擎或浏览器，也不会要求账号登录。把官方导出整理为上述格式后即可导入。JavaScript 渲染页面仍需单独的浏览器检查；自动启动浏览器尚未加入此版本。

The tool does not connect to Search Console, answer engines, or a browser, and does not request account login. Convert an authorized export to this format before import. JavaScript-rendered pages still need a separate browser check; automatic browser launching is not part of this version.
