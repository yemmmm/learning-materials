# Completion提示词消失：诊断与最小复现

日期：2026-09-08。状态：线上静态包已确认同类错误转换，定位到前端协同初始化；待修复及线上验收。扫描只核对关键代码，不代表整份参考源码与线上完全相同。WebApp access-mode 401为独立问题。

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

## 后续：刷新复发与协同初始化转换（2026-09-08）

用户确认切Chat再切回Completion后，POST结构和保存恢复；但刷新后再次失效，每次都需重新切换。此绕过并非持久修复。

在参考[collaboration-manager.ts](https://github.com/langgenius/dify/blob/60a18fa/web/app/components/workflow/collaboration/core/collaboration-manager.ts)的populateNodeContainer中找到更上游的确定性转换：

```ts
const listFields = new Set(['variables', 'prompt_template', 'parameters'])
// ...
if (listFields.has(key))
  this.syncList(container, key, Array.isArray(value) ? value : [])
else dataContainer.set(key, toLoroValue(value))
```

prompt_template被无条件列为列表字段；Completion对象转换成[]，Chat数组保留。此转换高度吻合刷新加载后复发的现象，优先于先前默认配置时序假设；线上构建是否包含同代码待本轮扫描确认。

本地从下载的实际源码直接提取Object.entries转换循环，以内存适配器执行（未运行真实Loro容器）：Completion basic对象、Completion Jinja对象都变成[]；Chat列表保持。增加仅针对prompt_template非数组的对象写入分支后，3类输入保持原值，再次转换也保持；其他variables/parameters数组对照不变。测试脚本本机/tmp/dify-completion-repro/reload-shape.cjs。

候选最小修复：

```ts
if (key === 'prompt_template' && !Array.isArray(value))
  dataContainer.set(key, toLoroValue(value))
else if (listFields.has(key))
  this.syncList(container, key, Array.isArray(value) ? value : [])
else dataContainer.set(key, toLoroValue(value))
```

这是供源码修复评审的建议，尚未改动部署。还须验证真实Loro容器中的对象/列表切换、初始化、刷新、协同合并和保存；不能把适配器测试等同线上修复验收。已损坏的旧数据应从历史快照或备份恢复，先修复转换以免再次覆盖。

## 线上代码确认（2026-09-08，命令98d46cf）

用户回传node_cwd=/app、pid1_cwd=/app/targets/next/web；已发现静态目录/app/targets/next/web/.next/static/chunks。

扫描器先要求new Set中同时包含variables、prompt_template、parameters，再输出附近转换。命中collaboration-manager-DGhvCEJY.js，回传指纹3754f2e301bf8be7，代码为：

```js
n.has(t) ? this.syncList(e,t,Array.isArray(a)?a:[]) : r.set(t,J(a))
```

另外命中2个打包文件的等价转换，文件名/指纹存在OCR疑点，未猜补。scanned=2106、candidates=3、skipped_large=0，扫描在3个候选处停止，不能据此认定只有3处代码副本。chunk_roots=2，第二个目录未回传。

结合已验证的运行规律与本地复现，定位结果为：前端协同节点初始化将Completion对象错误列表化成[]，后续Completion编辑向数组写入text而JSON不保留该属性。不是发布动作导致，也不由RBAC、worker或数据库保存失败解释。

修复交付建议：由厂商提供匹配部署版本的web修复镜像，或在对应版本源码修复populateNodeContainer并重新构建web。不要仅修改一个命中的chunk：存在多个候选及多个静态根，且扫描未穷尽。修复API/worker或修改环境变量无法替代这处数据结构转换修复。

必须验收：Completion basic/Jinja对象在初始化、刷新、保存、发布后仍为对象且文本不变；Chat角色数组保持；同节点Chat/Completion切换；两个浏览器协同加载/编辑。当前未发布修复、未修改任何远程文件。旧提示词仅在历史快照确实保留时可恢复，新编辑从未进入请求的内容不能从数据库承诺找回。
