"""Build v0.2 as standalone HTML with embedded fonts, assets and speaker notes."""
from pathlib import Path
import base64
import html
import importlib.util
import json
import re

import tiktoken
from content import SLIDES, SOURCES

HERE=Path(__file__).resolve().parent
EXPORTS=HERE.parent/'exports'
VERSION='v0.2'
spec=importlib.util.spec_from_file_location('legacy_font_build',HERE.parent/'deck/build.py')
legacy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

def data_asset(match):
    name=match[1]
    path=HERE/'assets'/name
    mime={'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}[path.suffix]
    return f'src="data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"'

def main():
    encoding=tiktoken.get_encoding('cl100k_base')
    tokens=[dict(text=t,tokens=[dict(id=i,piece=encoding.decode_single_token_bytes(i).decode('utf-8')) for i in encoding.encode(t)]) for t in ['今天开会。','Hello, world!','print("Hello")']]
    initial=''.join(f'<span class="token">{html.escape(t["piece"])}<small>ID {t["id"]}</small></span>' for t in tokens[0]['tokens'])
    notes=[]
    sections=[]
    for n,s in enumerate(SLIDES,1):
        body=s['body'].replace('__TOKENS__',initial).replace('__TOKEN_COUNT__',str(len(tokens[0]['tokens'])))
        body=re.sub(r'data-asset="([^"]+)"',data_asset,body)
        sources=[dict(title=SOURCES[k][0],url=SOURCES[k][1]) for k in s['sources']]
        notes.append(dict(title=s['title'],text=s['notes'],sources=sources))
        source_text=' · '.join(html.escape(SOURCES[k][0]) for k in s['sources'][:2])
        footer=html.escape(s['foot']) or source_text or '差旅助手 · 教学示例'
        sections.append(f'''<section class="slide {s['cls']} {'active visible' if n==1 else ''}" data-page="{n}" aria-label="第 {n} 页：{html.escape(s['title'])}">
<div class="mast"><span>LLM / 大模型常见概念</span><span>{html.escape(s['chapter'])}</span></div>
<header><h1>{s['title']}</h1><p class="lead">{s['lead']}</p></header>
<div class="slide-body">{body}</div><div class="takeaway">{s['takeaway']}</div>
<footer><span>{footer}</span><b>{n:02} / {len(SLIDES)}</b></footer></section>''')
    controls='''<nav class="deck-controls" aria-label="演示控制"><button id="prev" title="上一页">←</button><span id="counter"></span><button id="next" title="下一页">→</button><button id="contents">目录 G</button><button id="notes">讲稿 N</button><button id="fullscreen">全屏 F</button></nav>
<div class="progress" id="progress"></div><div class="edit-hotzone" id="editHotzone"></div><button class="edit-toggle" id="editToggle" aria-pressed="false" title="编辑（E）；Ctrl+S 下载">编辑 E</button><div id="save-status" role="status"></div>
<dialog id="contentsDialog"><div class="dialog-head"><h2>大模型常见概念 · 目录</h2><button data-close="contentsDialog" aria-label="关闭目录">×</button></div><div class="contents-list">'''
    controls+=''.join(f'<button data-go="{i}">{i:02} · {html.escape(s["title"])}</button>' for i,s in enumerate(SLIDES,1))
    controls+='''</div></dialog><dialog id="notesDialog"><div class="dialog-head"><h2 id="noteTitle"></h2><button data-close="notesDialog" aria-label="关闭讲稿">×</button></div><div class="dialog-body" id="noteText"></div><div class="dialog-links" id="noteSources"></div></dialog>'''
    js=(HERE/'deck.js').read_text()
    markup='\n'.join(sections)
    fonttext=re.sub('<[^>]+>','',html.unescape(markup+controls))+json.dumps(notes,ensure_ascii=False)+json.dumps(tokens,ensure_ascii=False)+js
    css=legacy.make_fonts(fonttext)+'\n'+(HERE.parent/'deck/vendor/frontend-slides/viewport-base.css').read_text()+'\n'+(HERE/'deck.css').read_text()
    notice=(HERE.parent/'deck/THIRD-PARTY-NOTICES.txt').read_text()
    jsjson=lambda value:json.dumps(value,ensure_ascii=False).replace('</','<\\/')
    doc=f'''<!doctype html>
<!-- {notice} -->
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>大模型常见概念 · {VERSION}</title><style>{css}</style></head>
<body><main class="deck-viewport"><div class="deck-stage" id="deckStage">{markup}</div></main>{controls}
<script type="application/json" id="notesData">{jsjson(notes)}</script><script type="application/json" id="tokenData">{jsjson(tokens)}</script><script>{js}</script></body></html>'''
    EXPORTS.mkdir(exist_ok=True)
    out=EXPORTS/f'llm-basics-slides-{VERSION}.html'
    out.write_text(doc)
    speech=f'''# 大模型常见概念：一个模型如何成为 AI 助手

版本：{VERSION}。日期：2026-11-18。对应 {len(SLIDES)} 页演示。

P01–P44 为主讲与交流；P45 为按需展开的成本与评测；P46–P47 为参考资料。建议约 60–70 分钟，模型规格与训练名词可快速带过，另留交流时间。具体时间按排练调整。

制度、汇率、金额与工具响应均为教学示例；不连接模型或业务 API。分词是 tiktoken / cl100k_base 的实际结果；其他交互是预写演示。文件清单摘录自官方仓库，已标注非网页截图。插图由 AI 生成。

'''
    for i,s in enumerate(SLIDES,1):
        speech+=f'## P{i:02} {s["title"]}\n\n{s["notes"]}\n\n'
        if s['sources']:
            speech+='来源（不朗读）：\n\n'+'\n'.join(f'- [{SOURCES[k][0]}]({SOURCES[k][1]})' for k in s['sources'])+'\n\n'
    (EXPORTS/f'llm-basics-speech-{VERSION}.md').write_text(speech)
    manifest=[dict(page=i,title=s['title'],chapter=s['chapter'],sources=s['sources']) for i,s in enumerate(SLIDES,1)]
    (HERE/'slide-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(SLIDES)} slides: {out}')
    print(f'HTML {out.stat().st_size:,} bytes; speech {len(speech):,} characters')

if __name__=='__main__': main()
