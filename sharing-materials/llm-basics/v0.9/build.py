"""Build v0.9 as standalone HTML with embedded fonts, assets and speaker notes."""
from pathlib import Path
import base64
import html
import importlib.util
import json
import re

from content import SLIDES, SOURCES

HERE=Path(__file__).resolve().parent
EXPORTS=HERE.parent/'exports'
ASSETS=HERE.parent/'v0.2/assets'
VERSION='v0.9'
spec=importlib.util.spec_from_file_location('legacy_font_build',HERE.parent/'deck/build.py')
legacy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)

# Verified against the Qwen3-8B tokenizer at the revision listed in sources.md.
VOCAB_EXCERPT = {'Hello': 9707, ',': 11, 'Ġworld': 1879, '!': 0}
TOKEN_SAMPLES = [
    ('Hello, world!', [(key.replace('Ġ', ' '), value) for key, value in VOCAB_EXCERPT.items()]),
    ('今天开会。', [('今天', 100644), ('开会', 113716), ('。', 1773)]),
    ('print("Hello")', [('print', 1350), ('("', 445), ('Hello', 9707), ('")', 899)]),
]

def data_asset(match):
    name=match[1]
    local=HERE/'assets'/name
    path=local if local.is_file() else ASSETS/name
    mime={'.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp'}[path.suffix]
    return f'src="data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"'

def token_chips(example):
    return ''.join(
        f'<span class="token">{html.escape(t["piece"].replace(" ", "␠"))}'
        f'<small>ID {t["id"]}</small></span>'
        for t in example['tokens']
    )

def main():
    tokens = [
        dict(text=text, tokens=[dict(piece=piece, id=token_id) for piece, token_id in entries])
        for text, entries in TOKEN_SAMPLES
    ]
    vocab_excerpt = html.escape(json.dumps(VOCAB_EXCERPT, ensure_ascii=False, indent=2))
    token_print=''.join(
        f'<div class="token-print-row"><div><b>{html.escape(example["text"])}</b>'
        f'<p class="small">{len(example["tokens"])} 个 Token</p></div>'
        f'<div class="token-list">{token_chips(example)}</div></div>'
        for example in tokens
    )
    notes=[]
    sections=[]
    main_count=sum(not slide['chapter'].startswith('附录') for slide in SLIDES)
    for n,s in enumerate(SLIDES,1):
        body=(s['body'].replace('__TOKENS__',token_chips(tokens[0]))
              .replace('__TOKEN_COUNT__',str(len(tokens[0]['tokens'])))
              .replace('__TOKEN_PRINT__',token_print)
              .replace('__VOCAB__',vocab_excerpt))
        body=re.sub(r'data-asset="([^"]+)"',data_asset,body)
        sources=[dict(title=SOURCES[k][0],url=SOURCES[k][1]) for k in s['sources']]
        notes.append(dict(title=s['title'],text=s['notes'],sources=sources))
        lead=f'<p class="lead">{s["lead"]}</p>' if s['lead'] else ''
        takeaway=f'<div class="takeaway">{s["takeaway"]}</div>' if s['takeaway'] else ''
        sections.append(f'''<section class="slide {s['cls']} {'active visible' if n==1 else ''}" data-page="{n}" aria-label="第 {n} 页：{html.escape(s['title'])}">
<div class="mast"><span>LLM / 大模型常见概念</span><span>{html.escape(s['chapter'])}</span></div>
<header><h1>{s['title']}</h1>{lead}</header>
<div class="slide-body">{body}</div>{takeaway}
<footer><b>{n:02} / {len(SLIDES)}</b></footer></section>''')
    controls='''<nav class="deck-controls" aria-label="演示控制"><button id="prev" title="上一页">←</button><span id="counter"></span><button id="next" title="下一页">→</button><button id="contents">目录 G</button><button id="notes">讲稿 N</button><button id="fullscreen">全屏 F</button></nav>
<div class="progress" id="progress"></div><div class="edit-hotzone" id="editHotzone"></div><button class="edit-toggle" id="editToggle" aria-pressed="false" title="编辑（E）；Ctrl+S 下载">编辑 E</button><div id="save-status" role="status"></div>
<dialog id="contentsDialog"><div class="dialog-head"><h2>大模型常见概念 · 目录</h2><button data-close="contentsDialog" aria-label="关闭目录">×</button></div><div class="contents-list">'''
    previous_chapter = None
    for i, slide in enumerate(SLIDES, 1):
        if slide['chapter'] != previous_chapter:
            previous_chapter = slide['chapter']
            controls += f'<h3 class="contents-section">{html.escape(previous_chapter)}</h3>'
        controls += f'<button data-go="{i}">{i:02} · {html.escape(slide["title"])}</button>'
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
    speech=f'''# 大模型常见概念

{VERSION} · 2026-11-19。对应 {len(SLIDES)} 页演示。

P01–P{main_count:02} 为主讲与回顾，P{main_count+1:02}–P{len(SLIDES):02} 为参考资料与演示说明。建议约 65 分钟，另留交流时间。

| 页码 | 内容 | 预计用时 |
| --- | --- | --- |
| P01–P05 | 开场、NLP、语言模型、使用方式与仓库 | 9 分钟 |
| P06–P13 | 分词、生成、加载、规格与推理服务 | 15 分钟 |
| P14–P17 | 训练、对话、提示词和上下文 | 11 分钟 |
| P18–P21 | 召回、重排序、Embedding 和单次工具调用 | 10 分钟 |
| P22–P28 | ReAct、Harness、构建排查与任务方法 | 12 分钟 |
| P29–P31 | 其他模型、推理指标、概念回顾与可选补讲 | 7 分钟 |

'''
    for i,s in enumerate(SLIDES,1):
        speech+=f'## P{i:02} {s["title"]}\n\n{s["notes"]}\n\n'
        if s['sources']:
            speech+='来源（不朗读）：\n\n'+'\n'.join(f'- [{SOURCES[k][0]}]({SOURCES[k][1]})' for k in s['sources'])+'\n\n'
    (EXPORTS/f'llm-basics-speech-{VERSION}.md').write_text(speech.rstrip()+'\n')
    manifest=[dict(page=i,title=s['title'],chapter=s['chapter'],sources=s['sources']) for i,s in enumerate(SLIDES,1)]
    (HERE/'slide-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Built {len(SLIDES)} slides: {out}')
    print(f'HTML {out.stat().st_size:,} bytes; speech {len(speech):,} characters')

if __name__=='__main__': main()
