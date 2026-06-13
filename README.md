# Personal AI-Assisted Learning & Coding System

大二软件工程学生的本地 AI 辅助系统。用 Claude Code (DeepSeek V4 Pro) 完成学习和编程，不依赖网页端 AI。

> 📖 **使用手册**：`commands.md` — 所有命令、工作流、常见场景
> ⚡ **命令速查**：`.claude/commands-speed-dial.md` — 最简短的命令参考
> 📋 **复习总控**：`REVIEW.md` — 考试日期、进度追踪、每日任务

## 核心工作流

```
课件拖入 inbox/ → /learn → 笔记(draft) → 自动更新 REVIEW.md
                      ↓
                 /study → 深度问答 → /study done → 洞察融入笔记
                      ↓
                 /review → 卡片自测/强制问答 → [x]会
                      ↓
                 /kb-review → 查漏补缺 → mastered
```

你只做三件事：**拖文件 → 说命令 → 回答问题**，其余全自动。

## 克隆回来（换电脑/丢失本地后）

### 1. 装 Git

```powershell
winget install --id Git.Git -e --source winget
```

装完**重启终端**。

### 2. 配置 SSH（国内必须，否则连不上 GitHub）

生成密钥（如果之前没生成过）：

```powershell
ssh-keygen -t ed25519 -C "你的邮箱"
```

把公钥添加到 GitHub：
1. 复制公钥内容：`cat ~/.ssh/id_ed25519.pub`
2. 打开 https://github.com/settings/keys → New SSH key → 粘贴 → 保存

配置 SSH 走 443 端口（国内绕过 GFW 的关键步骤）：

```powershell
@"
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
"@ | Set-Content -Path "$env:USERPROFILE\.ssh\config" -Encoding Ascii
```

验证连接：

```powershell
ssh -T git@github.com
```

看到 `Hi <用户名>! You've successfully authenticated` 就说明通了。

### 3. 克隆仓库

```powershell
git clone git@github.com:Yan-zhe060219/--NJU_ISE.git
cd --NJU_ISE
```

### 4. 装 Python 依赖

```powershell
pip install -r requirements.txt
```

### 5. 在项目目录启动 Claude Code

```powershell
claude
```

---

## 日常使用

> 完整手册见 `commands.md`，下面是快速概览。

### 学习课程课件

```
/learn inbox/<课程名>/              批量处理课程文件夹
/learn inbox/<课程名>/ --single     每天学一章
/learn <文件或URL>                  单文件自动分类
```

> `/learn` 处理完课件后**自动更新 REVIEW.md**（新增条目、重算进度、调整计划）。笔记初始状态为 `draft`，不会自动标记为"已学"——你需要通过 `/review` 来勾选。

### 深度问答

```
/study start <课程名>                进入问答模式
/study start <课程名> --chapter N    聚焦特定章节
/study done                          结束并保存洞察
/study status                        查看会话状态
```

### 期末复习

```
/review                              展示今日任务和倒计时
/review done <笔记名>                 标记复习完成
/review progress                     查看全局进度
/review plan                         查看复习阶段计划
```

### 编程作业

```
/homework <作业描述>
```

### 复习巩固

```
/kb-review                           查漏补缺
/kb-review 快速问答                   随机自测
```

---

## 目录结构

```
Personnal/
├── inbox/                    # 课件放入这里（按课程分文件夹）
│   ├── OS/                   # 操作系统课件（PDF/PPTX）
│   ├── 互联网计算/            # 计算机网络课件
│   ├── 数据库/                # 数据库课件
│   ├── 软件工程/              # 软工课件
│   └── 高级算法/              # 算法课件
├── knowledge-base/           # 个人知识库（笔记即资产）
│   ├── courses/              # 按课程组织的笔记
│   ├── cs/                   # 计算机科学主题整合
│   ├── math/                 # 数学
│   └── software-eng/         # 软件工程主题
├── practice/                 # 练习资料（往年卷、复习思考题）
├── tools/                    # 课件预处理脚本
│   ├── extract_file.py       # 统一文本提取（MarkItDown 优先，回退 PDF/PPTX）
│   ├── extract_pdfs.py       # PDF → 文本（回退，EasyOCR 扫描件）
│   ├── extract_pptx.py       # PPTX → 文本（回退，演讲者备注）
│   ├── ocr_pdf.py            # 扫描件 OCR（EasyOCR + 图像预处理）
│   └── scan_transcripts.py   # 会话记录分析（诊断用）
├── templates/                # Prompt 模板
├── .claude/                  # Claude Code 配置
│   ├── commands/             # 自定义命令（learn, study, review, homework 等）
│   ├── references/           # 共享原则和映射表
│   ├── skills/               # 自定义技能（占位）
│   ├── settings.json         # 项目级权限配置
│   └── settings.local.json   # 本地覆盖配置（不提交）
├── CLAUDE.md                 # 项目说明书（AI 读取）
├── commands.md                # 使用手册（你读的）
├── .claude/commands-speed-dial.md  # 命令速查手册
├── .claude/adr.md             # 架构决策记录
├── .claude/summer-refactor-plan.md  # 暑假重构计划
├── .mcp.json                 # MCP 服务器配置
├── REVIEW.md                 # 期末复习总控面板
└── requirements.txt          # Python 依赖
```

## 远程同步

```powershell
git add .
git commit -m "描述你改了什么"
git push
```

每次学完一章、改完笔记后提交一次，相当于实时备份到 GitHub。

---

## 文档导航

| 你要做什么 | 看哪个文件 |
|-----------|-----------|
| 快速查命令怎么用 | `.claude/commands-speed-dial.md` |
| 了解完整工作流、常见场景 | `commands.md` |
| 看考试日期、复习进度 | `REVIEW.md` |
| 了解项目架构和规范 | `CLAUDE.md` |
| 设置新电脑环境 | 本文件（README.md） |
