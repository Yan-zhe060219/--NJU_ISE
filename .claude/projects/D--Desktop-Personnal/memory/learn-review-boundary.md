---
name: learn-review-boundary
description: /learn 生成新笔记后更新 REVIEW.md 时，新条目必须用 [ ]学 [ ]会，绝不能自动勾选 [x]学
metadata:
  type: feedback
---

# /learn 更新 REVIEW.md 时绝不自动勾选 [x]学

**问题**：之前处理 OS Ch14 和软工 3 篇补充课件时，在 REVIEW.md 中新增条目写成了 `[x]学 [ ]会`，而用户尚未通读这些笔记。

**Why:** `学` = "第一遍通读完成"，是 `/review` 流程中的学习动作，不是 `/learn` 生成笔记时能自动标记的。生成笔记 ≠ 学过。`/review` 是唯一能勾选 `[x]学` 和 `[x]会` 的命令。

**How to apply:** 每次 `/learn` 更新 REVIEW.md 时：
1. 新条目格式必须是 `- [ ]学 [ ]会`（两个都未勾选）
2. 不要因为同课程下已有条目是 `[x]学` 就复制该格式
3. 更新进度表时，"已学"数只计入已勾选 `[x]学` 的条目
4. 更新完自查：新条目的 `学` 是否确实未勾选？

详细规则见 [[review-learn-boundary]] 和 `.claude/references/principles.md#reviewmd-的-learn-与-review-职责边界`。
