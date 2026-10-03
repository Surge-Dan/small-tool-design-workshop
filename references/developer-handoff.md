# 导出给下一位AI的开发参考包

用户需要将原型交给AI写代码、继续迭代或在新会话复用时读取。目标是让下一位AI知道“保留什么、实现什么、如何验收”，不只凭截图猜。

## 交付范围

默认交付可运行的HTML及简短说明；用户要开发参考时，另交付ZIP参考包。用户只要单HTML时不强制多文件，不把导出ZIP按钮塞进终端用户界面；这是创作者交付能力，与工具里的保存图片不是同一个动作。

包内包括：

- `prototype.html`：本次最新原型，是外观与交互参考；不是未经审查即可上线的生产代码。
- `design-spec.json`：已确认需求、页面／状态、交互、规则、设计参数、模拟部分、资产清单与验证记录。
- `HANDOFF.md`：由同一份JSON生成的可读交接，需求ID对应验收与证据，明确未完成项。
- `AI-START.md`：交给下一位AI的开工说明，要求先读原型与约束，再按用户指定技术栈开发。
- `screenshots/`：已有关键页面／错误／结果状态的实际截图，标注状态与视口。截图来自当前版本；不要用参考图或生图冒充实测截图。

没有截图工具时可以导出HTML和交接，但必须注明缺少实际截图。不能编造图片、设备测试、Figma文件或下载链接。Figma/Pixso仅在用户要求且实际可用时另行交付；ZIP参考包不是可编辑设计源文件。

## 填写设计记录

可从模板复制，或运行：

```text
python scripts/build_handoff.py init --output <项目目录>/design-spec.json --title <工具名>
```

不要把占位说明当成需求或测试结论。字段约定如下：

| 字段 | 要记录什么 |
| --- | --- |
| `schema_version`、`title` | 当前为1；实际工具名称 |
| `brief` | `status`为draft／confirmed／delegated；确认依据、用户／场景／目标、排除项、离线要求和待解决的关键问题 |
| `pages[].states[]` | 全局唯一状态ID与描述；布局说明用实际信息顺序 |
| `requirements[]` | 唯一ID、描述、关联页面、可观察验收句；实现状态planned／partial／implemented；验证级别not_run／static／browser／device及证据ID |
| `interactions[]` | 唯一ID、触发、前后状态、条件、反馈与保留的数据；状态可在同一页面，不要求独立页 |
| `logic[]` | 输入、具体规则、可检查的例子、是否模拟；无业务规则的展示工具可为空 |
| `visual` | 方向、实际采用的设计参数、动效说明及资产来源／许可／用途／是否内嵌；可附design_plan、motion_plan与review，不可只写“高级” |
| `evidence[]` | 唯一ID、类型、具体观察、涉及状态；可附当前项目下的PNG／JPEG／WebP截图或文本日志相对路径 |
| `assumptions`、`limitations` | 已说明的默认值、缺少的能力／验证、已知问题；缺截图或断网验证由脚本另行提示 |
| `revision`、`changes` | 可选，当前版本和本次变动；修改后同步记录，不保留过期证据 |

证据类型为 `screenshot`、`static`、`browser`、`device`、`offline` 或 `export`。截图必须有对应状态及`viewport`宽高；未记录的维度用null并说明，不把长截图的图片高度当成视口高度。截图只证明该画面。browser／device验证需关联对应级别的操作记录，不把截图当作操作测试。`offline` 记录禁用网络后直接打开文件的实际步骤与结果，不能用搜索外链代替。

路径相对JSON所在目录，资源文件必须位于该目录内；外部截图先复制进项目。不读取任意目录，不把账号凭据、用户隐私、完整浏览器日志或生产密钥收入交接。必要日志先截取或脱敏。包内路径转换为相对路径，不携带本机绝对路径。

设计参数从实际HTML／样式中提取并核对，不从预想方案推测。需求的验证级别可以为not_run，部分完成也可以交付，但要如实标明。确认状态不等于需求已实现，更不等于运行通过。

### 视觉计划与复查

新原型需要开发交接时填写以下可选扩展；旧版设计记录仍能导出，并提示未记录视觉路线／复查。它们与 [visual-sop.md](visual-sop.md) 对应，避免下一位AI只拿到颜色和字号却不知道表现意图。

- `visual.design_plan`：主要`route`为typographic／object-led／asset-led／scene-led；`intent`和`reference_basis`说明表现意图与参考或原创依据；`anchors`、`techniques`、`acceptance`分别记录保留特征、方法及理由、视觉验收句。路线可混用，route只标主要路线。不能将草稿的undecided直接导出。
- `visual.review`：`status`为not_reviewed／reviewed／needs_revision；`level`为not_run／static／rendered；`evidence_ids`关联已有证据。static需静态记录，rendered需实际画面截图；复查结果由执行Agent记录，打包器不独立判断图像质量。
- `review.findings[]`：唯一`id`、`severity`为blocker／major／minor、`location`、`state_ids`、`observation`、`action`、`status`为open／fixed／accepted。accepted须有`acceptance_evidence`记录用户明确接受依据，不能自行批准偏离用户方向。

存在未修复blocker或未处理major时，不得把复查状态写成reviewed；可以标needs_revision导出部分交付并说明缺陷。rendered只表示查看过实际画面，不证明业务已运行、所有状态合格或性能通过；没有浏览器时保留static或not_run。reviewed表示记录的复查完成，不是自动“审美合格证”。

### 关键运动与连续操作

`visual.motion`保留简短文本，旧记录无`motion_plan`也能导出。按[动画与交互](motion-and-interaction.md)设计了需要交接的关键行为时，可加`visual.motion_plan`数组；没有有关运动时留空或省略，不强制每个按钮建立规格。

| 每项字段 | 内容 |
| --- | --- |
| `id`、`interaction_id` | 唯一运动ID、已有交互ID；触发与前后状态取自该交互 |
| `purpose`、`continuity` | 表现目的；保持哪个对象、焦点、选区或滚动关系 |
| `properties` | 非空字符串数组，实际变化的属性 |
| `duration_ms`、`easing` | 有限非负毫秒数、实际曲线说明；不是套用固定动画时长 |
| `interrupt`、`reduced_motion` | 快速重复、中途返回/关闭如何处理；减少动效时如何保留反馈与业务结果 |
| `verification`、`evidence_ids` | not_run／static／browser／device，已有证据ID |

非not_run级别需关联同类型记录；browser／device记录合起来需覆盖对应交互的前后状态。操作记录说明开始、中途、结束及适用的重复、中断和回退检查，不能用截图冒充动态验证。脚本只检查记录结构与引用，不观看运动，也不验证日志是否真实或动画是否专业。

HANDOFF.md会呈现这些行为，AI-START.md提醒保留连续性及回退。已有截图可解释关键画面；短录屏可按用户要求另交，当前打包器的证据附件仍只接受图片和UTF-8文本，不声称自动打包视频。缺少动态验证会明确提示，但不阻止如实交付部分完成的参考包。

## 构建与检查

```text
python scripts/build_handoff.py build --spec <项目目录>/design-spec.json --html <项目目录>/原型.html --output <新目录>/dinner-handoff
```

脚本使用Python标准库，生成目录与同名ZIP；拒绝覆盖已有输出。构建前检查确认状态、关键问题、ID与页面／状态／证据引用、验证级别、证据路径和文件类型。检查不通过时不生成包。未实现／部分实现、未验证、无截图或无断网记录会在交接里显式提示。

脚本只校验记录结构和打包完整性，不运行浏览器、不证明效果好看、不检查HTML与规则是否一致。`evidence`里的执行结论由实际操作的Agent记录，不能为了通过格式检查伪造证据。HTML有运行时外链时不能以`offline:true`掩盖；仍须按 [mobile-h5-patterns.md](mobile-h5-patterns.md) 验证。

不要在Skill安装目录内写用户项目。使用脚本的绝对路径，示例相对路径是相对当前项目／仓库运行。Python不可用时按同样结构手动交付文件；不能声称运行过打包器。

## 下一位AI如何使用

先读`AI-START.md`、`HANDOFF.md`和JSON，再打开HTML及截图。已确认业务规则和交互行为是实现约束；截图解释视觉，原型代码提供参考。用户明确的最新变更优先；文件彼此冲突时列出具体冲突再确认，不自动换成通用页面或照搬模拟服务。保留需求ID对应的验收例子，按用户指定技术栈落实；未指定技术栈、真实数据来源或平台时，下一位AI先澄清这些开发问题。
