---
paths: [".claude/**", "CLAUDE.md", "REVIEW.md"]
---

# 架构维护

## 依赖拓扑

```
CLAUDE.md（宪法层 — 很少改）
  ├── .claude/references/principles.md（法律层 — 被 learn/study/review 引用）
  ├── .claude/references/mappings.md（法律层 — 被 learn/study/review 引用）
  │
  ├── .claude/commands/（执行层 — 经常改）
  │   ├── learn.md   → 引用 principles.md, mappings.md
  │   ├── study.md   → 引用 principles.md, mappings.md
  │   ├── review.md  → 引用 principles.md, mappings.md
  │   ├── homework.md
  │   └── kb-review.md
  │
  ├── REVIEW.md（数据层 — 复习总控，被 review.md 读写）
  ├── .claude/commands-speed-dial.md（参考层 — 命令速查）
  ├── .claude/adr.md（参考层 — 架构决策记录）
  │
  └── tools/（工具层 — 课件预处理脚本，被 learn.md 调用）
      ├── extract_file.py       ← 统一入口（--backend 控制引擎）
      ├── mineru_extract.py     ← MinerU 引擎
      ├── extract_pdfs.py       ← PDF 回退引擎
      └── extract_pptx.py       ← PPTX 回退引擎
```

**原则**：上层文件不引用下层；同级不互相引用；共享定义只有法律层一份。

## 检查清单

修改以下内容后，检查对应项：

| 改了 | 需检查 |
|------|--------|
| principles.md | learn.md、study.md、review.md 中的原则引用是否过时 |
| mappings.md 映射表 | learn.md 第七节、review.md 第二节约课程匹配是否正确 |
| mappings.md schema | study.md、review.md 中 session 读写逻辑 |
| 新增课程 | REVIEW.md 和 knowledge-base/courses/_index.md 是否同步 |
| 命令文件中的模板 | 另一命令中是否有相同模板需要同步 |
| REVIEW.md 考试日期 | commands-speed-dial.md 第七节的考试时间线是否同步 |
| requirements.txt | tools/ 中的脚本是否能正常工作 |
| .claude/adr.md | 新条目日期是否在已有条目之后（追加约束） |
| README.md 目录结构 | CLAUDE.md 目录结构是否同步 |
