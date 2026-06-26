import unittest
from unittest.mock import patch

import scrape


class ScrapeFilterTest(unittest.TestCase):
    @patch('scrape.summarize_readmes')
    @patch('scrape.fetch_readme')
    @patch('scrape.fetch_trending')
    def test_non_english_readmes_do_not_enter_summary_loop(
        self,
        fetch_trending,
        fetch_readme,
        summarize_readmes,
    ):
        fetch_trending.return_value = [
            {'title': 'owner / english-one', 'description': '', 'url': 'https://github.com/one'},
            {'title': 'owner / cjk', 'description': '', 'url': 'https://github.com/two'},
            {'title': 'owner / english-two', 'description': '', 'url': 'https://github.com/three'},
        ]
        fetch_readme.side_effect = [
            'This README explains a developer reporting tool.',
            '这是一个用于生成报告的工具，帮助用户每天查看项目趋势和摘要内容。',
            'This README explains another developer reporting tool.',
        ]
        summarize_readmes.return_value = [
            {
                'summary': 'First summary.',
                'summary_bullets': ['First summary.'],
                'tags': ['developer tool'],
                'tokens_used': 10,
                'status': 'ok',
            },
            {
                'summary': 'Second summary.',
                'summary_bullets': ['Second summary.'],
                'tags': ['developer tool'],
                'tokens_used': 12,
                'status': 'ok',
            },
        ]

        repositories = scrape.scrape_trending(limit=3)

        summarized_titles = [
            item['title']
            for item in summarize_readmes.call_args.args[0]
        ]
        report_titles = [repo['title'] for repo in repositories]

        self.assertEqual(summarized_titles, ['owner / english-one', 'owner / english-two'])
        self.assertEqual(report_titles, ['owner / english-one', 'owner / english-two'])
        self.assertEqual(repositories[0]['summary_tokens_used'], 10)
        self.assertEqual(repositories[1]['summary_tokens_used'], 12)


if __name__ == '__main__':
    unittest.main()
