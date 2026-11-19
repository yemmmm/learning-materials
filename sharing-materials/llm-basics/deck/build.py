"""Build the offline HTML and matching speech. Run with uv and fonttools/tiktoken."""
from pathlib import Path
import base64
import html
import io
import json
import re

from fontTools import subset
from fontTools.ttLib import TTFont
import tiktoken

from content import SLIDES, SOURCES

HERE = Path(__file__).resolve().parent
EXPORTS = HERE.parent / "exports"
VERSION = "v0.1"


def make_fonts(text):
    rules = []
    for source, family, weight in [
        ("NotoSansCJK-Regular.ttc", "Deck Sans", 400),
        ("NotoSansCJK-Bold.ttc", "Deck Sans", 700),
        ("NotoSerifCJK-Bold.ttc", "Deck Serif", 700),
    ]:
        font = TTFont("/usr/share/fonts/opentype/noto/" + source, fontNumber=2)
        options = subset.Options()
        options.flavor = "woff"
        sub = subset.Subsetter(options=options)
        sub.populate(text=text + "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz␠←→×")
        sub.subset(font)
        font.flavor = "woff"
        buffer = io.BytesIO()
        font.save(buffer)
        encoded = base64.b64encode(buffer.getvalue()).decode()
        rules.append(f"@font-face{{font-family:'{family}';font-weight:{weight};font-display:swap;src:url(data:font/woff;base64,{encoded}) format('woff')}}")
        font.close()
    return "\n".join(rules)


def main():
    EXPORTS.mkdir(exist_ok=True)
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = [dict(text=text, tokens=[dict(id=token_id, piece=encoding.decode_single_token_bytes(token_id).decode("utf-8")) for token_id in encoding.encode(text)]) for text in ["今天开会。", "Hello, world!", 'print("Hello")']]
    initial_tokens = "".join(f'<span class="token">{html.escape(t["piece"])}<small>ID {t["id"]}</small></span>' for t in tokens[0]["tokens"])
    notes, sections = [], []
    for number, slide in enumerate(SLIDES, 1):
        esc = html.escape
        body = slide["body"].replace("__TOKENS__", initial_tokens)
        sections.append(f'''<!-- === P{number:02}: {esc(slide['title'])} === -->
<section class="slide {slide['cls']} {'active visible' if number == 1 else ''}" data-page="{number}" aria-label="第 {number} 页：{esc(slide['title'])}">
<div class="mast"><span>LLM / 大模型基础</span><span>{esc(slide['chapter'])}</span></div>
<header><h1>{slide['title']}</h1><p class="lead">{slide['lead']}</p></header>
<div class="slide-body">{body}</div><div class="takeaway">{slide['takeaway']}</div>
<footer><span>{slide['foot']}</span><b>{number:02} / {len(SLIDES)}</b></footer></section>''')
        notes.append(dict(title=slide["title"], text=slide["notes"], sources=[dict(title=SOURCES[key][0], url=SOURCES[key][1]) for key in slide["sources"]]))
    controls = '''<!-- === CONTROLS AND SPEAKER NOTES === -->
<nav class="deck-controls" aria-label="演示控制"><button id="prev" title="上一页（←）">←</button><span id="counter"></span><button id="next" title="下一页（→ 或空格）">→</button><button id="contents">目录 G</button><button id="notes">讲稿 N</button><button id="fullscreen">全屏 F</button></nav>
<div class="progress" id="progress"></div><div class="edit-hotzone" id="editHotzone"></div><button class="edit-toggle" id="editToggle" aria-pressed="false" title="编辑（E）；Ctrl+S 下载">编辑 E</button><div id="save-status" role="status"></div>
<dialog id="contentsDialog"><div class="dialog-head"><h2>大模型常见概念 · 目录</h2><button data-close="contentsDialog" aria-label="关闭目录">×</button></div><div class="contents-list">'''
    controls += "".join(f'<button data-go="{i}">{i:02} · {html.escape(s["title"])}</button>' for i, s in enumerate(SLIDES, 1))
    controls += '''</div></dialog><dialog id="notesDialog"><div class="dialog-head"><h2 id="noteTitle"></h2><button data-close="notesDialog" aria-label="关闭讲稿">×</button></div><div class="dialog-body" id="noteText"></div><div class="dialog-links" id="noteSources"></div></dialog>'''
    markup = "\n".join(sections)
    css = (HERE / "vendor/frontend-slides/viewport-base.css").read_text() + "\n" + (HERE / "deck.css").read_text()
    js = (HERE / "deck.js").read_text()
    fontcss = make_fonts(re.sub(r"<[^>]+>", "", html.unescape(markup + controls)) + json.dumps(notes, ensure_ascii=False) + js + json.dumps(tokens, ensure_ascii=False))
    notice = (HERE / "THIRD-PARTY-NOTICES.txt").read_text()
    json_script = lambda value: json.dumps(value, ensure_ascii=False).replace("</", "<\\/")
    document = f'''<!doctype html>
<!-- {notice} -->
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>大模型常见概念 · {VERSION}</title><style>{fontcss}\n{css}</style></head>
<body><main class="deck-viewport"><div class="deck-stage" id="deckStage">{markup}</div></main>{controls}
<script type="application/json" id="notesData">{json_script(notes)}</script><script type="application/json" id="tokenData">{json_script(tokens)}</script><script>{js}</script></body></html>'''
    html_file = EXPORTS / f"llm-basics-slides-{VERSION}.html"
    html_file.write_text(document)
    speech = f"""# 大模型常见概念：从日常使用到 AI 应用开发\n\n初稿 {VERSION} · 编制日期：2026-11-17。\n\n对应 {len(SLIDES)} 页演示，P01–P26 为主讲与交流，P27–P28 为选讲词汇，P29 为来源。按原大纲安排 60 分钟分享，另留 10 分钟交流；时长包含三个演示、停顿与现场提问，正式使用前建议按语速排练。\n\n【演示】为讲者操作提示，不需要朗读。除指定分词器的真实分词外，公司文档、回答对照、状态与工单均为教学设定。演示不连接模型 API 或业务系统。\n\n## 时间分配\n\n认识大模型 6 分钟；一次对话 8 分钟；任务表达 8 分钟；能力边界 7 分钟；公司知识 10 分钟；工具与 Agent 10 分钟；调用成本 6 分钟；评测选择 5 分钟。开场、回顾和三个短演示计入这些时段。\n\n"""
    speech += "\n".join(f'## P{i:02} {n["title"]}\n\n{n["text"]}\n' for i, n in enumerate(notes, 1))
    speech += "\n## 参考资料（不朗读）\n\n"
    for i, note in enumerate(notes, 1):
        if note["sources"]:
            speech += f'### P{i:02} {note["title"]}\n\n' + "\n".join(f'- [{source["title"]}]({source["url"]})' for source in note["sources"]) + "\n\n"
    (EXPORTS / f"llm-basics-speech-{VERSION}.md").write_text(speech.rstrip() + "\n")
    print(f"Built {len(SLIDES)} slides: {html_file}")
    print(f"Matching speech: {len(speech):,} characters; tokens: {[len(t['tokens']) for t in tokens]}")


if __name__ == "__main__":
    main()
