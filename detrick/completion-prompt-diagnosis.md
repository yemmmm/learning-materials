# Completion提示词消失：诊断与最小复现

日期：2026-09-08。状态：本地复现直接丢失机制；远程构建匹配、数组来源和修复验收尚未完成。WebApp access-mode 401为独立问题。

## 现场证据

- Completion节点data.model.mode=completion，旧节点prompt_template为system/user列表，GET仍返回旧文本，编辑器为空。
- 草稿与当前发布版均有2条、总414字符；这是历史文本仍在的证据，不是新文本保存成功。
- Chat模型对照可以保留提示词。Completion不发布也丢失，POST workflows/draft的prompt_template=[]。
- 默认模板响应中的completion_model.prompt是含text、edition_type的对象。其请求状态码未明确回传，不能推断前端store已正确接收模板。
- socket.io返回101；不能等同协同保存验收。

## 源码与本地验证

参考提交60a18fa（不是远程前端构建一致性证明）：

- [Completion编辑回调](https://github.com/langgenius/dify/blob/60a18fa/web/app/components/workflow/nodes/llm/components/config-prompt.tsx)：handleCompletionPromptChange在produce(payload as PromptItem)中给draft.text或draft.jinja2_text赋值。TypeScript类型断言不转换数组。
- [模型切换](https://github.com/langgenius/dify/blob/60a18fa/web/app/components/workflow/nodes/llm/use-config.ts)：模式变化且defaultConfig就绪时替换模板。
- [初始化](https://github.com/langgenius/dify/blob/60a18fa/web/app/components/workflow/nodes/llm/hooks/use-llm-input-manager.ts)：inputs.prompt_template为真时跳过初始化，空数组也为真。
- 参考提交pnpm-workspace.yaml指定Immer 11.1.15。下载其npm包至本机/tmp/dify-completion-repro，运行production实现；未改动部署和项目依赖。

复现逻辑（仅使用合成文本）：

```js
const { produce } = require('/tmp/dify-completion-repro/package/dist/cjs/immer.cjs.production.js')
const result = produce([], draft => { draft.text = 'DIAG_NEW' })
console.log(result.text)          // DIAG_NEW
console.log(JSON.stringify(result)) // []
```

对照断言已通过：

| 初始数据 | 编辑后内存.text | 请求JSON |
|---|---|---|
| [] | DIAG_NEW | [] |
| [{role:system,text:OLD}] | DIAG_NEW | 仅保留原列表中的OLD |
| {text:'',edition_type:basic} | DIAG_NEW | 对象包含DIAG_NEW |

结论：若Completion编辑器收到数组，参考production代码会将新文本写在数组自定义属性上；JSON序列化只保留数组条目，故新文本未进入请求。该机制与现场全部上述特征相符。尚未证明线上为何生成/保留数组，也未证明远程依赖版本相同。

## 最小下一步和修复边界

在已经用于测试的临时应用节点中，等待默认模板响应完成，再从Completion切到Chat，再切回真实的Completion模型。模式切换可能重置提示词，只在临时节点测试。

1. 切回后重新输入DIAG_COMPLETION_20260908。
2. 检查POST草稿prompt_template是否成为含text的对象，而非数组。
3. 保存后重进；若保留，再发布并重进验证。

如果转换为对象且保存正常，证明通过模型切换可绕过当前结构错误，但数组最初来源仍待定位。如果仍为数组，不继续反复切换，应核对远程web镜像、默认模板进入store的路径及实际模型切换实现。

长期修复需确保模型mode与prompt_template的运行时结构一致；空数组可以按Completion默认对象初始化；已有非空角色列表不能静默丢弃或随意拼接，需要明确转换规则并保留旧内容。不要只做TypeScript断言，也不要把真实Completion模型标为Chat。至少覆盖空数组、非空历史列表、正确对象、默认配置延迟加载和模型切换的回归测试。

验收尚未完成。数据库补写不能代替前端修复，权限回填不适用于该文本丢失机制。
