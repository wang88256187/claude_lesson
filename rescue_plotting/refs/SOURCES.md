# 参考资料下载地址

原文件不入库（体积大）。需要核对时按下面地址下载到本目录：

| 文件 | 内容 | 地址 |
|---|---|---|
| mem_202101.pdf | XF/T 3013-2020《国家综合性消防救援队伍常用标号》全文（扫描版，36 页） | https://www.mem.gov.cn/gk/zfxxgkpt/fdzdgknr/202101/W020210118711682130047.pdf |
| gbt35649.pdf | GB/T 35649-2017《突发事件应急标绘符号规范》全文（23 页，用户提供；国标委可免费在线阅读，境外 IP 可能无法访问） | https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=74F315245BF52E92018C295FE0F2F41F |

渲染页面图片：`python -c "import pymupdf;d=pymupdf.open('mem_202101.pdf');[d[i].get_pixmap(dpi=110).save(f'pages/p{i+1:02d}.png') for i in range(d.page_count)]"`
（需先 `mkdir pages` 并 `pip install pymupdf`）
