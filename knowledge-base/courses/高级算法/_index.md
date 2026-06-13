---
course: "高级算法"
tags: ["随机化算法", "大数据", "哈希", "sketching", "网络流", "线性规划", "对偶"]
created: 2026-05-15
status: learning
---

# 高级算法

## 课程概述

南京大学苏州校区 2026 春，刘明谋。涵盖两大板块：(1) 基于哈希的大数据随机化算法——指纹、哈希表、数据流 Sketch、降维；(2) 网络流与线性规划——最大流算法、LP 形式化与求解、LP 松弛与舍入、对偶理论。

五大模块递进：
1. **Fingerprinting**：用随机采样生成"指纹"替代逐位比对 → PIT、Freivald、Karp-Rabin、Lipton
2. **Hashing**：深入哈希的理论基础 → Balls into Bins、负载均衡、Cuckoo、完美哈希、简洁字典
3. **Sketching**：用极少空间做估算 → Morris 近似计数、Count-Min、Flajolet-Martin、Bloom Filter
4. **Dimension Reduction**：降维与近似最近邻搜索 → JL 引理、LSH、FJLT、子空间嵌入
5. **Network Flow & Linear Programming**：最大流与增广路算法族、LP 形式化与求解、LP Relaxation & Rounding 近似算法设计、对偶理论与 Primal-Dual 框架

## 章节笔记

| 序号 | 章节 | 状态 |
|------|------|------|
| 01 | [Fingerprinting — 指纹与随机化身份检测](01-Fingerprinting.md) | reviewed |
| 02 | [Hashing — 哈希、负载均衡与字典数据结构](02-Hashing.md) | reviewed |
| 03 | [Sketching — 数据流草图与近似计数](03-Sketching.md) | reviewed |
| 04 | [Dimensionality Reduction — 降维、JL 引理与近似最近邻](04-Dimension.md) | reviewed |
| 05 | [Network Flow & Linear Programming — 网络流与线性规划](05-Flow-LP.md) | draft ⚠️ 未学 |

## 重要概念索引

### 核心方法论
- **随机化指纹（Fingerprint）** — 用小摘要代表大对象，one-sided error
- **Schwartz-Zippel 定理** — 多变量 PIT 错误率 ≤ d/|S|
- **Chernoff Bound** — 独立伯努利和的最强集中不等式
- **Universal Hashing** — k-universal 族：只需要 k-wise independence 不需要完全随机
- **Median-of-Means 技巧** — 降低方差的通用配方：均值 + 中位数

### 数据结构
- **FKS Perfect Hashing** — O(n) 空间、O(1) 查询静态字典
- **Cuckoo Hashing** — 2 次内存访问查询，O(1) 期望均摊更新
- **Bloom Filter** — 有假阳性的近似集合成员查询，每条目 ~10 bits

### 数据流算法
- **Morris Counter** — O(log log n) 空间近似计数
- **Flajolet-Martin** — O(log log N) 空间去重计数
- **Count-Min Sketch** — (ε,δ) 频率估计，取最小值去碰撞
- **Count Sketch (Tug-of-War)** — 随机符号 ±1，无偏估计 F₂

### 降维与近似搜索
- **Johnson-Lindenstrauss 定理** — n 点可嵌入 O(ε⁻² log n) 维，距离保持 (1±ε)
- **Locality-Sensitive Hashing** — 用哈希碰撞概率区分远近，ρ = log p/log q 决定时空复杂度
- **Fast JL Transformation (FJLT)** — Hadamard + 采样，O(d log d) 时间取代 O(dk)
- **Oblivious Subspace Embedding (OSE)** — 通过 γ-net 保证整个 d 维子空间嵌入，目标维度 O(d/ε²)

### 网络流
- **Residual Graph** — 流网络的核心数据结构，包含 forth edges（剩余容量）和 back edges（可撤销流）
- **Ford-Fulkerson / Edmonds-Karp / Dinitz** — 增广路算法族，从伪多项式到强多项式的演进
- **Max-Flow Min-Cut Theorem** — 最大流 = 最小割，提供最优性证书

### 线性规划与近似
- **LP Relaxation & Rounding** — 近似算法设计范式：ILP → LP → 舍入 → 近似比分析
- **LP Duality** — Weak/Strong Duality、Complementary Slackness：最优解的证书体系
- **Primal-Dual Schema** — 同时构造 primal 整数解和 dual 分数解，relaxed slackness 得近似比
- **Integrality Gap** — LP 松弛质量度量：OPT/OPT_LP 的上确界

## 本课程学习路线图

```
第1章 Fingerprinting → 第2章 Hashing → 第3章 Sketching → 第4章 Dimension Reduction → 第5章 Flow & LP
(随机化指纹范式)    (概率工具+字典)   (数据流+空间压缩)   (降维+近似搜索,集大成)   (优化:流+LP+对偶)
                         ↓                   ↓                              ↓
                  重点复习顺序：
                  1. Chernoff Bound (02) — 所有概率分析的基础，JL 证明的核心
                  2. Max-Flow Min-Cut + Duality (05) — 优化理论基石，对偶思想贯穿整章
                  3. Johnson-Lindenstrauss (04) — 降维的理论基石
                  4. LP Relaxation & Rounding (05) — 近似算法的标准套路
                  5. LSH 框架 (04) — 近似最近邻搜索的标准工具箱
                  6. Schwartz-Zippel (01) — 多项式方法的根基
                  7. Count-Min Sketch (03) — 工业界最常用的 sketch
                  8. γ-net argument (04) — 理解"有限覆盖无限"的关键技巧
```

## 学习进度

- [x] 01-Fingerprinting
- [x] 02-Hashing
- [x] 03-Sketching
- [x] 04-Dimensionality Reduction
- [ ] 05-Flow & LP
