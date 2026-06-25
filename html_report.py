import json
import re
from html import escape
from urllib.parse import quote


DATED_REPORT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\.json$')


def render_index_html(reports):
    report_items = sorted(reports, key=lambda report: report.get('date', ''), reverse=True)
    report_cards = '\n'.join(render_report_index_card(report) for report in report_items)
    if not report_cards:
        report_cards = '<div class="empty">No reports have been generated yet.</div>'

    return '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Trending Reports</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #19181a;
      --panel: #221f22;
      --panel-strong: #2d2a2e;
      --text: #fcfcfa;
      --muted: #c1c0c0;
      --border: #403e41;
      --accent: #ffd866;
      --purple: #ab9df2;
      --shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    header {{
      background: linear-gradient(180deg, #2d2a2e 0%, #221f22 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px;
    }}

    .topbar,
    main {{
      max-width: 920px;
      margin: 0 auto;
    }}

    h1 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
      color: var(--accent);
    }}

    .meta {{
      margin-top: 10px;
      color: var(--muted);
    }}

    main {{
      padding: 20px;
    }}

    .reports {{
      display: grid;
      gap: 12px;
    }}

    .report-link {{
      display: grid;
      gap: 8px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      color: inherit;
      padding: 16px;
      text-decoration: none;
    }}

    .report-link:hover {{
      border-color: rgba(255, 216, 102, 0.48);
      background: var(--panel-strong);
    }}

    .report-title {{
      color: var(--accent);
      font-size: 19px;
      font-weight: 700;
    }}

    .report-stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
    }}

    .open-label {{
      color: var(--purple);
      font-weight: 700;
    }}

    .empty {{
      border: 1px dashed var(--border);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      padding: 24px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <h1>GitHub Trending Reports</h1>
      <div class="meta">{report_count} {report_label} available</div>
    </div>
  </header>
  <main>
    <section class="reports">{report_cards}</section>
  </main>
</body>
</html>
'''.format(
        report_cards=report_cards,
        report_count=len(report_items),
        report_label='report' if len(report_items) == 1 else 'reports',
    )


def render_report_index_card(report):
    date = str(report.get('date') or '')
    href = quote(date) + '.html'
    repositories = int(report.get('total_repositories') or 0)
    tokens = int(report.get('total_summary_tokens_used') or 0)

    return '''<a class="report-link" href="{href}">
  <span class="report-title">{date}</span>
  <span class="report-stats">
    <span>{repositories} repositories</span>
    <span>{tokens} summary tokens</span>
  </span>
  <span class="open-label">Open report</span>
</a>'''.format(
        href=escape(href, quote=True),
        date=escape(date),
        repositories=repositories,
        tokens=tokens,
    )


def load_dated_reports(output_dir):
    reports = []
    for report_path in output_dir.glob('*.json'):
        if not DATED_REPORT_RE.match(report_path.name):
            continue

        try:
            report = json.loads(report_path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue

        if report.get('date') == report_path.stem:
            reports.append(report)

    return reports


def render_report_html(report):
    report_json = json.dumps(report, ensure_ascii=False).replace('<', '\\u003c')

    return '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Trending Report</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #19181a;
      --panel: #221f22;
      --panel-strong: #2d2a2e;
      --text: #fcfcfa;
      --muted: #c1c0c0;
      --border: #403e41;
      --accent: #ffd866;
      --accent-strong: #ff6188;
      --accent-soft: rgba(255, 216, 102, 0.14);
      --green: #a9dc76;
      --cyan: #78dce8;
      --purple: #ab9df2;
      --warn: #fc9867;
      --shadow: 0 14px 40px rgba(0, 0, 0, 0.28);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    header {{
      background: linear-gradient(180deg, #2d2a2e 0%, #221f22 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px;
    }}

    .topbar {{
      max-width: 1180px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}

    .title-block {{
      display: grid;
      gap: 12px;
    }}

    h1 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
      color: var(--accent);
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }}

    .sidebar-toggle {{
      width: 42px;
      min-height: 42px;
      display: inline-grid;
      place-items: center;
      padding: 0;
      flex: 0 0 auto;
    }}

    .sidebar-toggle span,
    .sidebar-toggle::before,
    .sidebar-toggle::after {{
      content: '';
      display: block;
      width: 18px;
      height: 2px;
      border-radius: 999px;
      background: currentColor;
    }}

    .sidebar-toggle {{
      gap: 4px;
    }}

    .layout {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 20px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 220px;
      gap: 18px;
      align-items: start;
    }}

    body.sidebar-collapsed .layout {{
      grid-template-columns: minmax(0, 1fr) 0;
    }}

    .content {{
      min-width: 0;
    }}

    .sidebar {{
      position: sticky;
      top: 16px;
      overflow: hidden;
      transition:
        opacity 220ms ease,
        transform 220ms ease;
    }}

    body.sidebar-collapsed .sidebar {{
      opacity: 0;
      pointer-events: none;
      transform: translateX(12px);
    }}

    .filters {{
      display: grid;
      gap: 8px;
    }}

    button {{
      min-height: 36px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel-strong);
      color: var(--text);
      cursor: pointer;
      font: inherit;
      padding: 7px 12px;
    }}

    button[aria-pressed="true"] {{
      background: var(--accent-strong);
      border-color: var(--accent-strong);
      color: #19181a;
      font-weight: 700;
    }}

    .filters button {{
      width: 100%;
      text-align: left;
    }}

    .grid {{
      position: relative;
      min-height: 220px;
      transition: height 260ms ease;
    }}

    .tile {{
      position: absolute;
      top: 0;
      left: 0;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
      overflow: hidden;
      transition:
        border-color 180ms ease,
        box-shadow 180ms ease,
        transform 320ms ease;
    }}

    .tile.expanded {{
      border-color: rgba(255, 216, 102, 0.48);
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.34);
    }}

    .tile-toggle {{
      width: 100%;
      min-height: 160px;
      display: grid;
      grid-template-rows: auto 1fr auto auto;
      gap: 10px;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: inherit;
      text-align: left;
      padding: 14px;
    }}

    .tile-toggle:focus-visible {{
      outline: 3px solid var(--accent);
      outline-offset: -3px;
    }}

    .repo-title {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      font-weight: 700;
      line-height: 1.25;
      overflow-wrap: anywhere;
      color: var(--text);
    }}

    .repo-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      min-height: 24px;
    }}

    .tag {{
      flex: 0 0 auto;
      border-radius: 999px;
      background: rgba(120, 220, 232, 0.16);
      color: var(--cyan);
      font-size: 12px;
      font-weight: 600;
      padding: 3px 8px;
      text-transform: lowercase;
    }}

    .description {{
      margin: 0;
      color: var(--muted);
      overflow: hidden;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
    }}

    .tile-footer {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      color: var(--muted);
      font-size: 13px;
    }}

    .status-ok {{
      color: var(--green);
    }}

    .status-failed,
    .status-readme_fetch_failed,
    .status-skipped,
    .status-stale_codex_exec_terminated {{
      color: var(--warn);
    }}

    .details {{
      max-height: 0;
      overflow: hidden;
      border-top: 0 solid transparent;
      background: var(--panel-strong);
      opacity: 0;
      padding: 0 14px;
      transition:
        max-height 320ms ease,
        opacity 180ms ease,
        padding 320ms ease,
        border-color 320ms ease,
        border-width 320ms ease;
    }}

    .tile.expanded .details {{
      border-top-width: 1px;
      border-top-color: var(--border);
      opacity: 1;
      padding: 14px;
    }}

    .summary-list {{
      margin: 0 0 12px;
      padding-left: 20px;
      color: var(--text);
    }}

    .summary-list li {{
      margin: 0 0 8px;
    }}

    .repo-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 36px;
      border: 1px solid rgba(171, 157, 242, 0.42);
      border-radius: 8px;
      background: rgba(171, 157, 242, 0.12);
      color: var(--purple);
      font-weight: 600;
      padding: 7px 12px;
      text-decoration: none;
    }}

    .repo-link:hover {{
      border-color: var(--purple);
      background: rgba(171, 157, 242, 0.18);
    }}

    .empty {{
      position: static;
      border: 1px dashed var(--border);
      border-radius: 8px;
      background: var(--panel);
      color: var(--muted);
      padding: 24px;
      text-align: center;
    }}

    @media (max-width: 720px) {{
      header {{
        padding: 16px;
      }}

      .layout {{
        grid-template-columns: minmax(0, 1fr) 190px;
        padding: 14px;
        gap: 12px;
      }}

      h1 {{
        font-size: 23px;
      }}

      .tile-toggle {{
        min-height: 140px;
      }}

      .repo-title {{
        display: grid;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div class="title-block">
        <h1>GitHub Trending Report</h1>
        <div class="meta" id="meta"></div>
      </div>
      <button type="button" class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle tag filters" aria-expanded="true"><span></span></button>
    </div>
  </header>
  <main class="layout">
    <section class="content">
      <section class="grid" id="repoGrid" aria-live="polite"></section>
    </section>
    <aside class="sidebar" id="sidebar">
      <nav class="filters" id="filters" aria-label="Tag filters"></nav>
    </aside>
  </main>

  <script>
    const report = {report_json};
    const state = {{
      report,
      activeTag: 'all',
    }};

    const meta = document.getElementById('meta');
    const filters = document.getElementById('filters');
    const repoGrid = document.getElementById('repoGrid');
    const sidebarToggle = document.getElementById('sidebarToggle');
    let tileObserver = null;

    sidebarToggle.addEventListener('click', () => {{
      const collapsed = document.body.classList.toggle('sidebar-collapsed');
      sidebarToggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      layoutTilesSoon();
    }});

    render();

    function render() {{
      renderMeta();
      renderFilters();
      renderRepos();
    }}

    function renderMeta() {{
      meta.innerHTML = [
        `<span>Date: ${{escapeHtml(state.report.date)}}</span>`,
        `<span>Repos: ${{state.report.total_repositories}}</span>`,
        `<span>Summary tokens: ${{state.report.total_summary_tokens_used}}</span>`,
      ].join('');
    }}

    function renderFilters() {{
      const repos = flattenRepos();
      const tags = sortedTagsByFrequency(repos);
      const buttons = ['all', ...tags].map((tag) => {{
        const label = tag === 'all' ? 'All' : `${{tag}} ${{tagCount(repos, tag)}}`;
        const pressed = state.activeTag === tag ? 'true' : 'false';
        return `<button type="button" aria-pressed="${{pressed}}" data-tag="${{escapeAttribute(tag)}}">${{escapeHtml(label)}}</button>`;
      }});

      filters.innerHTML = buttons.join('');
      filters.querySelectorAll('button').forEach((button) => {{
        button.addEventListener('click', () => {{
          state.activeTag = button.dataset.tag;
          render();
        }});
      }});
    }}

    function renderRepos() {{
      const repos = flattenRepos().filter((repo) => {{
        return state.activeTag === 'all' || repoTags(repo).includes(state.activeTag);
      }});

      if (!repos.length) {{
        repoGrid.innerHTML = '<div class="empty">No repositories for this filter.</div>';
        repoGrid.style.height = 'auto';
        return;
      }}

      repoGrid.innerHTML = repos.map(renderRepo).join('');
      observeTileSizes();
      repoGrid.querySelectorAll('.tile-toggle').forEach((button) => {{
        button.addEventListener('click', () => {{
          const tile = button.closest('.tile');
          const wasExpanded = tile.classList.contains('expanded');

          if (wasExpanded) {{
            closeExpandedTile();
            layoutTilesSoon();
            return;
          }}

          closeExpandedTile();
          tile.classList.add('expanded');
          button.setAttribute('aria-expanded', 'true');
          setDetailsHeight(tile);
          layoutTilesSoon();
        }});
      }});
      layoutTilesSoon();
    }}

    function closeExpandedTile() {{
      repoGrid.querySelectorAll('.tile.expanded').forEach((tile) => {{
        tile.classList.remove('expanded');
        const details = tile.querySelector('.details');
        if (details) {{
          details.style.maxHeight = '0px';
        }}
        const button = tile.querySelector('.tile-toggle');
        if (button) {{
          button.setAttribute('aria-expanded', 'false');
        }}
      }});
    }}

    function setDetailsHeight(tile) {{
      const details = tile.querySelector('.details');
      if (details) {{
        details.style.maxHeight = `${{details.scrollHeight + 160}}px`;
      }}
    }}

    function observeTileSizes() {{
      if (tileObserver) {{
        tileObserver.disconnect();
      }}

      tileObserver = new ResizeObserver(() => layoutTilesSoon());
      repoGrid.querySelectorAll('.tile').forEach((tile) => tileObserver.observe(tile));
    }}

    function layoutTilesSoon() {{
      requestAnimationFrame(layoutTiles);
    }}

    function layoutTiles() {{
      const tiles = [...repoGrid.querySelectorAll('.tile')];
      if (!tiles.length) {{
        return;
      }}

      const gap = 14;
      const minColumnWidth = 280;
      const containerWidth = repoGrid.clientWidth;
      const columns = Math.max(1, Math.floor((containerWidth + gap) / (minColumnWidth + gap)));
      const columnWidth = (containerWidth - gap * (columns - 1)) / columns;
      const columnHeights = Array(columns).fill(0);

      tiles.forEach((tile) => {{
        tile.style.width = `${{columnWidth}}px`;
        const column = columnHeights.indexOf(Math.min(...columnHeights));
        const x = column * (columnWidth + gap);
        const y = columnHeights[column];

        tile.style.transform = `translate(${{x}}px, ${{y}}px)`;
        columnHeights[column] += tile.offsetHeight + gap;
      }});

      repoGrid.style.height = `${{Math.max(...columnHeights) - gap}}px`;
    }}

    window.addEventListener('resize', layoutTilesSoon);

    function sortedTagsByFrequency(repos) {{
      const counts = new Map();
      repos.forEach((repo) => {{
        repoTags(repo).forEach((tag) => {{
          counts.set(tag, (counts.get(tag) || 0) + 1);
        }});
      }});

      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
        .map(([tag]) => tag);
    }}

    function tagCount(repos, tag) {{
      return repos.filter((repo) => repoTags(repo).includes(tag)).length;
    }}

    function repoTags(repo) {{
      return Array.isArray(repo.tags) ? repo.tags.slice(0, 5) : [];
    }}

    function repoBullets(repo) {{
      if (Array.isArray(repo.summary_bullets) && repo.summary_bullets.length) {{
        return repo.summary_bullets;
      }}

      return [repo.summary || 'Summary unavailable.'];
    }}

    function flattenRepos() {{
      return state.report.languages.flatMap((language) => {{
        return language.repositories.map((repo) => ({{ ...repo }}));
      }});
    }}

    function renderRepo(repo) {{
      const statusClass = `status-${{repo.summary_status}}`;
      const tags = repoTags(repo);
      const tagHtml = tags.length
        ? tags.map((tag) => `<span class="tag">${{escapeHtml(tag)}}</span>`).join('')
        : '<span class="tag">untagged</span>';
      const bullets = repoBullets(repo)
        .map((bullet) => `<li>${{escapeHtml(bullet)}}</li>`)
        .join('');

      return `
        <article class="tile">
          <button type="button" class="tile-toggle" aria-expanded="false">
            <div class="repo-title">
              <span>${{escapeHtml(repo.title)}}</span>
            </div>
            <p class="description">${{escapeHtml(repo.description || 'No description provided.')}}</p>
            <div class="repo-tags">${{tagHtml}}</div>
            <div class="tile-footer">
              <span class="${{escapeHtml(statusClass)}}">${{escapeHtml(repo.summary_status)}}</span>
              <span>${{repo.summary_tokens_used}} tokens</span>
            </div>
          </button>
          <div class="details">
            <ul class="summary-list">${{bullets}}</ul>
            <a class="repo-link" href="${{escapeAttribute(repo.url)}}" target="_blank" rel="noopener">Open repository</a>
          </div>
        </article>
      `;
    }}

    function escapeHtml(value) {{
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }}

    function escapeAttribute(value) {{
      return escapeHtml(value).replace(/`/g, '&#96;');
    }}
  </script>
</body>
</html>
'''.format(report_json=report_json)
