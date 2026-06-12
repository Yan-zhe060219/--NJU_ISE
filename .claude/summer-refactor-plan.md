# 暑假重构计划

> 目标：简化目录结构 + 引入项目知识积累 + 降低认知负担。
> 执行时间：2026年7月4日之后（期末考试全部结束后）。
> 当前状态：两件小事已完成（memory/ 合并、COMMANDS.md + ARCHITECTURE.md 迁移至 .claude/）。

---

## 一、目录简化（根目录 10 → 7 个条目）

### 1.1 practice/ → 合并进 knowledge-base/courses/

练习资料本来就跟课程走，单独一个目录增加查找负担。

```
knowledge-base/courses/<课程名>/practice/     # 原 practice/<课程名>/
```

改 CLAUDE.md 和 review.md 中的路径引用。

### 1.2 templates/ → 合并进 .claude/templates/

Prompt 模板是配置层的，不是独立的知识资产。

```
.claude/templates/    # 原 templates/
```

### 1.3 最终结构

```
Personnal/                        # 7 个根级条目（从 10 降到 7）
├── CLAUDE.md                     # 精简到 ~60 行：原则 + 指针
├── README.md                     # 克隆指南（保留）
├── REVIEW.md                     # 学期中才存在，考后可删除或存档
├── inbox/                        # 待处理课件
├── knowledge-base/               # 知识资产（合并了 practice/）
│   ├── courses/<课程名>/         # 课程笔记 + practice/
│   ├── projects/                 # 🆕 项目收获
│   ├── cs/ math/ software-eng/  # 主题笔记
│   └── other/
├── tools/                        # 脚本
├── .claude/                      # 全部配置
│   ├── commands/
│   ├── references/
│   ├── templates/                # 原根目录 templates/
│   ├── adr.md                    # 架构决策记录
│   ├── commands-speed-dial.md    # 命令速查
│   ├── summer-refactor-plan.md   # 本文件
│   └── ...
└── requirements.txt
```

### 1.4 CLAUDE.md 瘦身

当前 184 行，目标是 ~60 行。删除内容：
- 知识库规范 → 移到 `knowledge-base/_index.md`
- 工作流细节 → 这些在命令文件里已有
- 目录结构展开 → 保留顶层结构，细节删掉

保留内容：
- 系统定位的一句话
- 目录顶层概览（一行一个）
- 指向各文件的指针表（去哪里找什么）
- Git 安全原则引用
- 架构维护原则引用（一行）

---

## 二、项目知识积累

### 2.1 项目代码：独立仓库，不放在 Personnal 里

**每个项目自己开 GitHub 仓库。** 原因：

1. **git 历史分离** — 项目有自己完整的 commit 线，不会和笔记的 commit 混在一起
2. **构建/依赖独立** — 项目有自己的 `package.json`/`go.mod`/`Cargo.toml`，不污染 Personnal 的 `requirements.txt`
3. **协作可能** — 以后如果需要给别人看代码，直接分享项目仓库即可
4. **Personnal 保持轻量** — 当前 1.4GB 主要来自 inbox 里的课件 PDF，加项目代码会爆炸

建议的目录布局：

```
D:\Desktop\
├── Personnal/              # 元系统（学习 + 知识管理）
├── <project-a>/            # 独立项目仓库 A
├── <project-b>/            # 独立项目仓库 B
└── ...
```

每个项目仓库里有自己的 `.claude/` + `CLAUDE.md`（可以用 `/init` 生成），描述该项目的技术栈和约定。

### 2.2 桥接机制：三层设计

核心问题：项目仓库和 Personnal 是独立的，每次切目录跑 `/retro` 太重了。
解决方案：三层捕获，从轻到重，覆盖不同场景。

#### 架构全景

```
D:\Desktop\
├── Personnal\                          # 元系统
│   └── inbox\project-insights\         # 🆕 桥接收件箱（项目写入这里）
│       └── <项目名>\                    # 每个项目一个子目录
│           ├── 2026-07-15-async-pool.md # 原始洞察（3-10行的轻量文件）
│           └── ...
├── <暑假项目>\                           # 项目仓库
│   ├── CLAUDE.md                       # 包含桥接指令（见模板）
│   └── .claude\commands\insight.md     # /insight 命令
```

**数据流**：

```
项目中的对话 ──→ /insight ──→ inbox/project-insights/<项目>/  （Layer 1：手动轻量）
项目 CLAUDE.md ──→ 自动提示 ──→ 同上                            （Layer 2：里程碑触发）
Personnal cron ──→ /kb-consolidate ──→ knowledge-base/          （Layer 3：定期收割）
```

#### Layer 1：项目侧的 `/insight` 命令（日常使用，摩擦最低）

在项目仓库里用 `/insight <一句话>`，自动写入 Personnal 的桥接收件箱。

命令文件 `.claude/commands/insight.md`（放在每个项目仓库里）：

```markdown
# /insight — 从项目中捕获一个洞察

将当前对话中产生的一个值得记住的发现/决策/踩坑记录写入 Personnal 的桥接收件箱。

## 用法

/insight <一句话描述>
/insight                      # 不带参数：AI 从当前对话中自动提取

## 执行

1. 如果用户给了一句话，用它；否则扫描当前对话提取 1-3 条值得记录的洞察
2. 每个洞察写入独立文件到 `D:\Desktop\Personnal\inbox\project-insights\<项目名>\YYYY-MM-DD-<slug>.md`
3. 每条洞察 3-8 行：问题 → 发现 → 为什么重要
4. 写完后告诉用户写了几条，不需要多余总结
```

使用体验：在项目里写完一段代码，说 `/insight 连接池在 asyncpg 下需要用 async context manager 否则会泄漏`，3 秒搞定，不用切目录。

#### Layer 2：项目 CLAUDE.md 中的自动提示（防遗忘）

每个项目仓库的 CLAUDE.md 中加入以下桥接指令：

```markdown
## 知识桥接

每次完成以下操作后，**主动建议**用户运行 `/insight` 来捕获收获：

- 修复了一个花了超过 30 分钟的 bug
- 做了一个涉及取舍的架构决策
- 用了一种之前没用过的技术/模式
- 发现了某个工具/库的非显而易见行为

建议格式：「💡 这个 [bug/决策/发现] 值得记下来。要我用 `/insight` 保存到知识库吗？」

如果用户说"不用"或"以后再说"，不纠缠。
```

这样你不需要自己记得要去捕获——AI 在合适的时机提醒你，但控制权在你。

#### Layer 3：Personnal 侧的定期收割（安全网）

在 Personnal 里新增两个命令：

**`/kb-consolidate` — 处理桥接收件箱**（处理 Layer 1/2 产出的原始洞察）：

```
/kb-consolidate                  # 处理 inbox/project-insights/ 中所有未处理的文件
/kb-consolidate --project <名称>  # 只处理特定项目
```

AI 做的事：
1. 扫描 `inbox/project-insights/` 下所有 `.md` 文件
2. 每条洞察判断归属：架构决策 → `.claude/adr.md`，可复用模式 → `knowledge-base/software-eng/`，课程关联 → 对应课程笔记的 `## 关联`
3. 在 `knowledge-base/projects/<项目>/` 下生成整理后的条目
4. 处理完的文件移到 `inbox/project-insights/<项目>/_processed/`

**cron 自动调度**：

```bash
hermes cron create "0 21 * * 0" "/kb-consolidate"   # 每周日晚 9 点自动收割
```

如果 inbox 是空的就什么都不做，零成本；如果有积压就自动处理。

### 2.3 为什么不直接全自动

你可能想：能不能完全不手动，AI 自己从项目对话里提取？

**不建议。** 原因：
- 自动提取的噪音比信号多——AI 会把你随手试的、后来废弃的、闲聊里的东西都当成"洞察"
- 手动 `/insight` 本身就是一次**主动回忆**——你说出"连接池会泄漏"的那一刻，已经在巩固记忆了
- 三层设计里，Layer 1 只花 3 秒，Layer 2 提醒你不遗忘，Layer 3 防止积压——已经足够省力

### 2.4 完整流程图

```
你在项目里写代码
       │
       ├─ 修了个 tricky bug ──→ Claude:「💡 值得记下来，/insight?」
       │                              │
       │                       你说「好」或 `/insight 连接池泄漏问题`
       │                              │
       │                              ▼
       │                 inbox/project-insights/<项目>/2026-07-15-asyncpg-leak.md
       │                              │
       │    ┌─ 你不想手动 ─────────────┘
       │    │
       ▼    ▼
   每周日晚 9 点  cron 触发 /kb-consolidate
       │
       ├─ 架构决策 → .claude/adr.md
       ├─ 通用模式 → knowledge-base/software-eng/
       ├─ 课程关联 → knowledge-base/courses/<课程>/... 的 ## 关联
       └─ 项目档案 → knowledge-base/projects/<项目>/
```

### 2.5 项目 CLAUDE.md 模板

每个暑假项目仓库的 CLAUDE.md 应该包含这些节（可以用 `/init` 生成基础版，然后加桥接节）：

```markdown
# <项目名>

<一句话描述>

## 技术栈
- 后端：...
- 数据库：...
- ...

## 约定
- ...

## 知识桥接

向 Personnal 回流知识：
- 手动：`/insight <描述>` — 保存一个洞察
- 自动：修复 30min+ 的 bug、做架构决策、用新技术时，我会主动提醒你记录
- 收割：每周日晚 Personnal 自动运行 `/kb-consolidate`

项目收获存档在 `D:\Desktop\Personnal\knowledge-base\projects\<项目名>/`。
```

---

## 三、上下文预算控制

### 当前状况
- CLAUDE.md 184 行 ≈ 2000 token（每次对话自动加载）
- DeepSeek V4 Pro 上下文 1M token → 不是瓶颈
- 真正的上下文消耗来自对话轮次，不是项目文件

### 瘦身后 CLAUDE.md 结构

```markdown
# Personal AI System

大二软件工程学生的本地 AI 辅助系统。

## 去哪里找什么

| 要找 | 去 |
|------|----|
| 命令用法 | `.claude/commands-speed-dial.md` |
| 学习原则 | `.claude/references/principles.md` |
| 课程映射 | `.claude/references/mappings.md` |
| 架构决策 | `.claude/adr.md` |
| 项目收获 | `knowledge-base/projects/` |

## 目录

Personnal/
├── inbox/              # 课件拖入这里
├── knowledge-base/     # 笔记 + 项目收获
├── tools/              # 预处理脚本
├── .claude/            # 全部配置
├── CLAUDE.md           # 本文件
├── README.md           # 克隆指南
└── requirements.txt    # Python 依赖

## 原则

- Git 安全原则：见 `.claude/references/principles.md#git-安全原则`
- 架构一致性：改完后说"检查架构一致性"
- 单一真相源 + 单向依赖
```

~40 行，每次启动只多占 ~500 token。

---

## 四、执行顺序

| 优先级 | 任务 | 预计耗时 |
|--------|------|---------|
| 1 | 创建 `inbox/project-insights/` 目录 | 1min |
| 2 | 新建 `knowledge-base/projects/_index.md` 和 `_project-card.md` 模板 | 10min |
| 3 | `practice/` 合并进 `knowledge-base/courses/`，更新路径引用 | 20min |
| 4 | `templates/` 移入 `.claude/templates/` | 5min |
| 5 | CLAUDE.md 瘦身到 ~60 行 | 15min |
| 6 | 实现 `/insight` 命令模板（放在 `.claude/templates/insight.md`，方便复制到新项目） | 15min |
| 7 | 实现 `/kb-consolidate` 命令（`.claude/commands/kb-consolidate.md`） | 30min |
| 8 | 设置每周 cron：`hermes cron create "0 21 * * 0" "/kb-consolidate"` | 1min |
| 9 | 为暑假项目初始化 CLAUDE.md（含桥接节） | 10min |

> 总耗时约 2 小时。建议 7/4 考完当晚或次日下午一次性搞定。

---

## 五、考后注意

- REVIEW.md 考试结束后可以删除或移到 `knowledge-base/other/archive/` — 它不会再被读取
- 考完后 inbox/ 里没用完的课件可以清掉（笔记已在 knowledge-base/ 里）
- 如果以后没有新课件，inbox/ 可能长期为空，可以考虑在 README 里注明"学期中才用"
