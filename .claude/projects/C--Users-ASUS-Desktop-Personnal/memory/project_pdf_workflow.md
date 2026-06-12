---
name: pdf-workflow
description: 处理课程课件（PDF/PPTX）的标准工作流——预处理提取文本后再生成笔记
metadata:
  type: project
---

# 课件学习工作流

## 标准流程

每次新课程（新文件夹）的学习流程：

```
1. 把 PDF / PPTX 放入 inbox/<课程名>/

2. 预处理——批量提取文本：
   python tools/extract_pdfs.py inbox/<课程名>
   python tools/extract_pptx.py inbox/<课程名>
   
   - 对 PDF 执行 pdfplumber 文本提取，对 PPTX 执行 python-pptx 提取（含演讲者备注）
   - 均生成到 .cache/ 子目录，与原始文件隔离
   - 支持 --force 强制覆盖已有 .txt
   - 进度分别记录在 inbox/.extracted 和 inbox/.extracted_pptx 文件中
   
3. 启动学习——逐章生成笔记：
   /learn inbox/<课程名>/
   
   - 读取 `.cache/` 中的 `.txt` 文件（速度更快、中文质量好）
   - 遵循知识库规范生成 courses/<课程名>/ 下笔记
   - --resume 从中断处继续
   - --single 每天学一章
   
4. 定期复习：
   /review
```

**Why:** 课程材料有 PDF 和 PPTX 两种格式。PDF 通常 15-40MB 幻灯片格式，Claude Read 无法直接处理或 OCR 质量差；PPTX 内容为提纲式，直接读取效率低。预处理提取为纯文本后可大幅提升处理质量和速度。

**PPTX 注意事项:** PPTX 幻灯片内容通常比 PDF 教材稀疏（提纲式），笔记质量取决于幻灯片本身的详细程度和演讲者备注的质量。如果幻灯片过于简略（仅有关键词），笔记中会标注"来源为幻灯片提纲，建议结合课堂讲解"。

**How to apply:** 每次拿到新课程材料时，先执行步骤 2 的两条提取命令，再进行步骤 3 的学习。

## 脚本复用

```
python tools/extract_pdfs.py                    # 扫描 inbox/ 下所有 PDF
python tools/extract_pptx.py                    # 扫描 inbox/ 下所有 PPTX
python tools/extract_pdfs.py inbox/OS           # 只处理指定课程 PDF
python tools/extract_pptx.py inbox/OS           # 只处理指定课程 PPTX
python tools/extract_pdfs.py --force inbox/OS   # 强制重新提取 PDF
python tools/extract_pptx.py --force inbox/OS   # 强制重新提取 PPTX
python tools/extract_pdfs.py --single inbox/OS  # 只提取下一个未提取的 PDF
python tools/extract_pptx.py --single inbox/OS  # 只提取下一个未提取的 PPTX
```

## 已知课程

- inbox/OS/ — 操作系统，南京大学软件学院 2026 春，钮鑫涛。10 个 PDF，已全部预提取到 .cache/ 子目录
