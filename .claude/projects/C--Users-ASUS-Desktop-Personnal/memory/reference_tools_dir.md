---
name: tools-dir
description: tools/ 目录下存放可复用脚本，extract_pdfs.py 用于批量提取 PDF 文本
metadata:
  type: reference
---

# tools/ 目录

`C:\Users\ASUS\Desktop\Personnal\tools\` 存放项目级别的可复用工具脚本。

## extract_pdfs.py

批量预处理 PDF → 文本提取。通过 pdfplumber 提取中文文本，保存到 `.cache/` 子目录，与 PDF 文件隔离。

## extract_pptx.py

批量预处理 PPTX → 文本提取。通过 python-pptx 提取幻灯片正文 + 演讲者备注，保存到 `.cache/` 子目录。接口与 extract_pdfs.py 一致。

调用方式：
```
python tools/extract_pdfs.py [target] [--force] [--single]
python tools/extract_pptx.py [target] [--force] [--single]
```

详见 [[pdf-workflow]]。
