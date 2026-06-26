import re
import unicodedata


MIN_NON_LATIN_LETTERS_IN_BLOCK = 12
NON_LATIN_BLOCK_RATIO = 0.5


def should_skip_non_english_readme(text):
    for block in paragraph_blocks(text):
        counts = count_latin_and_non_latin_letters(block)
        total_letters = counts['latin'] + counts['non_latin']
        if not total_letters:
            continue

        non_latin_letters = counts['non_latin']
        non_latin_ratio = non_latin_letters / total_letters
        if (
            non_latin_letters >= MIN_NON_LATIN_LETTERS_IN_BLOCK
            and non_latin_ratio >= NON_LATIN_BLOCK_RATIO
        ):
            return True

    return False


def paragraph_blocks(text):
    return [
        block.strip()
        for block in re.split(r'\n\s*\n+', text or '')
        if block.strip()
    ]


def count_latin_and_non_latin_letters(text):
    counts = {
        'latin': 0,
        'non_latin': 0,
    }

    for character in text:
        if not is_letter(character):
            continue

        if is_latin_letter(character):
            counts['latin'] += 1
        else:
            counts['non_latin'] += 1

    return counts


def is_letter(character):
    return unicodedata.category(character).startswith('L')


def is_latin_letter(character):
    return 'LATIN' in unicodedata.name(character, '')
