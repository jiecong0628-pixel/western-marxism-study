from collections import Counter
from pathlib import Path
import json, re, zipfile

data = json.loads(Path('work/course_data.json').read_text())
md = Path('outputs/西马原笔记完整整理.md').read_text()
html = Path('outputs/西马45天整合学习网页.html').read_text()
source = data['source']

assert len(source) == 1225
assert [x['id'] for x in source] == [f'P{i:04d}' for i in range(1, 1226)]
md_paras = re.findall(r'^\*\*【原笔记】(P\d{4})\*\*  (.*)$', md, flags=re.M)
assert md_paras == [(x['id'], x['text']) for x in source]
assert md.count('**【原笔记图片 G') == 3
assert set(data['imagePositions']) == {'G1', 'G2', 'G3'}
assert all(data['images'][g].startswith('data:image/png;base64,') for g in data['images'])

assert len(data['foundations']) == 18
assert len(data['chapters']) == 9
assert all(c['chars'] >= 2500 and len(c['sections']) >= 8 for c in data['chapters'])
assert len(data['quiz']) == 36
assert len(data['essays']) == 33
assert len(data['cards']) == 74
assert len(data['days']) == 45
assert len({q['id'] for q in data['quiz']}) == 36
assert len({q['id'] for q in data['essays']}) == 33
assert all(q['type'] == '模拟题' and len(q['o']) == len(q['ex']) == 4 and 0 <= q['a'] < 4 and all(q['ex']) for q in data['quiz'])
assert all(q['type'] == '模拟题' and all(q.get(k) for k in ('title', 'answer', 'points', 'loss', 'ref')) for q in data['essays'])
assert all(q['essay'] in {x['id'] for x in data['essays']} for q in data['days'])

ch = {c['key']: c for c in data['chapters']}
used = {k: set() for k in ch}
foundation_used = set()
max_source = (0, 0)
daily_source = set()
for day in data['days']:
    if day['chapter'] == 'base':
        foundation_used.update(day['sections'])
    elif day['chapter'] in ch:
        used[day['chapter']].update(day['sections'])
        assert all(0 <= i < len(ch[day['chapter']]['sections']) for i in day['sections'])
    ids = []
    for part in day['source'].split(';'):
        match = re.fullmatch(r'P(\d{4})(?:-P(\d{4}))?', part)
        assert match, (day['day'], part)
        start = int(match.group(1))
        end = int(match.group(2) or match.group(1))
        assert 1 <= start <= end <= 1225
        ids.extend(range(start, end + 1))
    daily_source.update(ids)
    count = sum(len(source[i - 1]['text']) for i in dict.fromkeys(ids))
    max_source = max(max_source, (count, day['day']))
    long_read = count > 1500
    if day['weekly']:
        times = [10, 10, 10, 15, 12, 3]
    elif long_read:
        times = [8, 14, 18, 10, 8, 2]
    else:
        times = [8, 10, 22, 10, 8, 2]
    assert sum(times) == 60
    if not day['weekly']:
        adjusted = [13, 9, 18, 10, 8, 2] if long_read else [13, 5, 22, 10, 8, 2]
        assert sum(adjusted) == 60
assert foundation_used == set(range(18))
assert all(used[k] == set(range(len(c['sections']))) for k, c in ch.items())
assert max_source[0] <= 2300
assert daily_source == set(range(1, 1226)), "每日原文漏排"

category = Counter(q['cat'] for q in data['quiz'])
assert category['基础'] == 9
assert all(category[c['name'].split('与')[0]] >= 3 for c in data['chapters'])
assert len(data['real']) == 1 and data['real'][0]['kind'] == '相关基础真题'
assert 'graduate.shisu.edu.cn' in data['real'][0]['url']
assert '27 道带评分点' not in html and '33 道带评分点' in html
assert len(re.findall(r'<script(?:\s|>)', html)) == 2
assert not re.search(r'<script[^>]+src=', html)
assert not re.search(r'<link[^>]+rel="stylesheet"', html)
assert html.count('data:image/png;base64,') >= 3
assert '共 ${DATA.cards.length} 张' in html

print('PASS: 原文 1225 段逐字相符、3 图入 MD 和网页')
print('PASS: 18 基础概念、9 章 2500+ 字且章节环节均排入日课')
print('PASS: 36 选择题逐项解析、33 主观题及答案评分点、74 短卡')
print('PASS: 45 日均有原文、讲解、练习与大题；最长日课原文', max_source)
print('PASS: 自编题／相关基础真题区分；网页无外部脚本或样式依赖')
