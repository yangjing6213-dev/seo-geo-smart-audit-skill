// Translation dictionary
const translations = {
  'zh-CN': {
    'meta.title': 'SearchScope｜独立站 SEO/GEO 智能巡检',
    'meta.description': '输入网址，检查独立站 SEO/GEO 基础，找出流量卡点并获得带证据的修复方案。',
    'creator.name': 'ENHE AI工作室',
    'header.subtitle': '一个不会让你失望的AI网站',
    'header.status': '在线工具',
    'hero.eyebrow': '公开网站检查',
    'hero.title': 'SearchScope',
    'hero.subtitle': '独立站 SEO/GEO 智能巡检',
    'hero.copy': '输入网址，一次看清搜索抓取、收录、页面结构、多语言和 AI 答案引擎可见性。报告会告诉你哪些做对了、哪里可能丢流量、先改什么，以及怎么验证。',
    'hero.point1': '技术 SEO',
    'hero.point2': '多语言',
    'hero.point3': '结构化数据',
    'hero.point4': 'GEO 可引用性',
    'hero.aside.desc': '把流量问题拆成能看懂、能执行、能验收的清单。',
    'hero.aside.link': '访问工作室官网',
    'hero.metric1': '页上限',
    'hero.metric2': '证据状态',
    'hero.metric3': '生产改动',
    'audit.step': '01 / 开始检查',
    'audit.title': '先输入你的网站',
    'audit.badge': '仅公开 URL · 不登录 · 不修改站点',
    'audit.urlLabel': '目标站点',
    'audit.pagesLabel': '巡检页数',
    'audit.pages10': '10 页 · 快速',
    'audit.pages25': '25 页 · 推荐',
    'audit.pages50': '50 页 · 深度',
    'audit.pages100': '100 页 · 完整',
    'audit.pages300': '300 页 · 最大',
    'audit.submit': '输入网址并开始巡检',
    'audit.evidenceLabel': '可选：导入搜索 / AI 抽样数据（JSON）',
    'audit.evidenceHelp': '只在本机汇总；不登录账号、不保存原始明细。',
    'audit.evidenceFormat': '查看数据格式',
    'audit.browserRenderLabel': '可选：用浏览器检查页面实际加载后的内容',
    'audit.browserRenderHelp': '默认关闭；需要单独安装浏览器组件。只加载同站公开只读资源。',
    'audit.browserRenderDocs': '查看安装和限制',
    'audit.evidenceTooLarge': '数据文件不能超过 256 KiB。',
    'audit.evidenceInvalid': '文件不是有效的 JSON。请检查文件后重试。',
    'audit.cancel': '取消巡检',
    'audit.progressLabel': '巡检进度',
    'audit.progressStarting': '正在读取站点目录并准备检查…',
    'audit.progressPages': '已检查 {processed} / {max} 个页面',
    'audit.progressRendering': '浏览器复核中：已完成 {processed} / {max} 页',
    'audit.progressComplete': '巡检完成。',
    'audit.progressCancelled': '巡检已取消。',
    'audit.progressTimeout': '巡检达到最长运行时间。',
    'audit.progressFailed': '巡检未能完成，请查看上方提示。',
    'audit.cancelRequested': '正在停止巡检，请稍候…',
    'audit.message': '默认阻止私网、回环和保留地址；不会提交表单、写入数据或执行答案引擎查询。',
    'empty.step': '02 / 报告会显示',
    'empty.title': '一份报告，帮你决定先改哪里。',
    'empty.verified': '当前静态抓取直接证明',
    'empty.render': '需浏览器渲染后确认',
    'empty.external': '需 GSC、CrUX 或真实平台探测',
    'report.step': '02 / 巡检报告',
    'report.title': '巡检结果',
    'report.downloadMd': '下载 Markdown',
    'report.downloadJson': '下载 JSON',
    'report.downloadPrompts': '下载智能体提示词',
    'report.scoreLabel': '网站健康度',
    'report.scoreWaiting': '等待评估',
    'report.scoreTitle': '这次检查结果怎么样',
    'report.scoreSummary': '完成检查后，这里会说明网站当前基础和最该先处理的问题。',
    'report.coverage': '检查证据完备度',
    'report.coverageHelp': '这是已有检查项中能得出结论的比例，不是已抓取页面比例。',
    'report.externalLabel': '补充数据',
    'report.externalTitle': '外部数据观察',
    'report.externalNote': '下列数字来自你导入的抽样或平台导出，不参与基础评分。',
    'report.browserRenderLabel': '补充检查',
    'report.browserRenderTitle': '浏览器渲染观察',
    'report.browserRenderNote': '最多抽查 10 页；观察结果不参与评分，渲染后的网页内容不会保存。',
    'report.pending': '待补证据',
    'report.deductions': '扣分依据',
    'report.strengthsLabel': '已经具备',
    'report.strengthsTitle': '当前 SEO/GEO 优势',
    'report.evidenceNote': '基于本次已抓取样本',
    'report.coverageLabel': '覆盖范围',
    'report.coverageTitle': '已抓取页面',
    'report.findingsLabel': '问题与方案',
    'report.findingsTitle': '按优先级处理',
    'report.recLabel': '其他优化建议',
    'report.recTitle': '建议的后续路线',
    'report.agentLabel': '交给智能体执行',
    'report.agentTitle': '修复提示词',
    'report.visitWebsite': '访问官网',
    'report.copyPrompt': '复制提示词',
    'agent.directoryLabel': '执行工具',
    'agent.directoryTitle': '选择你的智能体',
    'agent.directoryDesc': '将报告生成的提示词粘贴到对应工具，并在目标代码仓库中执行。',
    'agent.codex': 'OpenAI 编程智能体',
    'agent.openclaw': '开源个人智能体',
    'agent.claude': 'Anthropic 编程智能体',
    'footer.title': 'SearchScope',
    'footer.tagline': '只读 · 可复现 · 证据优先',
    'footer.creator': '创作者：',
    'loading': '正在检查网站，请稍候…',
    'message.required': '请输入公开站点 URL。',
    'message.running': '正在检查公开页面、收录信号、页面结构和机器可读资源。',
    'message.complete': '检查完成。先看评分和扣分依据，再按顺序处理问题。',
    'message.failed': '巡检请求失败。',
    'severity.all': '全部',
    'severity.critical': '严重',
    'severity.high': '高',
    'severity.medium': '中',
    'severity.low': '低',
    'severity.info': '信息',
    'status.verified': '已验证',
    'status.render_required': '需渲染复核',
    'status.external_data_required': '需外部数据',
    'status.hypothesis': '待验证假设',
    'summary.strengths': '已验证优势',
    'summary.issues': '问题与待取证',
    'summary.urgent': '高优先级',
    'summary.render': '需渲染复核',
    'summary.external': '外部数据待补',
    'score.pendingSuffix': '项',
    'score.points': '分',
    'score.noDeduction': '本次没有需要扣分的已验证问题。',
    'score.excellentLabel': '基础扎实',
    'score.excellentSummary': '网站基础做得不错。接下来补齐细节和待验证数据，就能更稳地提升搜索与答案引擎可见性。',
    'score.goodLabel': '整体良好',
    'score.goodSummary': '网站具备可用基础，但还有几处会拖慢收录或影响页面理解的问题，按扣分项逐个处理即可。',
    'score.optimizeLabel': '需要优化',
    'score.optimizeSummary': '当前有多项基础问题正在影响抓取、收录或内容理解，建议先处理扣分最高的项目。',
    'score.urgentLabel': '优先修复',
    'score.urgentSummary': '目前的基础问题较集中，可能明显影响搜索流量。先修复严重和高优先级问题，再补做其他优化。',
    'strength.none': '本次样本尚未形成可确认的优势项。',
    'strength.verified': '已验证',
    'strength.details': '查看优势证据',
    'finding.none': '当前筛选条件下没有问题。',
    'finding.solution': '解决方案',
    'finding.verification': '验收方式：',
    'finding.evidence': '查看当前证据',
    'coverage.nonHtml': '非 HTML',
    'coverage.robotsBlocked': 'robots 阻止',
    'coverage.none': '未抓取到页面。',
    'recommendation.next': '下一步：',
    'recommendation.none': '当前没有额外建议。',
    'external.searchConsole': 'Search Console',
    'external.period': '数据周期',
    'external.rows': '页面行数',
    'external.clicks': '点击',
    'external.impressions': '展示',
    'external.ctr': '汇总点击率',
    'external.position': '按展示加权的平均排名',
    'external.answerEngine': '答案引擎抽样',
    'external.sampleSize': '抽样问题数',
    'external.citations': '引用本站的问题数',
    'external.citationRate': '抽样引用率',
    'external.noPosition': '未提供',
    'browser.summary': '浏览器检查汇总',
    'browser.renderedPages': '成功渲染 / 抽样页面',
    'browser.blockedRequests': '已拦截请求',
    'browser.samplePage': '抽样页面',
    'browser.statusCompleted': '完成',
    'browser.statusFailed': '未完成',
    'browser.http': 'HTTP',
    'browser.title': '页面标题',
    'browser.noTitle': '未检测到页面标题',
    'browser.description': '摘要描述',
    'browser.noDescription': '未检测到摘要描述',
    'browser.h1': '一级标题',
    'browser.noH1': '未检测到一级标题',
    'browser.differences': '与静态抓取不同',
    'browser.noDifferences': '未发现差异',
    'browser.canonical': '规范网址',
    'browser.language': '页面语言',
    'browser.robots': '抓取指令',
    'browser.structuredData': '结构化数据块',
    'prompt.none': '本次报告没有生成智能体提示词。',
    'prompt.website': '官网：',
    'copy.success': '已复制',
    'copy.failed': '复制失败',
  },
  'en': {
    'meta.title': 'SearchScope | Independent Site SEO/GEO Auditor',
    'meta.description': 'Enter a website URL to audit SEO/GEO foundations, identify traffic blockers, and get evidence-backed fixes.',
    'creator.name': 'ENHE AI Studio',
    'header.subtitle': 'An AI website that won\'t disappoint you',
    'header.status': 'Online Tool',
    'hero.eyebrow': 'Public Website Check',
    'hero.title': 'SearchScope',
    'hero.subtitle': 'SEO/GEO Audit for Independent Sites',
    'hero.copy': 'Enter a URL to see search crawling, indexing, page structure, multilingual and AI answer engine visibility at once. The report tells you what\'s right, where you might lose traffic, what to fix first, and how to verify.',
    'hero.point1': 'Technical SEO',
    'hero.point2': 'Multilingual',
    'hero.point3': 'Structured Data',
    'hero.point4': 'GEO Citation Readiness',
    'hero.aside.desc': 'Break traffic issues into understandable, actionable, verifiable checklists.',
    'hero.aside.link': 'Visit Studio Website',
    'hero.metric1': 'Page Limit',
    'hero.metric2': 'Evidence Status',
    'hero.metric3': 'Production Changes',
    'audit.step': '01 / Start Check',
    'audit.title': 'Enter your website first',
    'audit.badge': 'Public URL only · No login · No site changes',
    'audit.urlLabel': 'Target Site',
    'audit.pagesLabel': 'Audit Pages',
    'audit.pages10': '10 pages · Quick',
    'audit.pages25': '25 pages · Recommended',
    'audit.pages50': '50 pages · Deep',
    'audit.pages100': '100 pages · Complete',
    'audit.pages300': '300 pages · Maximum',
    'audit.submit': 'Enter a URL and Start Audit',
    'audit.evidenceLabel': 'Optional: import search or AI sample data (JSON)',
    'audit.evidenceHelp': 'Summarized locally; no account login or raw rows are stored.',
    'audit.evidenceFormat': 'View data format',
    'audit.browserRenderLabel': 'Optional: check the page after it loads in a browser',
    'audit.browserRenderHelp': 'Off by default; requires a separate browser setup. Only same-site public read-only resources are loaded.',
    'audit.browserRenderDocs': 'View setup and limits',
    'audit.evidenceTooLarge': 'The data file must be 256 KiB or smaller.',
    'audit.evidenceInvalid': 'The file is not valid JSON. Check it and try again.',
    'audit.cancel': 'Cancel audit',
    'audit.progressLabel': 'Audit progress',
    'audit.progressStarting': 'Reading site discovery files and preparing checks…',
    'audit.progressPages': 'Checked {processed} / {max} pages',
    'audit.progressRendering': 'Browser check: {processed} / {max} pages processed',
    'audit.progressComplete': 'Audit complete.',
    'audit.progressCancelled': 'Audit cancelled.',
    'audit.progressTimeout': 'The audit reached its time limit.',
    'audit.progressFailed': 'The audit could not be completed. See the message above.',
    'audit.cancelRequested': 'Stopping the audit…',
    'audit.message': 'Blocks private, loopback and reserved addresses by default; no form submission, data writing or answer engine queries.',
    'empty.step': '02 / Report Shows',
    'empty.title': 'A report to help you decide what to fix first.',
    'empty.verified': 'Proven by current static crawl',
    'empty.render': 'Needs browser rendering to confirm',
    'empty.external': 'Needs GSC, CrUX or real platform detection',
    'report.step': '02 / Audit Report',
    'report.title': 'Audit Results',
    'report.downloadMd': 'Download Markdown',
    'report.downloadJson': 'Download JSON',
    'report.downloadPrompts': 'Download Agent Prompts',
    'report.scoreLabel': 'Site Health',
    'report.scoreWaiting': 'Waiting for evaluation',
    'report.scoreTitle': 'How is this check result',
    'report.scoreSummary': 'After the check, this will explain the site\'s current baseline and what to handle first.',
    'report.coverage': 'Evidence completeness',
    'report.coverageHelp': 'This is the share of checks with a conclusion, not the share of pages crawled.',
    'report.externalLabel': 'Supplemental data',
    'report.externalTitle': 'External data observations',
    'report.externalNote': 'These figures come from your imported samples or platform export and do not affect the base score.',
    'report.browserRenderLabel': 'Additional check',
    'report.browserRenderTitle': 'Browser-rendered observations',
    'report.browserRenderNote': 'Up to 10 pages are sampled. These observations do not affect the score, and rendered page HTML is not retained.',
    'report.pending': 'Pending Evidence',
    'report.deductions': 'Deduction Basis',
    'report.strengthsLabel': 'Already Have',
    'report.strengthsTitle': 'Current SEO/GEO Advantages',
    'report.evidenceNote': 'Based on this crawled sample',
    'report.coverageLabel': 'Coverage',
    'report.coverageTitle': 'Crawled Pages',
    'report.findingsLabel': 'Issues & Solutions',
    'report.findingsTitle': 'Handle by Priority',
    'report.recLabel': 'Other Optimization Suggestions',
    'report.recTitle': 'Recommended Next Steps',
    'report.agentLabel': 'Hand over to Agent',
    'report.agentTitle': 'Fix Prompts',
    'report.visitWebsite': 'Visit Website',
    'report.copyPrompt': 'Copy Prompt',
    'agent.directoryLabel': 'Execution Tools',
    'agent.directoryTitle': 'Choose Your Agent',
    'agent.directoryDesc': 'Paste the generated prompts into the corresponding tool and execute in the target code repository.',
    'agent.codex': 'OpenAI Coding Agent',
    'agent.openclaw': 'Open Source Personal Agent',
    'agent.claude': 'Anthropic Coding Agent',
    'footer.title': 'SearchScope',
    'footer.tagline': 'Read-only · Reproducible · Evidence-first',
    'footer.creator': 'Created by: ',
    'loading': 'Checking website, please wait...',
    'message.required': 'Enter a public website URL.',
    'message.running': 'Checking public pages, indexability signals, page structure, and machine-readable assets.',
    'message.complete': 'Audit complete. Review the score and deductions, then address issues in priority order.',
    'message.failed': 'The audit request failed.',
    'severity.all': 'All',
    'severity.critical': 'Critical',
    'severity.high': 'High',
    'severity.medium': 'Medium',
    'severity.low': 'Low',
    'severity.info': 'Info',
    'status.verified': 'Verified',
    'status.render_required': 'Render check required',
    'status.external_data_required': 'External data required',
    'status.hypothesis': 'Hypothesis to verify',
    'summary.strengths': 'Verified strengths',
    'summary.issues': 'Issues and evidence gaps',
    'summary.urgent': 'High priority',
    'summary.render': 'Render checks',
    'summary.external': 'External data gaps',
    'score.pendingSuffix': 'items',
    'score.points': 'points',
    'score.noDeduction': 'No verified issues caused a score deduction.',
    'score.excellentLabel': 'Strong foundation',
    'score.excellentSummary': 'The site has a strong baseline. Close the remaining detail and evidence gaps to improve search and answer-engine visibility more consistently.',
    'score.goodLabel': 'Good overall',
    'score.goodSummary': 'The site has a usable foundation, with several issues that may slow indexing or weaken page understanding. Address the deductions in order.',
    'score.optimizeLabel': 'Needs optimization',
    'score.optimizeSummary': 'Several foundational issues are affecting crawling, indexing, or content understanding. Start with the largest deductions.',
    'score.urgentLabel': 'Fix first',
    'score.urgentSummary': 'Foundational problems are concentrated and may materially affect search traffic. Resolve critical and high-priority issues first.',
    'strength.none': 'No confirmed strengths were established in this sample.',
    'strength.verified': 'Verified',
    'strength.details': 'View supporting evidence',
    'finding.none': 'No issues match the current filter.',
    'finding.solution': 'Solution',
    'finding.verification': 'Acceptance check: ',
    'finding.evidence': 'View current evidence',
    'coverage.nonHtml': 'Non-HTML',
    'coverage.robotsBlocked': 'blocked by robots',
    'coverage.none': 'No pages were crawled.',
    'recommendation.next': 'Next step: ',
    'recommendation.none': 'No additional recommendations are available.',
    'external.searchConsole': 'Search Console',
    'external.period': 'Data period',
    'external.rows': 'Page rows',
    'external.clicks': 'Clicks',
    'external.impressions': 'Impressions',
    'external.ctr': 'Combined CTR',
    'external.position': 'Impression-weighted average position',
    'external.answerEngine': 'Answer-engine sample',
    'external.sampleSize': 'Query samples',
    'external.citations': 'Samples citing this site',
    'external.citationRate': 'Sample citation rate',
    'external.noPosition': 'Not provided',
    'browser.summary': 'Browser check summary',
    'browser.renderedPages': 'Rendered / sampled pages',
    'browser.blockedRequests': 'Blocked requests',
    'browser.samplePage': 'Sample page',
    'browser.statusCompleted': 'Complete',
    'browser.statusFailed': 'Incomplete',
    'browser.http': 'HTTP',
    'browser.title': 'Page title',
    'browser.noTitle': 'No page title found',
    'browser.description': 'Description',
    'browser.noDescription': 'No description found',
    'browser.h1': 'Main headings',
    'browser.noH1': 'No main heading found',
    'browser.differences': 'Different from static crawl',
    'browser.noDifferences': 'No differences found',
    'browser.canonical': 'Canonical URL',
    'browser.language': 'Page language',
    'browser.robots': 'Crawl directives',
    'browser.structuredData': 'Structured data blocks',
    'prompt.none': 'No coding-agent prompts were generated for this audit.',
    'prompt.website': 'Website: ',
    'copy.success': 'Copied',
    'copy.failed': 'Copy failed',
  }
};

let currentLang = 'zh-CN';

function translate(key) {
  return translations[currentLang]?.[key] ?? translations['zh-CN'][key] ?? key;
}

function applyLanguage(lang) {
  currentLang = translations[lang] ? lang : 'zh-CN';
  document.documentElement.lang = currentLang;
  const dict = translations[currentLang];
  document.title = dict['meta.title'];
  document.querySelector('#audit-progress-bar')?.setAttribute('aria-label', translate('audit.progressLabel'));
  const description = document.querySelector('#page-description');
  if (description) description.content = dict['meta.description'];

  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  // Update select options
  document.querySelectorAll('select option[data-i18n]').forEach(option => {
    const key = option.getAttribute('data-i18n');
    if (dict[key]) {
      option.textContent = dict[key];
    }
  });

  // Update language switcher buttons
  document.querySelectorAll('.language-option').forEach(btn => {
    const isActive = btn.dataset.language === currentLang;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', String(isActive));
  });

  if (latestResult) renderReport(latestResult, false);
  renderMessage();
  if (latestAuditStatus) renderAuditProgress(latestAuditStatus);

  // Store preference
  try {
    localStorage.setItem('preferred-language', currentLang);
  } catch (e) {
    // Ignore storage errors
  }
}

function initLanguageSwitcher() {
  // Check stored preference
  let savedLang = 'zh-CN';
  try {
    savedLang = localStorage.getItem('preferred-language') || 'zh-CN';
  } catch (e) {
    // Ignore storage errors
  }

  // Apply initial language
  applyLanguage(savedLang);

  // Bind click events
  document.querySelectorAll('.language-option').forEach(btn => {
    btn.addEventListener('click', () => {
      applyLanguage(btn.dataset.language);
    });
  });
}

const form = document.querySelector('#audit-form');
const urlInput = document.querySelector('#target-url');
const maxPagesInput = document.querySelector('#max-pages');
const externalEvidenceFileInput = document.querySelector('#external-evidence-file');
const submitButton = document.querySelector('#submit-button');
const message = document.querySelector('#form-message');
const auditProgress = document.querySelector('#audit-progress');
const auditProgressText = document.querySelector('#audit-progress-text');
const auditProgressBar = document.querySelector('#audit-progress-bar');
const cancelAuditButton = document.querySelector('#cancel-audit');
const emptyState = document.querySelector('#empty-state');
const report = document.querySelector('#report');
const scoreValue = document.querySelector('#score-value');
const scoreLabel = document.querySelector('#score-label');
const scoreSummary = document.querySelector('#score-summary');
const scoreCoverage = document.querySelector('#score-coverage');
const scorePending = document.querySelector('#score-pending');
const scoreDeductions = document.querySelector('#score-deductions');
const summaryCards = document.querySelector('#summary-cards');
const strengthsList = document.querySelector('#strengths-list');
const findingsList = document.querySelector('#findings-list');
const filters = document.querySelector('#severity-filters');
const coverageList = document.querySelector('#coverage-list');
const recommendationsList = document.querySelector('#recommendations-list');
const externalEvidenceSection = document.querySelector('#external-evidence-section');
const externalEvidenceList = document.querySelector('#external-evidence-list');
const browserRenderCheckbox = document.querySelector('#render-browser');
const browserRenderSection = document.querySelector('#browser-render-section');
const browserRenderList = document.querySelector('#browser-render-list');
const agentSelector = document.querySelector('#agent-selector');
const agentPromptName = document.querySelector('#agent-prompt-name');
const agentPromptWebsite = document.querySelector('#agent-prompt-website');
const agentPromptContent = document.querySelector('#agent-prompt-content');
const copyAgentPromptButton = document.querySelector('#copy-agent-prompt');
const MAX_EXTERNAL_EVIDENCE_BYTES = 262144;
let latestResult = null;
let activeSeverity = 'all';
let activeAgent = 'codex';
let messageState = { key: 'audit.message', text: '', isError: false };
let auditInProgress = false;
let auditProgressTimer = null;
let latestAuditStatus = null;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initLanguageSwitcher);
} else {
  initLanguageSwitcher();
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatEvidence(evidence) {
  if (typeof evidence === 'string') return evidence;
  return JSON.stringify(evidence, null, 2);
}

function renderMessage() {
  message.textContent = messageState.key
    ? translate(messageState.key)
    : messageState.text;
  message.classList.toggle('error', messageState.isError);
}

function showMessage(text, isError = false) {
  messageState = { key: null, text, isError };
  renderMessage();
}

function showTranslatedMessage(key, isError = false) {
  messageState = { key, text: '', isError };
  renderMessage();
}

function renderAuditProgress(status) {
  if (!status || status.status === 'idle') return;
  latestAuditStatus = status;
  auditProgress.classList.remove('hidden');
  if (status.running) {
    const processed = Number(status.pages_processed) || 0;
    const max = Number(status.max_pages) || 0;
    const progressMessage = status.phase === 'browser_render'
      ? translate('audit.progressRendering')
      : translate('audit.progressPages');
    auditProgressText.textContent = processed
      ? progressMessage.replace('{processed}', processed).replace('{max}', max)
      : translate('audit.progressStarting');
    auditProgressBar.value = max ? Math.min(100, Math.round((processed / max) * 100)) : 0;
    cancelAuditButton.classList.remove('hidden');
    cancelAuditButton.disabled = false;
    return;
  }

  const messages = {
    starting: 'audit.progressStarting',
    completed: 'audit.progressComplete',
    cancelled: 'audit.progressCancelled',
    timeout: 'audit.progressTimeout',
    failed: 'audit.progressFailed',
  };
  const messageKey = messages[status.status];
  if (messageKey) auditProgressText.textContent = translate(messageKey);
  if (status.status === 'completed') auditProgressBar.value = 100;
  cancelAuditButton.classList.add('hidden');
  cancelAuditButton.disabled = false;
}

async function refreshAuditProgress() {
  try {
    const response = await fetch('/api/audit/status', { cache: 'no-store' });
    if (response.ok) {
      const status = await response.json();
      if (!auditInProgress || status.running) renderAuditProgress(status);
    }
  } catch {
    // The audit response remains the source of truth if progress polling fails.
  }
}

function renderSummary(summary) {
  const counts = summary.finding_counts || {};
  const urgentCount = (counts.critical ?? 0) + (counts.high ?? 0);
  const cards = [
    { label: translate('summary.strengths'), value: summary.strength_count ?? latestResult.audit.strengths.length, className: 'positive' },
    { label: translate('summary.issues'), value: latestResult.audit.findings.length, className: '' },
    { label: translate('summary.urgent'), value: urgentCount, className: urgentCount ? 'high' : 'positive' },
    { label: translate('summary.render'), value: latestResult.audit.findings.filter((item) => item.status === 'render_required').length, className: 'info' },
    { label: translate('summary.external'), value: latestResult.audit.findings.filter((item) => item.status === 'external_data_required').length, className: 'info' },
  ];
  summaryCards.innerHTML = cards.map((card) => `
    <article class="summary-card ${card.className}">
      <span class="label">${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
    </article>
  `).join('');
}

function renderScore(score) {
  let tier = 'urgent';
  if (score.overall >= 90) tier = 'excellent';
  else if (score.overall >= 75) tier = 'good';
  else if (score.overall >= 60) tier = 'optimize';
  scoreValue.textContent = score.overall;
  scoreLabel.textContent = translate(`score.${tier}Label`);
  scoreSummary.textContent = translate(`score.${tier}Summary`);
  scoreCoverage.textContent = `${score.evidence_coverage}%`;
  scorePending.textContent = `${score.pending_count} ${translate('score.pendingSuffix')}`;
  scoreDeductions.innerHTML = score.deductions.length
    ? score.deductions.map((item) => `
      <div class="score-deduction">
        <span>${escapeHtml(item.finding_id)} · -${escapeHtml(item.points)} ${escapeHtml(translate('score.points'))}</span>
        <p>${escapeHtml(item.issue)}</p>
      </div>
    `).join('')
    : `<p class="score-no-deduction">${escapeHtml(translate('score.noDeduction'))}</p>`;
}

function renderStrengths() {
  const strengths = latestResult.audit.strengths || [];
  if (!strengths.length) {
    strengthsList.innerHTML = `<p class="empty-findings">${escapeHtml(translate('strength.none'))}</p>`;
    return;
  }
  strengthsList.innerHTML = strengths.map((item) => `
    <article class="strength-item">
      <div class="strength-top"><span>${escapeHtml(item.id)} · ${escapeHtml(item.category)}</span><b>${escapeHtml(translate('strength.verified'))}</b></div>
      <h4>${escapeHtml(item.title)}</h4>
      <p>${escapeHtml(item.value)}</p>
      <details>
        <summary>${escapeHtml(translate('strength.details'))}</summary>
        <pre>${escapeHtml(formatEvidence(item.evidence))}</pre>
      </details>
    </article>
  `).join('');
}

function renderFilters() {
  const available = ['all', 'critical', 'high', 'medium', 'low', 'info'];
  filters.innerHTML = available.map((severity) => {
    const label = translate(`severity.${severity}`);
    return `<button class="filter-button ${severity === activeSeverity ? 'active' : ''}" type="button" data-severity="${severity}">${label}</button>`;
  }).join('');
  filters.querySelectorAll('button').forEach((button) => {
    button.addEventListener('click', () => {
      activeSeverity = button.dataset.severity;
      renderFilters();
      renderFindings();
    });
  });
}

function renderFindings() {
  const findings = latestResult.audit.findings.filter((finding) => activeSeverity === 'all' || finding.severity === activeSeverity);
  if (!findings.length) {
    findingsList.innerHTML = `<p class="empty-findings">${escapeHtml(translate('finding.none'))}</p>`;
    return;
  }

  findingsList.innerHTML = findings.map((finding) => `
    <article class="finding ${escapeHtml(finding.severity)}">
      <div class="finding-top">
        <span class="finding-code">${escapeHtml(finding.id)} · ${escapeHtml(finding.category)} · ${escapeHtml(finding.code)}</span>
        <span class="severity">${escapeHtml(translate(`severity.${finding.severity}`))}</span>
      </div>
      <h4>${escapeHtml(finding.issue)}</h4>
      <span class="status ${escapeHtml(finding.status)}">${escapeHtml(translate(`status.${finding.status}`))}</span>
      <div class="solution-block"><span>${escapeHtml(translate('finding.solution'))}</span><p>${escapeHtml(finding.action)}</p></div>
      <p class="verification-line"><strong>${escapeHtml(translate('finding.verification'))}</strong>${escapeHtml(finding.verification)}</p>
      <details>
        <summary>${escapeHtml(translate('finding.evidence'))}</summary>
        <pre>${escapeHtml(formatEvidence(finding.evidence))}</pre>
      </details>
    </article>
  `).join('');
}

function renderCoverage(pages) {
  const visiblePages = (pages || []).slice(0, 25);
  coverageList.innerHTML = visiblePages.map((page) => `
    <article class="coverage-item">
      <div class="coverage-url" title="${escapeHtml(page.url)}">${escapeHtml(page.url)}</div>
      <div class="coverage-meta">HTTP ${escapeHtml(page.status ?? '—')} · ${page.is_html ? 'HTML' : escapeHtml(translate('coverage.nonHtml'))}${page.blocked_by_robots ? ` · ${escapeHtml(translate('coverage.robotsBlocked'))}` : ''}</div>
    </article>
  `).join('') || `<p class="empty-findings">${escapeHtml(translate('coverage.none'))}</p>`;
}

function renderExternalEvidence(evidence) {
  const cards = [];
  const searchConsole = evidence?.search_console;
  if (searchConsole) {
    const position = searchConsole.average_position === null
      ? translate('external.noPosition')
      : searchConsole.average_position;
    cards.push(`
      <article class="summary-card">
        <span class="label">${escapeHtml(translate('external.searchConsole'))} · ${escapeHtml(translate('external.period'))}: ${escapeHtml(searchConsole.period_start)} – ${escapeHtml(searchConsole.period_end)}</span>
        <strong>${escapeHtml(searchConsole.ctr_percent)}%</strong>
        <p>${escapeHtml(translate('external.rows'))}: ${escapeHtml(searchConsole.page_rows)} · ${escapeHtml(translate('external.clicks'))}: ${escapeHtml(searchConsole.clicks)} · ${escapeHtml(translate('external.impressions'))}: ${escapeHtml(searchConsole.impressions)} · ${escapeHtml(translate('external.position'))}: ${escapeHtml(position)}</p>
      </article>
    `);
  }
  (evidence?.answer_engine_samples || []).forEach((sample) => {
    cards.push(`
      <article class="summary-card">
        <span class="label">${escapeHtml(translate('external.answerEngine'))} · ${escapeHtml(sample.checked_at)}</span>
        <strong>${escapeHtml(sample.citation_rate_percent)}%</strong>
        <p>${escapeHtml(sample.engine)} · ${escapeHtml(translate('external.citations'))}: ${escapeHtml(sample.queries_with_site_citation)} / ${escapeHtml(sample.query_samples)} ${escapeHtml(translate('external.sampleSize').toLowerCase())}</p>
      </article>
    `);
  });
  externalEvidenceList.innerHTML = cards.join('');
  externalEvidenceSection.classList.toggle('hidden', cards.length === 0);
}

function renderBrowserEvidence(rendering, pages) {
  if (!rendering?.enabled) {
    browserRenderSection.classList.add('hidden');
    browserRenderList.innerHTML = '';
    return;
  }

  const cards = [`
    <article class="summary-card">
      <span class="label">${escapeHtml(translate('browser.summary'))}</span>
      <strong>${escapeHtml(rendering.rendered_pages ?? 0)} / ${escapeHtml(rendering.sampled_pages ?? 0)}</strong>
      <p>${escapeHtml(translate('browser.renderedPages'))} · ${escapeHtml(translate('browser.blockedRequests'))}: ${escapeHtml(rendering.blocked_requests ?? 0)}</p>
    </article>
  `];
  const fieldLabels = {
    title: translate('browser.title'),
    meta_description: translate('browser.description'),
    canonical: translate('browser.canonical'),
    html_lang: translate('browser.language'),
    robots_directive: translate('browser.robots'),
    h1: translate('browser.h1'),
    json_ld_static_count: translate('browser.structuredData'),
  };
  (pages || []).forEach((page, index) => {
    const observation = page.browser_render;
    if (!observation) return;
    const status = observation.status === 'completed'
      ? translate('browser.statusCompleted')
      : translate('browser.statusFailed');
    const title = observation.title || translate('browser.noTitle');
    const description = observation.meta_description || translate('browser.noDescription');
    const headings = (observation.h1 || []).join('、') || translate('browser.noH1');
    const differences = (observation.differences || [])
      .map((field) => fieldLabels[field] || field)
      .join('、') || translate('browser.noDifferences');
    cards.push(`
      <article class="summary-card">
        <span class="label">${escapeHtml(translate('browser.samplePage'))} ${index + 1} · ${escapeHtml(status)} · ${escapeHtml(translate('browser.http'))} ${escapeHtml(observation.http_status ?? '—')}</span>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(translate('browser.description'))}: ${escapeHtml(description)}</p>
        <p>${escapeHtml(translate('browser.h1'))}: ${escapeHtml(headings)}</p>
        <p>${escapeHtml(translate('browser.differences'))}: ${escapeHtml(differences)}</p>
        ${observation.error ? `<p>${escapeHtml(observation.error)}</p>` : ''}
      </article>
    `);
  });
  browserRenderList.innerHTML = cards.join('');
  browserRenderSection.classList.remove('hidden');
}

function renderRecommendations() {
  const recommendations = latestResult.audit.recommendations || [];
  recommendationsList.innerHTML = recommendations.map((item) => `
    <article class="recommendation-item">
      <span>${escapeHtml(item.priority)}</span>
      <div>
        <h4>${escapeHtml(item.title)}</h4>
        <p>${escapeHtml(item.reason)}</p>
        <p><strong>${escapeHtml(translate('recommendation.next'))}</strong>${escapeHtml(item.next_step)}</p>
      </div>
    </article>
  `).join('') || `<p class="empty-findings">${escapeHtml(translate('recommendation.none'))}</p>`;
}

function renderAgentPrompts() {
  const prompts = latestResult.audit.agent_prompts || [];
  if (!prompts.length) {
    agentSelector.innerHTML = '';
    agentPromptContent.textContent = translate('prompt.none');
    return;
  }
  if (!prompts.some((item) => item.id === activeAgent)) activeAgent = prompts[0].id;
  agentSelector.innerHTML = prompts.map((item) => `
    <button class="agent-selector-button ${item.id === activeAgent ? 'active' : ''}" type="button" data-agent="${escapeHtml(item.id)}">${escapeHtml(item.name)}</button>
  `).join('');
  agentSelector.querySelectorAll('button').forEach((button) => {
    button.addEventListener('click', () => {
      activeAgent = button.dataset.agent;
      renderAgentPrompts();
    });
  });
  const selected = prompts.find((item) => item.id === activeAgent) || prompts[0];
  agentPromptName.textContent = selected.name;
  agentPromptWebsite.href = selected.website;
  agentPromptContent.textContent = selected.prompt;
}

function formatReportMeta(audit) {
  const locale = currentLang === 'en' ? 'en-US' : 'zh-CN';
  const finishedAt = new Date(audit.meta.finished_at).toLocaleString(locale, { hour12: false });
  if (currentLang === 'en') {
    return `Completed ${finishedAt} · ${audit.summary.html_pages} HTML pages · ${audit.summary.failed_pages} failed pages`;
  }
  return `完成于 ${finishedAt} · ${audit.summary.html_pages} 个 HTML 页面 · ${audit.summary.failed_pages} 个失败页面`;
}

function renderReport(result, scrollToReport = true) {
  latestResult = result;
  activeSeverity = 'all';
  activeAgent = 'codex';
  const { audit } = result;
  document.querySelector('#report-target').textContent = audit.meta.target;
  document.querySelector('#report-meta').textContent = formatReportMeta(audit);
  renderScore(audit.score);
  renderSummary(audit.summary);
  renderExternalEvidence(audit.external_evidence);
  renderBrowserEvidence(audit.browser_rendering, audit.pages);
  renderStrengths();
  renderFilters();
  renderFindings();
  renderCoverage(audit.pages);
  renderRecommendations();
  renderAgentPrompts();
  emptyState.classList.add('hidden');
  report.classList.remove('hidden');
  if (scrollToReport) report.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function download(content, filename, contentType) {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([content], { type: contentType }));
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.append(textarea);
  textarea.select();
  document.execCommand('copy');
  textarea.remove();
}

function buildPromptBundle() {
  return (latestResult?.audit.agent_prompts || []).map((item) => [
    `# ${item.name}`,
    `${translate('prompt.website')}${item.website}`,
    '',
    item.prompt,
  ].join('\n')).join('\n\n---\n\n');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const target = urlInput.value.trim();
  if (!target) {
    showTranslatedMessage('message.required', true);
    urlInput.focus();
    return;
  }

  let externalEvidence = null;
  const evidenceFile = externalEvidenceFileInput.files?.[0];
  if (evidenceFile) {
    if (evidenceFile.size > MAX_EXTERNAL_EVIDENCE_BYTES) {
      showTranslatedMessage('audit.evidenceTooLarge', true);
      return;
    }
    try {
      externalEvidence = JSON.parse(await evidenceFile.text());
      if (!externalEvidence || typeof externalEvidence !== 'object' || Array.isArray(externalEvidence)) {
        throw new Error('invalid evidence object');
      }
    } catch {
      showTranslatedMessage('audit.evidenceInvalid', true);
      return;
    }
  }

  latestResult = null;
  report.classList.add('hidden');
  emptyState.classList.remove('hidden');
  submitButton.disabled = true;
  submitButton.innerHTML = `<span class="loading-dot"></span><span>${escapeHtml(translate('loading'))}</span>`;
  showTranslatedMessage('message.running');
  auditInProgress = true;
  renderAuditProgress({
    running: false,
    status: 'starting',
    pages_processed: 0,
    max_pages: Number(maxPagesInput.value),
  });
  auditProgressTimer = window.setInterval(refreshAuditProgress, 1000);
  try {
    const requestPayload = {
      url: target,
      max_pages: Number(maxPagesInput.value),
      render_browser: browserRenderCheckbox.checked,
    };
    if (externalEvidence !== null) requestPayload.external_evidence = externalEvidence;
    const response = await fetch('/api/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestPayload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || translate('message.failed'));
    renderReport(data);
    showTranslatedMessage('message.complete');
  } catch (error) {
    showMessage(error.message || translate('message.failed'), true);
  } finally {
    auditInProgress = false;
    if (auditProgressTimer !== null) {
      window.clearInterval(auditProgressTimer);
      auditProgressTimer = null;
    }
    await refreshAuditProgress();
    submitButton.disabled = false;
    submitButton.innerHTML = `<span data-i18n="audit.submit">${escapeHtml(translate('audit.submit'))}</span><span aria-hidden="true">↗</span>`;
  }
});

cancelAuditButton.addEventListener('click', async () => {
  if (!auditInProgress) return;
  cancelAuditButton.disabled = true;
  showTranslatedMessage('audit.cancelRequested');
  try {
    const response = await fetch('/api/audit/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-SearchScope-Request': 'same-origin',
      },
      body: '{}',
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || translate('message.failed'));
  } catch (error) {
    showMessage(error.message || translate('message.failed'), true);
    cancelAuditButton.disabled = false;
  }
});

document.querySelector('#download-markdown').addEventListener('click', () => {
  if (latestResult) download(latestResult.markdown, 'seo-geo-audit.md', 'text/markdown;charset=utf-8');
});

document.querySelector('#download-json').addEventListener('click', () => {
  if (latestResult) download(JSON.stringify(latestResult.audit, null, 2), 'seo-geo-audit.json', 'application/json;charset=utf-8');
});

document.querySelector('#download-prompts').addEventListener('click', () => {
  if (latestResult) download(buildPromptBundle(), 'seo-geo-agent-prompts.md', 'text/markdown;charset=utf-8');
});

copyAgentPromptButton.addEventListener('click', async () => {
  if (!latestResult || !agentPromptContent.textContent) return;
  const original = copyAgentPromptButton.textContent;
  try {
    await copyText(agentPromptContent.textContent);
    copyAgentPromptButton.textContent = translate('copy.success');
  } catch {
    copyAgentPromptButton.textContent = translate('copy.failed');
  }
  window.setTimeout(() => { copyAgentPromptButton.textContent = original; }, 1600);
});
