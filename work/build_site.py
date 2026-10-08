"""在仓库根目录重新生成单文件学习网页。"""

from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, 'work/build_course.py'], cwd=root, check=True)
template = (root / 'work/app_template.html').read_text(encoding='utf-8')
data = (root / 'work/course_data.json').read_text(encoding='utf-8').replace('<', '\\u003c')
addon = (root / 'work/question_bank_app.js').read_text(encoding='utf-8')
css = (root / 'work/question_bank_style.css').read_text(encoding='utf-8')
template = template.replace('</style>', css + '\n</style>').replace('\nrender();\n', '\n' + addon + '\nrender();\n')
assert template.count('__DATA__') == 1
output = root / 'outputs/西马45天整合学习网页.html'
output.write_text(template.replace('__DATA__', data), encoding='utf-8')
print(f'已生成 {output}')
