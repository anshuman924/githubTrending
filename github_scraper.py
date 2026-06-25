import requests
from pyquery import PyQuery as pq


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
}

GITHUB_URL = 'https://github.com'
TIMEOUT = 20


def fetch_trending():
    url = '{github}/trending'.format(github=GITHUB_URL)
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    document = pq(response.content)
    repositories = []

    for item in document('div.Box article.Box-row'):
        repo = pq(item)
        repo_path = repo('.lh-condensed a').attr('href')
        if not repo_path:
            continue

        repositories.append({
            'title': repo('.lh-condensed a').text(),
            'description': repo('p.col-9').text(),
            'url': GITHUB_URL + repo_path,
        })

    return repositories


def fetch_readme(repo_url):
    response = requests.get(repo_url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    document = pq(response.content)
    readme = document('article.markdown-body')
    return readme.text().strip()
