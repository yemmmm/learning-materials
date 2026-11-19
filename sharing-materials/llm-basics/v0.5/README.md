# v0.5 制作说明

P01–P43 为主讲和回顾，P44–P45 为参考资料与演示说明。 [大纲](../outline-v0.5.md) · [离线演示](../exports/llm-basics-slides-v0.5.html)

## 文件

- `content.py`：逐页可见内容、讲稿和引用。
- `deck.css`：纸色、深绿配色，1920×1080 固定画布版式与打印样式。
- `deck.js`：翻页、目录、讲稿、文字编辑与五个离线交互。
- `build.py`：生成独立 HTML、Markdown 讲稿和页清单；字体及图片均内嵌。
- `export.cjs`：使用 Playwright / Chromium 导出 PDF。
- `slide-manifest.json`：页码、标题、章节与引用键。
- `sources.md`：来源和教学示例说明。
- `../v0.2/assets/manifest.json` 记录本版沿用的两张插图与文件清单的来源。

字体打包复用 `../deck/build.py` 的 `make_fonts`，基础画布复用 `../deck/vendor/frontend-slides/viewport-base.css`，许可见 `../deck/THIRD-PARTY-NOTICES.txt`。

## 重建 HTML 与讲稿

在 `/home/yangxiang/sharing-materials/` 执行：

```bash
env PYTHONDONTWRITEBYTECODE=1 uv run --python 3.14 \
  --with fonttools==4.68.0 --with tiktoken==0.14.0 --with regex==2026.11.15 \
  python llm-basics/v0.5/build.py
```

需要本机 `/usr/share/fonts/opentype/noto/` 中的 Noto CJK 字体。依赖和 tiktoken 编码已有缓存时，可给 `uv run` 加上 `--offline`。生成的文件可独立离线使用。

## 导出 PDF

需要可用的 Playwright Node 包和 Chromium。可使用已经安装的环境：

```bash
NODE_PATH=/home/yangxiang/.nvm/versions/node/v22.22.1/lib/node_modules/@playwright/cli/node_modules \
CHROMIUM_PATH=/home/yangxiang/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell \
node llm-basics/v0.5/export.cjs
```

若系统已能直接加载 `playwright` 且安装了对应 Chromium，可直接运行 `node llm-basics/v0.5/export.cjs`。

导出按 CSS 页面尺寸每页一张，包含背景。修改源码后先重建 HTML，再导出 PDF。PDF 展开三类分词样例、逐步生成、工具往返和 ReAct 的关键步骤与分支，聊天模板展示第二轮。交互演示使用 HTML。
