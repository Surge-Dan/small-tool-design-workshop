# README 视觉样例

README按基础工具、视觉进阶、复杂交互排列。原有9幅是静态视觉概念，新增3幅是可运行原型的浏览器截图；二者的制作与验证边界不同，不能据此宣称真机兼容或平台审核已通过。

下表9幅概念图使用内置 imagegen 生成。行李清单沿用此前生成的鲜彩插画方向，其余样例为同批制作；完整提示词和原始输出文件标识保留在[prompts.json](prompts.json)中。未使用其他项目的示例图或用户截图作为素材。图像生成的字形与最终代码字体可能不同；价格、天气、书名与记录数据均为概念样例，不代表真实查询结果。

| 文件 | 类型 | 重点 |
| --- | --- | --- |
| [packing.png](packing.png) | 清单核对 | 分类插画、鲜明色块与完成态 |
| [dinner.png](dinner.png) | 预算推荐 | 菜品插画、预算与结果关系 |
| [outfit.png](outfit.png) | 搭配选择 | 服饰图像、场景选择与替换 |
| [focus.png](focus.png) | 计时工具 | 计时对象、读数与操作反馈 |
| [mood.png](mood.png) | 卡片生成 | 内容预览、情绪选择与保存入口 |
| [split.png](split.png) | 计算工具 | 数字层级、人数与金额关系 |
| [plants.png](plants.png) | 日常记录 | 不同植物的识别与待办状态 |
| [reading.png](reading.png) | 进度记录 | 书籍、页码和操作；书名为概念样例 |
| [photo.png](photo.png) | 内容编辑 | 画布、选中边界与素材工具 |

这些是创作案例，不是安装后必须选择的九套模板。Skill的制作路线可以组合；真正交付时仍从用户任务与明确偏好推导。

## 实际原型截图｜2026-10-18

| 文件 | 对应原型 | 状态与验证边界 |
| --- | --- | --- |
| [roam-live.png](roam-live.png) | [半日漫游](../../examples/advanced/roam.html) | 实际390×844初始状态；地点与路程是演示数据 |
| [wardrobe-live.png](wardrobe-live.png) | [随身衣橱](../../examples/advanced/wardrobe.html) | 实际390×844初始状态；独立服装素材由imagegen制作，搭配是本地规则 |
| [darkroom-live.png](darkroom-live.png) | [口袋暗房](../../examples/advanced/darkroom.html) | 实际390×844初始状态；示例照片由imagegen制作，UI与像素处理由代码实现 |

截图直接来自Edge离线渲染，没有重绘、添加虚假功能或将概念图冒充运行截图。截图只证明该画面；操作检查另见[案例文件与验证说明](../../examples/advanced/README.md)。这三张不属于prompts.json中的九幅概念图。
