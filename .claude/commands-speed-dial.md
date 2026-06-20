# Claude Code 命令速查手册

> 你的个人 AI 辅助系统命令参考。自定义命令位于 `.claude/commands/`，可随时修改。

---

## 一、自定义命令（你的四大核心命令）

### 📖 `/learn` — 学习材料 → 知识库笔记

```
/learn inbox/OS/                  批量处理课程文件夹（自动预处理 PDF/PPTX/DOCX 等）
/learn inbox/OS/ --single         每天学一章（只处理下一篇）
/learn inbox/OS/ --resume         从中断处继续
/learn inbox/OS/ --force          重新处理全部（覆盖旧笔记）
/learn 某文件.pdf                  单个文件，自动分类到知识库
/learn https://...                 网页/视频 URL，自动分类
```

> 课件预处理已自动化：`/learn` 会自动调用 `tools/extract_file.py`（MarkItDown 优先，失败回退到 extract_pdfs/extract_pptx），无需手动运行。

### 💬 `/study` — 课程深度问答，对话自动沉淀到笔记

```
/study start <课程名>              进入问答模式，加载全部笔记上下文
/study start <课程名> --chapter N  聚焦特定章节
/study done                        结束会话，AI 提取对话洞察，追加到笔记
/study status                      查看当前会话状态
/study cancel                      取消会话（不保存）
/study list                        列出知识库中已有课程
```

> 学习闭环核心：`/learn` 生成初始笔记 → `/study` 深度问答迭代 → `/kb-review` 巩固复习。

### 🏠 `/homework` — 编程作业引导式辅导

```
/homework <作业描述>
```

自动读取本地代码 → 评估进度 → 分层引导（不直接给答案）。

### 📋 `/review` — 期末复习总控 🆕

```
/review                       展示今日任务 + 五科倒计时
/review start                 同上，进入复习模式
/review done <笔记名>          标记该笔记复习完成，更新进度
/review progress               查看五科整体进度和剩余天数
/review finish                 勾选今日全部任务，预填明天任务
/review plan                   查看三阶段复习计划
```

> 总控文件：`REVIEW.md`。复习方式：直接对话问答（"考我 XX 的记忆卡片"）或配合 `/study`。

---

## 二、辅助命令

| 命令 | 用途 |
|------|------|
| `/simplify` | 审查代码：复用性、质量、效率 |
| `/loop <间隔> <命令>` | 定时执行，如 `/loop 5m /review` |
| `/init` | 为新项目生成 CLAUDE.md |
| `/update-config` | 修改 Claude Code 设置（权限、环境变量等） |
| `/keybindings-help` | 自定义键盘快捷键 |
| `/review` | Code review 一个 PR |
| `/security-review` | 安全审查当前分支 |
| `/clear` | 清空对话上下文 |
| `/config` | 打开设置界面（模型、主题等） |
| `/help` | 查看所有可用命令 |

---

## 三、课件预处理（已自动化） 🆕

`/learn` 命令会**自动**调用 `tools/extract_file.py` 提取文本，无需手动操作。

**原理**：`extract_file.py` → MarkItDown（主引擎，12+ 种格式）→ 失败则回退 `extract_pdfs.py` / `extract_pptx.py`。

支持的格式：PDF、PPTX、DOCX、XLSX、图片（OCR）、HTML、CSV、JSON、XML 等。

只有在特殊情况下才需要手动运行：
```bash
python tools/extract_file.py inbox/<课程名>             # 提取该文件夹所有支持的文件
python tools/extract_file.py inbox/<课程名> --force     # 强制重新提取
python tools/extract_file.py inbox/<课程名> --single    # 只提取下一个未处理的
python tools/extract_file.py <具体文件路径> --force      # 单文件强制提取

# 旧脚本仍可用作回退：
python tools/extract_pdfs.py --force inbox/<课程名>     # PDF 专用（EasyOCR 扫描件）
python tools/extract_pptx.py --force inbox/<课程名>     # PPTX 专用（演讲者备注）
```

---

## 四、知识库结构

```
Personnal/
├── inbox/                         # 待处理：按课程放课件（PDF/PPTX/DOCX 等）
├── knowledge-base/
│   ├── courses/<课程>/            # 课程笔记（跟教学大纲）
│   ├── cs/ math/ software-eng/   # 主题笔记（跨课程整合）
│   └── other/
├── tools/extract_file.py           # 统一提取脚本（MarkItDown 优先，回退 PDF/PPTX）
├── tools/extract_pdfs.py           # PDF 预处理（回退，EasyOCR 扫描件）
├── tools/extract_pptx.py           # PPTX 预处理（回退，演讲者备注）
├── CLAUDE.md                      # 项目说明书
└── .claude/commands-speed-dial.md # 本文件
```

---

## 五、常用快捷操作

| 操作 | 怎么做 |
|------|--------|
| 新课程 | ① 建文件夹 `inbox/<课名>/` ② 拖入课件 ③ `/learn inbox/<课名>/`（自动预处理） |
| 每天学一点 | `/learn inbox/<课名>/ --single` |
| 继续上次 | `/learn inbox/<课名>/ --resume` |
| 深度问答 | `/study start <课名>` → 随意提问 → `/study done` |
| 聚焦单章提问 | `/study start <课名> --chapter 3` |
| 查看问答进度 | `/study status` |
| 强制重提课件 | `python tools/extract_file.py --force inbox/<课名>/` |
| 复习已学 | `/kb-review` |
| 查漏补缺 | `/kb-review 查漏补缺` |
| 自测掌握度 | `/kb-review 快速问答` |
| 做编程作业 | `/homework 题目描述` |

---

## 六、官方资源

- **Claude Code 官方文档**：https://docs.claude.codes/
- **Claude Code 问题反馈**：https://github.com/anthropics/claude-code/issues
- **Claude API 文档**：https://docs.anthropic.com/en/docs/claude-code
- **Claude Code 入门指南**：https://docs.claude.codes/overview

---

## 七、期末复习流程

> 总控文件：`REVIEW.md`（考试日期、逐篇笔记追踪、每日任务、三阶段时间表）
> 核心命令：`/review`（`.claude/commands/review.md`）

### 每日复习指令

| 命令 | 作用 |
|------|------|
| `/review` 或 `/review start` | 展示今日任务 + 五科倒计时，进入复习模式 |
| `/review done <笔记名>` | 标记该笔记复习完成，更新进度条 |
| `/review finish` | 勾选今日全部任务，自动预填明天任务 |
| `/review progress` | 查看五科整体进度、剩余天数、阶段状态 |
| `/review plan` | 查看三阶段复习计划 + 考试日历 |

### 复习方式

复习不是被动重读笔记。在 `/review start` 之后两种方式二选一：

1. **对话问答**：直接说"考我软工模块二的记忆卡片"或"让我推导 OS 的 Futex 两阶段锁"
2. **/study 模式**：`/study start <课程名> --chapter N` → 聚焦提问 → `/study done` 保存洞察

### 新课件加入时

```
/learn inbox/<课程名>/ --single     # 处理新课件生成笔记
```
Claude 会自动在 REVIEW.md 对应课程下新增待复习条目，并调整阶段计划。

### 考试时间线

| 日期 | 考试 | 笔记数 | 时间 |
|------|------|--------|------|
| 6.24 周三 | 软件工程 | 32 | 10:30 |
| 6.26 周五 | 操作系统 | 14 | 08:00 |
| 6.29 周一 | 数据库 | 22 | 08:00 |
| 6.30 周二 | 高级算法 | 5(考2) | 08:00 |
| 7.1 周三 | 中国近代史纲要 | 记忆卡 | 16:30 |
| 7.3 周五 | 互联网计算 | 13 | 08:00 |

### 其他复习工具

| 操作 | 怎么做 |
|------|--------|
| 日常巩固 | `/kb-review` |
| 随机自测 | `/kb-review 快速问答` |
| 生成复习路线 | `/kb-review 复习清单` |
| 查漏补缺 | `/kb-review 查漏补缺` |

---

> 最后更新：2026-06-16
