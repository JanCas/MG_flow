#!/usr/bin/env python3
"""Check static links, source references and exported quantity boundaries."""
import csv
import json
import re
import struct
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.h1s = set(), [], 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, f'Duplicate HTML id: {a["id"]}'
            self.ids.add(a['id'])
        if tag == 'h1': self.h1s += 1
        for key in ('href', 'src'):
            if key in a: self.links.append(a[key])

def main():
    from build import GROUPS, md
    assert md(md('[S01]')) == md('[S01]'), 'Markdown citations must be idempotent'
    data = json.loads((ROOT/'data/research.json').read_text())
    source_ids = [s['id'] for s in data['sources']]
    entity_ids = [p['id'] for p in data['profiles'] + data['projects']]
    assert len(source_ids) == len(set(source_ids))
    assert len(entity_ids) == len(set(entity_ids))
    grouped = [id for _, ids in GROUPS for id in ids]
    assert sorted(grouped) == sorted(p['id'] for p in data['profiles']), 'Every producer must appear in exactly one comparison group'
    for ref in re.findall(r'\[(S\d+)\]', json.dumps(data)):
        assert ref in source_ids, ref
    for p in data['profiles'] + data['projects']:
        assert all(s in source_ids for s in p['sources'])
    sections=data['quality_trade']['sections']+data['processes']['sections']+data['us_development']['sections']
    assert len({s['id'] for s in sections}) == len(sections)
    for s in sections:
        if 'table' not in s: continue
        t=s['table']
        with (ROOT/'data'/t['csv']).open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.DictReader(stream))
        assert len(rows)==len(t['rows']), t['csv']
        assert all(row['source_urls'] for row in rows), t['csv']
    assert '99.98' in (ROOT/'quality-trade.html').read_text()
    assert '## Purity requirements and commodity flows' in (ROOT/'report.md').read_text()
    assert '## How magnesium metal is produced' in (ROOT/'report.md').read_text()
    assert '## A U.S. case for electrochemical magnesium' in (ROOT/'report.md').read_text()
    assert 'id="us-development"' in (ROOT/'report.html').read_text()
    us_page=(ROOT/'us-development.html').read_text()
    assert '77,900' in us_page and 'Jan–Jun 2026 (t)' in us_page
    assert 'not observed plant performance' in us_page
    figures=ROOT/'figures/v1'
    charts=json.loads((figures/'charts.json').read_text())['charts']
    assert len(charts)==6 and sum(c['analysis'] for c in charts)==1
    assert len({c['id'] for c in charts})==6
    for chart in charts:
        assert chart['alt'] and all(s in source_ids for s in chart['source_ids'])
        raw=(figures/(chart['id']+'.png')).read_bytes()
        assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(3840,2160)
        svg=ET.parse(figures/(chart['id']+'.svg')).getroot()
        assert svg.find('{http://www.w3.org/2000/svg}desc') is not None
        with (figures/(chart['id']+'.csv')).open(encoding='utf-8-sig',newline='') as stream:
            observations=list(csv.DictReader(stream))
        assert observations
        if chart['analysis']:
            assert len(observations)==27
            for row in observations:
                expected=float(row['assumed_electricity_kwh_per_kg'])*float(row['assumed_price_usd_per_mwh'])/1000
                assert abs(float(row['electricity_cost_usd_per_kg'])-expected)<1e-10
        else:
            assert all(row['source_id']=='S01' and row['source_url'] for row in observations)
    process_page=(ROOT/'processes.html').read_text()
    assert process_page.count('<ol class="process-steps">') == 3
    assert 'laboratory conditions' in process_page and 'Historical modeled/reference case' in process_page
    for q in data['quantities']:
        assert q['entity_id'] in entity_ids
        assert q['source_id'] in source_ids
        assert isinstance(q['value_t'], (int,float)) and q['value_t'] >= 0
        assert q['value_max_t'] is None or q['value_max_t'] >= q['value_t']
    # These are different material/reporting bases; the exports must preserve them.
    assert any(q['entity_id']=='dead-sea-magnesium' and q['value_t']==17800 and q['metric']=='primary production' for q in data['quantities'])
    assert all(q['metric']!='primary production' for q in data['quantities'] if q['entity_id'] in ('magontec','remt','baowu'))
    pages = {p.resolve():Page(p.read_text()) for p in ROOT.rglob('*.html')}
    links = 0
    for path,page in pages.items():
        assert page.h1s == 1, path
        for href in page.links:
            u=urlsplit(href)
            if u.scheme or u.netloc: continue
            assert not u.path.startswith('/'), f'Not GitHub subpath-safe: {href}'
            target=(path.parent/unquote(u.path)).resolve() if u.path else path
            assert target.is_relative_to(ROOT), href
            assert target.is_file(), f'{path.relative_to(ROOT)} -> missing {href}'
            if u.fragment and target.suffix=='.html':
                assert unquote(u.fragment) in pages[target].ids, f'Missing anchor: {href}'
            links += 1
    for f in (ROOT/'data').glob('*.csv'):
        with f.open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.reader(stream))
        assert len(rows)>1 and len(rows[0])==len(set(rows[0])), f
        assert all(len(row)==len(rows[0]) for row in rows), f
    with (ROOT/'data/quantities.csv').open(encoding='utf-8-sig',newline='') as stream:
        exported=list(csv.DictReader(stream))
    assert len(exported)==len(data['quantities'])
    assert not re.search(r'\[S\d+\](?!\s*—|\()', (ROOT/'report.md').read_text()), 'Unresolved Markdown source token'
    assert (ROOT/'.nojekyll').exists()
    print(f'PASS: {len(pages)} pages, {links} local links, {len(source_ids)} sources, {len(list((ROOT/"data").glob("*.csv")))} CSV tables; quantity bases preserved.')

if __name__=='__main__': main()
