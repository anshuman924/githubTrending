import unittest

from language_filter import should_skip_non_english_readme


class LanguageFilterTest(unittest.TestCase):
    def test_allows_english_readme(self):
        readme = '''
# Useful Tool

This project helps developers inspect local configuration files and generate
small static reports for review.
'''

        self.assertFalse(should_skip_non_english_readme(readme))

    def test_allows_one_or_two_non_latin_characters(self):
        readme = '''
# Project

This README is written in English and mentions 项目 as a short label only.
'''

        self.assertFalse(should_skip_non_english_readme(readme))

    def test_skips_cjk_paragraph(self):
        readme = '''
# Project

这是一个用于生成报告的工具，帮助用户每天查看项目趋势和摘要内容。
'''

        self.assertTrue(should_skip_non_english_readme(readme))

    def test_skips_cyrillic_paragraph(self):
        readme = '''
# Project

Этот инструмент помогает разработчикам создавать ежедневные отчеты по проектам.
'''

        self.assertTrue(should_skip_non_english_readme(readme))

    def test_ignores_urls_numbers_punctuation_and_emoji(self):
        readme = '''
# Project

https://example.com/path?x=123 !!! 🚀🚀🚀 12345
'''

        self.assertFalse(should_skip_non_english_readme(readme))

    def test_allows_accented_latin_text(self):
        readme = '''
# Cafe

Café résumé naïve façade jalapeño déjà vu coöperate São Tomé.
'''

        self.assertFalse(should_skip_non_english_readme(readme))


if __name__ == '__main__':
    unittest.main()
