---
name: "source-command-kb-review"
description: "复习知识库已有笔记，发现关联，查漏补缺，更新掌握状态"
---

# source-command-kb-review

Use this skill when the user asks to run the migrated source command `kb-review`.

## Command Template

# 知识库复习技能

帮助用户复习、串联、巩固知识库中的内容。

## 处理流程

1. **扫描知识库** — 列出所有笔记及其 frontmatter（标题、标签、状态、关联）
2. **执行一个复习动作**（根据用户指令选择）：

   ### 如果没有指定动作，默认执行"查漏补缺"

   **关联发现**：
   - 找出所有 `related: []` 为空的笔记
   - 阅读笔记内容，尝试与其他笔记建立关联
   - 更新 `related` 字段

   **状态升级**：
   - 用户自评掌握程度：`draft → reviewed → mastered`
   - 更新 frontmatter 中的 `status`

   **生成复习清单**：
   - 按主题整理所有笔记，生成一份复习路线
   - 标注笔记之间的依赖关系：哪些应该先看，哪些是进阶

   **快速问答**：
   - 随机从知识库中抽取概念，出 3-5 道简答题
   - 评分用户回答，指出薄弱点

3. **更新索引** — 确保 `_index.md` 与实际笔记同步

## 复习策略建议
- **间隔复习**：新笔记 1 天后复习，然后 3 天、7 天、30 天
- **交叉复习**：不要一次复习同一主题太多内容，交替不同主题效果更好
- **费曼技巧**：尝试用自己的话解释概念，发现说不清楚的地方就是薄弱点
