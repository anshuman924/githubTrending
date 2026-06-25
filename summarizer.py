import json
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path


CODEX_TIMEOUT = 600
CODEX_MODEL = 'gpt-5.4-mini'
CODEX_PROCESS_REGISTRY = Path('.codex_exec_processes.json')
MAX_README_CHARS = 12000
MAX_BATCH_TOKENS = 300000
CHARS_PER_TOKEN_ESTIMATE = 4
TECHNICAL_TAGS = {
    'python', 'javascript', 'typescript', 'java', 'go', 'golang', 'rust',
    'swift', 'kotlin', 'ruby', 'php', 'c', 'c++', 'c#', 'scala', 'dart',
    'elixir', 'haskell', 'lua', 'zig', 'react', 'vue', 'svelte', 'angular',
    'node', 'nodejs', 'node.js', 'django', 'flask', 'rails', 'spring',
    'nextjs', 'next.js', 'docker', 'kubernetes', 'sqlite', 'postgres',
    'mysql', 'graphql', 'grpc', 'rest api', 'api', 'mcp', 'json', 'yaml',
}


def summarize_readme(repo_title, repo_url, readme_text):
    return summarize_readmes([{
        'title': repo_title,
        'url': repo_url,
        'readme': readme_text,
    }])[0]


def summarize_readmes(readme_items):
    results = [None] * len(readme_items)
    batch = []

    for index, item in enumerate(readme_items):
        readme_text = item.get('readme') or ''
        if not readme_text:
            results[index] = skipped_summary('README content was not found.', 'skipped')
            continue

        batch_item = {
            'index': index,
            'title': item.get('title', ''),
            'url': item.get('url', ''),
            'readme': readme_text[:MAX_README_CHARS],
        }

        if batch and estimate_batch_tokens(batch + [batch_item]) > MAX_BATCH_TOKENS:
            apply_batch_results(results, batch, summarize_readme_batch(batch))
            batch = []

        batch.append(batch_item)

    if batch:
        apply_batch_results(results, batch, summarize_readme_batch(batch))

    return results


def summarize_readme_batch(batch):
    prompt = build_batch_prompt(batch)
    killed_processes = kill_stale_codex_exec_processes()
    if killed_processes:
        return {
            'status': 'stale_codex_exec_terminated',
            'error': 'Summary unable to generate: stale Codex exec process was still running and was terminated.',
            'tokens_used': 0,
            'repositories': {},
        }

    with tempfile.NamedTemporaryFile('r+', encoding='utf-8', delete=False) as output_file:
        output_path = output_file.name

    process = None
    try:
        command = build_codex_command(output_path)
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        register_codex_process(process.pid)
        stdout, stderr = process.communicate(input=prompt, timeout=CODEX_TIMEOUT)
        if process.returncode:
            raise subprocess.CalledProcessError(process.returncode, command, stdout, stderr)

        with open(output_path, encoding='utf-8') as f:
            repositories = parse_batch_summary_response(f.read())

        tokens_used = parse_tokens_used(stdout + stderr)
        return {
            'status': 'ok',
            'tokens_used': tokens_used,
            'repositories': repositories,
        }
    except subprocess.TimeoutExpired:
        if process:
            terminate_process_group(process.pid)

        return {
            'status': 'failed',
            'error': 'Summary unable to generate: Codex exec timed out and was terminated.',
            'tokens_used': 0,
            'repositories': {},
        }
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        return {
            'status': 'failed',
            'error': 'Summary generation failed: {error}'.format(error=error),
            'tokens_used': 0,
            'repositories': {},
        }
    finally:
        if process:
            unregister_codex_process(process.pid)

        try:
            os.remove(output_path)
        except OSError:
            pass


def apply_batch_results(results, batch, batch_result):
    token_allocations = allocate_batch_tokens(batch, batch_result.get('tokens_used', 0))
    batch_summaries = batch_result.get('repositories', {})

    for item in batch:
        index = item['index']
        repo_id = repo_batch_id(index)
        summary_data = batch_summaries.get(repo_id)

        if batch_result.get('status') != 'ok':
            results[index] = skipped_summary(batch_result.get('error', 'Summary generation failed.'), batch_result['status'])
        elif not summary_data:
            results[index] = skipped_summary('Summary generation failed: Codex response did not include this repository.', 'failed')
        else:
            results[index] = {
                'summary': clean_summary(' '.join(summary_data['summary_bullets'])),
                'summary_bullets': summary_data['summary_bullets'],
                'tags': summary_data['tags'],
                'tokens_used': token_allocations.get(repo_id, 0),
                'status': 'ok',
            }


def skipped_summary(message, status):
    return {
        'summary': message,
        'summary_bullets': [message],
        'tags': [],
        'tokens_used': 0,
        'status': status,
    }


def build_batch_prompt(batch):
    repositories = []
    for item in batch:
        repositories.append('''<repository id="{id}">
Title: {title}
URL: {url}
README:
{readme}
</repository>'''.format(
            id=repo_batch_id(item['index']),
            title=item['title'],
            url=item['url'],
            readme=item['readme'],
        ))

    return '''You are writing data for a GitHub Trending report.

Return only valid JSON with this exact shape:
{{"repositories":[{{"id":"repo-0","summary_bullets":["..."],"tags":["..."]}}]}}

Rules:
- Return one repositories item for every repository id in the input.
- Preserve each repository id exactly.
- Write 3 to 5 concise summary_bullets strings per repository.
- Each bullet should explain what the project does, what problem it solves, or who uses it.
- Do not include markdown bullet markers.
- Do not include marketing language or claims not supported by the README.
- Generate 1 to 5 broad topic tags from each README.
- Tags should describe the problem space or user-facing domain, not implementation details.
- Prefer broad tags such as "ai agent", "cli tool", "music", "audio", "design tool", "trading", "education", "networking", "developer tool", "android", "game", "security", "collaboration".
- Avoid programming-language, framework, library, package-manager, protocol, file-format, and vendor tags unless the README clearly makes that the main user-facing problem space.
- Use lowercase tags.
- Do not over-generate tags.

Repositories:
{repositories}
'''.format(repositories='\n\n'.join(repositories))


def estimate_batch_tokens(batch):
    return max(1, len(build_batch_prompt(batch)) // CHARS_PER_TOKEN_ESTIMATE)


def repo_batch_id(index):
    return 'repo-{index}'.format(index=index)


def allocate_batch_tokens(batch, tokens_used):
    if not tokens_used:
        return {repo_batch_id(item['index']): 0 for item in batch}

    weights = {
        repo_batch_id(item['index']): max(1, len(item['readme']))
        for item in batch
    }
    total_weight = sum(weights.values())
    allocations = {}
    allocated = 0

    for repo_id, weight in weights.items():
        allocation = int(tokens_used * weight / total_weight)
        allocations[repo_id] = allocation
        allocated += allocation

    remainder = tokens_used - allocated
    for repo_id in list(weights)[:remainder]:
        allocations[repo_id] += 1

    return allocations


def parse_batch_summary_response(response_text):
    data = json.loads(extract_json_text(response_text))
    repositories = {}

    for repo_data in data.get('repositories', []):
        repo_id = str(repo_data.get('id', '')).strip()
        if not repo_id:
            continue

        parsed = parse_summary_data(repo_data)
        repositories[repo_id] = parsed

    if not repositories:
        raise ValueError('repositories missing from Codex response')

    return repositories


def parse_summary_data(data):
    bullets = [
        clean_summary(str(bullet))
        for bullet in data.get('summary_bullets', [])
        if clean_summary(str(bullet))
    ][:5]
    tags = normalize_tags(data.get('tags', []))

    if not bullets:
        raise ValueError('summary_bullets missing from Codex response')

    return {
        'summary_bullets': bullets,
        'tags': tags,
    }


def build_prompt(repo_title, repo_url, readme_text):
    return '''You are writing data for a GitHub Trending report.

Repository: {title}
URL: {url}

Return only valid JSON with this exact shape:
{{"summary_bullets":["..."],"tags":["..."]}}

Summary rules:
- Write 3 to 5 concise bullet strings.
- Each bullet should explain what the project does, what problem it solves, or who uses it.
- Do not include markdown bullet markers.
- Do not include marketing language or claims not supported by the README.

Tag rules:
- Generate 1 to 5 broad topic tags from the README.
- Tags should describe the problem space or user-facing domain, not implementation details.
- Prefer broad tags such as "ai agent", "cli tool", "music", "audio", "design tool", "trading", "education", "networking", "developer tool", "android", "game", "security", "collaboration".
- Avoid programming-language, framework, library, package-manager, protocol, file-format, and vendor tags unless the README clearly makes that the main user-facing problem space.
- Use lowercase tags.
- Do not over-generate tags.

README:
{readme}
'''.format(title=repo_title, url=repo_url, readme=readme_text)


def clean_summary(summary):
    return ' '.join(summary.strip().split())


def parse_summary_response(response_text):
    data = json.loads(extract_json_text(response_text))
    return parse_summary_data(data)


def extract_json_text(response_text):
    text = response_text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*```$', '', text)

    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end < start:
        raise ValueError('JSON object missing from Codex response')

    return text[start:end + 1]


def normalize_tags(tags):
    normalized_tags = []
    seen = set()

    for tag in tags:
        normalized_tag = clean_summary(str(tag).lower()).strip(' .,#')
        if not normalized_tag or normalized_tag in seen or normalized_tag in TECHNICAL_TAGS:
            continue

        seen.add(normalized_tag)
        normalized_tags.append(normalized_tag)

        if len(normalized_tags) == 5:
            break

    return normalized_tags


def build_codex_command(output_path):
    return [
        'codex',
        'exec',
        '--json',
        '--model',
        CODEX_MODEL,
        '--ignore-user-config',
        '--ignore-rules',
        '--skip-git-repo-check',
        '--ephemeral',
        '--sandbox',
        'read-only',
        '-o',
        output_path,
        '-',
    ]


def kill_stale_codex_exec_processes():
    processes = read_codex_process_registry()
    killed_processes = []
    active_processes = []

    for process_info in processes:
        pid = process_info.get('pid')
        if not pid or not process_is_running(pid):
            continue

        if process_is_codex_exec(pid):
            if terminate_process_group(pid):
                killed_processes.append(pid)
            continue

        active_processes.append(process_info)

    write_codex_process_registry(active_processes)
    return killed_processes


def register_codex_process(pid):
    processes = read_codex_process_registry()
    processes.append({
        'pid': pid,
        'started_at': time.time(),
    })
    write_codex_process_registry(processes)


def unregister_codex_process(pid):
    processes = [
        process_info
        for process_info in read_codex_process_registry()
        if process_info.get('pid') != pid
    ]
    write_codex_process_registry(processes)


def read_codex_process_registry():
    try:
        with open(CODEX_PROCESS_REGISTRY, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return data


def write_codex_process_registry(processes):
    if not processes:
        try:
            CODEX_PROCESS_REGISTRY.unlink()
        except OSError:
            pass
        return

    with open(CODEX_PROCESS_REGISTRY, 'w', encoding='utf-8') as f:
        json.dump(processes, f)


def process_is_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False

    return True


def process_is_codex_exec(pid):
    try:
        result = subprocess.run(
            ['ps', '-p', str(pid), '-o', 'command='],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

    command = result.stdout
    return 'codex' in command and 'exec' in command


def terminate_process_group(pid):
    try:
        process_group_id = os.getpgid(pid)
    except OSError:
        return False

    try:
        os.killpg(process_group_id, signal.SIGTERM)
    except OSError:
        return False

    deadline = time.time() + 5
    while time.time() < deadline:
        if not process_is_running(pid):
            return True
        time.sleep(0.1)

    try:
        os.killpg(process_group_id, signal.SIGKILL)
    except OSError:
        return False

    return True


def parse_tokens_used(output):
    tokens_used = 0
    for line in (output or '').splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get('type') != 'turn.completed':
            continue

        usage = event.get('usage') or {}
        if 'total_tokens' in usage:
            tokens_used += int(usage.get('total_tokens') or 0)
        else:
            tokens_used += int(usage.get('input_tokens') or 0)
            tokens_used += int(usage.get('output_tokens') or 0)

    if tokens_used:
        return tokens_used

    match = re.search(r'tokens used\s+([\d,]+)', output or '', re.IGNORECASE)
    if not match:
        return 0

    return int(match.group(1).replace(',', ''))
