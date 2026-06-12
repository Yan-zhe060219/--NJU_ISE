---
name: tools-dir
description: tools/ 目录下存放可复用脚本，extract_file.py 是统一入口（MarkItDown 优先）
metadata:
  type: reference
---

# tools/ 目录

`C:\Users\ASUS\Desktop\Personnal\tools\` 存放项目级别的可复用工具脚本。

## extract_file.py（主入口）

统一文件提取脚本。MarkItDown 优先（12+ 种格式），失败自动回退到 extract_pdfs/extract_pptx。
支持的格式：PDF、PPTX、DOCX、XLSX、图片(OCR)、HTML、CSV、JSON、XML、IPYNB、EPUB。

调用方式：
```
python tools/extract_file.py <folder> [--force] [--single]
python tools/extract_file.py <file> --force
```

## extract_pdfs.py（回退）

PDF 专用提取。通过 pdfplumber + EasyOCR(扫描件) 提取文本。当 MarkItDown 处理 PDF 失败时作为回退。

## extract_pptx.py（回退）

PPTX 专用提取。通过 python-pptx 提取幻灯片正文 + 演讲者备注。当 MarkItDown 处理 PPTX 失败时作为回退。

详见 [[pdf-workflow]]。
