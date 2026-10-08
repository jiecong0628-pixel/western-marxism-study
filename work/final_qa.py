"""内容与交互逻辑检查；不冒充实际浏览器和手机验证。"""
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import base64, json, re, subprocess
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'work/course_data.json').read_text())
md=(ROOT/'outputs/西马原笔记完整整理.md').read_text()
html=(ROOT/'outputs/西马45天整合学习网页.html').read_text()
source=data['source']
assert len(source)==1225
assert [x['id'] for x in source]==[f'P{i:04d}' for i in range(1,1226)]
assert re.findall(r'^\*\*【原笔记】(P\d{4})\*\*  (.*)$',md,re.M)==[(x['id'],x['text']) for x in source]
assert md.count('**【原笔记图片 G')==3 and set(data['imagePositions'])=={'G1','G2','G3'}
docx=ROOT/'01黄羽学姐西马复习笔记.docx'
if docx.exists():
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
    with ZipFile(docx) as z:
        xml=ET.fromstring(z.read('word/document.xml'));original=[]
        for p in xml.findall('./w:body/w:p',ns):
            s=''.join(t.text or '' for t in p.findall('.//w:t',ns)).strip()
            if s:original.append(s)
        assert original==[x['text'] for x in source], 'DOCX 与整理版不同'
        rels={e.get('Id'):e.get('Target') for e in ET.fromstring(z.read('word/_rels/document.xml.rels'))}
        images=[z.read('word/'+rels[b.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')]) for b in xml.findall('.//a:blip',ns)]
        assert len(images)==3
        for i,b in enumerate(images,1):assert b==base64.b64decode(data['images'][f'G{i}'].split(',',1)[1])
    print('PASS：原始DOCX与整理MD／网页的1225段、3图逐字节对应')
else:print('未验证：原始DOCX缺失，仅检查整理版与网页一致性')

def ids(spec):
    out=set()
    for a,b in re.findall(r'P(\d{4})(?:[—–-]P(\d{4}))?',spec):
        assert 1<=int(a)<=int(b or a)<=1225
        out.update(range(int(a),int(b or a)+1))
    assert out,spec
    return out
units={u['id']:u for u in data['knowledge']};quiz={q['id']:q for q in data['quiz']};essays={q['id']:q for q in data['essays']}
refs={r['id'] for r in data['refs']}
assert len(units)==84 and len(quiz)==len(data['quiz'])==372 and len(essays)==len(data['essays'])==111
assert len(quiz.keys()|essays.keys())==483
assert len(data['legacyQuiz'])==36 and len(data['legacyEssays'])==33
assert len({q['q'] for q in quiz.values()})==372 and len({q['title'] for q in essays.values()})==111
assert len(data['foundations'])==18 and len(data['chapters'])==9 and len(data['cards'])==74
assert all(c['chars']>=2500 and len(c['sections'])>=8 for c in data['chapters'])
cover=set()
for u in units.values():
    if u['chapter']!='base':cover.update(ids(u['ref']))
    assert len(u['quizIds'])>=4 and len(set(u['quizIds']))==len(u['quizIds'])
    assert {'概念与边界','论证与易混','情境应用','反例与评价'}<={quiz[i]['angle'] for i in u['quizIds']}
    assert all(u['id'] in quiz[i]['kp'] for i in u['quizIds']) and all(u['id'] in essays[i]['kp'] for i in u['essayIds'])
    assert u['refs'] and set(u['refs'])<=refs
    assert u['definition'] and len(u['chain'])==3 and u['boundary'] and '教学假设' in u['case']
    assert all(1<=d<=45 for d in u['learnDays']+u['reviewDays'])
assert cover==set(range(1,1226))
counts=Counter(q['chapter'] for q in quiz.values());assert counts['base']==72
for key in ['luk','hork','habermas']:assert 35<=counts[key]<=50
assert all(counts[c['key']]>=20 for c in data['chapters'])
for q in quiz.values():
    assert q['type']=='模拟题' and q['kind']=='选择题'
    assert q['priority'] in ['核心必会','重点掌握','拓展理解'] and q['difficulty'] in ['入门','进阶','综合']
    assert len(q['o'])==len(q['ex'])==len(set(q['o']))==4 and 0<=q['a']<4 and all(len(x)>=10 for x in q['ex'])
    assert all(q.get(k) for k in ['why','remedy','lesson','recall','ref','topic','kp'])
    assert set(q['kp'])<=units.keys() and ids(q['ref'])
    if 'statements' in q:
        assert len(q['statements'])==2 and q['ex'][q['a']].count('本项判断正确。')==2
        assert all(i==q['a'] or x.count('本项判断正确。')<2 for i,x in enumerate(q['ex']))
    else:
        assert '应选' in q['ex'][q['a']] and all(i==q['a'] or '应选' not in x for i,x in enumerate(q['ex']))
assert sum('statements' not in q for q in quiz.values())==36
scores={'名词解释':8,'简答':10,'比较':15,'论述':25,'材料分析':20}
minimum={'名词解释':120,'简答':240,'比较':300,'论述':600,'材料分析':330}
for q in essays.values():
    assert q['type']=='模拟题' and q['kind'] in scores
    assert all(q.get(k) for k in ['answer','expanded','audit','structure','outline','rubric','loss','accepted','variation','ref'])
    assert sum(r['score'] for r in q['rubric'])==scores[q['kind']] and len(q['answer'])>=minimum[q['kind']],q['id']
    assert q['minutes'] in [5,9,12,20] and set(q['kp'])<=units.keys() and ids(q['ref'])
for c in data['chapters']:assert {q['kind'] for q in essays.values() if q['chapter']==c['key']}==set(scores)
assert len(data['audits'])==15
assert all(set(n['kp'])<=units.keys() and set(n['refs'])<=refs and ids(n['ref']) for n in data['audits'])
assert len(data['real'])==1 and data['real'][0]['kind']=='相关基础真题'
assert data['real'][0]['officialScore']==12 and data['real'][0]['subject']=='马克思主义原理（思想政治教育专业）'
assert 'graduate.shisu.edu.cn' in data['real'][0]['url']
print('PASS：84单元覆盖1225段；372选择题逐项反馈；111主观题分题型答案、评分与变式')
print('PASS：15条订正／限定／争议记录；483道自编模拟题与1道基础真题分开')
chapters={c['key']:c for c in data['chapters']};used={k:set() for k in chapters};base=set();max_read=(0,0);daily_source=set()
assert [d['day'] for d in data['days']]==list(range(1,46))
for d in data['days']:
    if d['chapter']=='base':base.update(d['sections'])
    elif d['chapter'] in chapters:
        used[d['chapter']].update(d['sections'])
        assert all(0<=i<len(chapters[d['chapter']]['sections']) for i in d['sections'])
    assert d['knowledge'] and set(d['knowledge'])<=units.keys() and d['essay'] in essays
    daily_source.update(ids(d['source']))
    max_read=max(max_read,(sum(len(source[i-1]['text']) for i in ids(d['source'])),d['day']))
assert base==set(range(18)) and all(used[k]==set(range(len(c['sections']))) for k,c in chapters.items())
assert max_read[0]<=2300
assert daily_source==set(range(1,1226)), '每日原文漏排'
scripts=re.findall(r'<script>(.*?)</script>',html,re.S);assert len(scripts)==2
assert json.loads(scripts[0].removeprefix('const DATA=').removesuffix(';'))==data
export=json.loads((ROOT/'outputs/西马专题题库数据.json').read_text())
assert export['quiz']==data['quiz'] and export['essays']==data['essays']
assert not re.search(r'<script[^>]+src=',html) and not re.search(r'<link[^>]+rel="stylesheet"',html)
assert 'viewport' in html and '@media(max-width:400px)' in html and html.count('data:image/png;base64,')>=3
subprocess.run(['node','--check'],input='\n'.join(scripts),text=True,check=True,cwd=ROOT)
print('PASS：网页、生成数据与导出题库同步；无外部脚本或样式；脚本语法检查')
subprocess.run(['node','work/qa_question_bank.js'],check=True,cwd=ROOT)
print('PASS：45日任务对应与60分钟预算；最长日课必读原文',max_read,'（字符数，学习日）')
print('未验证：真实浏览器存储、下载/文件选择、手机触摸与排版、学生完成时长和提分效果')
