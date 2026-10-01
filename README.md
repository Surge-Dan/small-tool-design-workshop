# 小工具设计工坊

面向小红书小工具的移动端设计与原型 Skill。

## 能做什么

- 需求模糊时，用少量问题收敛核心玩法；
- 需求完整或用户要求“直接做”时，直接产出主题化移动端原型；
- 生成单 HTML、离线可打开、可操作的轻量 H5；
- 审查并消除模板化 AI 设计：无意义英文、空泛口号、通用渐变和粗糙卡片堆叠；
- 保持设计与产品任务一致，避免为了“好看”增加无效页面和文案；
- 将明确需求逐项落实到页面与操作，按场景覆盖输入边界、返回修改、重置和保存失败等交互；
- 检查实际渲染与操作，交付时区分已验证、模拟及未验证部分。

## 安装

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo Surge-Dan/small-tool-design-workshop `
  --path . `
  --name small-tool-design-workshop
```

安装后在下一次任务中使用 `$small-tool-design-workshop`，也可以直接描述你的产品需求。

## 使用示例

```text
使用 $small-tool-design-workshop 设计一个移动端单 HTML：
用户输入预算和人数，得到今晚晚餐建议。
整体像菜市场手写价签，不要做成 AI 对话框。
```

## 核心原则

- 先做最短可用路径，再补视觉和节奏；
- 用户只要玩法或方案时，不擅自生成 HTML；
- 笔记本、手册、记录类任务优先使用单页结构；
- 默认轻量验证，不在每次使用时跑长测试或全面审计。
- 视觉表达由具体内容决定，保留有情绪、品牌或辨识价值的装饰，不把所有主题做成同一种极简手册。

## 目录

```text
SKILL.md                 # 入口与工作模式
references/              # 按需读取的设计、视觉、反 AI、移动端规则
agents/openai.yaml       # Codex UI 元数据
evals/evals.json         # 最小评估样例
mood-handbook.html       # 可直接打开的示例原型
```

## 示例原型

打开 `mood-handbook.html`，可体验“选择心情 → 可选记录 → 生成并保存分享卡”的完整流程。
