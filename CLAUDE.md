# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# Personal AI-Assisted Learning & Coding System

大二软件工程学生的本地 AI 辅助系统。目标是：不依赖网页端 AI，用 Claude Code (DeepSeek V4 Pro) 完成学习和编程。

> **维护状态**：暑假前稳定维护，不做大改。大规模瘦身（~60 行）已规划在 `.claude/summer-refactor-plan.md`，7 月 4 日后执行。

## 目录结构

```
Personnal/
├── inbox/                          # 待处理课件，按课程分文件夹（PDF/PPTX 直接拖入）
│   ├── README.md                   # 使用说明
│   ├── <课程名>/                   # 每门课一个文件夹
│   │   ├── .learned                # 自动生成，追踪已处理的文件
│   │   └── .cache/                 # 自动生成，存放提取的文本
├── knowledge-base/                 # 个人知识库（笔记即资产）
│   ├── courses/                    # 按课程组织的笔记（跟随教学大纲）
│   ├── cs/ math/ software-eng/    # 按主题跨课程整合
│   └── other/
├── practice/                       # 练习资料：往年卷、复习思考题、exam-intel.md
├── tools/                          # 课件预处理脚本
│   ├── extract_file.py              # 统一文本提取（MarkItDown 优先，回退 PDF/PPTX）
│   ├── extract_pdfs.py             # PDF → 文本提取（回退，EasyOCR 扫描件）
│   ├── extract_pptx.py             # PPTX → 文本提取（回退，演讲者备注）
│   ├── ocr_pdf.py                  # 扫描件 PDF OCR（EasyOCR + 图像预处理）
│   └── scan_transcripts.py         # 会话记录分析工具（诊断用）
├── templates/                      # Prompt 模板
├── .claude/                        # Claude Code 配置
│   ├── commands/                   # 自定义命令（learn, study, review, homework 等）
│   ├── references/                 # 共享原则和映射表（法律层）
│   ├── skills/                     # Claude Code 技能
│   ├── settings.json               # 项目级权限配置
│   ├── settings.local.json         # 本地覆盖配置（不提交）
│   └── study-session.json          # 当前学习会话状态
├── .claude/adr.md                  # 架构决策记录（ADR 风格）
├── .claude/commands-speed-dial.md  # 命令速查手册（日常参考用）
├── REVIEW.md                       # 期末复习总控面板
├── CLAUDE.md                       # 本文件（宪法层）
└── requirements.txt                # Python 依赖（pdfplumber, python-pptx 等）
```

## 配套文件

- **.claude/commands-speed-dial.md** — 所有命令的速查手册（flags、示例），日常操作先查它
- **.claude/adr.md** — 架构决策记录，新增/删除架构元素时在这里写条目
- **REVIEW.md** — 期末复习的单一真相源（考试日期、进度追踪、阶段计划）
- **.claude/summer-refactor-plan.md** — 暑假重构计划（考后执行）

## Python 环境

课件预处理需要 Python 3.10+。首次使用前安装依赖：

```bash
pip install -r requirements.txt
```

主要依赖：`pdfplumber`（PDF）、`python-pptx`（PPTX）、`PyMuPDF`（PDF 回退）、`easyocr`（扫描件 OCR）。

`/learn` 命令会**自动**调用 `tools/extract_file.py`（MarkItDown 引擎），无需手动运行。只有在预处理失败或需要强制重新提取时才手动调用。

验证工具是否正常：

```bash
python tools/extract_file.py --help
python tools/extract_pdfs.py --help
python tools/extract_pptx.py --help
```

## 知识库分层

- **courses/** — 按课程组织，跟随课堂节奏，方便应对考试
- **cs/ math/ software-eng/** — 按主题跨课程整合，建立深度理解

同一知识点可能出现在两处：课程笔记侧重跟随课堂，主题笔记侧重概念本质和跨课程关联。

## 知识库规范

### 课程笔记（courses/ 下）
- 文件名：`<序号>-<章节标题>.md`
- frontmatter 包含：title, course, chapter, tags, source, status, related
- 笔记结构：一句话总结 → 知识地图 → 核心概念 → 难点突破 → 关联 → 记忆卡片

### 主题笔记（cs/ math/ software-eng/ 下）
- 文件名：`YYYY-MM-DD-主题-标题.md`
- frontmatter 包含：title, tags, created, source, status, related
- 笔记结构：一句话总结 → 核心概念 → 为什么重要 → 推导/原理 → 关联 → 类比 → 记忆要点

### 通用规范
- 每个目录下有 `_index.md` 作为索引
- 笔记之间通过 `related` 字段和 Markdown 链接互相引用
- status 四阶段：`draft → learned → reviewed → mastered`（详见 `.claude/references/principles.md` §双向映射）

## 工作流

### Git 安全流程（所有操作的前提）

> 详见 `.claude/references/principles.md#git-安全原则`

1. **频繁提交**：每完成一个逻辑独立的修改单元（~20-50 行），立即 `git commit` + `git push`
2. **删除前必提交**：任何删除操作前，先 commit + push 当前所有修改；删除完成后立即再 commit
3. **Push 不拖延**：commit 后马上 push，本地 commit 不被视为"已保存"
4. **高风险操作前检查**：`reset --hard`、`clean -fd`、批量删除前，确认工作区干净

### 学习流程（课程模式）
1. 在 `inbox/` 下为每门课程创建文件夹
2. 把该课程的所有课件（PDF/PPTX）拖入对应文件夹
3. 运行 `/learn inbox/<课程名>/` → AI 自动预处理课件文本，然后逐份处理生成笔记
4. 运行 `/study start <课程名>` → 进入问答模式，读原文档过程中有疑问随时问
5. 理解透彻后运行 `/study done` → AI 自动提取对话中的洞察，补充到对应笔记
6. 每天学一点：`/learn inbox/<课程名>/ --single`
7. 定期运行 `/kb-review` 复习巩固

### 学习流程（单文件/URL）
1. 运行 `/learn <路径或URL>`
2. AI 自动分类保存到 courses/ 或对应主题目录

### 深度问答流程
1. 运行 `/study start <课程名>` 进入问答模式（可选 `--chapter N` 聚焦单章）
2. 像聊天一样自然提问，AI 会关联到具体章节
3. 运行 `/study done` 保存洞察，AI 自动将对话中的新理解**融入笔记原有框架**（见下方"洞察融入规则"）
4. 中途可用 `/study status` 查看会话状态，`/study cancel` 放弃保存

#### 洞察融入规则（/study done 时执行）

对话中产生的新理解**不追加、不另起段落**，而是直接修改对应笔记文件，融入其既有结构：

| 洞察类型 | 融入目标 | 方式 |
|----------|---------|------|
| 对某个核心概念有了更深理解 | `## 核心概念` 下对应小节 | 在原段落中补充细节、类比或推导过程 |
| 澄清了一个之前卡住的难点 | `## 难点突破` | 新增或改善突破方法，保留有效的旧内容 |
| 发现了与另一章节/课程的联系 | `## 关联` / frontmatter `related` | 添加链接，简述关联逻辑 |
| 突然悟到的"一句话概括" | `## 一句话总结` | 如有更精炼的表达则替换，否则不强行改 |
| 新的记忆卡片 | `## 记忆卡片` | 增量添加 Q&A，删掉冗余的旧卡片 |
| 纠正了之前的错误理解 | 对应位置 | 直接修正，不留"旧理解→新理解"的修订痕迹 |

**核心原则**：
- **融入后像从未被修改过**——阅读体验和原笔记一致，看不出"后来补的"
- **宁精勿多**——一个真正理解的概念比三个半懂的好
- **保持原文风格**——笔记已有自己的语气和结构，融入时匹配之
- **不记录"学习过程"**——如"我今天学到了"、"经过讨论发现"等元信息不进入笔记

### 期末复习流程

总控文件：`REVIEW.md`，核心命令：`/review`（详见 `.claude/commands/review.md`）。

1. 运行 **`/review`** → 展示今日任务和各科倒计时
2. 复习方式：直接对话问答（如"考我软工模块二的记忆卡片"）或 `/study start <课程名>`
3. 完成一篇笔记后运行 **`/review done <笔记名>`** → 自动勾选并更新进度
4. 今日复习完成后运行 **`/review finish`** → 全部勾选，预填明天任务
5. 随时运行 **`/review progress`** 查看全局状态，**`/review plan`** 查看阶段计划
6. 导入新课件（inbox/ 下新增文件）→ 运行 `/learn` 处理，Claude 自动更新 REVIEW.md

### 编程作业流程
1. 在作业目录打开 Claude Code
2. 运行 `/homework <作业描述>`
3. AI 读取本地代码，引导式辅导

## 架构维护

### 依赖拓扑

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
  ├── .claude/commands-speed-dial.md（参考层 — 命令速查，被 CLAUDE.md 引用）
  ├── .claude/adr.md（参考层 — 架构决策记录，被 CLAUDE.md 引用）
  │
  └── tools/（工具层 — 课件预处理脚本，被 learn.md 调用）
      ├── extract_file.py
      ├── extract_pdfs.py
      └── extract_pptx.py
```

**原则**：上层文件不引用下层；同级不互相引用；共享定义只有法律层一份。

### 修改后检查

修改以下内容后，运行对应检查命令（或直接说"帮我检查架构一致性"）：

| 改了 | 需检查 |
|------|--------|
| principles.md | learn.md、study.md、review.md 中的原则引用是否过时 |
| mappings.md 映射表 | learn.md 第七节、review.md 第二节约课程匹配是否正确 |
| mappings.md schema | study.md、review.md 中 session 读写逻辑 |
| 新增课程 | REVIEW.md 和 knowledge-base/courses/_index.md 是否同步 |
| 命令文件中的模板 | 另一命令中是否有相同模板需要同步 |
| REVIEW.md 考试日期 | .claude/commands-speed-dial.md 第七节的考试时间线是否同步 |
| requirements.txt | tools/ 中的脚本是否能正常工作 |
| .claude/adr.md | 新条目日期是否在已有条目之后（追加约束） |
| README.md 目录结构 | CLAUDE.md 目录结构是否同步 |
