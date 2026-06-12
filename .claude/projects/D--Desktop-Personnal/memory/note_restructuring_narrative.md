---
name: note-restructuring-narrative
description: 英文碎片化课件笔记必须重构为情景化叙事，覆盖原文，不看课件也能复习
metadata:
  type: project
---

英文源 + PPT 碎片化课件生成的笔记，必须重构为情景化叙事结构：串联上下文、场景驱动（"你是一个帧…"）、严格覆盖原文所有定义/机制/数据、类比辅助、对比用表格、对话感语气。目标：用户不看原课件只看笔记也能达到同等复习效果。

**Why:** 英文 PPT 课件知识点分散在各页，缺少上下文衔接，直接按概念罗列生成的笔记只见树木不见森林。重构后知识点之间有因果链和叙事流，复习时不需要来回翻课件。

**How to apply:** `/learn` 生成英文源笔记时默认使用此风格；`/review` 阶段用户说"重构"或"按其他笔记风格统一"时执行。参考模板：`knowledge-base/courses/互联网计算/06-网络层-路由器与IP.md`。

Related: [[project_ai_system]], [[project_pdf_workflow]]
