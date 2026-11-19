# v0.2 制作说明

对应 [本版大纲](../outline-v0.2.md) 和 [离线演示](../exports/llm-basics-slides-v0.2.html)。保留 v0.1 源码和导出。

## 文件

- `content.py`：逐页可见内容、讲稿和引用。
- `deck.css`：纸色、深绿配色，1920×1080 固定画布版式与打印样式。
- `deck.js`：翻页、目录、讲稿、文字编辑与五个离线交互。
- `build.py`：生成独立 HTML、Markdown 讲稿和页清单；字体及图片均内嵌。
- `export.cjs`：使用 Playwright / Chromium 导出 PDF。
- `slide-manifest.json`：页码、标题、章节与引用键。
- `sources.md`：来源和教学示例说明。
- `assets/manifest.json`：概念插图、文件清单的来源与含义边界。

字体打包复用 `../deck/build.py` 的 `make_fonts`，基础画布复用 `../deck/vendor/frontend-slides/viewport-base.css`，许可见 `../deck/THIRD-PARTY-NOTICES.txt`。v0.1 构建脚本保持原有版本目标，执行它会重新生成 v0.1，不用于重建 v0.2。

## 重建 HTML 与讲稿

在 `/home/yangxiang/sharing-materials/` 执行：

```bash
uv run --with fonttools --with tiktoken python llm-basics/v0.2/build.py
```

需要本机 `/usr/share/fonts/opentype/noto/` 中的 Noto CJK 字体。tiktoken 第一次获取编码可能联网，已有缓存后可离线构建；生成的文件无需联网使用。

## 导出 PDF

需要可用的 Playwright Node 包和 Chromium。可使用已经安装的环境：

```bash
NODE_PATH=/home/yangxiang/.nvm/versions/node/v22.22.1/lib/node_modules/@playwright/cli/node_modules \
CHROMIUM_PATH=/home/yangxiang/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell \
node llm-basics/v0.2/export.cjs
```

若系统已能直接加载 `playwright` 且安装了对应 Chromium，可直接运行 `node llm-basics/v0.2/export.cjs`。路径随本机环境变化，以实际安装为准。

导出包含背景、无页眉页脚，按 CSS 页面尺寸每页一张。修改源码后先重建 HTML，再导出 PDF。PDF 展示各交互的默认状态；完整演示使用 HTML。
