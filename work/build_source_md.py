from pathlib import Path
from zipfile import ZipFile
from lxml import etree
from shutil import copyfile
project=Path(__file__).resolve().parents[1]
src=project/'01黄羽学姐西马复习笔记.docx'
out=project/'outputs'; out.mkdir(exist_ok=True)
chap={1:'卢卡奇',156:'科尔施',257:'法兰克福学派与霍克海默',395:'阿多诺',502:'马尔库塞',610:'弗洛姆',749:'哈贝马斯',896:'鲍德里亚',1096:'阿尔都塞'}
img_text={1:'图 1：印刷字为“思想和理想”“社会性格”“经济基础”，相邻层次间画有上下两个方向的箭头。它表示社会性格与经济基础、思想理想之间的双向联系；图本身没有解释因果强弱。',2:'图 2：背景标题“生活世界”；上方可辨“文化背景”，中间 A1、A2 和交往／语言一类手写标记，左右写“内在世界”，下方“自然世界”，右侧另有“客观世界”的手写标注。部分笔迹无法可靠辨认，不能把这张草图当作哈贝马斯理论的标准图式。',3:'图 3：时间轴上标 A、B、C、D，D 处被圈出并有红字“我们研究的认识对象”（末字及完整语境可能不清）；绿色字可辨“研究不同的结构，及其关系”。曲线从早期位置延伸至 D，可能提示历时结构关系；此解释属于整理者推测，原图未有完整图注。'}
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with ZipFile(src) as z:
 root=etree.fromstring(z.read('word/document.xml'))
 relroot=etree.fromstring(z.read('word/_rels/document.xml.rels'))
 rel={e.get('Id'):e.get('Target','') for e in relroot}
 lines=['# 《01黄羽学姐西马复习笔记》完整整理版','',f'> 来源：`{src.name}`。正文按原 DOCX 段落顺序逐段转录；非空文字段落编号 P0001—P1225。**文字未校订、未改错、未统一术语**，包括原有口语、别字和不完整句。章标题是整理者加的导航，不算原文。三张图片放回原来位置，用 G1—G3 定位。原文件没有表格。','', '> 阅读标签：**【原笔记】**下方编号段落均为原有文字；**【整理者图注】**仅帮助读图；**【待核实】**不等于原文有结论。网页内会另行标出核实后的讲解。','', '## 原笔记原文','']
 pnum=0; inum=0
 for p in root.findall('.//w:body/w:p',ns):
  s=''.join(p.xpath('.//w:t/text()',namespaces=ns)).strip()
  if s:
   pnum+=1
   if pnum in chap: lines += [f'## {chap[pnum]}｜P{pnum:04d} 起（原文件章标题；后缀为整理者导航）','']
   if pnum in (158,219): lines += [f'### 原文件小标题｜P{pnum:04d} 起','']
   lines += [f'<a id="P{pnum:04d}"></a>','**【原笔记】P%04d**  %s'%(pnum,s),'']
  for img in p.xpath('.//a:blip',namespaces=ns):
   inum+=1
   rid=img.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
   name=Path(rel[rid]).name
   b=z.read('word/media/'+name)
   suffix=Path(name).suffix.lower()
   op=out/f'西马原图{inum}{suffix}';op.write_bytes(b)
   lines += [f'<a id="G{inum}"></a>',f'**【原笔记图片 G{inum}；位于 P{pnum:04d} 之后】**','',f'![原笔记图 {inum}](西马原图{inum}{suffix})','',f'**【整理者图注】** {img_text[inum]}','']
 lines += ['## 原文核对说明','',f'- 正文非空文字段落：{pnum}；图片：{inum}。编号连续，图片不占 P 编号。','- 源文可能含输入错误、用词含混或课堂简写，整理版维持原貌；解释、订正和争议另见学习网页对应单元。','- 图 2、图 3 手写较难辨的词没有补写成确定原文。','- DOCX 中 220 个空白段落用于排版，未逐个生成空段；不含可辨识文字。','']
 (out/'西马原笔记完整整理.md').write_text('\n'.join(lines),encoding='utf-8')
 print('paragraphs',pnum,'images',inum,'size',len('\n'.join(lines)))
