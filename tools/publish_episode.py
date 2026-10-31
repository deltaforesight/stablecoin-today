"""Stablecoin Today の1話を公開する（Releasesへ音声、feedへ項目、Pagesへpush）。

Usage: python3 tools/publish_episode.py YYYY-MM-DD MP3 META_JSON

META_JSON は {"title": ..., "summary": ..., "notes": [{"title": ..., "sources": [[媒体, URL], ...]}, ...]}。
同じ日付で再実行してもよい（Releaseの資産は上書き、feedの項目は差し替え）。
"""
import json, os, shutil, subprocess, sys, tempfile, urllib.request
from datetime import date, timedelta

REPO = 'deltaforesight/stablecoin-today'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw).stdout.strip()


def main(day, mp3, meta_path):
    y, m, d = (int(v) for v in day.split('-'))
    dt = date(y, m, d)
    meta = json.load(open(meta_path, encoding='utf-8'))
    size = os.path.getsize(mp3)
    seconds = float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', mp3))
    if not 60 <= seconds <= 600:
        sys.exit(f'音声が {seconds:.0f} 秒で想定（60〜600秒）の外。台本を確認する。')

    tag, asset = f'ep-{day}', f'stablecoin-today_{day}.mp3'
    tmp = os.path.join(tempfile.mkdtemp(), asset)
    shutil.copy2(mp3, tmp)
    title = f'Stablecoin Today — {dt.strftime("%b")} {dt.day}, {dt.year}'
    exists = subprocess.run(['gh', 'release', 'view', tag, '--repo', REPO],
                            capture_output=True, text=True).returncode == 0
    if exists:
        run('gh', 'release', 'upload', tag, tmp, '--repo', REPO, '--clobber')
    else:
        run('gh', 'release', 'create', tag, tmp, '--repo', REPO, '--title', title,
            '--notes', meta['summary'])

    eps_path = os.path.join(ROOT, 'tools', 'episodes.json')
    eps = json.load(open(eps_path, encoding='utf-8'))
    guid = f'stablecoin-today-{day}'
    entry = {
        'guid': guid,
        'title': meta['title'],
        'pub': f'{dt + timedelta(days=1)}T08:00:00+09:00',
        'summary': meta['summary'],
        'audio_url': f'https://github.com/{REPO}/releases/download/{tag}/{asset}',
        'bytes': size,
        'seconds': seconds,
        'notes': meta['notes'],
    }
    eps = [e for e in eps if e['guid'] != guid] + [entry]
    json.dump(eps, open(eps_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(run('python3', os.path.join(ROOT, 'tools', 'build_feed.py'), ROOT))

    run('git', '-C', ROOT, 'add', 'tools/episodes.json', 'docs/feed.xml')
    if subprocess.run(['git', '-C', ROOT, 'diff', '--cached', '--quiet']).returncode:
        run('git', '-C', ROOT, 'commit', '-m', f'Publish episode for {day}')
        run('git', '-C', ROOT, 'push')

    req = urllib.request.Request(entry['audio_url'], method='HEAD')
    with urllib.request.urlopen(req) as r:
        print('enclosure', r.status, r.headers.get('content-length'))
    print('published', guid, f'{seconds:.0f}s', size, 'bytes')


if __name__ == '__main__':
    main(*sys.argv[1:4])
