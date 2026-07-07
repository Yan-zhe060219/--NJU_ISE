---
paths: ["tools/**", "inbox/**", "requirements.txt"]
---

# Python 环境与课件预处理

## 环境要求

Python 3.10+。首次使用前：

```bash
pip install -r requirements.txt
```

主要依赖：`pdfplumber`（PDF）、`python-pptx`（PPTX）、`PyMuPDF`（PDF 回退）、`easyocr`（扫描件 OCR）。

## 统一入口：tools/extract_file.py

`/learn` 命令会**自动**调用此脚本，无需手动运行。只有在预处理失败或需要强制重新提取时才手动调用。

```bash
python tools/extract_file.py <路径>                    # MarkItDown 优先
python tools/extract_file.py <路径> --backend mineru   # MinerU 引擎
python tools/extract_file.py <路径> --backend auto      # 三级回退（最全面）
```

## MinerU 高质量引擎

用于含**公式、表格、图表、扫描件**的复杂 PDF（`conda env mineru`，Python 3.10）。

**何时使用 MinerU：**
- 数学/物理/工程类教材 PDF（LaTeX 公式需要保留）
- 含有大量表格的文献（表格还原度要求高）
- 扫描版 PDF（OCR 需求）
- MarkItDown 提取结果不理想时

```bash
# 独立调用 MinerU 批量处理
python tools/mineru_extract.py <文件夹>
python tools/mineru_extract.py <文件夹> --effort high    # 高质量（含图片分析）
python tools/mineru_extract.py <文件夹> -m ocr           # 强制 OCR 模式
```

## 工具验证

```bash
python tools/extract_file.py --help
python tools/mineru_extract.py --help
python tools/extract_pdfs.py --help
python tools/extract_pptx.py --help
```
