# 抢险救援标绘符号库（泥石流场景）v0.1.0

用于"智能标图工具"的基础符号库。共 57 个符号：38 个点状、9 个线状、8 个面状。

- `symbols.json`：符号库数据，前端和后端都读它
- `preview.html`：可视化预览，用浏览器直接打开
- `build_symbols.py`：生成脚本。增删改符号请改这里，然后运行 `python build_symbols.py`

## ⚠ 重要说明：这不是官方标号

| 资料 | 公开情况 | 本库是否采用 |
|---|---|---|
| 《中国人民解放军作战标图规定》（2013，总参发布） | 部队内部法规，没有公开全文。公开资料只说明它是"诸军兵种和武警部队制定补充规定或常用标号的依据" | 否 |
| 武警部队补充规定和常用标号 | 内部资料，没有公开版本 | 否 |
| **GB/T 35649-2017《突发事件应急标绘符号规范》** | 公开的国家推荐标准（2018-07-01 实施） | **只参考了它的分类框架** |
| 美军 ATP 7-100.3《Chinese Tactics》（2021） | 公开出版物。它讲的是战术，不是 PLA 原生标号，而且主要面向作战，和抢险救援关系不大 | 否 |
| 国外学者对 PLA 和武警救灾的研究（如汶川、玉树地震） | 公开。内容是组织指挥层面，不含标号 | 仅作背景参考 |

因此，本库的**图形、颜色和编号都是本项目自定义的示意**，不对应上述任何标准的原始编码。正式使用前，请用本单位下发的标图规定逐项替换或校核（方法见下文"替换为单位正式标号"）。

## 分类体系

分类框架参考 GB/T 35649：点状分为事件、危险源、防护目标、应急保障资源四类，另有线状和面状。本库在此基础上单列了"救援力量与行动"和"泥石流本体"两类。

| 前缀 | 类别 | 外框（点状） | 颜色 |
|---|---|---|---|
| EV | 灾害事件 | 三角形 | 橙 `#D35400` |
| HZ | 危险源/隐患 | 菱形 | 紫 `#8E44AD` |
| TG | 防护目标 | 方形 | 蓝 `#1F6FB2` |
| FC | 救援力量与行动（我方） | 矩形；指挥所用旗形 | 红 `#C0392B` |
| SP | 应急保障资源 | 圆形 | 绿 `#1E8449` |
| LN | 线状（流向、路线、警戒线等） | — | 按含义取色 |
| AR | 面状（危险区、责任区、安置区等） | — | 按含义取色 |

"我方力量用红色"沿用了军队标图的一般习惯。救灾场景里没有"敌方"，所以不使用蓝色表示敌方，蓝色留给防护目标。

框内的图形用会意汉字（如"泥""困""搜"），目的是在屏幕和打印时都能一眼认出。

## 字段说明（symbols.json）

```jsonc
{
  "id": "FC-03",              // 本库编号，不是国标编码
  "name": "救援分队",
  "geometry": "point",        // point | line | polygon
  "category": "force",
  "color": "#C0392B",
  "svg": "<svg ...>",         // 点状是图标；线状和面状是预览图
  "style": { ... },           // 只有线状和面状有：stroke/width/dash/arrow_end/fill/fill_opacity/hatch
  "description": "...",
  "attributes": ["label", "echelon", "headcount", "equipment", "task", "time", "remark"]
}
```

- `echelons`：力量规模的可选值（组、班、排、中队、大队、支队），在标绘时作为属性注记。
- `attributes`：该符号在图上可以填写的属性，后续的"智能标图"会用自然语言把这些属性填好。

## 替换为单位正式标号

1. 在 `build_symbols.py` 里找到对应条目，把 `svg` 换成单位标号的 SVG，把 `id` 换成正式编码。
2. 单位标号库里有、本库没有的符号，照现有写法新增一条。
3. 运行 `python build_symbols.py` 重新生成，再打开 `preview.html` 核对。

也可以扩展参考公开的国外应急标号：美军 MIL-STD-2525 和北约 APP-6 里都有应急管理和自然事件类符号。

## 参考来源

- GB/T 35649-2017 突发事件应急标绘符号规范：[国家标准全文公开系统](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=74F315245BF52E92018C295FE0F2F41F)、[国家标准馆](https://www.ndls.org.cn/standard/detail/342d2ecb7d5bdea81db8d582478b9d95)
- 军队标号（概念、《作战标图规定》的定位）：[百度百科·军队标号](https://baike.baidu.com/item/%E5%86%9B%E9%98%9F%E6%A0%87%E5%8F%B7/3522934)
- 滑坡崩塌泥石流调查规范（泥石流要素参考）：[中国地质调查局相关规范](https://dnr.gxzf.gov.cn/ygd/bszn/bszn/W020230322488629346386.pdf)
- ATP 7-100.3 Chinese Tactics（2021）：[Army Pubs](https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN34236-ATP_7-100.3-001-WEB-3.pdf)、[Internet Archive](https://archive.org/details/atp-7-100.3-chinese-tactics-2021)
- 国外关于中国军队和武警救灾的研究：[Hoover CLM · 汶川地震军队应对](https://www.hoover.org/sites/default/files/research/docs/CLM25JM.pdf)、[Hoover CLM · 玉树地震](https://www.hoover.org/sites/default/files/uploads/documents/CLM33JM.pdf)、[USAFA · PLA 与 HA/DR](https://www.usafa.edu/app/uploads/14_LENDING-A-HELPING-HAND-THE-PEOPLES-LIBERATION-ARMY-AND-HUMANITARIAN-ASSISTANCE-DISASTER-RELIEF.pdf)、[IDSA · 汶川地震与中国军队](https://www.idsa.in/system/files/jds_6_1_KamleshAgnihotri.pdf)
