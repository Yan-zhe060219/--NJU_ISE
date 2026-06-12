---
name: pdf-workflow
description: 处理课程课件（PDF/PPTX/DOCX 等）的标准工作流——MarkItDown 提取文本后再生成笔记
metadata:
  type: project
---

# 课件学习工作流

## 标准流程

每次新课程（新文件夹）的学习流程：

```
1. 把课件放入 inbox/<课程名>/（支持 PDF/PPTX/DOCX/XLSX/图片/HTML 等）

2. 预处理——统一提取文本：
   python tools/extract_file.py inbox/<课程名>
   
   - MarkItDown 主引擎，支持 12+ 种格式 → Markdown
   - PDF 失败 → 回退 extract_pdfs.py（pdfplumber + EasyOCR 扫描件）
   - PPTX 失败 → 回退 extract_pptx.py（python-pptx + 演讲者备注）
   - 均生成到 .cache/ 子目录，与原始文件隔离
   - 支持 --force 强制覆盖、--single 单文件
   
3. 启动学习——逐章生成笔记：
   /learn inbox/<课程名>/
   
   - 读取 `.cache/` 中的 `.txt` 文件
   - 遵循知识库规范生成 courses/<课程名>/ 下笔记
   - --resume 从中断处继续
   - --single 每天学一章
   
4. 定期复习：
   /review
```

**Why:** 课程材料格式多样（PDF/PPTX/DOCX 等）。Claude Read 无法直接处理二进制文件或 OCR 质量差。MarkItDown 统一转换为纯文本，大幅提升处理质量和速度。旧脚本（extract_pdfs/extract_pptx）保留作为回退，处理 MarkItDown 可能不适配的中文扫描件 PDF。

**PPTX 注意事项:** PPTX 幻灯片内容通常比 PDF 教材稀疏（提纲式），笔记质量取决于幻灯片本身的详细程度和演讲者备注的质量。如果幻灯片过于简略（仅有关键词），笔记中会标注"来源为幻灯片提纲，建议结合课堂讲解"。

**How to apply:** 每次拿到新课程材料时，先执行步骤 2 的提取命令（python tools/extract_file.py inbox/<课程名>/），再进行步骤 3 的学习。

## 脚本复用

```
python tools/extract_file.py inbox/<课名>/              # 统一提取（推荐）
python tools/extract_file.py inbox/<课名>/ --force      # 强制重新提取
python tools/extract_file.py inbox/<课名>/ --single     # 只提取下一个未处理的
python tools/extract_file.py <文件> --force             # 单文件强制提取

# 回退脚本（MarkItDown 不适配时手动使用）
python tools/extract_pdfs.py --force inbox/<课名>/      # PDF 专用（EasyOCR）
python tools/extract_pptx.py --force inbox/<课名>/      # PPTX 专用（演讲者备注）
```

## 已知课程

- inbox/OS/ — 操作系统，南京大学软件学院 2026 春，钮鑫涛
