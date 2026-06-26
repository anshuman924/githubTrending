import argparse
import datetime
import json
import subprocess
from pathlib import Path

from github_scraper import fetch_readme, fetch_trending
from html_report import load_dated_reports, render_index_html, render_report_html
from language_filter import should_skip_non_english_readme
from summarizer import summarize_readmes


DEFAULT_LIMIT = 16
REPORTS_DIR = Path('docs')
PUBLISH_REMOTE = 'origin'
PUBLISH_BRANCH = 'main'


def build_report(limit=DEFAULT_LIMIT):
    report_date = current_date()
    repositories = scrape_trending(limit=limit)
    summary_tokens = sum(repo['summary_tokens_used'] for repo in repositories)

    report = {
        'date': report_date,
        'languages': [{
            'name': 'trending',
            'repository_count': len(repositories),
            'summary_tokens_used': summary_tokens,
            'repositories': repositories,
        }],
        'total_repositories': len(repositories),
        'total_summary_tokens_used': summary_tokens,
    }

    return report


def scrape_trending(limit=DEFAULT_LIMIT):
    if limit == 0:
        return []

    repositories = fetch_trending()
    if limit is not None:
        repositories = repositories[:limit]

    report_repositories = []
    readme_items = []

    for repo in repositories:
        try:
            readme = fetch_readme(repo['url'])
        except Exception as error:
            repo['summary'] = 'README fetch failed: {error}'.format(error=error)
            repo['summary_bullets'] = [repo['summary']]
            repo['tags'] = []
            repo['summary_tokens_used'] = 0
            repo['summary_status'] = 'readme_fetch_failed'
            report_repositories.append(repo)
        else:
            if should_skip_non_english_readme(readme):
                continue

            report_index = len(report_repositories)
            report_repositories.append(repo)
            readme_items.append({
                'index': report_index,
                'title': repo['title'],
                'url': repo['url'],
                'readme': readme,
            })

    summaries = summarize_readmes(readme_items)
    for item, result in zip(readme_items, summaries):
        repo = report_repositories[item['index']]
        repo['summary'] = result['summary']
        repo['summary_bullets'] = result.get('summary_bullets', [result['summary']])
        repo['tags'] = result.get('tags', [])
        repo['summary_tokens_used'] = result['tokens_used']
        repo['summary_status'] = result['status']

    return report_repositories


def write_report(report, output_dir=REPORTS_DIR):
    output_dir.mkdir(exist_ok=True)

    dated_path = output_dir / '{date}.json'.format(date=report['date'])
    dated_html_path = output_dir / '{date}.html'.format(date=report['date'])
    index_path = output_dir / 'index.html'
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    html_text = render_report_html(report)

    dated_path.write_text(json_text + '\n', encoding='utf-8')
    dated_html_path.write_text(html_text, encoding='utf-8')
    index_path.write_text(render_index_html(load_dated_reports(output_dir)), encoding='utf-8')

    return dated_path


def publish_generated_files(report_date, output_dir=REPORTS_DIR):
    run_git(['add', str(output_dir)])

    if not staged_changes_exist(output_dir):
        return False

    run_git(['commit', '-m', 'Update GitHub Trending report for {date}'.format(date=report_date), '--', str(output_dir)])
    run_git(['push', PUBLISH_REMOTE, PUBLISH_BRANCH])
    return True


def staged_changes_exist(output_dir=REPORTS_DIR):
    result = subprocess.run(
        ['git', 'diff', '--cached', '--quiet', '--', str(output_dir)],
        text=True,
    )
    if result.returncode in (0, 1):
        return result.returncode == 1

    result.check_returncode()


def run_git(args):
    subprocess.run(['git'] + args, check=True)


def current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d')


def job(limit=DEFAULT_LIMIT, push=True):
    report = build_report(limit=limit)
    write_report(report)
    if push:
        publish_generated_files(report['date'])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def parse_args():
    parser = argparse.ArgumentParser(description='Generate a GitHub Trending report with README summaries.')
    parser.add_argument(
        '--limit',
        type=int,
        default=DEFAULT_LIMIT,
        help='Maximum repositories to summarize from https://github.com/trending. Defaults to 16.',
    )
    parser.add_argument(
        '--no-push',
        action='store_true',
        help='Generate files without committing and pushing docs/ to GitHub.',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    job(limit=args.limit, push=not args.no_push)
