<div align="center">

# 🛠️Small Tool Design Workshop

### 面向小工具创作者的高保真原型设计Skill

![Platform](https://img.shields.io/badge/Platform-Codex-blue)
![Focus](https://img.shields.io/badge/Focus-Prototype-brightgreen)
![Output](https://img.shields.io/badge/Output-Single_HTML-orange)
![Delivery](https://img.shields.io/badge/Delivery-Offline-teal)

**从需求确认到视觉与交互设计，完成可体验、可继续开发的小工具原型**

</div>

小工具设计工坊适合想验证产品、试一试玩法，或把设计交给AI继续开发的人。你可以提供一个想法、一份需求、参考图或已有HTML。Skill会先确认使用场景、页面布局和视觉方向，再制作可交互的高保真原型，并保留方便后续修改和开发的设计说明。

> 想法还没成形，可以先聊；方向确定以后，再把画面和交互认真做好。

## 使用方式

**已经有具体需求**，安装后在新任务中直接说：

```text
使用$small-tool-design-workshop，做一个晚餐推荐工具。
输入预算和人数，输出菜名、估价和人均价格，支持返回修改。
视觉像菜市场手写价签，离线可用，交付移动端单HTML。
```

**只有一个想法**，也可以从“我想做一个健身记录器”开始。Skill会帮你梳理主要用途，给出可选方向，确认后再做原型。你不必先写一份完整需求文档。

如果需求已经完整，可以直接委托：“按这些要求制作，布局和风格你来定。”已有决定不重复确认，字体、间距和动画曲线等细节由设计师处理。

**想修改已有原型**，说清楚改哪里就行：

```text
只改结果页：把推荐理由讲清楚，增加返回修改按钮。
首页、配色和主流程保持不变。
```

## 🧭制作流程

从需求到交付，通常经过四步。需要你选择的方向会集中确认，具体设计细节在制作时打磨。

1. **确认需求**：谁在什么情况下使用，输入什么，得到什么，以及怎样判断结果符合要求。把操作路径、布局和视觉方向整理成一份短简报，合并确认。
2. **确定设计**：从使用场景选择版式和视觉表达。风格模糊或参考冲突时，用真实内容做关键页面小样，说明差异并给推荐；复杂效果先验证能否实现。
3. **制作原型**：围绕核心操作完成页面、状态和反馈。计算与本地处理使用真实输入；尚未接入的外部服务明确标注为演示。
4. **检查交付**：实际打开页面，检查画面、交互、动画和相关异常情况。修正问题后交付，并说明验证范围。需要继续开发时，再导出参考包。

只要玩法，就先讨论玩法；只改一个细节，就检查相关部分。完整方案或明确委托可以直接制作，简单工具不增加无关流程。

修改前保存可恢复版本，写清改动与保留项；修改后同时检查。快照包含HTML、已有设计记录和引用附件，可恢复到新目录，方便找回上一版满意的设计。具体方法见[修改与恢复](references/iteration-and-evidence.md)。

需求确认和修改方法见[需求与评审](references/brief-and-review.md)。

## 🎨视觉设计

视觉从工具的用途出发。晚餐工具可以用价签突出菜名和价格，训练记录器要方便快速记组，图片工具则需要给预览和对比留足空间。

| 设计方式 | 主要打磨什么 |
| --- | --- |
| 版式与字体 | 字级、比例、网格、阅读顺序 |
| 物件与材质 | 结构、边缘、触感、光影 |
| 图片与插画 | 构图、裁切、色板、素材关系 |
| 空间与动态 | 层次、对象关系、运动和操作反馈 |

这些方式可以组合。简约设计重点看比例、留白和细节；复杂设计则要控制层次、素材和动态，让主要操作始终清楚。

风格可以是清爽的记录本、可爱的卡通界面，也可以是复古掌机、杂志拼贴或有空间感的场景。主题会影响内容怎么排列、按钮怎么操作、结果怎么呈现，相关页面和状态也会一起设计。

**素材与渲染**按需要选择：统一的图标、授权插画、特色字体、生图工具，以及GSAP、Canvas／PixiJS、Three.js等方案。离线交付时，将许可允许的必要资源打包进HTML，保留来源与署名。工具缺失时说明限制；高成本生图、素材购买或长调研开始前，先说明范围与成本。

完成后，从用户使用、视觉设计和开发接手三个角度复查，问题要落到具体页面或状态。没有渲染条件时，标注静态检查范围。

详细方法见[视觉设计流程](references/visual-sop.md)、[视觉语言](references/visual-language.md)、[常见设计问题](references/anti-ai-slop.md)和[素材与渲染](references/visual-resources.md)。

## 动画与交互

点击、展开、生成和返回都需要清楚的反馈。动画会围绕操作前后的变化来设计，例如新记录出现在哪里、返回后继续编辑哪一项。

除了正常操作，还会根据工具的用途检查这些情况：

- 输入缺失或不合法时，就近说明问题，修正后可以继续。
- 返回修改时保留输入，新结果对应最新内容。
- 连续点击、切换和返回时，数据、焦点与滚动位置合理。
- 删除或清空前有确认或撤销；保存失败、无结果或取消分享时，保留内容并提供适用的恢复方式。
- 动画能处理重复触发和中途返回；开启减少动效后，状态变化仍然清楚。

动画的时长和曲线按任务与风格调整。静态截图用于检查画面，动画需要实际操作检查。具体方法见[动画与交互](references/motion-and-interaction.md)。

## 原型交付

默认提供：

- 一个可离线打开的HTML，内嵌CSS、JavaScript和必要资源。
- 简短的设计说明，包括核心任务、操作路径和视觉依据。
- 已实现内容、实际检查结果、关键假设和限制。

默认按移动端设计，以390×844为主要基准，同时检查窄屏和长内容；指定桌面端时，按对应使用场景制作。有浏览器工具时实际打开检查，未测试的设备和环境会标明。

需要持续记录时，可以按需求实现本机保存、历史回看和数据导出，并说明存储位置与备份方式。本机保存不包含跨设备同步。真实账号、支付、服务端数据库和生产API需要另行明确需求。

## 📦开发参考包

需要交给AI写代码时，直接说：“把当前原型导出成AI开发参考包。”

```text
工具名-handoff.zip
└── 工具名-handoff/
    ├── prototype.html      可运行原型
    ├── design-spec.json    需求、状态与设计参数
    ├── HANDOFF.md          交接说明与验收要求
    ├── AI-START.md         下一位AI的开工说明
    ├── ARTIFACT.json       原型与证据的版本清单
    ├── screenshots/        有实际截图时附带
    └── evidence/           有文本证据附件时附带
```

参考包保留原型、需求、页面状态、交互规则、设计参数和验收说明。关键动画还可记录触发条件、前后状态、时长曲线、中断方式和减少动效行为。

解压后，把整个目录交给能读取本地文件的AI，让它先读AI-START.md，再按你的目标平台和技术栈实现。只支持附件的工具，优先提供HTML、HANDOFF.md和关键截图。

缺少截图或动态验证时，会在交接说明中标明。只要单HTML时，不强制生成参考包，也不会在原型里添加面向开发者的导出按钮。

打包器仅依赖Python标准库，检查确认状态、文件引用和证据，生成目录与ZIP。草稿、未解决的关键问题或无效引用会阻止导出，已有输出不会被覆盖。打包成功只说明记录与文件符合要求，原型仍需实际运行检查。

新记录和证据可绑定实际HTML版本。HTML或已绑定附件变化后，导出会提示失效并停止；旧版未绑定记录仍可导出，并明确说明版本无法核验。哈希用于核对文件，不代表功能或视觉已经通过检查。

详细格式见[开发交接](references/developer-handoff.md)。

## 安装方式

在Codex环境中，通过Skill安装器执行：

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo Surge-Dan/small-tool-design-workshop `
  --path . `
  --name small-tool-design-workshop
```

安装后，在新任务中使用`$small-tool-design-workshop`，也可以直接描述需求，让Agent按任务匹配Skill。

## 项目结构

| 文件 | 用途 |
| --- | --- |
| [SKILL.md](SKILL.md) | Skill入口与工作要求 |
| [references/](references/) | 需求、视觉、交互与交付方法 |
| [agents/openai.yaml](agents/openai.yaml) | Codex展示信息与调用设置 |
| [assets/design-spec.template.json](assets/design-spec.template.json) | 设计记录模板 |
| [scripts/build_handoff.py](scripts/build_handoff.py) | 初始化记录、校验并导出参考包 |
| [scripts/prototype_state.py](scripts/prototype_state.py) | 保存与恢复版本、绑定已观察的证据 |
| [tests/test_build_handoff.py](tests/test_build_handoff.py) | 打包器测试 |
| [tests/test_prototype_state.py](tests/test_prototype_state.py) | 版本恢复与证据绑定测试 |
| [evals/evals.json](evals/evals.json) | 评估提示词与预期行为 |
| [evals/comparison.md](evals/comparison.md) | 内部真实任务对照方法 |

## 本地验证

运行打包器测试：

```text
python -m unittest discover -s tests -v
```

初始化设计记录，再填入实际需求、状态和验证结果：

```text
python scripts/build_handoff.py init --output <项目目录>/design-spec.json --title <工具名>
python scripts/build_handoff.py build --spec <项目目录>/design-spec.json --html <项目目录>/原型.html --output <新目录>/工具名-handoff
```

这些检查覆盖记录格式、打包、版本恢复与证据失效。视觉效果、动画和使用体验需要在生成的原型中单独验证。内部对照会记录实际产物、需求遗漏和修改情况；未收集用户偏好时，不宣称已经证明优于直接使用Agent。

## 💬贡献与反馈

欢迎提交[Issue](https://github.com/Surge-Dan/small-tool-design-workshop/issues)或[PullRequest](https://github.com/Surge-Dan/small-tool-design-workshop/pulls)。为了方便定位问题，请尽量提供：

- 可复现的需求描述、操作步骤或脱敏后的输入示例；
- 使用的Agent、Skill版本和运行环境，报错时附完整错误信息；
- 期望效果与实际结果之间的差异。

视觉或交互问题，欢迎附上截图或最小HTML文件。分享前请移除真实账号、APIKey、Cookie及其他个人敏感信息。

如果它帮你把一个小想法做成了满意的原型，欢迎点一个⭐，让更多创作者发现它。
