"""Stablecoin Today の RSS（Apple/Spotify 用）を episodes.json から生成する。

Usage: python3 tools/build_feed.py REPO
REPO/tools/show.json と REPO/tools/episodes.json を読み、REPO/docs/feed.xml を書く。
"""
import json, os, sys
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

d = sys.argv[1]
show = json.load(open(os.path.join(d, 'tools', 'show.json'), encoding='utf-8'))
eps = sorted(json.load(open(os.path.join(d, 'tools', 'episodes.json'), encoding='utf-8')), key=lambda e: e['pub'], reverse=True)

def x(s):
    return escape(s, {'"': '&quot;'})

def notes_html(e):
    items = ''.join(f'<li>{x(n["title"])} ({", ".join(f"<a href={chr(34)}{x(u)}{chr(34)}>{x(m)}</a>" for m, u in n["sources"])})</li>' for n in e['notes'])
    return f'<p>{x(e["summary"])}</p><ul>{items}</ul><p>{x(show["disclaimer"])}</p>'

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:podcast="https://podcastindex.org/namespace/1.0">',
       '<channel>',
       f'<title>{x(show["title"])}</title>',
       f'<link>{x(show["link"])}</link>',
       f'<atom:link href="{x(show["feed_url"])}" rel="self" type="application/rss+xml"/>',
       f'<language>{show["language"]}</language>',
       f'<copyright>{x(show["copyright"])}</copyright>',
       f'<description>{x(show["description"])}</description>',
       f'<itunes:summary>{x(show["description"])}</itunes:summary>',
       f'<itunes:author>{x(show["author"])}</itunes:author>',
       f'<itunes:owner><itunes:name>{x(show["author"])}</itunes:name><itunes:email>{x(show["email"])}</itunes:email></itunes:owner>',
       f'<itunes:image href="{x(show["image"])}"/>',
       f'<image><url>{x(show["image"])}</url><title>{x(show["title"])}</title><link>{x(show["link"])}</link></image>']
for cat, sub in show['categories']:
    out.append(f'<itunes:category text="{x(cat)}"><itunes:category text="{x(sub)}"/></itunes:category>' if sub else f'<itunes:category text="{x(cat)}"/>')
out += ['<itunes:explicit>false</itunes:explicit>', '<itunes:type>episodic</itunes:type>',
        f'<podcast:locked>yes</podcast:locked>',
        f'<podcast:guid>{show["podcast_guid"]}</podcast:guid>',
        f'<lastBuildDate>{format_datetime(datetime.now(timezone.utc))}</lastBuildDate>']
for e in eps:
    pub = datetime.fromisoformat(e['pub'])
    out += ['<item>',
            f'<title>{x(e["title"])}</title>',
            f'<link>{x(e.get("link", show["link"]))}</link>',
            f'<itunes:image href="{x(show["image"])}"/>',
            f'<description>{x(notes_html(e))}</description>',
            f'<content:encoded><![CDATA[{notes_html(e)}]]></content:encoded>',
            f'<itunes:summary>{x(e["summary"])}</itunes:summary>',
            f'<enclosure url="{x(e["audio_url"])}" length="{e["bytes"]}" type="audio/mpeg"/>',
            f'<guid isPermaLink="false">{x(e["guid"])}</guid>',
            f'<pubDate>{format_datetime(pub)}</pubDate>',
            f'<itunes:duration>{int(e["seconds"])}</itunes:duration>',
            '<itunes:episodeType>full</itunes:episodeType>',
            '<itunes:explicit>false</itunes:explicit>',
            '</item>']
out += ['</channel>', '</rss>']
os.makedirs(os.path.join(d, 'docs'), exist_ok=True)
open(os.path.join(d, 'docs', 'feed.xml'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('feed.xml', len(eps), 'episodes')
