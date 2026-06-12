# 共享映射表与 Schema

> **被引用者：** learn.md, study.md, review.md
> **修改本文件时**，需同步检查上述三个命令文件中引用映射表和 schema 的逻辑是否仍然正确。

---

## 课程名映射

用于 `/learn` 自动更新 REVIEW.md 时匹配课程，以及 `/review` 解析用户输入的课程简称。

| 用户输入/笔记 course | REVIEW.md 中的课程名 | knowledge-base 目录 |
|---------------------|-------------------|-------------------|
| 软件工程 | 软件工程 | knowledge-base/courses/软件工程 |
| 操作系统 / OS | 操作系统 | knowledge-base/courses/OS |
| 数据库 | 数据库 | knowledge-base/courses/数据库 |
| 高级算法 / 算法 | 高级算法 | knowledge-base/courses/高级算法 |
| 互联网计算 / 网络 | 互联网计算 | knowledge-base/courses/互联网计算 |

**模糊匹配规则**：如果笔记 course 值在 REVIEW.md 的课程列表中没有精确匹配，尝试含有关键词（如 course="数据结构与算法" 匹配 REVIEW.md 中的 "数据结构"）。匹配不到则跳过。

---

## study-session.json Schema

会话文件路径：`.claude/study-session.json`

```json
{
  "active": true,
  "course": "<完整课程名>",
  "courseDir": "knowledge-base/courses/<目录名>",
  "startedAt": "YYYY-MM-DDTHH:MM:SS",
  "focusChapter": "<章节标识或null>",
  "chapterFile": "<具体笔记文件路径或null>",
  "source": "study",
  "phase": "<当前复习阶段标识或null>"
}
```

字段说明：
- `active` — 是否有活跃会话
- `course` — 完整课程名（如"操作系统"，非目录名）
- `courseDir` — 课程目录相对路径
- `startedAt` — 会话开始时间（ISO 8601）
- `focusChapter` — 聚焦章节标识（如 "03-多处理器编程"），null 表示全部章节
- `chapterFile` — 具体笔记文件的相对路径（如 "knowledge-base/courses/互联网计算/02-应用层.md"），null 表示无特定文件
- `source` — 会话来源：`"study"`（/study start 启动）或 `"review"`（/review go 启动）
- `phase` — 当前复习阶段标识（如 "Phase 1"），仅在 source="review" 时有意义，null 表示无阶段

生命周期：
- **创建**：`/study start` 或 `/review go <笔记名>` 时写入
- **读取**：`/study status`、`/study done` 时读取
- **清除**：`/study done` 或 `/study cancel` 后将 `active` 设为 false
- **过期**：若会话超过 24 小时未活动，新会话启动时自动覆盖
