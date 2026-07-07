# 课程学习助手使用指南

> 面向“隔很久之后重新打开项目”的自己。先读本文件，再决定要不要看更细的配置文档。

## 这个项目现在是什么

这是一个只服务学校课程学习的本地 AI 辅助系统。

- 正式课程资料放在 `courses/<学期>/<课程>/`
- 当前活跃学期是 `courses/2026-spring/`
- Claude Code 负责执行学习命令和整理资料
- Codex 负责规划、审计、给 Claude 指令
- `practice/` 已收尾归档，日常不再使用
- `legacy/` 只保存历史遗留资料，不作为正式学习入口
- `staging/` 保存不确定、未验证、未匹配课程的资料

一句话：日常只看 `courses/`、`inbox/`、`REVIEW.md`。

## 回来后先做什么

在项目根目录执行：

```powershell
git status -sb
git pull
```

然后看三个文件：

1. `USER_GUIDE.md`：你现在正在看的总入口
2. `REVIEW.md`：当前学期复习和考试状态
3. `.claude/commands-speed-dial.md`：命令速查

如果很久没用，先问 Codex：

```text
请只读检查这个课程学习助手当前状态，告诉我当前活跃学期、课程目录、REVIEW.md 状态、是否有未提交改动，以及我下一步该怎么开始用。
```

## 日常学习流程

### 1. 导入课件

把课件放到：

```text
inbox/<课程名>/
```

例如：

```text
inbox/操作系统/
inbox/数据库/
```

### 2. 让 Claude 生成课程笔记

在 Claude Code 中运行：

```text
/learn inbox/<课程名>/ --single
```

每天学一点用 `--single`。如果确定要批量处理整门课：

```text
/learn inbox/<课程名>/
```

生成的正式笔记会进入：

```text
courses/2026-spring/<课程名>/notes/
```

### 3. 深度问答

开始某门课问答：

```text
/study start <课程名>
```

聚焦某一章：

```text
/study start <课程名> --chapter N
```

结束并把有价值的理解沉淀回笔记：

```text
/study done
```

取消本次会话：

```text
/study cancel
```

### 4. 复习

查看今天该复习什么：

```text
/review
```

查看整体进度：

```text
/review progress
```

标记某篇完成：

```text
/review done <笔记名>
```

查漏补缺：

```text
/kb-review
/kb-review 快速问答
```

## 目录怎么理解

```text
courses/2026-spring/<课程>/
├── README.md      # 课程说明
├── syllabus/      # 大纲
├── lectures/      # 原始课件
├── notes/         # 正式学习笔记
├── assignments/   # 作业资料
├── exams/         # 往年卷、考试资料
├── review/        # 错题本、复习资料、exam-intel
├── assets/        # 图片和附件
└── legacy/        # 历史遗留/未精细整理资料
```

使用原则：

- 新课件先放 `inbox/<课程名>/`
- 生成后的正式笔记进 `notes/`
- 作业资料进 `assignments/`
- 考试资料进 `exams/`
- 复习资料进 `review/`
- 不确定资料进 `staging/`
- 不要从 `legacy/` 自动生成笔记，除非你明确要求

## Claude 和 Codex 怎么分工

推荐工作方式：

```text
你 → Codex：请给 Claude 一段执行指令
Codex → 生成短指令
你 → Claude：粘贴执行
Claude → commit + push + 报告
你 → Codex：粘贴报告
Codex → 只读审计
```

Claude 适合：

- 跑 `/learn`、`/study`、`/review`
- 整理资料
- 批量移动文件
- 更新文档
- commit + push

Codex 适合：

- 判断方向
- 设计目录结构
- 审计 Claude 报告
- 检查风险
- 给下一步短指令

## 新学期怎么切换

不要用软链接，不要改名旧学期目录。

切换步骤：

1. 确认工作区干净：

   ```powershell
   git status -sb
   ```

2. 给旧学期打标签或提交备份。

3. 创建新学期：

   ```text
   courses/2026-fall/
   ```

4. 为每门课创建：

   ```text
   README.md
   syllabus/
   lectures/
   notes/
   assignments/
   exams/
   review/
   assets/
   legacy/
   ```

5. 归档旧 `REVIEW.md`：

   ```text
   archive/reviews/REVIEW-2026-spring.md
   ```

6. 创建新的 `REVIEW.md`。

7. 更新这些文件中的当前学期路径：

   ```text
   AGENTS.md
   CLAUDE.md
   README.md
   USER_GUIDE.md
   .claude/commands-speed-dial.md
   .claude/commands/learn.md
   .claude/commands/study.md
   .claude/commands/review.md
   ```

8. commit + push。

如果不确定，直接让 Codex 先给 Claude 指令。

## 什么不要做

- 不要把 API key、token、个人绝对路径写进可提交文件
- 不要把编程项目塞进这个课程学习助手
- 不要把 AI 生成资料直接放进正式课程目录
- 不要为了清理而删除不确定资料
- 不要继续使用 `practice/` 作为日常入口
- 不要把 `legacy/` 当作正式笔记来源

## 常用文件索引

| 文件 | 用途 |
|------|------|
| `USER_GUIDE.md` | 重新上手总入口 |
| `README.md` | 项目概览、环境恢复、文档导航 |
| `AGENTS.md` | Codex 总控规则 |
| `CLAUDE.md` | Claude Code 执行规则 |
| `.claude/commands-speed-dial.md` | 命令速查 |
| `.claude/commands/learn.md` | `/learn` 具体规则 |
| `.claude/commands/study.md` | `/study` 具体规则 |
| `.claude/commands/review.md` | `/review` 具体规则 |
| `REVIEW.md` | 当前学期复习总控 |

## 秋季回来时可以直接复制给 Codex

```text
我很久没打开这个课程学习助手了。请只读检查当前仓库状态：
1. git status 和最近提交
2. 当前活跃学期
3. courses/ 下有哪些学期和课程
4. REVIEW.md 是否还对应当前学期
5. inbox/、staging/、legacy/ 是否有待处理资料
6. 给我下一步最短使用建议

不要修改文件。
```

## 当前系统是否完善

以“课程学习助手”的定位来看，当前系统已经基本完善。

剩余工作不是阻塞项，而是未来维护项：

- 真正到秋季时切换当前学期
- 给新学期课程补 `README.md`
- 初始化新的 `REVIEW.md`
- 定期确认本地 token 没有进入 Git
- 只在需要时整理 `legacy/` 和 `staging/`

