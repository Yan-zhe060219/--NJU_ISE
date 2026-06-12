# MCP 服务器配置指南

## 什么是 MCP

MCP (Model Context Protocol) 让 Claude 能直接调用外部工具（读文件、访问数据库、搜索网页等）。Claude Code 已经内置了文件系统和网页搜索，以下 MCP 是对你学习场景的补充。

## 当前你已经有（内置）

| 功能 | 说明 |
|------|------|
| 文件读写 | Read / Write / Edit / Glob / Grep — 直接操作本地文件 |
| 网页搜索 | WebSearch — 搜索互联网最新信息 |
| 网页抓取 | WebFetch — 获取指定 URL 内容 |
| PDF 阅读 | Read 工具直接支持 .pdf 文件 |

## 推荐添加的 MCP

### 1. YouTube Transcript（视频学习必备）

**作用**：获取 YouTube 视频的字幕文本，让你可以分析视频讲座内容。

**配置方法**：
```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "npx",
      "args": ["-y", "@macrat/mcp-youtube-transcript"]
    }
  }
}
```

前提：你需要安装 Node.js。没有的话去 https://nodejs.org 下载 LTS 版。

**用法示例**：
> "请用 youtube-transcript 获取 https://youtube.com/watch?v=xxx 的字幕，然后帮我整理成知识笔记。"

### 2. Context7（查技术文档）

**作用**：获取最新版本的第三方库/框架文档。比网页搜索更精准。

**配置方法**：
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

**用法示例**：
> "用 context7 查一下 React 19 的 useOptimistic hook 怎么用。"

## 如何添加配置

### 方法一：直接编辑 settings.json

用 Claude Code 打开配置：
```
/config
```
选择 "Edit settings.json"，在 `mcpServers` 字段中添加上述配置。

### 方法二：用命令行

让我帮你添加（在 Claude Code 中直接说）：
> "帮我在 settings.json 中添加 YouTube transcript MCP 服务器"

## 注意事项

- MCP 服务器会启动本地进程，第一次运行时 `npx` 会自动下载依赖，需要网络
- 你用的是 DeepSeek 后端，部分 MCP 工具可能因模型能力限制而表现不稳定
- 不要装太多 MCP，先装 youtube-transcript 这一个，用熟了再加别的
- MCP 服务器运行需要 Node.js ≥ 18
