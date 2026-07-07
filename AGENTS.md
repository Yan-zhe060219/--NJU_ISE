# AGENTS.md

大二软件工程学生的本地 AI 辅助系统。不依赖网页端 AI，用 Codex (DeepSeek V4 Pro) 完成学习和编程。

> **维护状态**：暑假重构中（2026-07-06 起），参考 `.Codex/summer-refactor-plan.md`。

## 目录结构

```
Personnal/
├── inbox/                          # 待处理课件（PDF/PPTX 拖入即处理）
├── knowledge-base/                 # 个人知识库（笔记即资产）
│   ├── courses/                    # 按课程组织（跟随教学大纲）
│   └── cs/ math/ software-eng/    # 按主题跨课程整合
├── practice/                       # 练习资料：往年卷、复习思考题、exam-intel
├── tools/                          # 课件预处理脚本（extract_file.py 统一入口）
│   └── *.py
├── .Codex/                        # Codex 配置
│   ├── commands/                   # 自定义命令（learn, study, review, homework, kb-review）
│   ├── references/                 # 共享原则和映射表
│   ├── rules/                      # 按需加载的领域规则（paths: frontmatter）
│   ├── agents/                     # 自定义子代理
│   └── settings.json               # 项目级权限配置
├── AGENTS.md                       # 本文件（宪法层：项目身份 + 全局约定）
├── Codex.local.md                 # 个人偏好（不提交，覆盖 AGENTS.md）
├── REVIEW.md                       # 期末复习总控面板
└── requirements.txt                # Python 依赖
```

## 配套文件

- **`.Codex/commands-speed-dial.md`** — 所有命令的速查手册（日常操作先查它）
- **`.Codex/adr.md`** — 架构决策记录
- **`REVIEW.md`** — 期末复习的单一真相源（考试日期、进度追踪、阶段计划）
- **`.Codex/summer-refactor-plan.md`** — 暑假重构计划

## 知识库规范

详见 `.Codex/rules/note-conventions.md`。核心要点：

- **课程笔记**：`<序号>-<章节标题>.md`，frontmatter 含 title/course/chapter/tags/source/status/related
- **主题笔记**：`YYYY-MM-DD-主题-标题.md`
- **status 四阶段**：`draft → learned → reviewed → mastered`
- **笔记间链接**：通过 `related` 字段和 Markdown 链接互相引用

## 工作流

所有工作流已实现为自定义命令，详见 `.Codex/commands/`：

| 命令 | 用途 | 何时用 |
|------|------|--------|
| `/learn` | 处理课件 → 生成结构化笔记 | 导入新课件时 |
| `/study` | 课程问答模式 → 对话沉淀到笔记 | 深入理解某个章节 |
| `/review` | 期末复习总控 → 每日任务追踪 | 考试季 |
| `/homework` | 编程作业引导式辅导 | 做编程作业时 |
| `/kb-review` | 知识库复习 → 查漏补缺 | 定期巩固 |

### Git 安全流程（所有操作的前提）

1. **频繁提交**：每完成 ~20-50 行，立即 `git commit` + `git push`
2. **删除前必提交**：先 commit + push 当前修改，删除后立即再 commit
3. **Push 不拖延**：commit 后马上 push，本地 commit 不被视为"已保存"
4. **高风险操作前检查**：`reset --hard`、`clean -fd`、批量删除前，确认工作区干净

## Python 环境

详见 `.Codex/rules/python-env.md`。
- Python 3.10+，依赖见 `requirements.txt`
- 统一入口：`tools/extract_file.py`（MarkItDown 优先 → 三级回退 → MinerU）
- MinerU 高质量引擎用于公式/表格/扫描件（`conda env mineru`，Python 3.10）

## 架构维护

详见 `.Codex/rules/architecture.md`。

**依赖拓扑**：上层不引用下层；同级不互相引用；共享定义只有法律层（`.Codex/references/`）一份。

修改配置后的检查清单见 `.Codex/rules/architecture.md#检查清单`。
