"""编译可编辑的题库原稿；原稿为自编教学内容，编号保持稳定。"""
from pathlib import Path
from collections import Counter
import re, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
ANGLE = ['概念与边界', '论证与易混', '情境应用', '反例与评价']

def rng(spec):
    out=[]
    for a,b in re.findall(r'P?(\d{4})(?:[—-]P?(\d{4}))?',spec):
        out.extend(range(int(a),int(b or a)+1))
    return sorted(set(out))

def enhance(data):
    data['legacyQuiz']=data['quiz']
    data['legacyEssays']=data['essays']
    data['refs'].append({'id':'R14','label':'阿尔都塞：意识形态与意识形态国家机器（原著英译）','url':'https://www.marxists.org/reference/archive/althusser/1970/ideology.htm'})
    data['refs'].append({'id':'R15','label':'马克思：《资本论》第一卷第八章，不变资本与可变资本（原著英译）','url':'https://www.marxists.org/archive/marx/works/1867-c1/ch08.htm'})
    for i,r in enumerate(data['refs'][:13],1):r['id']=f'R{i}'
    data['methods']=[
      {'name':'先回忆后反馈','url':'https://pubmed.ncbi.nlm.nih.gov/16507066/','how':'Roediger 与 Karpicke（2006）的 prose 实验支持延迟记忆中的提取练习。界面先作答再给解析，大题先写自己的提纲；这不等于该研究已经证明本哲学题库的提分效果。'},
      {'name':'间隔复习','url':'https://pubmed.ncbi.nlm.nih.gov/16719566/','how':'Cepeda 等（2006）综述发现适合的间隔与保留时间相关。课程按学习日安排 1、3、7 日延迟，并依答错重新排期；这是可调整的教学规则，不是唯一最优间隔。'},
      {'name':'交错比较','url':'https://digitalcommons.usf.edu/etd/529/','how':'Taylor（2008）数学研究比较混合与分块练习，并控制间隔。每周跨作者比较是迁移到哲学的教学推断，以本人的每周表现检查效果。'},
      {'name':'示范逐步退场','url':'https://ies.ed.gov/ncee/wwc/PracticeGuide/1','how':'IES（2007）指南建议交替示范与独立解题。前期允许查看答题步骤，后期默认收起提示；大题需独立提纲再看完整答案，再作变式。'},
    ]
    data['real'][0].update(subject='马克思主义原理（思想政治教育专业）',kind='相关基础真题',verified='2026-10-08：学校 PDF 文本核验，试卷第 1 页',title='哲学基本问题',format='名词解释',officialScore=12,
      answer='哲学基本问题通常指思维与存在的关系问题。第一方面是何者为第一性，形成唯物主义与唯心主义的基本区别；第二方面是思维能否认识存在，涉及可知论与不可知论。作答应明确这是哲学基本问题的教材表述，不能简化为某个具体社会议题。',points='自拟教学评分：关系表述4分，第一方面4分，第二方面4分；不是院校官方评分细则。')
    units=[];current=None
    for line in (ROOT/'work/question_bank/chapters.txt').read_text().splitlines():
        if line.startswith('@'):
            a=line[1:].split('|'); assert len(a)==10,(len(a),line[:100])
            key,ident,term,bounds,priority,definition,chain,boundary,case,refs=a
            start,end=map(int,bounds.split('-'))
            current=dict(id=ident,chapter=key,term=term,ref=f'P{start:04d}-P{end:04d}',priority=priority,definition=definition,chain=chain.split('~'),boundary=boundary,case=case,refs=refs.split(','),raw=[])
            units.append(current)
        elif line.startswith('?'):
            a=line[1:].split('|');assert len(a)==7,line
            current['raw'].append(a)
    for line in (ROOT/'work/question_bank/foundations.txt').read_text().splitlines():
        if line.startswith('@'):
            n=int(line[1:]);f=data['foundations'][n-1]
            current=dict(id=f'G{n:02d}',chapter='base',term=f['term'],ref=f['ref'].replace('—','-'),priority='核心必会' if n not in (12,14,17) else '重点掌握',definition=f['plain']+' '+f['strict'],chain=[f['plain'],f['strict'],f['answer']],boundary=f['mistake']+'；请区分概念定义、经验判断与理论应用。',case='教学假设／例子：'+f['example'],refs=[],raw=[],foundation=n-1)
            units.append(current)
        elif line.startswith('?'):
            current['raw'].append(line[1:].split('|'))
    assert len(units)==84 and all(len(u['raw'])==4 for u in units)
    background_refs={1:['R4'],2:['R1'],3:['R2','R5'],4:['R3'],5:['R3'],6:['R3'],7:['R3'],8:['R2'],9:['R2','R4'],10:['R4'],11:['R11','R14'],12:['R1'],13:['R2','R3'],14:['R8'],15:['R6','R10'],16:['R9'],17:['R11'],18:['R12']}
    for u in units:
        if u['chapter']=='base':u['refs']=background_refs[u['foundation']+1]
    chapters={x['key']:x for x in data['chapters']}
    quizzes=[];essays=[]
    for u in units:
        k=u['chapter'];num=int(re.search(r'\d+',u['id'])[0]);c=chapters.get(k)
        if k=='base':
            learn=[d['day'] for d in data['days'] if d['chapter']=='base' and u['foundation'] in d['sections']]
            u['lessonSection']=u['foundation']
        else:
            choices=[d for d in data['days'] if d['chapter']==k]
            target=set(rng(u['ref']))
            best=max(choices,key=lambda d:len(target.intersection(rng(d['source']))))
            learn=[best['day']]
            # 单元微课提供直接对应，章节索引另提供背景展开；不伪造精确原讲义标题匹配。
            words=[w for w in re.split(r'[、与及：]',u['term']) if len(w)>1]
            u['lessonSection']=max(range(len(c['sections'])),key=lambda i:sum(c['sections'][i]['text'].count(w)*len(w) for w in words))
        first=learn[0];u['learnDays']=learn;u['reviewDays']=sorted(set(min(45,first+x) for x in (1,3,7)))
        u['reason']='理论主线与后续比较的必要前提' if u['priority']=='核心必会' else '关键中介、易混区分或应用边界' if u['priority']=='重点掌握' else '补充思想史分类与争论背景'
        u['status']='原笔记主线＋教学重构（非原文）；核查提示与原文分开展示'
        qids=[]
        for j,a in enumerate(u['raw']):
            stem,s1,t1,e1,s2,t2,e2=a;truth=[bool(int(t1)),bool(int(t2))];statements=[s1,s2];reasons=[e1,e2]
            # 部分原稿误读改成作者提供的正确限定；稳定散布在各题，避免
            # 学生从“第几问”猜真假。交换两条陈述的次序不改变考查对象。
            seed=hashlib.sha256(f'{u["id"]}-{j}'.encode()).digest()
            for z in range(2):
                if not truth[z] and seed[z]%10<3:
                    statements[z]=reasons[z]
                    reasons[z]='成立：此判断补上推论所需的限定或中介。'+reasons[z]
                    truth[z]=True
            if seed[2]%2:truth.reverse();statements.reverse();reasons.reverse()
            specs=[(True,True),(True,False),(False,True),(False,False)]
            shift=seed[3]%4;specs=specs[shift:]+specs[:shift]
            opts=[];ex=[]
            for spec in specs:
                opts.append(('①成立' if spec[0] else '①不成立')+'，'+('②成立' if spec[1] else '②不成立'))
                bits=[]
                for z in range(2):
                    correct=spec[z]==truth[z]
                    bits.append(f'{"①②"[z]}：'+('本项判断正确。' if correct else '本项把该判断的成立性判反了。')+reasons[z])
                ex.append(' '.join(bits))
            ident=f'X-{u["id"]}-{j+1}';qids.append(ident)
            quizzes.append(dict(id=ident,chapter=k,cat='基础' if k=='base' else c['name'].split('与')[0],kp=[u['id']],topic=u['term'],priority=u['priority'],difficulty=['入门','进阶','综合','综合'][j],angle=ANGLE[j],type='模拟题',kind='选择题',q=stem+' 请判断以下两项陈述，选择唯一正确的组合。',statements=statements,o=opts,a=specs.index(tuple(truth)),ex=ex,ref=u['ref'],why=f'先定位“{u["term"]}”的问题，分别判断两条陈述，不能因为其中一条有道理就接受整组选项。两条判断的根据为：'+ '；'.join(reasons),remedy='；'.join(f'{"①②"[z]}'+('成立，无需改成相反判断：' if truth[z] else '不成立，修正方向：')+reasons[z] for z in range(2)),lesson=u['definition']+' 论证线索：'+' → '.join(u['chain'])+'。',recall='用一句话说明：'+u['term']+'的判断需要什么条件？再闭书复述：'+' → '.join(u['chain']),estimated=4,plannedDays=[first,u['reviewDays'][0],u['reviewDays'][1],u['reviewDays'][-1]][j]))
        u['quizIds']=qids
        kind='名词解释' if num%2 else '简答';ident='W-'+u['id']
        title=('解释“'+u['term']+'”，交代理论语境并区分易混点。') if kind=='名词解释' else ('简述“'+u['term']+'”的论证过程，说明一个误读及应用边界。')
        outline=['先限定问题与概念：'+u['definition'],'再写出中介：'+' → '.join(u['chain']),'最后辨析与限定：'+u['boundary']]
        if kind=='名词解释':
            answer=u['definition']+'\n\n其关系可概括为：'+'；'.join(u['chain'])+'。\n\n需注意：'+u['boundary']
            rubric=[{'text':'概念含义与语境：'+u['definition'],'score':3},{'text':'关键关系：'+' → '.join(u['chain']),'score':3},{'text':'边界辨析：'+u['boundary'],'score':2}]
        else:
            answer='本题首先需要限定对象。'+u['definition']+'\n\n论证依次展开：'+''.join(f'第{["一","二","三"][i]}步，{x}。' for i,x in enumerate(u['chain']))+'关键不在并列几个名词，而在说明后一步怎样由前一步及其条件形成。\n\n可用下列例子理解，但它不是理论的证明：'+u['case']+'\n\n最后，应避免如下跳步：'+u['boundary']
            rubric=[{'text':'问题与定义：'+u['definition'],'score':2},{'text':'三个环节及其联系：'+' → '.join(u['chain']),'score':4},{'text':'辨析和边界：'+u['boundary'],'score':2},{'text':'用例并说明证据：'+u['case'],'score':2}]
        essay=dict(id=ident,chapter=k,cat='基础' if k=='base' else c['name'].split('与')[0],topic=u['term'],kp=[u['id']],kind=kind,type='模拟题',title=title,priority=u['priority'],difficulty='入门' if kind=='名词解释' else '进阶',minutes=5 if kind=='名词解释' else 9,outline=outline,answer=answer,expanded='阅读原笔记时先分清原文和本答案。'+u['definition']+'\n\n'+ '\n\n'.join(f'辨析训练 {i+1}：{q[0]} 判断依据：{q[3]}；{q[6]}' for i,q in enumerate(u['raw']))+'\n\n现实应用仍需核验：'+u['case'],rubric=rubric,points='；'.join(x['text']+f'（{x["score"]}分）' for x in rubric),loss=u['boundary'],accepted='可以换用有同等论证作用的例子或调整顺序，但要保留本题概念关系；'+u['boundary'],variation='不用本题例子，重新说明“'+u['term']+'”与一个相近概念的差别；指出你的判断还需要哪条条件。',audit='名词解释先限定术语及语境，勿写成泛泛人物简介。' if kind=='名词解释' else '逐步解释因果或理论中介，不要把三个环节仅当成清单。',structure='定义与语境 → 关键关系 → 区别或边界' if kind=='名词解释' else '问题与前提 → 中介与结论 → 案例 → 限定',ref=u['ref'])
        essays.append(essay);u['essayIds']=[ident]
    um={u['id']:u for u in units};key=None;direct_counts=Counter()
    for line in (ROOT/'work/question_bank/direct.txt').read_text().splitlines():
        if line.startswith('@'):key=line[1:];continue
        if not line:continue
        ids,difficulty,angle,stem,options,answer,explanations,why,remedy=line.split('|')
        ks=ids.split(',');us=[um[x] for x in ks];direct_counts[key]+=1
        ident=f'X-{key}-D{direct_counts[key]}'
        options=options.split('~');explanations=explanations.split('~');answer=int(answer)
        assert len(options)==len(explanations)==4 and 0<=answer<4
        shift=int(hashlib.sha256(ident.encode()).hexdigest()[:4],16)%4
        options=options[shift:]+options[:shift];explanations=explanations[shift:]+explanations[:shift];answer=(answer-shift)%4
        first=min(u['learnDays'][0] for u in us)
        quizzes.append(dict(id=ident,chapter=key,cat=chapters[key]['name'].split('与')[0],kp=ks,topic='跨理论比较' if angle=='跨理论比较' else us[0]['term'],priority='核心必会' if any(u['priority']=='核心必会' for u in us) else '重点掌握',difficulty=difficulty,angle=angle,type='模拟题',kind='选择题',q=stem,o=options,a=answer,ex=explanations,ref=';'.join(dict.fromkeys(u['ref'] for u in us)),why=why,remedy=remedy,lesson='\n'.join(u['term']+'：'+u['definition']+' 论证线索：'+' → '.join(u['chain'])+'。' for u in us),recall='闭书比较：'+ '；'.join(u['term'] for u in us)+'。各自回答什么问题，需要哪些中介？',estimated=4,plannedDays=min(45,first+[0,3,7,14][direct_counts[key]-1])))
        for u in us:u['quizIds'].append(ident)
    for line in (ROOT/'work/question_bank/synthesis.txt').read_text().splitlines():
        if line.startswith('@'):key=line[1:];continue
        if not line:continue
        kind,title,answer,score,accepted,variation,ids=line.split('|');ks=ids.split(',');us=[um[x] for x in ks]
        ident=f'W-{key}-'+{'比较':'C','论述':'E','材料分析':'A'}[kind]
        rubric=[dict(text=m.group(1),score=int(m.group(2))) for s in score.split('；') if (m:=re.fullmatch(r'(.+?)(\d+)',s))]
        assert sum(r['score'] for r in rubric)==(15 if kind=='比较' else 25 if kind=='论述' else 20)
        outlines=([us[0]['definition'],us[-1]['definition'],'交代共同问题，再写机制差异与边界'] if kind=='比较' else [u['term']+'：'+' → '.join(u['chain']) for u in us[:5]])
        expanded='\n\n'.join('【'+u['term']+'】'+u['definition']+' 论证：'+' → '.join(u['chain'])+'。核查边界：'+u['boundary'] for u in us)
        e=dict(id=ident,chapter=key,cat=chapters[key]['name'].split('与')[0],topic='跨理论比较' if kind=='比较' else '综合应用' if kind=='材料分析' else '论证整合',kp=ks,kind=kind,type='模拟题',title=title,priority='核心必会',difficulty='综合',minutes=12 if kind=='比较' else 20,outline=outlines,answer=answer,expanded=expanded,rubric=rubric,points=score,loss='；'.join(u['boundary'] for u in (us[:1]+us[-1:])),accepted=accepted,variation=variation,audit='比较需有共同问题和不同机制。' if kind=='比较' else '材料分析先摘事实，再用概念解释，最后列需要的证据。' if kind=='材料分析' else '论述须有前提、中介、结论与评价；“评价”不是只列优缺点。',structure='共同问题 → 各家前提与机制 → 差异 → 边界' if kind=='比较' else '材料事实 → 概念与机制 → 替代解释 → 证据及限定' if kind=='材料分析' else '提出问题 → 解释理论 → 论证联系 → 评价 → 有条件结论',ref=';'.join(dict.fromkeys(u['ref'] for u in us)))
        essays.append(e)
        for u in us:u['essayIds'].append(ident)
    extra={};eid=None
    for line in (ROOT/'work/question_bank/answer_expansions.txt').read_text().splitlines():
        if line.startswith('@'):eid=line[1:];extra[eid]=[]
        elif line:extra[eid].append(line)
    for e in essays:
        if e['id'] in extra:e['answer']+='\n\n'+'\n\n'.join(extra[e['id']])
        elif e['kind']=='比较':
            us=[um[k] for k in e['kp']]
            e['answer']+='\n\n应用比较时应明确同一个教学对象的不同提问：'+us[0]['case']+' 另一侧的分析边界为：'+us[-1]['boundary']+' 先分别还原概念，再比较前提、机制和结论，不以共同关键词推出立场相同。'
        elif e['kind']=='材料分析':
            us=[um[k] for k in e['kp']]
            e['answer']+='\n\n把材料与理论连接的论证线索可进一步展开为：'+ '；'.join(u['term']+'：'+' → '.join(u['chain']) for u in us[:2])+'。这些联系是提出调查问题的依据，不是题干已经证实的全部事实。评价应把可解释的环节与仍需现实证据的环节分开。'
    data['audits']=json.loads((ROOT/'work/question_bank/audits.json').read_text())
    old_mapping=json.loads((ROOT/'work/question_bank/legacy_coverage.json').read_text())
    for u in units:u['auditIds']=[n['id'] for n in data['audits'] if u['id'] in n['kp']]
    for u in units:u['oldQuizIds']=old_mapping.get(u['id'],[])
    data['knowledge']=units;data['quiz']=quizzes;data['essays']=essays
    for d in data['days']:
        active=[u for u in units if d['day'] in u['learnDays']]
        if d['chapter'] in chapters:
            active=active or [u for u in units if u['chapter']==d['chapter']]
        elif d['weekly']:
            active=[u for u in units if d['day']-6<=u['learnDays'][0]<=d['day']]
        elif d['day']>=39:
            groups={39:['luk','habermas'],40:['marcuse','fromm'],41:['hork','baudrillard'],42:['adorno','althusser'],43:['luk'],44:['hork','marcuse'],45:list(chapters)}
            active=[u for u in units if u['chapter'] in groups.get(d['day'],list(chapters))]
        d['knowledge']=[u['id'] for u in active]
        d['legacyEssay']=d['essay']
        if d['day']>=39:
            match={39:'W-luk-C',40:'W-marcuse-C',41:'W-baudrillard-C',42:'W-althusser-C',43:'W-luk-E',44:'W-marcuse-E',45:'W-habermas-E'}
            d['essay']=match[d['day']]
        elif d['weekly']:
            d['essay']='W-'+({7:'luk',14:'korsch',21:'adorno',28:'fromm',35:'habermas'}[d['day']])+'-C' if d['day']!=7 else 'W-G10'
        else:d['essay']=active[0]['essayIds'][0]
        d['practiceBudget']=15 if d['weekly'] else 8 if d['day'] in (43,44) else 10
        d['writtenMode']='限时成文＋逐点核对' if d['day'] in (43,44) else '独立提纲＋核对' if d['day']>14 else '先写自己的解释，再看示范'
    data['bankVersion']=2
    data['bankCounts']={'quiz':len(quizzes),'essays':len(essays),'units':len(units),'kinds':dict(Counter(x['kind'] for x in essays)),'chapterQuiz':dict(Counter(q['chapter'] for q in quizzes))}
    export(data)

def export(data):
    out=ROOT/'outputs'
    prior=sum(bool(u['oldQuizIds']) for u in data['knowledge'])
    h=['# 西马知识点与题库覆盖表','', '2026-10-08。84个教学知识单元：18基础＋66章内单元。每单元有4个实质不同的辨析任务；另有36道四选一的论证、应用和比较题。完整编号是学习映射，不是院校考纲。','', '原文1225段的范围均有对应；这表示段落已纳入审阅与专题映射，不把一段短课堂比喻当成一个独立考点。每个单元的多个概念还通过主观题、综合题和原文阅读联系。题目重点是教学判断，非出题频率。复习日期是可选的建议学习日；每日必做按时间和表现选取，并非要求刷完全部题。','', f'升级前：{prior}单元有直接相关的旧选择题（含只测术语的薄覆盖）；{84-prior}单元没有直接选择题。不能把原文范围重叠当作知识点已被测到。旧Q36只测学习方法，不列为哲学知识覆盖。升级后：84单元均有至少4道不同角度题及1道直接主观题，新增角度和深度并替换全部旧短解析。原笔记核查15条：明确措辞尚待核实N14；其余分别为订正、语境限定和学术争议，不将它们统称未核实。','', '|单元/概念|原文段号|重点/依据|讲解定位|旧选择题覆盖|新版选择题|主观题|首次学习/建议复习|','|---|---|---|---|---|---|---|---|']
    for u in data['knowledge']:
        h.append('|'+ '|'.join([u['id']+' '+u['term'],u['ref'],u['priority']+'：'+u['reason'],'单元微课；章节 '+u['chapter']+' 第'+str(u['lessonSection']+1)+'节背景','、'.join(u['oldQuizIds']) or '新增直接考查', '、'.join(u['quizIds']),'、'.join(u['essayIds']),str(u['learnDays'])+' / '+str(u['reviewDays'])])+'|')
    h+=['','## 旧题处置','旧36道选择题和33道主观题保留在生成数据的 legacyQuiz/legacyEssays 中供旧进度显示；主题库改用新版题，避免短解析混入新验收。原每日答案和反思字段继续保存，题面变化后新版大题独立存储。','', '## 原笔记核查清单：区分订正、语境限定与待核']
    for n in data['audits']:
        h+=['','### '+n['id']+' '+n['status']+' · '+n['ref'],'- 原笔记说法／概括：'+n['original'],'- 核查与补充：'+n['note'],'- 对应单元：'+','.join(n['kp'])+'；来源：'+','.join(n['refs'])]
    (out/'西马知识点与题库覆盖表.md').write_text('\n'.join(h),encoding='utf-8')
    (out/'西马专题题库数据.json').write_text(json.dumps({k:data[k] for k in ('bankVersion','bankCounts','knowledge','quiz','essays','audits','refs','real','methods')},ensure_ascii=False,indent=2),encoding='utf-8')
    source_notes=['# 西马题库来源与核查说明','','日期：2026-10-08。主材料为用户笔记，题干和答案为教学重构，均为模拟题。单元微课不是原笔记原文，查看原文按钮展示保留的P段落。核查资料用于校正概念边界与争议；不是对具体现实案例的经验认证。案例全部写为教学假设。','']
    source_notes+=['- '+r.get('id','')+' '+r['label']+'：'+r['url'] for r in data['refs']]
    source_notes+=['','学习研究：']+['- '+r['name']+'：'+r['how']+' '+r['url'] for r in data['methods']]
    source_notes+=['','真题：本轮学校PDF已核验，上海外国语大学2016年思想政治教育专业《马克思主义原理》，第1页名词解释第1题“哲学基本问题”，12分。它是相关基础题，不是西马专题，不据此推断任何院校考点。参考答案和分步评分均为自拟。原PDF链接：'+data['real'][0]['url'],'','边界：三张图的原图及图注保留；G3字母不作无依据补写。原文夸张、含混与错误不悄悄替换，单元核查栏单独提示。题库的哲学学习效果与考研提分尚未通过真实学生试验验证。']
    (out/'西马题库来源与核查说明.md').write_text('\n'.join(source_notes),encoding='utf-8')
    plan=['# 西马题库版45天逐日计划','','以网页“今天学习”为执行入口。每次按学习日推进，不要求追赶日历。九章原文在首轮连续阅读中完整覆盖；基础课和后期复习可重复。必做约96次选择作答＋45次书面训练（多数为提纲，43/44日限时成文），不要求刷完483道模拟题。其他专题题属选做。','', '用时顺序：回忆／原文／讲解／选择与订正／书面训练／反思，单位为分钟。每周低于75%时将5分钟阅读转入回忆，总时长保持60。90%以上可在同一预算内选综合变式。预算是教学估计，尚未由零基础学生计时验证；超时先停止选做，将一个未清问题记入反思。','', '|学习日|任务与原文|讲解单元|必做小题／自测|书面训练|用时分配|','|---|---|---|---|---|---|']
    for d in data['days']:
        long=len(''.join(data['source'][i-1]['text'] for i in rng(d['source'])))>1500
        times=[8,6,12,8,22,4] if d['day'] in (43,44) else [10,10,10,15,12,3] if d['weekly'] else [8,14,18,10,8,2] if long else [8,10,22,10,8,2]
        names='、'.join(d['knowledge'][:6])+('等；本日只精读书面题相关单元' if len(d['knowledge'])>6 else '')
        plan.append('|'+ '|'.join([str(d['day']),d['focus']+'；'+d['source'],names,('3' if d['weekly'] else '2')+'题：当天内容＋到期错题变式；'+('周检分别核对概念、论证、信心' if d['weekly'] else '闭书说出判断条件'),d['essay']+' '+d['writtenMode'],'／'.join(map(str,times))+'＝60'])+'|')
    plan+=['','## 每周如何调整','第7、14、21、28、35、42日：独立作答后分别看选择题正确性、书面题教学自评和作答前信心。把综合表现填入日课反思。低于75%增加回忆并优先薄弱单元；75—89%保持；90%以上可在原预算内减少提示、选择综合变式。阈值是课程用的实用规则，不是经过本课程样本校准的心理学常数。','', '## 到期再练','错概念进入次学习日队列；之后延迟答对再间隔3日、7日。当天重复不推进阶段。题目优先改用同单元其他问法，大题低于75%另排次日。每日最多先用一个到期单元替换当天小题，其余按预算后移，不挤掉阅读与反思。45日后仍可在错题页自主再练。']
    (out/'西马题库版45天逐日计划.md').write_text('\n'.join(plan),encoding='utf-8')
