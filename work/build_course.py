from pathlib import Path
import re, json, base64, subprocess, html, csv
root=Path('outputs')
source=[{'id':a,'text':b} for a,b in (ln.split('\t',1) for ln in Path('work/source_paragraphs.tsv').read_text().splitlines())]
found=[]
for ln in Path('work/foundations.tsv').read_text().splitlines():
 a=ln.split('|'); assert len(a)==8,(len(a),ln[:30]);found.append(dict(term=a[0],plain=a[1],strict=a[2],example=a[3],mistake=a[4],question=a[5],answer=a[6],ref=a[7]))
chapter_keys=['luk','korsch','hork','adorno','marcuse','fromm','habermas','baudrillard','althusser']
chapter_names=['卢卡奇','科尔施','霍克海默与《启蒙辩证法》','阿多诺','马尔库塞','弗洛姆','哈贝马斯','鲍德里亚','阿尔都塞']
chapter_ranges=['P0001—P0155','P0156—P0256','P0257—P0394','P0395—P0501','P0502—P0609','P0610—P0748','P0749—P0895','P0896—P1095','P1096—P1225']
chapter_maps=[['商品形式','可计算的社会关系','物化意识','总体性认识','阶级意识与实践'],['理论的历史位置','反对实证化','哲学维度','理论与实践统一'],['传统理论的限度','批判理论','启蒙的支配风险','文化工业'],['同一性思维','对象的剩余','非同一性','否定辩证法'],['文明的限制','额外压抑','需要被组织','单向度','解放的可能'],['经济生活条件','社会性格','观念与行为','逃避自由／积极联系'],['交往行动','有效性要求','系统／生活世界','殖民化','商议民主'],['使用与交换','符号价值','差异编码','仿真与理论转向'],['问题框架','症候阅读','意识形态召唤','结构因果性']]
raw=Path('outputs/西马零基础图文讲义.md').read_text()
base_parts=[p for p in re.split(r'(?=^## \d+\. )',raw,flags=re.M) if re.match(r'## (?:[2-9]|10)\. ',p)]
add_parts=[p for p in re.split(r'(?=^## )',Path('work/expanded_chapters.md').read_text(),flags=re.M) if p.startswith('## ')]
fur_parts=[p for p in re.split(r'(?=^## )',Path('work/chapter_further.md').read_text(),flags=re.M) if p.startswith('## ')]
boost_parts=[p for p in re.split(r'(?=^## )',Path('work/chapter_boost.md').read_text(),flags=re.M) if p.startswith('## ')]
assert len(base_parts)==len(add_parts)==len(fur_parts)==len(boost_parts)==9

def inl(s):
 s=html.escape(s)
 s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2" target="_blank" rel="noopener">\1</a>',s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
 s=re.sub(r'(P\d{4})(?:[—–-](P\d{4}))?',lambda m:f'<button class="source-link" data-ref="{m.group(1)}" type="button">{m.group(0)}</button>',s)
 s=re.sub(r'\[待核\]|\[待核实\]',r'<span class="tag tag-uncertain">待核实／争议</span>',s)
 s=re.sub(r'\[笔记\]',r'<span class="tag tag-note">原笔记</span>',s)
 s=re.sub(r'\[补充\]',r'<span class="tag tag-extra">核实补充</span>',s)
 return s

def md(s):
 lines=s.strip().splitlines();out=[];i=0
 while i<len(lines):
  line=lines[i].strip()
  if not line or line=='---':i+=1;continue
  if line.startswith('#'):
   n=len(line)-len(line.lstrip('#'));out.append(f'<h{min(n+1,5)}>{inl(line[n:].strip())}</h{min(n+1,5)}>');i+=1;continue
  if line.startswith('|'):
   rows=[]
   while i<len(lines) and lines[i].strip().startswith('|'):
    cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
    if not all(re.fullmatch(r':?-{2,}:?',c) for c in cells):rows.append(cells)
    i+=1
   if rows:
    out.append('<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+inl(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
    for row in rows[1:]:out.append('<tr>'+''.join('<td>'+inl(c)+'</td>' for c in row)+'</tr>')
    out.append('</tbody></table></div>')
   continue
  if line.startswith('>'):
   out.append('<blockquote>'+inl(line[1:].strip())+'</blockquote>');i+=1;continue
  if re.match(r'^(?:[-*]|\d+\.)\s',line):
   items=[]
   while i<len(lines) and re.match(r'^(?:[-*]|\d+\.)\s',lines[i].strip()):
    items.append(re.sub(r'^(?:[-*]|\d+\.)\s','',lines[i].strip()));i+=1
   out.append('<ul>'+''.join('<li>'+inl(x)+'</li>' for x in items)+'</ul>');continue
  out.append('<p>'+inl(line)+'</p>');i+=1
 return '\n'.join(out)
chapters=[]
for ix,(b,a,f,z) in enumerate(zip(base_parts,add_parts,fur_parts,boost_parts)):
 intro=b.split('\n',1)[1].strip()
 extra=a.split('\n',1)[1]+'\n'+f.split('\n',1)[1]+'\n'+z.split('\n',1)[1]
 sections=[]
 for m in re.finditer(r'^### (.+?)\n(.*?)(?=^### |\Z)',extra,flags=re.M|re.S):
  sections.append({'title':m.group(1),'html':md(m.group(2)),'text':m.group(2).strip()})
 chapters.append(dict(key=chapter_keys[ix],name=chapter_names[ix],range=chapter_ranges[ix],intro=md(intro),sections=sections,map=chapter_maps[ix],chars=len(b)+len(a)+len(f)+len(z)))
assert all(len(x['sections'])>=7 for x in chapters)
# Existing quiz data: take only the literal array before app code.
old=Path('outputs/西马互动练习.html').read_text()
chunk=old.split('const quizData=',1)[1].split(';\nconst pairData=',1)[0]
node='const d='+chunk+';process.stdout.write(JSON.stringify(d))'
legacy=json.loads(subprocess.check_output(['node','-e',node],text=True))
legacy_ex=[
 ['对；它误把社会关系问题写成购物习惯。','使用价值确实存在，不是此句的错误。','劳动的社会联系恰是分析要点。','价格数字不是这里的主要误解。'],
 ['数字本身不足以构成物化。','对；须分析规则和社会关系。','排行榜只是表面形式。','数字制度仍可具体分析。'],
 ['对；把人造规则当自然规律是物化意识。','符号价值研究消费身份意义。','症候阅读研究文本框架。','基本压抑研究文明限制。'],
 ['总体性并非知识总量。','对；把局部放回关系。','不能推出整体压倒个人。','不同理论不能强合并。'],
 ['术语数量不是关键。','对；他重理论的历史实践联系。','他批评把理论缩成中立科学。','统计形式不能回答问题。'],
 ['只看流量仍在优化手段。','对；批判理论追问目的与社会后果。','不能机械否定所有数字。','受众喜欢与否不是第一问。'],
 ['对；非同一性提醒概念的遗漏。','机械趋同属于弗洛姆。','策略行动属于哈贝马斯。','符号价值属于鲍德里亚。'],
 ['所有规则不等于额外压抑。','对；需作历史社会区分。','不能由劳动本身推出无意义。','区分是可讨论的。'],
 ['对；社会心理理论可提问，不能随意诊断。','交换价值不能解释心理机制。','客体优先性是阿多诺概念。','认识论断裂是阿尔都塞概念。'],
 ['对；事实陈述首先可验真假。','正当性主要对应规范。','真诚性对应主观表达。','符号价值无关。'],
 ['真理性指事实陈述。','对；校规公平需规范理由。','交换价值关乎商品。','客体优先性关乎认识。'],
 ['系统出现不自动构成殖民化。','对；关键是越界挤压交往。','效率提升并非充分条件。','效率下降也非充分条件。'],
 ['对；品牌身份可用符号价值分析。','基本压抑关乎文明限制。','阶级意识关乎历史主体。','客体优先性关乎概念与对象。'],
 ['现实生产没有字面消失。','对；是有争议的理论诊断。','服务业消失不是其含义。','不同于商品拜物教。'],
 ['对；先查可问与不可问的问题。','纸张颜色无关问题框架。','空白不证明作者恶意。','不等于所有答案虚假。'],
 ['不是伦理上反对尊重人。','对；反对抽象人性作解释起点。','与医学诊断无关。','仍须分析主体形成与行动。']]
assert len(legacy)==len(legacy_ex)==16
for i,(q,ex) in enumerate(zip(legacy,legacy_ex),1):q.update(id=f'Q{i:02d}',ex=ex,type='模拟题')
quiz=list(legacy)
for ln in Path('work/quiz_additions.tsv').read_text().splitlines():
 a=ln.split('|');assert len(a)==12,(len(a),a[0]);cat,q,*_=a
 quiz.append(dict(id=f'Q{len(quiz)+1:02d}',cat=a[0],q=a[1],o=a[2:6],a=int(a[6]),ex=a[7:11],ref=a[11],type='模拟题'))
assert len(quiz)==36
# Existing written exercises, preserving detailed answers and scoring rubrics.
exercise=Path('outputs/西马练习与答案.md').read_text()
questions={}
for ln in exercise.splitlines():
 m=re.match(r'^\| ((?:C|S|J|L)\d\d) \| (.*?) \| (.*?) \|$',ln)
 if m:
  ident=m.group(1)
  if ident not in questions:questions[ident]=dict(id=ident,title=m.group(2),ref=m.group(3),type='模拟题')
  else:questions[ident].update(answer=m.group(2),loss=m.group(3))
for ident in ['L01','L02','L03','L04']:
 m=re.search(r'\*\*'+ident+r' [^\n]+\*\*\n(.*?)(?=\n\*\*L\d\d |\n### F\.|\Z)',exercise,flags=re.S)
 assert m,ident
 block=m.group(1);ans=re.search(r'\*\*参考答案\*\*：(.*?)(?=\n- \*\*得分要点)',block,flags=re.S)
 points=re.search(r'\*\*得分要点\*\*：(.*?)(?=\n- \*\*常见失分)',block,flags=re.S)
 loss=re.search(r'\*\*常见失分\*\*：(.*?)(?:来源位置|\n|$)',block,flags=re.S)
 questions[ident].update(answer=ans.group(1).strip() if ans else '',points=points.group(1).strip() if points else '',loss=loss.group(1).strip() if loss else '')
for ident,q in questions.items():
 if 'points' not in q:
  q['points']=('定义 3 分、联系 2 分、边界或例子 1 分' if ident.startswith('C') else '三个论证环节各 3 分、术语准确与收束 1 分' if ident.startswith('S') else '共同问题 2 分、各家论证各 4 分、关键差异 3 分、边界 2 分')
 q['kind']='概念辨析' if ident.startswith('C') else '简答' if ident.startswith('S') else '比较' if ident.startswith('J') else '论述'
assert len(questions)==27,len(questions)
foundation_big=[
 ('F01','用一个具体例子区分主体与客体，并解释它们为何不是固定身份。','在讨论校规时，学生是提出理由的主体，校规是讨论对象；在学校管理中，学生又可能成为制度处理的对象。主体和客体是在一定认识或实践关系中的位置，须说明关系和活动。','定义关系 3 分；例子 3 分；说明位置可变 2 分。','只把主体写为单个人、客体写为物品。','P0088—P0104'),
 ('F02','商品拜物教为什么不等于喜欢购物？','马克思分析的是生产者之间的社会劳动关系为何在商品交换中呈现为物与物的关系；消费偏好只是个人行为，不能替代对价值形式和社会关系的分析。','定义 3 分；中介机制 3 分；与购物习惯区分 2 分。','仅批评消费欲望。','P0008—P0015'),
 ('F03','为什么对象化劳动不必然是异化劳动？','对象化表示人的能力通过劳动成为对象；异化劳动特指劳动活动及其产品在特定社会关系中成为异己力量。做出作品本身不足以证明异化，须分析劳动者对活动与成果的关系。','两概念各 2 分；关系 2 分；条件 2 分。','把所有产品都说成异己力量。','P0021—P0028'),
 ('F04','总体性为什么不是掌握全部事实？','总体性要求把局部置于其具体历史社会联系，说明不同因素怎样中介并改变局部意义；它不是知识量竞赛，也不允许用整体口号抹去对象差异。','原则 3 分；中介 3 分；边界 2 分。','只写“整体大于部分”。','P0071—P0096'),
 ('F05','意识形态为什么不能只定义为故意撒谎？','在阿尔都塞那里，意识形态涉及人对其存在条件的想象性关系，并在学校、家庭等制度实践中塑造主体。谎言可能是其中现象，但不足以解释稳定的身份、习惯与社会再生产。','定义 3 分；制度实践 3 分；与谎言区分 2 分。','把意识形态仅当宣传口号。','P1131—P1184'),
 ('F06','为什么批判工具理性不等于反对科学技术？','工具理性问达到目的的有效手段；批判理论质疑当手段计算成为唯一标准时，目的、自由和人的关系会被遮蔽。技术可有积极作用，关键是目的、制度和使用方式。','定义 2 分；批判条件 3 分；技术边界 3 分。','说效率本身一定有害。','P0274—P0393')]
for ident,title,answer,points,loss,ref in foundation_big:questions[ident]=dict(id=ident,title=title,answer=answer,points=points,loss=loss,ref=ref,type='模拟题',kind='基础简答')

# Two genuinely verifiable items: only one source currently accessible, clearly foundational rather than a Western Marxism topic.
real=[dict(id='T01',school='上海外国语大学',year='2016',kind='相关基础真题',title='哲学基本问题（名词解释）',ref='马克思主义原理基础；非西马专题',url='https://graduate.shisu.edu.cn/_upload/article/d7/6d/ac3adba145629c9f532c302a9c4e/82c0ed57-b508-4037-8847-c858c04cd11e.pdf',answer='哲学基本问题通常指思维与存在的关系，包括何者为第一性、思维能否认识存在两个方面。',points='关系 4 分；两个方面各 3 分。',loss='只说人和自然的关系。')]
# Daily plan.
days=[]
for ln in Path('work/daily.tsv').read_text().splitlines():
 a=ln.split('|');assert len(a)==6,a
 days.append(dict(day=int(a[0]),chapter=a[1],sections=[int(x) for x in a[2].split(',')],source=a[3],focus=a[4],essay=a[5],weekly=int(a[0]) in (7,14,21,28,35,42),final=int(a[0])==45))
assert len(days)==45 and [x['day'] for x in days]==list(range(1,46))
images={f'G{i}':'data:image/png;base64,'+base64.b64encode((root/f'西马原图{i}.png').read_bytes()).decode() for i in (1,2,3)}
image_positions={}
srcmd=(root/'西马原笔记完整整理.md').read_text()
for m in re.finditer(r'\*\*【原笔记图片 (G\d)；位于 (P\d{4}) 之后】\*\*',srcmd):image_positions[m.group(1)]=m.group(2)
refs=[{'label':m.group(1),'url':m.group(2)} for m in re.finditer(r'^- \[R\d+\] \[([^]]+)\]\((https?://[^)]+)\)',raw,flags=re.M)]
methods=[{'name':'主动回忆与练习测验','url':'https://doi.org/10.1177/1529100612453266','how':'每天开头先合上讲义解释概念，再作答并核对。'}, {'name':'间隔复习','url':'https://pubmed.ncbi.nlm.nih.gov/16719566/','how':'答错题在后续第 1、3、7 个学习日再次出现。'}, {'name':'交错练习','url':'https://eric.ed.gov/?id=EJ786797','how':'每周检查及最后七天混合比较不同思想家；此研究在数学任务中验证，迁移到哲学答题是教学设计推断。'}, {'name':'提取练习实验','url':'https://doi.org/10.1111/j.1467-9280.2006.01693.x','how':'先写自己的解释再看参考答案，以减少只重读造成的熟悉感。'}]
with Path('outputs/西马记忆卡片.csv').open(newline='',encoding='utf-8') as fp:
 cards=[dict(front=row[0],back=row[1],tag=row[2]) for row in csv.reader(fp) if len(row)==3 and not row[0].startswith('#')]
assert all(x['front'] and x['back'] for x in cards)
data=dict(source=source,foundations=found,chapters=chapters,quiz=quiz,essays=list(questions.values()),real=real,days=days,images=images,imagePositions=image_positions,refs=refs,methods=methods,cards=cards)
from build_question_bank import enhance
enhance(data)
Path('work/course_data.json').write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
print('chapters',[(x['name'],x['chars'],len(x['sections'])) for x in chapters]);print('foundations',len(found),'quiz',len(data['quiz']),'essays',len(data['essays']),'cards',len(cards),'days',len(days),'source',len(source))
