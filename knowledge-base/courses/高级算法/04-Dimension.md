---
title: "Dimensionality Reduction — 降维、JL 引理与近似最近邻"
course: "高级算法"
tags: ["降维", "Johnson-Lindenstrauss", "LSH", "OSE", "FJLT", "近似最近邻", "高维数据", "度量空间"]
created: 2026-05-18
source: "Dimension.pdf"
status: reviewed
related: ["02-Hashing", "03-Sketching"]
chapter: 4
---

## 一句话总结

Johnson-Lindenstrauss 定理是降维的基石：n 个 d 维点可以嵌入到仅 $O(\epsilon^{-2}\log n)$ 维，所有 pairwise 距离只变 $(1\pm\epsilon)$。本章从此定理出发，展开为三个实用框架——LSH（近似近邻搜索）、FJLT（快速变换）、OSE（子空间嵌入）——最终形成从理论到工程落地的完整管线。

---

## 前置知识：度量空间、维度与"维度灾难"

### 什么是度量空间？

**度量空间** $(X, \text{dist})$ 由一个集合 X 和一个距离函数 $\text{dist}: X \times X \to \mathbb{R}_{\ge 0}$ 组成，满足：
1. **非负性**：$\text{dist}(x,y) \ge 0$，且 $\text{dist}(x,y)=0 \iff x=y$
2. **对称性**：$\text{dist}(x,y) = \text{dist}(y,x)$
3. **三角不等式**：$\text{dist}(x,z) \le \text{dist}(x,y) + \text{dist}(y,z)$

本章涉及的度量空间：
- **欧氏空间** $(\mathbb{R}^d, \|\cdot\|_2)$：$\|x-y\|_2 = \sqrt{\sum (x_i-y_i)^2}$
- **汉明空间** $(\{0,1\}^d, \text{dist}_H)$：$\text{dist}_H(x,y) = \#\{i : x_i \neq y_i\}$（不同比特位数）

### 范数：向量的"长度"

本章大量使用 $\|\cdot\|$ 符号。**范数（norm）** 是度量单个向量大小的函数，满足：
1. **非负性**：$\|x\| \ge 0$，且 $\|x\|=0 \iff x=0$
2. **齐次性**：$\|\alpha x\| = |\alpha| \cdot \|x\|$
3. **三角不等式**：$\|x+y\| \le \|x\| + \|y\|$

范数和距离的关系：在欧氏空间中 $\text{dist}(x,y) = \|x-y\|$。范数是单向量长度，距离是两向量差的范数。

本章涉及的范数：

| 符号 | 名称 | 定义 | 直觉 |
|------|------|------|------|
| $\|x\|_2$ | 欧氏范数 / $\ell_2$ | $\sqrt{\sum x_i^2}$ | 平常说的"长度"，勾股定理 |
| $\|x\|_2^2$ | 欧氏范数的平方 | $\sum x_i^2$ | JL 证明中大量出现（免去根号） |
| $\|x\|_{\infty}$ | 最大范数 / $\ell_{\infty}$ | $\max_i |x_i|$ | 绝对值最大的坐标 |

**阅读笔记时的快速指南**：
- $\|Au\|_2^2$ 展开就是 $\sum_i (Au)_i^2$，即向量 Au 各坐标的平方和
- JL 定理写 $\|Ax-Ay\|_2^2 = (1\pm\epsilon)\|x-y\|_2^2$，意思是映射后两点距离的平方保持在原距离平方的 $(1\pm\epsilon)$ 倍
- FJLT 中 $\|y\|_{\infty}$ 用于刻画向量的"峰值"——所有坐标中最大的那个

### 维度的本质

在算法语境中，"维度 d"不只是一个数字，它直接决定了计算代价：
- 两个 d 维向量的距离计算：$O(d)$ 时间
- n 个点的 pairwise 距离：$O(n^2 d)$ 时间
- 精确最近邻搜索：维度高时，已知的确定性数据结构要么空间超多项式，要么时间超多项式

**维度灾难（Curse of Dimensionality）**：当 $d \gg \log n$ 时，猜想精确 NNS 需要 $\text{super-poly}(n)$ 空间或 $\text{super-poly}(d)$ 时间。这不是常数能救的——高维空间的几何直觉彻底失效（比如单位球的体积集中在表面、随机点之间几乎等距）。

### 降维问题的形式化

**输入**：n 个 d 维点 $x_1,...,x_n \in \mathbb{R}^d$
**输出**：n 个 k 维点 $y_1,...,y_n \in \mathbb{R}^k$（$k \ll d$），使得 $\forall i,j$：
$$(1-\epsilon)\|x_i - x_j\| \le \|y_i - y_j\| \le (1+\epsilon)\|x_i - x_j\|$$

这里的 $\forall i,j$ 是"对**所有** $i$ 和 $j$"——即 n 个点中任取两个构成的**所有 $n(n-1)/2$ 对（pairwise）** 距离都要被保持。pairwise = 两两之间、成对地。

**核心问题**：k 能有多小？嵌入需要多快？

### Metric Embedding 视角

更一般地，**度量嵌入**是从 $(X, d_X)$ 到 $(Y, d_Y)$ 的映射 $\phi$，其**失真（distortion）** $\alpha$ 定义为满足下式的最小值：
$$\forall x_1,x_2 \in X: d_X(x_1,x_2) \le d_Y(\phi(x_1),\phi(x_2)) \le \alpha \cdot d_X(x_1,x_2)$$

JL 定理本质上说：n 个点的任意 d 维度量空间可以以 $(1+\epsilon)$ 失真嵌入到 $O(\epsilon^{-2}\log n)$ 维欧氏空间。这是一个关于"度量空间的压缩极限"的深刻结论。

---

## 知识地图

```
Metric Embedding（度量空间 + 失真定义）
       ↓
Johnson-Lindenstrauss Theorem
  "n 点可嵌入 O(ε⁻² log n) 维，距离保持 (1±ε)"
  三种构造：Gaussian / Random Subspace / ±1
       ↓
  ┌────┴────────────────────────────┐
  ↓                                  ↓
Nearest Neighbor Search           Linear Regression
  维度灾难 → 近似 + 随机化           Sketch-and-Solve
  ↓                                  ↓
Hamming Space JL                  OSE（子空间嵌入）
  Bernoulli(p) 矩阵                γ-net argument
  s = (3/8 - 2^{-(c+2)})k           m = O(d/ε²)
  ↓                                  ↓
LSH 框架                           Count Sketch OSE
  (r,cr,p,q)-LSH                   列密度排序 + 分解分析
  Tensorization: p^k, q^k           m = Θ(d²/ε²δ)
  ρ = log p / log q
  Space O(n^{1+ρ}), Time O(n^ρ log n)
       ↓
Fast JL Transform (FJLT)
  Π = SHD/√m
  Hadamard + Rademacher (Khintchine)
  O(d log d) 时间
```

---

## 核心概念

### 1. Johnson-Lindenstrauss 定理 — 降维的理论基石

#### 1.1 问题：降维的极限在哪里？

给定 n 个任意 d 维欧氏空间中的点。我们想把它们映射到 k 维，保持所有 pairwise 距离在 $(1\pm\epsilon)$ 倍以内。k 最小能是多少？

**直觉上的猜测**：可能依赖于 d（原始维度）？可能依赖于点集的"几何复杂度"？

**JL 定理（1984）的惊人回答**：$k = O(\epsilon^{-2}\log n)$，**与原始维度 d 无关**。一百万维的数据只需约 $O(\log n)$ 维就能保持距离！

#### 1.2 定理陈述

$\forall 0 < \epsilon < 1$，对任意 d 维空间中 n 个点的集合 S，存在线性映射 $A \in \mathbb{R}^{k \times d}$（$k = O(\epsilon^{-2}\log n)$），使得 $\forall x,y \in S$：
$$(1-\epsilon)\|x-y\|_2^2 \le \|Ax-Ay\|_2^2 \le (1+\epsilon)\|x-y\|_2^2$$

**概率方法**：一个随机的 A 以高概率（$\ge 1 - O(1/n)$）满足条件。这意味着不仅存在这样的映射，而且可以**随机生成**。

**具体例子**：假设有 n=1000 张图像，每张用 d=10⁶ 维特征向量表示。取 $\epsilon=0.1$（允许 10% 距离误差）：
- JL 定理说只需 $k \approx \frac{\ln 1000}{0.1^2} \approx 690$ 维
- 从 1,000,000 维压到 690 维——减少了 99.93%
- 任意两张图的距离（相似度）变化不超过 10%
- k **不依赖** d=10⁶！即使 d 涨到 10⁹ 维，k 仍是 ~690

三种经典构造：
1. **Gaussian**（Indyk-Motwani）：$A_{ij} \sim \mathcal{N}(0, 1/k)$ i.i.d.

> **记号说明**：$\mathcal{N}$ 是**正态分布**（Normal / Gaussian distribution）的标准数学记号。$\mathcal{N}(\mu, \sigma^2)$ 表示均值为 $\mu$、方差为 $\sigma^2$ 的正态分布。所以 $\mathcal{N}(0, 1/k)$ 读作"均值为 0、方差为 $1/k$ 的正态分布"——采样值大多集中在 0 附近，标准差为 $1/\sqrt{k}$。$\sim$ 表示"服从"，i.i.d. 表示"独立同分布"。

2. **Random Subspace**（原始 JL / Dasgupta-Gupta）：A 的行是均匀随机 k 维子空间的正交基
3. **±1 entries**（Achlioptas）：$A_{ij} \in \{-1/\sqrt{k}, +1/\sqrt{k}\}$ 均匀随机

#### 1.3 Gaussian JL 的完整证明

**问题**：JL 定理声称 $k = O(\epsilon^{-2}\log n)$ 维就够。但凭什么？我们需要证明一个**随机**的 $k \times d$ 高斯矩阵确实能以高概率保持所有 pairwise 距离。

**思路**：整条证明分五步走——(1) 把任意一对点的问题简化成"单位向量经随机投影后长度是否接近 1"；(2) 分析投影后单个坐标的分布；(3) 发现 k 个坐标的平方和服从卡方分布；(4) 用 Chernoff bound 证明它高度集中在期望 1 附近；(5) Union bound 覆盖所有 $n^2$ 对点。核心技巧只有一个：**Markov 不等式 + 指数变换**把尾概率从多项式压到指数级。

**构造**：$A \in \mathbb{R}^{k \times d}$，每个元素独立从 $\mathcal{N}(0, 1/k)$ 采样。

**第 1 步：归约到单位向量**

令 $u = x - y$。只需证对任意单位向量 $u \in \mathbb{R}^d$（$\|u\|_2 = 1$），$\|Au\|_2^2 \approx 1$。

因为如果所有单位向量的范数都保持，那么任意 $x-y$ 的范数也保持（差一个 $\|x-y\|^2$ 的缩放）。

> **矩阵与向量的具体含义**：$A$ 是 $k \times d$ 矩阵（k 行 d 列），$A_{ij}$ 是第 i 行第 j 列的**一个元素**（标量）。$u$ 是 d 维列向量。$Au$ 是矩阵左乘向量——A 作为从 $\mathbb{R}^d$ 到 $\mathbb{R}^k$ 的**线性映射**，把 d 维的 u 变成 k 维的输出向量。$(Au)_i = \sum_{j=1}^d A_{ij}u_j$ 就是这个输出向量的第 i 个分量，即 A 的第 i 行与 u 的内积。

**第 2 步：$(Au)_i$ 的分布**

$$(Au)_i = \sum_{j=1}^d A_{ij} u_j$$

每个 $A_{ij} \sim \mathcal{N}(0, 1/k)$ 独立（独立 = 一个取什么值不影响另一个的分布）。**高斯分布的核心性质：独立高斯之和仍是高斯，均值相加、方差相加。** 每一项 $A_{ij}u_j \sim \mathcal{N}(0, u_j^2/k)$（常数 $u_j$ 乘以高斯 → 均值乘 $u_j$、方差乘 $u_j^2$），d 项相加：
$$(Au)_i \sim \mathcal{N}\left(0, \sum_j \frac{u_j^2}{k}\right) = \mathcal{N}\left(0, \frac{1}{k}\right)$$

且不同 i 的 $(Au)_i$ 互相独立（因为 A 的不同行独立）。

**第 3 步：$\|Au\|_2^2$ 的分布**

$$\|Au\|_2^2 = \sum_{i=1}^k (Au)_i^2$$

k 个 i.i.d. $\mathcal{N}(0, 1/k)$ 的平方和。

**缩放技巧：把 $\mathcal{N}(0, 1/k)$ 标准化。** $\mathcal{N}(0, 1/k)$ 的方差为 $1/k$（标准差 $1/\sqrt{k}$）。乘以 $\sqrt{k}$，方差变为 $k \cdot (1/k) = 1$。类比：把一根缩短的弹簧放大了 k 倍，恢复成标准长度。定义 $X_i = \sqrt{k} \cdot (Au)_i \sim \mathcal{N}(0,1)$，则 $(Au)_i = X_i/\sqrt{k}$，平方得 $(Au)_i^2 = X_i^2/k$。k 项相加：

$$\|Au\|_2^2 = \frac{1}{k} \sum_{i=1}^k X_i^2, \quad X_i \sim \mathcal{N}(0,1) \text{ i.i.d.}$$

**$\chi^2(k)$ 是什么？** k 个独立标准正态 $\mathcal{N}(0,1)$ 各自平方再求和，这个和的分布就是 $\chi^2(k)$。$\sum X_i^2 \sim \chi^2(k)$，所以 $\|Au\|_2^2 \sim \chi^2(k)/k$。

**为什么期望为 1？** 对标准正态 $X_i$，$\mathbb{E}[X_i^2] = \text{Var}(X_i) + \mathbb{E}[X_i]^2 = 1 + 0 = 1$。k 个独立相加：$\mathbb{E}[\sum X_i^2] = k$。故 $\mathbb{E}[\|Au\|_2^2] = k/k = 1$——无偏，说明随机投影在期望上既不拉伸也不压缩向量。

**从生成矩阵到目标量的完整链条：**

$$\underbrace{A_{ij} \sim \mathcal{N}(0,1/k)}_{\text{随机生成矩阵}} \;\xrightarrow{\text{第2步}}\; \underbrace{(Au)_i \sim \mathcal{N}(0,1/k)}_{\text{输出每维的分布}} \;\xrightarrow{\text{缩放}}\; \underbrace{X_i = \sqrt{k}(Au)_i \sim \mathcal{N}(0,1)}_{\text{标准化}} \;\xrightarrow{\text{平方和}}\; \underbrace{\|Au\|^2 = \frac{1}{k}\sum X_i^2 \sim \frac{\chi^2(k)}{k}}_{\text{目标量的分布}} \;\xrightarrow{\text{期望}}\; \mathbb{E}[\|Au\|^2] = 1$$

**第 4 步：Chernoff bound for χ² 分布**

对独立 $X_1,...,X_k \sim \mathcal{N}(0,1)$：
$$Pr\left[\sum X_i^2 > (1+\epsilon)k\right] < e^{-\epsilon^2 k/8}$$
$$Pr\left[\sum X_i^2 < (1-\epsilon)k\right] < e^{-\epsilon^2 k/8}$$

**证明思路**（上尾）：

**底层公式：Markov 不等式。** 对任意非负随机变量 $Z$ 和 $t > 0$：$Pr[Z > t] \le \mathbb{E}[Z]/t$。直观：如果全班平均分 60，超过 90 分的人最多占 2/3。

**应用到 $\chi^2$：** 令 $Z = e^{\lambda\sum X_i^2}$（指数输出恒 > 0，满足 Markov 非负要求），$t = e^{\lambda(1+\epsilon)k}$：

$$Pr\left[\sum X_i^2 > (1+\epsilon)k\right] = Pr\left[e^{\lambda\sum X_i^2} > e^{\lambda(1+\epsilon)k}\right] \le \frac{\mathbb{E}[e^{\lambda\sum X_i^2}]}{e^{\lambda(1+\epsilon)k}} = e^{-\lambda(1+\epsilon)k} \cdot \mathbb{E}[e^{\lambda\sum X_i^2}]$$

**拆开 $\mathbb{E}[e^{\lambda\sum X_i^2}]$：** $\sum X_i^2$ 在指数上 → $e^{\lambda\sum X_i^2} = \prod_{i=1}^k e^{\lambda X_i^2}$。$X_i$ 独立 → 乘积的期望 = 期望的乘积：

$$\mathbb{E}[\prod_{i=1}^k e^{\lambda X_i^2}] = \prod_{i=1}^k \mathbb{E}[e^{\lambda X_i^2}] = \mathbb{E}[e^{\lambda X_i^2}]^k$$

所有 $X_i$ 同分布，每个期望相等，直接写成 k 次方。

**为什么要绕这个弯？** 直接用 Markov 对 $\sum X_i^2$ 只能得到 $1/(1+\epsilon)$ 级别的弱 bound。套上指数函数 $e^{\lambda(\cdot)}$ 后，$\lambda$ 变成可调参数——选最优的 $\lambda$，bound 从多项式级变成指数级衰减 $e^{-\epsilon^2 k/8}$。这就是 **Chernoff 技巧的核心：Markov + MGF（矩母函数）+ 参数调优 = 指数级紧的尾概率**。这个模式在全书四章中反复出现（伯努利 Chernoff、Count Sketch 分析、LSH 碰撞概率）。

对 $X \sim \mathcal{N}(0,1)$，$\mathbb{E}[e^{\lambda X^2}] = 1/\sqrt{1-2\lambda}$（对 $\lambda < 1/2$）。所以：
$$\le e^{-\lambda(1+\epsilon)k} \cdot (1-2\lambda)^{-k/2}$$

取 $\lambda = \epsilon/(2(1+\epsilon))$，代入化简得 $e^{-\epsilon^2 k/8}$。

**第 5 步：Union bound over all pairs**

对一对 $(x,y)$，令 $u = (x-y)/\|x-y\|_2$：
$$Pr\left[\big| \|A(x-y)\|_2^2 - \|x-y\|_2^2 \big| > \epsilon \|x-y\|_2^2\right] < 2e^{-\epsilon^2 k/8}$$

取 $k = O(\epsilon^{-2}\log n)$，这条概率 $< 1/n^3$。Union bound 过所有 $O(n^2)$ 对：
$$Pr[\text{任何一对失败}] \le \binom{n}{2} \cdot \frac{1}{n^3} = O\left(\frac{1}{n}\right)$$

所以 w.h.p.（with high probability = 以高概率，失败概率 $\le 1/\text{poly}(n)$，即"几乎一定对"）所有 pairwise 距离都被保持。∎

**关键总结**：JL 证明的四个步骤是 (1) 归约到单位向量 → (2) 分析单坐标的高斯分布 → (3) 发现 $\|Au\|^2$ 服从缩放后的 χ² 分布 → (4) Chernoff bound 压到尾概率指数小 → (5) Union bound 覆盖所有点对。

#### 1.4 Random Subspace JL 的证明（对称性论证）

**问题**：Gaussian JL 用满的高斯矩阵，每个元素都是实数，矩阵乘法 $O(kd)$。有没有更"几何"的做法？原始 JL 论文的做法是——不乘以矩阵，而是把点投影到一个**随机方向的 k 维平面**上。

**场景**：想象你在 d=3 维空间里有 n 个点。Random Subspace JL 说——随机转一个 k=2 维平面（像随机扔一张纸在三维空间里），把所有点垂直投影到这张纸上，点之间的距离几乎不变。这比 Gaussian JL 更直观——它是在做"随机角度的拍照"。

**思路**：直接分析"固定向量在随机平面上的投影长度"很难——平面是随机的，方向是固定的。但有一个巧妙的对称性：固定向量在随机平面上的投影长度，和随机向量在固定平面上的投影长度，**概率分布完全一样**。这就把问题变成了更容易分析的形式。

**构造**：A 的行是 k 个正交单位向量，构成 $\mathbb{R}^d$ 的均匀随机 k 维子空间。等价于将点投影到随机 k 维子空间。

**核心洞察**：球对称性 → 固定方向在随机子空间上的投影长度，与随机方向在固定子空间上的投影长度，是**同分布的**。

形式化：对任意固定单位向量 u，$\|Au\|_2$ 的分布等同于取 d 维均匀随机单位向量 $Y = (Y_1,...,Y_d)$ 的前 k 个坐标的范数 $\sqrt{Y_1^2 + \cdots + Y_k^2}$。

**证明路线**：

1. 生成均匀随机单位向量 Y：采样 i.i.d. $X_1,...,X_d \sim \mathcal{N}(0,1)$，令 $Y = X/\|X\|_2$。

**为什么高斯能生成均匀球面分布？** d 维标准高斯向量的**密度函数（density / PDF）**为：

$$f(x) = \prod_{i=1}^d \frac{1}{\sqrt{2\pi}} e^{-x_i^2/2} = (2\pi)^{-d/2} e^{-\|x\|_2^2/2}$$

密度不是概率本身（连续变量在某点的概率恒为 0），而是描述"在该点附近出现的相对可能性"——对一段区间积分才得到概率。

关键洞察：密度只依赖于 $\|x\|_2^2$（离原点的距离），与方向无关。同一个球面上所有点的密度相等 → **球对称（spherically symmetric）**。标准化 $X/\|X\|_2$ 后，方向被均匀分布——因为高斯不偏爱任何方向，球面上每个方向"出生概率"相等。这保证了随机子空间是真正"均匀随机"的。

2. 所以 $\|Au\|_2^2$ 与 $\sum_{i=1}^k X_i^2 / \sum_{i=1}^d X_i^2$ 同分布。

3. 需要证明这个比率集中在 $k/d$ 附近：
$$Pr\left[\frac{\sum_{i=1}^k X_i^2}{\sum_{i=1}^d X_i^2} > (1+\epsilon)\frac{k}{d}\right] < \frac{1}{2n^3}$$

**为什么是 $k/d$？** 均匀随机向量 Y 的每个坐标"平均约 $1/d$ 的平方范数"。前 k 个坐标的平方和，自然集中在总平方和的 $k/d$。Random Subspace 中的缩放因子 $\sqrt{d/k}$ 正是为了"校准"回原来的长度——投影后的平方范数约为 $k/d$，乘以 $d/k$ ≈ 恢复为 1（无偏）。

**代数变形：** 比率不好直接处理——分子分母都含随机变量。技巧是**交叉相乘**把比率不等式变成线性不等式。设 $S_1 = \sum_{i=1}^k X_i^2$（前 k 个坐标）、$S_2 = \sum_{i=k+1}^d X_i^2$（后 d-k 个坐标）。比率 > $(1+\epsilon)k/d$，交叉相乘：

$$\frac{S_1}{S_1 + S_2} > (1+\epsilon)\frac{k}{d} \iff S_1 \cdot d > (1+\epsilon)k(S_1 + S_2)$$
$$\iff dS_1 - (1+\epsilon)kS_1 - (1+\epsilon)kS_2 > 0$$
$$\iff (d - (1+\epsilon)k)S_1 - (1+\epsilon)kS_2 > 0$$

等价于：
$$Pr\left[(d - (1+\epsilon)k)\sum_{i=1}^k X_i^2 - (1+\epsilon)k\sum_{i=k+1}^d X_i^2 > 0\right] < \frac{1}{2n^3}$$

**物理直觉：** $S_1$ 的系数 $(d-(1+\epsilon)k)$ 是正是负取决于 k 和 d 的关系。当期望比率是 $k/d$ 时，若 k 偏离期望，$S_1$ "太大"意味着上尾事件——这里正化的是 $S_1$ 与 $S_2$ 的加权差，捕捉了比率偏离期望的方向和幅度。

4. 这是一个"两个 $\chi^2$ 变量加权差 > 0"的事件。用 **Markov + MGF**（和 Gaussian JL 第 4 步同一套路）。

**4.1 定义与变量设定**

设 $S_1 = \sum_{i=1}^k X_i^2 \sim \chi^2(k)$，$S_2 = \sum_{i=k+1}^d X_i^2 \sim \chi^2(d-k)$。$S_1$ 和 $S_2$ 独立（它们用了不重叠的 $X_i$）。为简化记号，令：

$$a = d - (1+\epsilon)k, \qquad b = (1+\epsilon)k$$

则事件变为 $a S_1 - b S_2 > 0$。对 $\epsilon < 1$ 且 $k \ll d$ 的典型情况，$a > 0$，$b > 0$。

**4.2 套指数 + Markov（Chernoff 起步）**

引入参数 $\lambda > 0$：

$$Pr[a S_1 - b S_2 > 0] = Pr\left[e^{\lambda(a S_1 - b S_2)} > e^0\right] = Pr\left[e^{\lambda(a S_1 - b S_2)} > 1\right]$$

由 Markov 不等式（非负随机变量 $Z = e^{\lambda(a S_1 - b S_2)}$，$t = 1$）：

$$Pr[a S_1 - b S_2 > 0] \le \mathbb{E}\left[e^{\lambda(a S_1 - b S_2)}\right] = \mathbb{E}\left[e^{\lambda a S_1} \cdot e^{-\lambda b S_2}\right]$$

**4.3 独立性拆分**

$S_1$ 只依赖 $X_1, \dots, X_k$，$S_2$ 只依赖 $X_{k+1}, \dots, X_d$。两群不重叠 → $S_1 \perp S_2$。乘积的期望 = 期望的乘积：

$$\mathbb{E}\left[e^{\lambda a S_1} \cdot e^{-\lambda b S_2}\right] = \mathbb{E}\left[e^{\lambda a S_1}\right] \cdot \mathbb{E}\left[e^{-\lambda b S_2}\right]$$

**4.4 $\chi^2$ 分布的 MGF（矩母函数）**

**什么是 MGF？** $\mathbb{E}[e^{tX}]$ 称为随机变量 $X$ 的矩母函数。它为什么有用？因为指数函数把加法变成乘法——$\mathbb{E}[e^{t(X+Y)}] = \mathbb{E}[e^{tX}]\mathbb{E}[e^{tY}]$（当 X, Y 独立时）。这把"和的概率分析"变成了"乘积的代数计算"。Chernoff 技巧本质上就是——用 Markov 不等式，把尾概率 bound 成 MGF 的表达式，然后选最优 t。

标准正态 $X \sim \mathcal{N}(0,1)$ 的 $X^2$ 的 MGF 为：

$$\mathbb{E}[e^{t X^2}] = \int_{-\infty}^{\infty} e^{t x^2} \cdot \frac{1}{\sqrt{2\pi}} e^{-x^2/2} \, dx = \frac{1}{\sqrt{2\pi}} \int_{-\infty}^{\infty} e^{-x^2(1-2t)/2} \, dx = \frac{1}{\sqrt{1-2t}}$$

推导：这是方差为 $1/(1-2t)$ 的高斯积分。令 $u = x\sqrt{1-2t}$，$dx = du/\sqrt{1-2t}$，$\frac{1}{\sqrt{2\pi}} \int e^{-u^2/2} du = 1$（标准正态 PDF 积分为 1）。要求 $1-2t > 0$ 即 $t < 1/2$，否则积分发散。

对 $S_1 = \sum_{i=1}^k X_i^2$（k 个独立同分布 $X_i^2$ 之和）：

$$\mathbb{E}[e^{\lambda a S_1}] = \mathbb{E}\left[\prod_{i=1}^k e^{\lambda a X_i^2}\right] = \prod_{i=1}^k \mathbb{E}[e^{\lambda a X_i^2}] = \prod_{i=1}^k \frac{1}{\sqrt{1 - 2\lambda a}} = (1 - 2\lambda a)^{-k/2}$$

要求 $\lambda a < 1/2$（MGF 定义域）。

对 $S_2$（注意指数上是 $-\lambda b$，为负值，自动满足 $-\lambda b < 1/2$）：

$$\mathbb{E}[e^{-\lambda b S_2}] = \prod_{i=k+1}^d \frac{1}{\sqrt{1 + 2\lambda b}} = (1 + 2\lambda b)^{-(d-k)/2}$$

代回得到 $\lambda$ 参数化的上界：

$$Pr[\text{上尾}] \le \underbrace{(1 - 2\lambda a)^{-k/2}}_{\text{来自 }S_1} \cdot \underbrace{(1 + 2\lambda b)^{-(d-k)/2}}_{\text{来自 }S_2}$$

约束：$0 < \lambda < \frac{1}{2a} = \frac{1}{2(d-(1+\epsilon)k)}$。

**4.5 选出最优 $\lambda$ — 微积分求极值**

现在我们有了一个含参数 $\lambda$ 的上界。**不同的 $\lambda$ 给出不同松紧的 bound**——$\lambda$ 太大会让 MGF 爆炸，太小又浪费了指数的压制力。我们要找到使 bound **最小**（最紧）的那个 $\lambda$。这就是一个求函数极值的问题——对 $\lambda$ 求导、令导数为零、解出最优 $\lambda$。

令 $f(\lambda) = -\frac{k}{2}\ln(1-2\lambda a) - \frac{d-k}{2}\ln(1+2\lambda b)$。目标是最小化 $f(\lambda)$（使 bound 最紧）。对 $\lambda$ 求导，令 $f'(\lambda) = 0$：

$$f'(\lambda) = -\frac{k}{2} \cdot \frac{-2a}{1-2\lambda a} - \frac{d-k}{2} \cdot \frac{2b}{1+2\lambda b} = \frac{ka}{1-2\lambda a} - \frac{(d-k)b}{1+2\lambda b} = 0$$

$$\frac{ka}{1-2\lambda a} = \frac{(d-k)b}{1+2\lambda b}$$

交叉相乘：$ka(1+2\lambda b) = (d-k)b(1-2\lambda a)$。展开：

$$ka + 2\lambda kab = (d-k)b - 2\lambda(d-k)ab$$

含 $\lambda$ 项移到左边：$2\lambda kab + 2\lambda(d-k)ab = (d-k)b - ka$。左边 $2\lambda ab(k + d - k) = 2\lambda abd$：

$$2\lambda abd = (d-k)b - ka$$

$$\lambda = \frac{(d-k)b - ka}{2abd}$$

**4.6 代入 $a, b$ 化简 $\lambda$**

代入 $a = d - (1+\epsilon)k$，$b = (1+\epsilon)k$：

分子：$(d-k)(1+\epsilon)k - k(d-(1+\epsilon)k)$

$= kd(1+\epsilon) - k^2(1+\epsilon) - kd + k^2(1+\epsilon)$

$= kd(1+\epsilon) - kd$

$= kd\epsilon$

分母：$2 \cdot (d-(1+\epsilon)k) \cdot (1+\epsilon)k \cdot d = 2kd \cdot (1+\epsilon)(d-(1+\epsilon)k)$

$$\boxed{\lambda = \frac{kd\epsilon}{2kd(1+\epsilon)(d-(1+\epsilon)k)} = \frac{\epsilon}{2(1+\epsilon)(d-(1+\epsilon)k)}}$$

**4.7 代回求 bound**

先算 $2\lambda a$：

$$2\lambda a = 2 \cdot \frac{\epsilon}{2(1+\epsilon)(d-(1+\epsilon)k)} \cdot (d-(1+\epsilon)k) = \frac{\epsilon}{1+\epsilon}$$

$$1 - 2\lambda a = 1 - \frac{\epsilon}{1+\epsilon} = \frac{1}{1+\epsilon}$$

$$(1 - 2\lambda a)^{-k/2} = (1+\epsilon)^{k/2}$$

再算 $2\lambda b$：

$$2\lambda b = 2 \cdot \frac{\epsilon}{2(1+\epsilon)(d-(1+\epsilon)k)} \cdot (1+\epsilon)k = \frac{\epsilon k}{d-(1+\epsilon)k}$$

$$1 + 2\lambda b = 1 + \frac{\epsilon k}{d-(1+\epsilon)k} = \frac{d-(1+\epsilon)k + \epsilon k}{d-(1+\epsilon)k} = \frac{d-k}{d-(1+\epsilon)k}$$

$$(1 + 2\lambda b)^{-(d-k)/2} = \left(\frac{d-k}{d-(1+\epsilon)k}\right)^{-(d-k)/2} = \left(1 - \frac{\epsilon k}{d-k}\right)^{(d-k)/2}$$

总 bound：

$$Pr[\text{上尾}] \le (1+\epsilon)^{k/2} \cdot \left(1 - \frac{\epsilon k}{d-k}\right)^{(d-k)/2}$$

**4.8 用对数不等式收紧到 $e^{-\epsilon^2 k/4}$**

取对数：

$$\ln Pr \le \frac{k}{2}\ln(1+\epsilon) + \frac{d-k}{2}\ln\left(1 - \frac{\epsilon k}{d-k}\right)$$

用泰勒上下界（比 $1+x \le e^x$ 更紧）：$\ln(1+x) \le x - \frac{x^2}{2} + \frac{x^3}{3}$（$x > -1$），$\ln(1-x) \le -x - \frac{x^2}{2}$（$0 \le x < 1$）。

$$\frac{k}{2}\ln(1+\epsilon) \le \frac{k}{2}\left(\epsilon - \frac{\epsilon^2}{2} + \frac{\epsilon^3}{3}\right)$$

$$\frac{d-k}{2}\ln\left(1 - \frac{\epsilon k}{d-k}\right) \le \frac{d-k}{2}\left(-\frac{\epsilon k}{d-k} - \frac{\epsilon^2 k^2}{2(d-k)^2}\right) = -\frac{\epsilon k}{2} - \frac{\epsilon^2 k^2}{4(d-k)}$$

加起来：$\frac{k\epsilon}{2}$ 和 $-\frac{k\epsilon}{2}$ 抵消：

$$\ln Pr \le -\frac{k\epsilon^2}{4} + \frac{k\epsilon^3}{6} - \frac{\epsilon^2 k^2}{4(d-k)}$$

对小的 $\epsilon$，$\epsilon^3$ 项被 $\epsilon^2$ 主导，且 $\frac{k}{d-k} \approx \frac{k}{d}$ 很小。保守取主导项：

$$\ln Pr \le -\frac{\epsilon^2 k}{4}$$

$$\boxed{Pr[\text{上尾}] \le e^{-\epsilon^2 k / 4}}$$

**4.9 下尾 + Union bound + 收尾**

下尾 $Pr\left[\frac{S_1}{S_1+S_2} < (1-\epsilon)\frac{k}{d}\right]$ 的推导对称——Chernoff 方向反过来，最优点 $\lambda = \frac{\epsilon}{2(1-\epsilon)(d-(1-\epsilon)k)}$，得同样 bound $\le e^{-\epsilon^2 k/4}$。

对固定一对点，上下尾合计 $\le 2e^{-\epsilon^2 k/4}$。取 $k = \frac{8}{\epsilon^2} \cdot 3\ln n = O(\epsilon^{-2}\log n)$：

$$2e^{-\epsilon^2 k/4} = 2e^{-6\ln n} = \frac{2}{n^6} < \frac{1}{n^3}$$

n 个点共 $\binom{n}{2} \le n^2/2$ 对，Union bound：

$$Pr[\text{任何一对失败}] \le \frac{n^2}{2} \cdot \frac{1}{n^3} = \frac{1}{2n} = O\left(\frac{1}{n}\right)$$

w.h.p. 所有 pairwise 距离保持。$\square$

**推导主干回顾：**

```
比值 → 线性组合 → Markov + 指数 → MGF 乘积
    → 最优化 λ（微积分 f'(λ)=0）→ 代入化简
    → 泰勒收紧 → e^{-ε²k/4} → k = O(ε^{-2} log n) → Union bound → w.h.p.
```

和 Gaussian JL 第 4 步的核心思想完全一致：**Markov + MGF + 参数最优化 + Union bound**。区别只在于这里处理的是两个 $\chi^2$ 变量的比值，所以 MGF 以乘积形式出现，需要微积分找到使乘积最小的 $\lambda$。

**证明流程总结：**
```
固定单位向量 u, 随机 k 维子空间 A
    ↓ 球对称性（对偶）
均匀随机单位向量 Y, 固定前 k 坐标
    ↓ 高斯表示
Y = X/∥X∥, Xi ∼ N(0,1) i.i.d.
    ↓
∥Au∥² 与 Σᵏᵢ₌₁ Xᵢ² / Σᵈᵢ₌₁ Xᵢ² 同分布
    ↓
需要证比率集中在 k/d 附近
    ↓ 代数变形
加权 χ² 差 > 0 的尾概率
    ↓ Markov + MGF
≤ e^{-ε²k/4} < 1/n³
    ↓ Union bound
w.h.p. 所有 pairwise 距离保持
```

**和 Gaussian JL 的对比**：
- Gaussian：需要 $O(kd)$ 时间做矩阵乘法（dense 矩阵）
- Random Subspace：需要先将数据投影到随机子空间（若用 Gram-Schmidt 正交化需 $O(kd^2)$）
- 两者理论上的目标维度 k 量级相同，但计算效率不同

#### 1.5 ±1 JL（Tug-Of-War）与 Count Sketch 的联系

**问题**：Gaussian JL 每个矩阵元素都得采样一次正态分布——全是浮点数。矩阵乘法 $A \cdot x$ 要做 $kd$ 次浮点乘法 + 加法。能不能更快？比如只用 +1 和 -1 这种整数？

**思路**：Achlioptas（2001）的惊人发现——矩阵元素不必是高斯，离散的 ±1（均匀随机）就能达到同样的 JL 保证。分析工具从"高斯 + 卡方"换成"有界随机变量和 + Hoeffding 不等式"。更深刻的理论依据是：±1 随机向量的偶数阶矩被高斯控制，所以它的尾概率不会比高斯更差。

##### 1.5.1 ±1 JL 是什么？

Gaussian JL 矩阵每个元素是正态采样——浮点数，计算慢。Achlioptas（2001）发现：**不需要高斯，用离散的 ±1 就行。**

**构造：** $A \in \mathbb{R}^{k \times d}$，每个元素 $A_{ij}$ 以 1/2 概率取 $+1/\sqrt{k}$，1/2 概率取 $-1/\sqrt{k}$。只有两个值、等概率、独立。

$$(Au)_i = \frac{1}{\sqrt{k}}\sum_{j=1}^d A_{ij} u_j, \quad A_{ij} \in \{+1, -1\} \text{ 均匀随机}$$

为什么叫 **Tug-Of-War（拔河）**？

每个坐标 $u_j$ 随机站队——$A_{ij}=+1$ 时加入"正队"（贡献 $+u_j$），$A_{ij}=-1$ 时加入"负队"（贡献 $-u_j$）。d 个坐标随机分配 → 正队总力量 vs 负队总力量 = 绳子往哪边偏。除以 $\sqrt{k}$ = 归一化。

**和 Gaussian JL 的核心区别：**

| | Gaussian JL | ±1 JL (Tug-Of-War) |
|------|------------|-------------------|
| 矩阵元素 | 浮点 $\mathcal{N}(0,1/k)$ | 离散 $\pm 1/\sqrt{k}$ |
| 计算方式 | 浮点乘法 + 加法 | **翻转符号 + 加法**（无浮点乘法） |
| 数学分析 | $\chi^2$ 分布 + 高斯 Chernoff | 有界随机变量和 + Hoeffding / Khintchine |
| JL 保证 | 同样：$k = O(\epsilon^{-2}\log n)$ | 同样：$k = O(\epsilon^{-2}\log n)$ |
| 物理直觉 | 随机微小拉伸/压缩的净效应 | 随机站队拔河的净拉力 |

##### 1.5.2 为什么 ±1 能替代高斯？— 两个互补的解释

**解释一：Hoeffding 不等式（有界随机变量版 Chernoff）**

$(Au)_i = \frac{1}{\sqrt{k}}\sum_{j=1}^d A_{ij}u_j$ 是 d 个独立随机变量的和。每个 $A_{ij}u_j$ 取值在 $[-|u_j|/\sqrt{k}, +|u_j|/\sqrt{k}]$ 内有界。

Hoeffding 不等式：d 个独立、零均值、有界 $[a_j, b_j]$ 的随机变量和 S，对任意 $t > 0$：

$$Pr[|S| \ge t] \le 2\exp\left(-\frac{2t^2}{\sum_j (b_j - a_j)^2}\right)$$

应用到 $S = (Au)_i$：$a_j = -|u_j|/\sqrt{k}$，$b_j = +|u_j|/\sqrt{k}$，跨度 $b_j-a_j = 2|u_j|/\sqrt{k}$。

$$\sum_j (b_j-a_j)^2 = \frac{4}{k}\sum_j u_j^2 = \frac{4}{k}$$

代入：

$$Pr[|(Au)_i| \ge t] \le 2\exp\left(-\frac{kt^2}{2}\right)$$

这和 Gaussian 情况下的尾概率结构完全一致（只差常数因子）。后续平方和 $\|Au\|^2 = \sum (Au)_i^2$ 再用一次 Chernoff（或直接用 Khintchine 不等式）——和 Gaussian JL 第 3-4 步同一条路线，最终到同一个 $e^{-\epsilon^2 k}$ bound。

**解释二：偶数阶矩被高斯控制（课件第 32-33 页）**

这是更深刻的理论依据。先解释**什么是"矩"**：随机变量 $X$ 的 k 阶矩就是 $\mathbb{E}[X^k]$——"取 k 次方再求期望"。一阶矩是均值，二阶矩和方差有关，高阶矩刻画分布的尾部有多"肥"。偶数阶矩越大 → 极端值越容易出现 → 尾概率越大。

设 r 是 d 维 ±1 均匀随机向量（每个分量独立、等概率 $\pm 1$），$Z \sim \mathcal{N}(0, I_d)$ 是 d 维标准高斯。对任意固定向量 x 和任意偶数阶矩 $2k$：

$$\mathbb{E}[\langle x, r\rangle^{2k}] \le \mathbb{E}[\langle x, Z\rangle^{2k}]$$

**逐符号解读：**
- $\langle x, r\rangle = \sum_j x_j r_j$——数据 x 与随机 ±1 向量 r 的内积（和 $(Au)_i$ 形式完全一致）
- $\langle x, Z\rangle = \sum_j x_j Z_j$——数据 x 与高斯向量 Z 的内积
- $(\cdot)^{2k}$——取 2k 次方（只考虑偶数阶矩，因为奇数是 0）

**这条不等式的含义：** 用 ±1 随机向量的所有偶数阶矩，都不超过用高斯的情况。偶数阶矩决定尾概率（矩越大 → 尾越肥 → 越容易偏离期望值）。±1 的偶数阶矩 ≤ 高斯的偶数阶矩 → ±1 的尾概率 ≤ 高斯的尾概率 → ±1 的集中性**不比 Gaussian 差**。

那就是为什么课件说"Count Sketch 的偶数阶矩被 Gaussian 控制"——Gaussian 是"尾界上界"，±1 只比 Gaussian 更集中（不容易出极端值），所以所有 Gaussian JL 的保证对 ±1 自动成立。

##### 1.5.3 三条 JL 的完整演进

```
Gaussian JL (Indyk-Motwani)
  A_ij ∼ N(0,1/k), 浮点矩阵乘法 O(kd)
  证明：χ² + 高斯 Chernoff
          ↓ 离散化（去掉浮点乘法）
±1 JL / Tug-Of-War (Achlioptas)
  A_ij ∈ {±1/√k}, 只翻转符号 + 加法，O(kd)
  证明：Hoeffding + 偶数阶矩被 Gaussian 控制
          ↓ 稀疏化（连 O(kd) 都嫌慢）
Count Sketch (第 3 章)
  Π = S·D, S 每行只有一个非零（采样）, D 是 ±1 对角
  时间 ∝ 数据非零元数
          ↓ 预均匀化（稀疏采样方差大的问题）
FJLT (本节第 5 节)
  Π = S·H·D, Hadamard 先均匀化向量，再稀疏采样
  时间 O(d log d)，d 很大时碾压前面所有
```

**它们都在保证同一件事：$k = O(\epsilon^{-2}\log n)$ 维，pairwise 距离 $(1\pm\epsilon)$ 保持。** 理论层面全等价，区别只在计算速度和工程实现上。

---

### 2. 最近邻搜索与维度灾难

#### 2.1 精确 NNS 及其在高维的困境

**问题（NNS，Nearest Neighbor Search）**：
- **输入**：n 个数据点 $y_1,...,y_n \in X$（度量空间），一个查询点 $x \in X$
- **输出**：$y_i$ 使得 $\text{dist}(x, y_i) = \min_j \text{dist}(x, y_j)$，即离 x 最近的那个数据点

**简单例子**：平面上有 {(2,3), (5,1), (8,7), (1,9)} 四个点，查询 x=(4,5)。精确 NNS 算出到所有四个点的欧氏距离——$\sqrt{8}, \sqrt{17}, \sqrt{20}, \sqrt{25}$——取最近的 (2,3)，距离 $\sqrt{8} \approx 2.83$。低维时这很简单：k-d tree 在 d=2 时可以快速剪枝，无需遍历全部 n 个点。

低维时（$d \ll \log n$）：k-d tree、Voronoi diagram 等空间分割方法有效。
高维时（$d \gg \log n$）：**维度灾难**——推测需要 super-poly(n) 空间或 super-poly(d) 时间。

**为什么高维难？** 直观：高维空间中，所有点彼此"几乎等距"（单位球体积集中在表面），空间分割方法退化为线性扫描。继续上面的例子——如果 d=10⁶ 而不是 d=2，四个点两两之间的距离几乎相等，k-d tree 的剪枝条件几乎永远不满足，退化为扫描所有 n 个点。

#### 2.2 近似近邻：用近似换效率

ANN 有两个版本——**优化版**直接找最近点，**决策版**回答"有没有近点"。决策版更基础，LSH 数据结构就是为决策版设计的，优化版通过分层调用决策版实现。

##### (c,r)-ANN 决策版的判定逻辑

**(c,r)-ANN（Approximate Near Neighbor）**：

```
查询点 x，给定半径 r，近似比 c

情况 A：存在某个数据点 y_j 满足 dist(x, y_j) ≤ r
  → 必须返回一个 y_i 满足 dist(x, y_i) ≤ c·r
  （可以是那个近点，也可以是稍远但仍在 cr 内的点）

情况 B：所有数据点距离都 > c·r
  → 必须回答 "no"（明确说没有）

中间地带（距离在 r 和 cr 之间）：
  → 随便答，答 yes 或 no 都算对
```

**直觉**：算法有两个"免责条款"——(1) 答 yes 时允许返回 c 倍远的点（近似容错），(2) 数据落在灰色地带时随便答（避免边界歧义）。两个阈值 r 和 cr 画出"一定近 / 一定远 / 灰色地带"三个区域。

##### c-ANN 优化版：从决策版到完整搜索

**c-ANN（Approximate Nearest Neighbor）**：返回 $y_i$ 满足 $\text{dist}(x, y_i) \le c \cdot \min_j \text{dist}(x, y_j)$。允许 c 倍的近似比。

##### r 的取值策略：为什么不能只取一个 r？

**核心矛盾**：你事先不知道查询点离最近数据点有多远。固定一个 r——

- 取太大 → 所有点都在 r 内，退化为"返回任意点"
- 取太小 → 所有点都在 cr 外，永远答 "no"

**解决办法**：用等比数列覆盖整个可能范围。

设数据点间的最小距离 $D_{\min} = \min_{i<j}\text{dist}(y_i,y_j)$，最大距离 $D_{\max} = \max_{i<j}\text{dist}(y_i,y_j)$。构造：

$$r \in \{D_{\min},\; c \cdot D_{\min},\; c^2 \cdot D_{\min},\; \dots,\; D_{\max}\}$$

共 $\log_c(D_{\max}/D_{\min})$ 层。对**每一层**独立建一个 $(c,r)$-ANN 结构。

**查询时**：对所有层都查一遍，收集每层返回的候选点，取真正距离最近的那个。

**代价**：如果单层用空间 s、时间 t，则总空间 $O(s \cdot \log_c R)$、总时间 $O(t \cdot \log_c R)$，其中 $R = D_{\max}/D_{\min}$。多一个对数因子——很小的代价换来覆盖任意查询距离的能力。

**一句话概括**：$(c,r)$-ANN 决策版用 r 和 cr 两个阈值画出三个区域做判定，然后通过等比数列 $r, cr, c^2r, \dots$ 覆盖所有可能的距离尺度，查遍所有层取最优——这就是从决策版到完整 c-ANN 的桥。

---

### 3. Hamming 空间中的降维 — 从欧氏到离散

#### 3.1 动机

欧氏空间 JL 需要矩阵乘法（浮点运算），在汉明空间 $\{0,1\}^d$ 中，我们想要更快的位运算。

#### 3.2 前置：GF(2) — 为什么能加速？

**GF(2)**（伽罗瓦域，Galois Field of order 2）是只有两个元素的代数系统 $\{0, 1\}$：

```
加法（XOR，mod 2）：        乘法（AND）：
0 + 0 = 0   0 + 1 = 1      0 × 0 = 0   0 × 1 = 0
1 + 0 = 1   1 + 1 = 0      1 × 0 = 0   1 × 1 = 1
```

**直觉**：加法就是"奇偶性运算"——$1+1=0$ 表示"两个奇数加起来变偶数"，只看结果是奇数(1)还是偶数(0)。减法和加法完全一样（模 2 下 $-1 \equiv 1$，即 $1-0=1$，$1-1=0$，$0-1=1$）。

**为什么需要它？** Hamming 空间是 $\{0,1\}^d$——每个坐标只有 0 或 1。在 GF(2) 上做矩阵乘法 $Ax \bmod 2$，所有运算自动变成位运算（XOR + AND），比浮点乘法快几个数量级。这就是"离散步长"背后的代数基础。

#### 3.3 Bernoulli 矩阵降维

**问题**：欧氏 JL 用稠密的高斯或 ±1 矩阵——每个输出维度都是所有 d 个输入的加权和。在 Hamming 空间 $\{0,1\}^d$ 中，能不能用**位运算**（XOR + AND）代替浮点运算？且矩阵元素只有 0/1，稀疏化后更快？

**思路**：用 Bernoulli(p) 随机矩阵 A——每个元素以概率 p 为 1，否则 0。在 GF(2) 上做 $Ax \bmod 2$，运算全是位运算。降维后把数据点按 k 位指纹存入桶中，查询时只查指纹相近的桶（半径 s 的球）。核心分析任务：调 p 和 s，让近点大概率指纹相近、远点大概率指纹不相近。

**构造**：$A \in \{0,1\}^{k \times d}$，每个条目独立 $\sim \text{Bernoulli}(p)$。在 GF(2) 上计算 $z_i = Ay_i \bmod 2$。$z_i \in \{0,1\}^k$ 是降维后的 k 位向量。

**存储结构**：对 $k$ 维汉明空间中所有可能的 $u \in \{0,1\}^k$，维护以 u 为中心、半径 s 的球 $B_s(u) = \{y_i : \text{dist}(u, z_i) \le s\}$。查询时计算 $Ax \bmod 2$，检索 $B_s(Ax)$。

空间：$O(n \cdot 2^k)$（存储所有球），查询时间：$O(kd)$（计算 Ax）。

**具体例子**：设 d=8，n=3 个数据点，降维到 k=3 位（实际应用需 k=O(log n)，这里 k=3 仅为演示计算过程）。

**数据点**：
$$a = 10110010,\quad b = 10101001,\quad c = 01010110$$

它们之间的 Hamming 距离：$\text{dist}_H(a,b)=4$，$\text{dist}_H(a,c)=4$，$\text{dist}_H(b,c)=8$。

**随机矩阵**（Bernoulli，p=0.2，3×8）：

$$A = \begin{pmatrix} 0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 & 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 & 0 & 0 & 0 & 1 \end{pmatrix}$$

A 的第 1 行只用坐标 3；第 2 行用坐标 2 和 7；第 3 行用坐标 4 和 8。

---

**预处理：为所有数据点计算 k 位"指纹"**

**a = 10110010**（位序列：$a_1$=1, $a_2$=0, $a_3$=1, $a_4$=1, $a_5$=0, $a_6$=0, $a_7$=1, $a_8$=0）：
- 第 1 行：只用 $a_3$=1 → 1
- 第 2 行：$a_2 + a_7 = 0+1 = 1$（mod 2）
- 第 3 行：$a_4 + a_8 = 1+0 = 1$（mod 2）
- → $z_a = \mathbf{111}$（桶编号 7）

**b = 10101001**（$b_1$=1, $b_2$=0, $b_3$=1, $b_4$=0, $b_5$=1, $b_6$=0, $b_7$=0, $b_8$=1）：
- 第 1 行：$b_3$=1 → 1
- 第 2 行：$b_2 + b_7 = 0+0 = 0$
- 第 3 行：$b_4 + b_8 = 0+1 = 1$
- → $z_b = \mathbf{101}$（桶编号 5）

**c = 01010110**（$c_1$=0, $c_2$=1, $c_3$=0, $c_4$=1, $c_5$=0, $c_6$=1, $c_7$=1, $c_8$=0）：
- 第 1 行：$c_3$=0 → 0
- 第 2 行：$c_2 + c_7 = 1+1 = 0$（mod 2）
- 第 3 行：$c_4 + c_8 = 1+0 = 1$
- → $z_c = \mathbf{001}$（桶编号 1）

---

**建球（Build）**：k=3 时有 $2^3=8$ 个可能的桶编号（000~111）。选定半径 s 后（取值见下文），对每个桶 u ∈ {0,1}³，将所有 $z$ 值落在 $\text{dist}_H(\cdot, u) \le s$ 范围内的数据点归入球 $B_s(u)$：

```
桶 u    B₀(u) —— s=0 时（仅精确匹配）      B₁(u) —— s=1 时（加相邻桶）
000     {}                                  {c: z_c=001 距离为1}
001     {c}                                 {c, 来自相邻桶的数据点}
010     {}                                  {}
011     {}                                  {}
100     {}                                  {}
101     {b}                                 {b}
110     {}                                  {}
111     {a}                                 {a}
```

**s=0 的含义**：只捡与查询指纹**完全一致**的桶。**s=1**：还捡 Hamming 距离 ≤1 的相邻桶。s 越大，召回率越高但候选也越多。

---

**查询（Query）**：来了查询点 $q = 10110001$。看 q 离 a 很近——逐位比对：

$$a=10110010,\quad q=10110001,\quad \text{dist}_H(a,q)=2 \quad\text{（仅第 7、8 位不同）}$$

而 $\text{dist}_H(b,q)=2$（第 4、5 位不同），$\text{dist}_H(c,q)=6$。所以 a 和 b 都是最近邻（距离均为 2），c 较远。

计算 q 的指纹：

- 第 1 行：$q_3$=1 → 1
- 第 2 行：$q_2 + q_7 = 0+0 = 0$
- 第 3 行：$q_4 + q_8 = 1+1 = 0$（mod 2）
- → $z_q = \mathbf{100}$（桶编号 4）

---

**判定**：若 s=0，$B_0(100)$ = {}（空桶），查询失败返回 "no"——错过了两个距离仅 2 的近邻。若 s=1，$B_1(100)$ = {b}（$z_b$=101 距离为 1），返回 b 满足 $\text{dist}_H(q,b)=2$。b 确实是最近邻之一（和 a 并列），所以 s=1 时判定正确。

但注意：a 同样距离为 2，却因为 $z_a$=111 离 $z_q$=100 的 Hamming 距离为 2 而落在 $B_1(100)$ 之外，被漏掉了。这恰好说明降维的哈希不是完美的——即使距离很近的点也可能因为降维后的随机性分到不同桶。增大 k 可以让近点碰撞概率 $p^k$ 足够高，$\ell = n^\rho$ 个独立哈希表进一步弥补漏检。

**这个玩具例子为什么失败？** 因为 k=3 太小了。小 k 意味着：
- 碰撞概率的集中性不够——Chernoff 尾概率还太大
- 近点 a 和 q（$\text{dist}_H=2$）在 3 行中有 2 行不同（$X=2$），远大于近点的期望 $k/4=0.75$

**实际参数会怎样？** 假设 n=10³, r=4, c=2（即区分 ≤4 和 >8 的点对）。取 $k = O(\log n) \approx 20$ 行。此时：
- 近点对的期望不碰撞行数 $\le 20/4 = 5$
- 远点对的期望不碰撞行数 $\ge (1/2-2^{-3}) \times 20 = 7.5$
- 阈值 $s = (3/8 - 2^{-4}) \times 20 = 6.25$，取整 s=6
- 单对错误概率 $< e^{-2(1/8-1/16)^2 \times 20} \approx e^{-0.31} \approx 0.73$—还是太高

继续增大到 $k=100$：单对错误概率 $< e^{-2(1/8-1/16)^2 \times 100} \approx e^{-1.56} \approx 0.21$—仍不够。课件中的分析用的是渐进记号 $k = O(\log n)$，隐藏的常数在最坏情况下需要通过精确计算才能确定。核心思路不变：k 要足够大让 Chernoff bound 把尾概率压到 $1/n^2$ 以下。

**要点**：这个例子演示了管线的**机械操作**——如何用 Bernoulli 矩阵把 d 位压成 k 位、如何建球、如何查询。概率保证依赖 $k = \Omega(\log n)$ 的渐进结论，玩具参数无法体现。

**整体管线**：
```
d 维 Hamming 数据 → Bernoulli 矩阵 A (GF(2) 乘法) → k 维位向量
                                                          ↓
                                         对每个 u ∈ {0,1}^k 建球 B_s(u)
                                                          ↓
                                         查询：算 Ax → 检 B_s(Ax) → 候选近邻
```

#### 3.4 单行的碰撞概率分析 — "活跃集"技巧

**问题**：Bernoulli(p) 矩阵的一行 $A_{i\cdot}$ 有 d 个独立元素（每个以概率 p 为 1）。对于两个数据点 x, y，这一行算出的两个哈希值 $(Ax)_i$ 和 $(Ay)_i$ 在 GF(2) 下相等的概率是多少？这个概率必须以某种方式依赖于 x 和 y 的距离——否则降维就没有"保持距离信息"可言。

**思路**：直接用 Bernoulli(p) 分析比较麻烦（每个坐标的取值有偏，p 可能很小）。换一种**等效的**生成方式：先随机圈一批"活跃坐标"（概率 2p），再在活跃坐标上均匀随机投 0/1。这样活跃坐标上的行为是完美均匀随机的，分析就简单了。

##### 3.4.1 碰撞概率公式

对一行 $A_{i\cdot}$（d 个独立 Bernoulli(p)），两个数据点 x, y 在这一行哈希值**不相等**的概率为：

$$Pr[(Ax)_i \neq (Ay)_i] = \frac{1}{2}\left(1 - (1-2p)^{\text{dist}(x,y)}\right)$$

为什么是这个公式？关键在于下面这个等效生成技巧。

##### 3.4.2 等效生成：把"有偏"矩阵变成"均匀随机 + 稀疏"

不要直接想"d 个独立 Bernoulli(p)"。换一种**完全等价**的方式生成 $A_{i\cdot}$：

```
第 1 层：每个坐标 j 独立地以概率 2p 进入"活跃集" D
        以概率 1-2p 不活跃

第 2 层：对活跃坐标 j ∈ D → A_ij 均匀随机取 0 或 1（各 1/2）
        对不活跃坐标 j ∉ D → A_ij = 0（强制为零）
```

**为什么等价？** 验证单个 $A_{ij}$：
- $Pr[A_{ij}=1] = Pr[j \in D] \cdot Pr[\text{均匀取到 }1] = 2p \times \frac{1}{2} = p$ ✓
- $Pr[A_{ij}=0] = Pr[j \notin D] + Pr[j \in D] \cdot Pr[\text{均匀取到 }0] = (1-2p) + 2p \times \frac{1}{2} = 1-p$ ✓

每个 $A_{ij}$ 独立（D 独立 + 第二层独立），所以两种生成方式的联合分布完全相同。

**这个技巧好在哪里？** 一旦活跃集 D 确定，$A_{i\cdot}$ 在 D 上的取值是**完全均匀随机**的 0/1 向量！这就把"有偏的 Bernoulli 矩阵"变成了两个独立的随机过程：(1) 先随机选一个活跃坐标子集，(2) 在活跃坐标上均匀随机投票。

##### 3.4.3 从等效生成推导碰撞概率

$(Ax)_i = \langle A_{i\cdot}, x\rangle \bmod 2$，$(Ay)_i = \langle A_{i\cdot}, y\rangle \bmod 2$。两者不相等，意味着 $A_{i\cdot}$ 在 x 和 y **有差异的坐标上**投出了分歧。

分两种情况：

**情况 A**：x 和 y 的**所有差异坐标都不在 D 中**（全都"不活跃"）。
- 这些坐标上 $A_{ij}=0$ → 贡献恒为 0
- $(Ax)_i$ 和 $(Ay)_i$ 完全一致 → **一定碰撞**
- 发生概率 = $(1-2p)^{\text{dist}(x,y)}$（每个差异坐标独立地以 $1-2p$ 概率不活跃）

**情况 B**：至少一个差异坐标在 D 中（活跃）。
- $A_{i\cdot}$ 在 D 上均匀随机 0/1 → 在活跃差异坐标上，x 和 y 的内积值有**恰好一半概率相等、一半概率不等**
- **不相等概率 = 1/2**
- 发生概率 = $1 - (1-2p)^{\text{dist}(x,y)}$

合并：

$$Pr[\text{不相等}] = \underbrace{(1-2p)^{\text{dist}} \times 0}_{\text{情况A：全不活跃，必相等}} + \underbrace{\left(1-(1-2p)^{\text{dist}}\right) \times \frac{1}{2}}_{\text{情况B：至少一个活跃，一半不等}}$$

$$= \frac{1}{2}\left(1 - (1-2p)^{\text{dist}(x,y)}\right)$$

对应的**碰撞概率**（课件中直接给出的形式）：
$$Pr[(Ax)_i = (Ay)_i] = 1 - Pr[\text{不相等}] = \frac{1}{2}\left(1 + (1-2p)^{\text{dist}(x,y)}\right)$$

**物理直觉**：Bernoulli 矩阵的每一行像一次"随机子集投票"——先随机圈选一批坐标（活跃集），再在这些坐标上随机投票（0/1）。近点的差异坐标少，容易全部逃过活跃区而强制碰撞；远点的差异坐标多，几乎一定会被某个活跃坐标抓到差异而分到不同桶。

#### 3.5 从单行到全部 k 行 — 参数选择与 (c,r)-ANN 保证

**问题**：单行只能给出一个微弱的概率 gap（近点 ≠ 概率 ≤ 1/4，远点 > 约 1/2）。单靠一行完全不可靠——近点有 25% 概率被判"远"，远点有近 50% 概率被判"近"。但如果我们用**很多行**，每行都独立地做一次投票，然后把 k 次投票汇总呢？

**思路**：这就像做 k 次独立实验——近点的"失败"（被判为不同）次数集中在 k/4 附近，远点的失败次数集中在约 k/2 附近。k 越大，这两个簇分得越开（Chernoff bound 保证偏离期望的概率指数级衰减）。取阈值 s 在中间，就能以高概率正确分类每对点。

有了单行的碰撞概率公式，接下来要决定两个东西：**p 取多少**能让远近点区分开？**k 取多少**能保证 w.h.p. 正确？

##### 3.5.1 选 p：让远近点的单行行为出现 gap

令 $(1-2p) = 2^{-1/r}$。代回公式：

**近点**（$\text{dist}(x,y) \le r$）：
$$Pr[\text{单行不相等}] \le \frac{1}{2}\left(1 - (2^{-1/r})^r\right) = \frac{1}{2}\left(1 - \frac{1}{2}\right) = \frac{1}{4}$$

**远点**（$\text{dist}(x,y) > c \cdot r$）：
$$Pr[\text{单行不相等}] > \frac{1}{2}\left(1 - (2^{-1/r})^{cr}\right) = \frac{1}{2}\left(1 - 2^{-c}\right) = \frac{1}{2} - 2^{-(c+1)}$$

| | 单行不相等概率 | 直觉 |
|---|---|---|
| **近点** ($\le r$) | $\le 1/4$ | 大概率碰撞（很少行判"不同"） |
| **远点** ($>cr$) | $> 1/2 - 2^{-(c+1)}$ | 大概率不碰撞（很多行判"不同"） |

两个概率之间有 **gap**：$(1/2 - 2^{-(c+1)}) - 1/4 = 1/4 - 2^{-(c+1)} > 0$（当 $c \ge 1$ 时）。这说明**单行就已经有区分能力**——近点的不相等概率更低。

##### 3.5.2 k 行汇总：定义统计量 X

降维后的 k 位指纹中，定义 $X$ = x 和 y 在**多少行上哈希值不同**：

$$X = \text{dist}_H(Ax, Ay) = \sum_{i=1}^k X_i, \quad X_i = \begin{cases} 1 & \text{如果 }(Ax)_i \neq (Ay)_i \\ 0 & \text{否则} \end{cases}$$

$X_i$ 是独立的 0/1 随机变量（不同行独立），k 行的汇总：

| | 单行期望 $E[X_i]$ | k 行期望 $E[X]$ |
|---|---|---|
| **近点** | $\le 1/4$ | $\le k/4$ |
| **远点** | $> 1/2 - 2^{-(c+1)}$ | $\ge (1/2 - 2^{-(c+1)})k$ |

##### 3.5.3 选阈值 s：在两个期望的正中间

近点期望上界和远点期望下界之间的 gap 宽度 = $(1/4 - 2^{-(c+1)})k$。把阈值 s 放在正中间：

$$s = \frac{k/4 + (1/2 - 2^{-(c+1)})k}{2} = \left(\frac{3}{8} - 2^{-(c+2)}\right)k$$

判定规则：若 $X \le s$ → 判为近；若 $X > s$ → 判为远。

##### 3.5.4 Chernoff-Hoeffding 压尾概率

X 是 k 个独立 0/1 随机变量之和。Chernoff-Hoeffding：独立有界随机变量之和偏离期望超过 $\Delta k$ 的概率以 $e^{-2\Delta^2 k}$ 衰减。

- **近点误判为远**（$X > s$，而 $E[X] \le k/4$）：偏离期望至少 $\Delta k = (1/8 - 2^{-(c+2)})k$

$$Pr[\text{近点被判远}] \le Pr[X > E[X] + \Delta k] < e^{-2\Delta^2 k}$$

- **远点误判为近**（$X \le s$，而 $E[X] \ge (1/2-2^{-(c+1)})k$）：偏离期望至少 $\Delta k$（对称）

$$Pr[\text{远点被判近}] \le Pr[X < E[X] - \Delta k] < e^{-2\Delta^2 k}$$

其中 $\Delta = 1/8 - 2^{-(c+2)} > 0$。

##### 3.5.5 收尾：$k = O(\log n)$ 即可

取 $k = C \cdot \Delta^{-2} \cdot \log n$（C 足够大），则单对错误概率 $< 1/n^2$。Union bound 过所有 $\binom{n}{2}$ 对数据点：

$$Pr[\text{任何一对判错}] \le n^2 \cdot \frac{1}{n^2} = o(1)$$

→ w.h.p. 所有近点对满足 $X \le s$，所有远点对满足 $X > s$。查询时只需检 $B_s(Ax)$——半径为 s 的球包含了所有真正 ≤r 的近点，排除了所有 >cr 的远点。$(c,r)$-ANN 解决！

##### 3.5.6 推导链回顾

```
Bernoulli(p) 矩阵
    ↓ 等效生成（活跃集 D）
单行碰撞概率公式 Pr[≠] = ½(1−(1−2p)^dist)
    ↓ 选 p: (1−2p) = 2^{−1/r}
近点单行≠概率 ≤ 1/4，远点 > 1/2−2^{−(c+1)}
    ↓ k 行独立求和 + 定义 X = Σ X_i
近点 E[X] ≤ k/4，远点 E[X] ≥ (½−2^{−(c+1)})k
    ↓ 阈值 s 取两个期望的正中间
Chernoff-Hoeffding → e^{−2Δ²k} 尾概率
    ↓ k = O(log n)
Union bound → w.h.p. 所有点对正确分类
```

#### 3.6 与欧氏 JL 的对比

| | 欧氏 JL（Gaussian/±1） | Hamming JL（Bernoulli） |
|---|---|---|
| 域 | $\mathbb{R}$（浮点） | GF(2)（位运算 XOR+AND） |
| 矩阵元素 | 实数 | $\{0,1\}$ |
| 运算 | 浮点矩阵乘法 $O(kd)$ | GF(2) 矩阵乘法，硬件位运算加速 |
| 降维输出 | $\mathbb{R}^k$ | $\{0,1\}^k$（k 位二进制串） |
| 距离保持 | 直接保持 pairwise $\ell_2$ 距离 | Hamming 距离通过碰撞概率**隐式**区分远近 |
| 判定方式 | $| \|Ax-Ay\|^2 - \|x-y\|^2 | \le \epsilon\|x-y\|^2$ | 不碰撞行数 vs 阈值 s |

**要害**：Hamming JL 不直接保持距离数值，而是通过"碰撞概率区分远近"——近点碰撞多（不碰撞行数少），远点碰撞少（不碰撞行数多）。这正是下一节 LSH 的核心思想：Hamming JL 是从纯 JL 到纯 LSH 的桥梁。

---

### 4. Locality-Sensitive Hashing (LSH) — 哈希版的降维

#### 4.1 问题：如何在大数据中快速找近似最近邻？

**回顾**：精确 NNS 在高维遭遇维度灾难。第 3 节的 Hamming 空间降维给出了希望——用 Bernoulli 矩阵降维后，近点和远点的碰撞概率不同。但我们想要一个**通用的**、**适用于任意度量空间**的框架。

**LSH 要解决的问题**：
- **输入**：n 个数据点（任意度量空间），查询点 x，参数 r 和 c
- **输出**：$(c,r)$-ANN 的答案——即存在 ≤r 的近点时返回一个 ≤cr 的点，所有点都 >cr 时答 "no"
- **手段**：设计一个随机哈希函数族，使得哈希碰撞的概率**编码了**距离远近

**核心思想**：汉明空间的降维给出一个启示——降维后的碰撞概率能区分远近点。LSH 把这个思想抽象为通用框架，适用于任意度量空间。

#### 4.2 形式化定义

随机函数 $h: X \to U$ 称为 **(r, cr, p, q)-LSH**，如果 $\forall x,y \in X$：
$$\text{dist}(x,y) \le r \implies Pr[h(x) = h(y)] \ge p$$
$$\text{dist}(x,y) > c \cdot r \implies Pr[h(x) = h(y)] \le q$$

要求 $p > q$（近点碰撞概率高于远点）。比值 $p/q$ 决定了能多好地区分远近。

**具体例子**：在二维平面上（欧氏距离），设计一个简单的 LSH：随机画一条穿过原点的直线，$h(x)$ = x 在直线的哪一侧（0 或 1）。

```
        · y (距离 x 很近，≤r)
       /
      /   ← 随机直线
  x  ·
    /
   /        · z (距离 x 很远，>cr)
```

- 近点 y：几乎就在 x 旁边，随机直线把它俩分到同一侧的概率很高（p ≈ 1 - θ/π，θ 很小）
- 远点 z：离 x 很远的点，直线把它俩分开的概率很大（碰撞概率 q 较小）
- 这个 $h$ 就是一个 $(r, cr, p, q)$-LSH：近点碰撞概率高(p)，远点碰撞概率低(q)

**汉明空间的简单 LSH**（4.5 节详述）：$h(x) = x_i$（随机选一个坐标），$p = 1 - r/d$，$q = 1 - cr/d$，$\rho \approx 1/c$。

#### 4.3 Tensorization（张量化）：放大 p 和 q 的差距

**问题**：一个 LSH 函数虽然 $p > q$，但差距可能很小——比如 p=0.9, q=0.85，近点碰撞概率只比远点高 5%。直接用一个哈希函数没法可靠地区分远近。

**思路**：用一个不够，就串起 k 个！k 个独立哈希全部碰撞的概率 = 每个碰撞概率的乘积——$p^k$ vs $q^k$。只要 $p > q$，$p^k/q^k = (p/q)^k$ 随 k 指数增长，区分度被放大。代价是近点的碰撞概率 $p^k$ 也会变小，所以需要 $\ell = 1/p^k$ 个独立的哈希表来保证至少有一个命中。

一个 $(r,cr,p,q)$-LSH 的区分度有限（p 和 q 可能很接近）。Tensorization 通过 k 个独立副本放大差距：

$$g(x) = (h_1(x), h_2(x), ..., h_k(x)) \in U^k$$

则 g 是 $(r, cr, p^k, q^k)$-LSH。因为 k 个独立哈希全部碰撞的概率 = 每个碰撞概率的乘积。

**关键参数 $\rho$**：定义 $\rho = \frac{\log p}{\log q}$。由于 $q < 1$，$\log q < 0$，而 $p < 1$ 也使 $\log p < 0$，所以 $\rho = \log p / \log q > 0$。p 越大于 q，$\rho$ 越小，区分度越好。

#### 4.4 LSH 完整数据结构

**问题**：有了 $(r,cr,p,q)$-LSH 函数族，怎么用它搭一个真正能回答 $(c,r)$-ANN 查询的数据结构？关键挑战——远点可能"碰巧"和查询点哈希到同一个桶（假阳性），近点又可能因为 $p^k$ 太小而总是和查询点分到不同桶（假阴性）。

**思路**：两个参数配合使用——k 控制"过滤力"（取 $k = \log_{1/q}n$ 让远点碰撞概率降到 $1/n$），$\ell$ 控制"召回力"（取 $\ell = n^{\rho}$ 个独立哈希表，保证近点至少在一个表中命中）。空间换精度：$\ell$ 个哈希表每个存 n 个点 → 空间 $n^{1+\rho}$。这就是 LSH 的经典时空权衡。

目标：解决 $(c,r)$-ANN。

1. 取 $k = \log_{1/q} n$。则 $q^k = 1/n$——远点发生碰撞的概率 $\le 1/n$。
2. 此时 $p^k = n^{-\rho}$——近点碰撞概率变为 $n^{-\rho}$。
3. 维护 $\ell = 1/p^k = n^{\rho}$ 个独立的哈希表（每个用独立的 $g_j$）。
4. **查询**：对所有 $\ell$ 个表，计算 $g_j(x)$，检索对应桶中的所有 $y_i$。检查是否 $\text{dist}(x, y_i) \le c \cdot r$，找到即返回。最多检查 $10\ell$ 个点后若没找到则返回 "no"。

**空间**：$O(n\ell) = O(n^{1+\rho})$（每个数据点存入 $\ell$ 个哈希表）。
**查询时间**：$O(\ell \log n) = O(n^{\rho} \log n)$（每个表检索一个桶，用 FKS 完美哈希）。

**正确性**（第 56-57 页）：
- 如果真实答案是 "no"（所有点都 $> c \cdot r$）：远点碰撞概率 $\le 1/n$，期望碰撞数 $\le n \cdot 1/n = 1$。Markov 给出 $\le 0.1 \cdot 10\ell$ 的概率遭遇超过 $10\ell$ 个假阳性。
- 如果存在近点（$\le r$）：$g_j(x) = g_j(y_{\text{near}})$ 的概率 $\ge p^k = 1/\ell$。$\ell$ 个独立表中至少有一个命中的概率 $\ge 1 - (1-1/\ell)^\ell \approx 1 - 1/e$。

合并：假阴性概率 $< 1/e + 0.1 < 0.5$。可以通过常数次重复降到任意小。

#### 4.5 汉明空间中的简单 LSH

最简单的 LSH：$h(x) = x_i$（随机选一个坐标）。

- $\text{dist}(x,y) \le r \implies Pr[h(x)=h(y)] \ge 1 - r/d$
- $\text{dist}(x,y) > c \cdot r \implies Pr[h(x)=h(y)] \le 1 - cr/d$

$$\rho = \frac{\log(1-r/d)}{\log(1-cr/d)} \approx \frac{1}{c}$$

**空间 $O(n^{1+1/c})$，查询时间 $O(n^{1/c}\log n)$。**

#### 4.6 LSH 与 JL 的关系

两者本质相通：JL 是"用随机投影保持距离"，LSH 是"用哈希碰撞概率区分远近"。汉明空间降维（第 3 节）可以看作 JL → LSH 的桥梁——Bernoulli 矩阵既是降维工具，也是 LSH 哈希族的构造方式。LSH 的 $\rho$ 参数和 JL 的目标维度 k 实质上都来自同一个概率集中现象：高维随机投影的分布。

---

### 5. Fast Johnson-Lindenstrauss Transform (FJLT)

#### 5.1 问题：Dense JL 太慢，能否在 sub-quadratic 时间内完成降维？

**问题（快速降维）**：
- **输入**：n 个 d 维向量，其中 d 极大（如 10⁶），目标维度 $k = O(\epsilon^{-2}\log n)$
- **标准 JL**：做 $k \times d$ 的 dense 矩阵乘法 Ax，每个点 $O(kd)$ 时间，n 个点共 $O(nkd)$
- **目标**：将每个点的处理时间降到 $o(kd)$，理想情况 $O(d \log d)$，同时保持 JL 的距离保证

**为什么这是问题？** 当 d=10⁶ 且 k≈690（$\epsilon=0.1$, n=1000），$kd \approx 6.9 \times 10^8$ 次浮点操作**每个点**。n=1000 个点就是 ~7×10¹¹ 次操作。而 FJLT 只需 $O(d \log d) \approx 2 \times 10^7$ 次操作每点——快了 30 倍，且差距随 d 增大而拉大。

标准 Gaussian/±1 JL 需要 $O(kd)$ 时间计算 Ax（dense 矩阵乘法）。当 d 很大（如图像/文本特征 d=10⁶），$O(d \cdot \epsilon^{-2}\log n)$ 本身就很昂贵。能否在 $o(kd)$ 时间内完成降维？

#### 5.2 朴素加速：随机采样坐标

**问题**：Dense JL 慢在矩阵乘法——每个输出维度都要和所有 d 个输入坐标做内积。能不能对每个输出维度只随机抽**一个**输入坐标？这样时间就从 $O(kd)$ 降到 $O(m)$。

**思路**：直觉上，如果一个向量的所有坐标"贡献均匀"，随机抽一个坐标再缩放 $\sqrt{d/m}$ 就是无偏估计。但问题出在"贡献不均匀"的向量——比如 $( \sqrt{d}, 0, 0, \dots )$ 这种只有一个坐标有巨大值的"尖峰向量"。这种情况下要么抽到峰值（估计偏大 d 倍），要么抽到零（估计为零）——方差炸了。

对每个输出维度 i，随机选一个输入坐标 j，乘以 $\sqrt{d/m}$：
$$y_i = x_j \cdot \sqrt{d/m}, \quad j \sim [d] \text{ uniformly}$$

- **优点**：时间 $O(m)$（非常快！）
- **无偏**：$\mathbb{E}[\|Y\|^2] = \mathbb{E}[X_J^2] \cdot d = \|X\|^2$
- **致命问题**：对方差敏感。对"峰值"向量 $x = (\sqrt{d}, 0, 0, ...)$：
  - $\|x\|^2 = d$，但 $X_J$ 以 $1-1/d$ 概率为 0，以 $1/d$ 概率为 $\sqrt{d}$
  - $\mathbb{E}[Y_i^2] = 1$，但 $\mathbb{E}[Y_i^4] = d \gg 1$——四阶矩爆炸

**教训**：$\ell_{\infty}$ 范数高的向量（有"尖峰"）采样方差巨大。需要先"均匀化"向量。

#### 5.3 FJLT+ 方案：Hadamard + Rademacher 预条件

**问题**：朴素采样失败的原因很明确——向量的 $\ell_{\infty}$ 范数（峰值的绝对大小）太大。如果能先对向量做一个快速的"均匀化"变换，让所有坐标的大小变得差不多，再稀疏采样就不会方差爆炸了。

**思路**：分三步——(1) D：随机翻转每个坐标的符号（打破任何"恶意"的符号模式），(2) H：Hadamard 变换（类似 FFT，$O(d\log d)$ 时间）把向量"铺开"——原来集中在一个坐标上的能量被均匀分散到所有坐标，(3) S：稀疏采样。核心保证来自 Khintchine 不等式：HD 后每个坐标的大小以高概率不超过 $O(\sqrt{\log d})$。

$$\Pi = \frac{1}{\sqrt{m}} \cdot S \cdot H \cdot D$$

- **D**：$d \times d$ 对角矩阵，对角线元素独立随机 $\in \{-1, +1\}$（Rademachers）——随机翻转每个坐标的符号
- **H**：$d \times d$ Hadamard 矩阵（$d = 2^t$）——快速正交变换，类似 FFT，$O(d\log d)$ 时间
- **S**：$m \times d$ 采样矩阵——每行随机均匀选一个坐标（稀疏）

##### 5.3.1 前置：什么是 Hadamard 变换？和 FFT 有什么相似？

**线性变换是什么？** 给定向量 $x = (x_1, \dots, x_d)$，乘一个 $d \times d$ 矩阵得到新向量。一般矩阵乘法要 $O(d^2)$ 时间。但有些矩阵有特殊结构，利用递归分治可以在 $O(d \log d)$ 时间内算完——FFT 和 Hadamard 都属于这类"快速变换"。

**Hadamard 矩阵**：只含 +1 和 -1，行与行正交。递归构造（$d=2^t$）：

$$H_1 = (1), \quad H_2 = \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}, \quad H_4 = \begin{pmatrix} H_2 & H_2 \\ H_2 & -H_2 \end{pmatrix}$$

展开 $H_4$：

$$H_4 = \begin{pmatrix}
1 & 1 & 1 & 1 \\
1 & -1 & 1 & -1 \\
1 & 1 & -1 & -1 \\
1 & -1 & -1 & 1
\end{pmatrix}$$

$H_8$ 就是把 $H_4$ 嵌在四个块里，以此类推。

**为什么是 $O(d \log d)$？** 递归分块结构：

$$\begin{pmatrix} H_2 & H_2 \\ H_2 & -H_2 \end{pmatrix} \cdot \begin{pmatrix} x_{top} \\ x_{bottom} \end{pmatrix} = \begin{pmatrix} H_2 \cdot x_{top} + H_2 \cdot x_{bottom} \\ H_2 \cdot x_{top} - H_2 \cdot x_{bottom} \end{pmatrix}$$

先递归算出 $H_{d/2} \cdot x_{top}$ 和 $H_{d/2} \cdot x_{bottom}$（两个大小为 d/2 的子问题），然后 $O(d)$ 时间做对应位置的加减。时间递推：

$$T(d) = 2 \cdot T(d/2) + O(d) = O(d \log d)$$

**Hadamard 对向量做了什么？** 看 $H_4$ 每一行的符号模式：

```
第 1 行: [+ + + +]  →  四坐标全加（"直流分量"）
第 2 行: [+ - + -]  →  相邻交替加减（"高频"）
第 3 行: [+ + - -]  →  前半加、后半减（"中频"）
第 4 行: [+ - - +]  →  交叉加减（"高频"）
```

Hadamard 把向量分解成不同"频率"的分量。一个峰值向量 $(\sqrt{d}, 0, 0, \dots, 0)$ 只有第一个坐标有能量——经过正交的 Hadamard（$\frac{1}{\sqrt{d}}H_d$）后，所有坐标分到均等的能量，$\ell_{\infty}$ 范数从 $\sqrt{d}$ 降到 $O(1)$。这就是 FJLT 要的"均匀化"。

**和 FFT 的类比**：FFT（快速傅里叶变换）也是 $O(d \log d)$，也是递归分治——偶数位和奇数位分组 → 算两个小 DFT → $O(d)$ 组合。类比的是**算法结构**和**时间复杂度**，不是数学内容：

| | FFT | Hadamard |
|---|---|---|
| 分治策略 | 偶/奇位置分组 | 上半/下半分组 |
| 递归 | 算两个小 DFT，组合 | 算两个小 Hadamard，组合 |
| 时间复杂度 | $O(d \log d)$ | $O(d \log d)$ |
| 基函数 | 正弦/余弦（复数） | ±1 方波 |
| 物理效果 | 揭示信号的频率成分 | 把集中能量均匀铺开 |

**为什么 FJLT 用 Hadamard 而不是 FFT？** Hadamard 只用 ±1——所有运算都是加法和符号翻转，无复数运算，比 FFT 更快更简单。目的也不是"做频谱分析"，而是利用它的"能量均匀化"效果让后续稀疏采样不炸方差。

**直觉**：HD 是"随机旋转"——它把任意向量变成一个所有坐标分布均匀的向量。具体来说，通过 Khintchine 不等式，$\|HDz\|_{\infty} \le \sqrt{2\log(4d/\delta)}$ w.h.p.——原来可能有 $\sqrt{d}$ 量级的峰值坐标被均匀化为 $O(\sqrt{\log d})$ 量级。

#### 5.4 Khintchine 不等式 — HD 均匀化的理论保证

##### 5.4.1 要证明什么

FJLT 管线是 $\Pi = \frac{1}{\sqrt{m}} \cdot S \cdot H \cdot D$。必须严格证明：经过 HD 后，输出向量 $y = HDz$ 的每个坐标**以高概率不太大**——具体地说，$\ell_\infty$ 范数不超过 $O(\sqrt{\log d})$。否则后面的稀疏采样方差会爆炸。

**关键观察**：$y_i = \sum_j H_{i,j} \cdot \delta_j \cdot z_j$。Hadamard 矩阵元素 $H_{i,j} \in \{\pm1\}$ 是**固定的**，$\delta_j \in \{\pm1\}$ 是**随机的**（Rademacher）。两个独立 ±1 的乘积仍是均匀 ±1 → $H_{i,j} \cdot \delta_j$ 整体等价于一个 Rademacher 随机变量。所以：

$$y_i = \langle \sigma^{(i)}, z \rangle, \quad \sigma^{(i)}_j = H_{i,j} \cdot \delta_j \sim \text{uniform } \{\pm1\}$$

**$y_i$ 本质上就是"一个 Rademacher 随机向量与固定向量 $z$ 的内积"。** Khintchine 不等式正是给这种内积的尾概率上界。

##### 5.4.2 Khintchine 不等式的完整证明

**目标**：对独立均匀 $\sigma_i \in \{-1,+1\}$ 和任意固定向量 $x$：

$$Pr[|\langle \sigma, x\rangle| \ge \lambda] \le 2\exp\left(-\frac{\lambda^2}{2\|x\|_2^2}\right)$$

整个证明是 **"Markov + 指数变换 + MGF 连环简化 + 参数最优化"** 的标准 Chernoff 套路，但 MGF 的处理和 Gaussian/伯努利情况不同——这里用的是**泰勒展开 + 奇偶项分离**。

---

**第 1 步：Markov + 指数变换（Chernoff 起手式）**

令 $X = \langle \sigma, x \rangle = \sum_i \sigma_i x_i$。对任意 $t > 0$：

$$Pr[X \ge \lambda] = Pr[e^{tX} \ge e^{t\lambda}] \le e^{-t\lambda} \cdot \mathbb{E}[e^{tX}]$$

**目的**：把"和偏离期望"的概率转化为矩母函数的界。$t$ 是待调参数，最后会被选到最优值。

---

**第 2 步：拆开矩母函数**

$$e^{tX} = e^{t\sum_i \sigma_i x_i} = \prod_i e^{t\sigma_i x_i}$$

$\sigma_i$ 独立 → 乘积的期望 = 期望的乘积：

$$\mathbb{E}[e^{tX}] = \prod_i \mathbb{E}[e^{t\sigma_i x_i}]$$

**目的**：把 d 个耦合的随机变量拆成 d 个**独立**的因子，每个只涉及一个 $\sigma_i$。这样就能单个击破。

---

**第 3 步：单个 $\sigma_i$ 的 MGF — 从离散定义出发**

$\sigma_i$ 取 +1 和 -1 各 1/2 概率：

$$\mathbb{E}[e^{t\sigma_i x_i}] = \frac{1}{2}e^{t x_i} + \frac{1}{2}e^{-t x_i} = \frac{e^{t x_i} + e^{-t x_i}}{2}$$

这是一个 $\cosh$ 函数：$\cosh(t x_i) = (e^{t x_i} + e^{-t x_i})/2$。

**目的**：把概率期望变成具体的代数表达式。现在离最终答案还很远——这个表达式带着两个指数，不便于连乘后求最优化。

---

**第 4 步（核心）：泰勒展开 → 奇偶项分离 → 放缩回指数**

这是整个证明中最精巧的一步。**泰勒展开**是把一个函数写成无穷多项式——$e^x = 1 + x + x^2/2! + x^3/3! + \dots$，每一项的系数是 $1/k!$。这里同时展开 $e^{tx_i}$ 和 $e^{-tx_i}$ 再相加，奇数次项恰好抵消，只剩偶数次项。

把两个指数分别泰勒展开：

$$e^{t x_i} = \sum_{k \ge 0} \frac{(t x_i)^k}{k!}, \quad e^{-t x_i} = \sum_{k \ge 0} \frac{(-t x_i)^k}{k!}$$

两者相加：

$$\frac{e^{t x_i} + e^{-t x_i}}{2} = \sum_{k \ge 0} \frac{(t x_i)^k + (-t x_i)^k}{2 \cdot k!}$$

**关键观察**：
- 奇数次项 $k=1,3,5,\dots$：$(t x_i)^k + (-t x_i)^k = 0$，全部抵消
- 偶数次项 $k=0,2,4,\dots$：$(t x_i)^k + (-t x_i)^k = 2(t x_i)^k$，翻倍

$$\Rightarrow \quad \sum_{k \ge 0} \frac{2(t x_i)^{2k}}{2 \cdot (2k)!} = \sum_{k \ge 0} \frac{(t x_i)^{2k}}{(2k)!}$$

**目的**：奇偶分离消除了正负号的不确定性——所有 $\sigma_i$ 的"随机性"现在被编码为"只有偶数阶矩不消失"这个事实。现在只剩纯代数放缩。

---

**第 5 步：$(2k)! \to k! \cdot 2^k$ 放缩**

需要把 $(2k)!$ 变得容易求和。$(2k)! = 1 \times 2 \times 3 \times 4 \times \cdots \times (2k)$，共 2k 个数相乘。技巧：**只保留偶数因子，每个提一个 2 出来**——$2 \times 4 \times 6 \times \cdots \times 2k = 2^k \times (1 \times 2 \times 3 \times \cdots \times k) = 2^k \cdot k!$。奇数因子 $(1, 3, 5, \dots)$ 都 $\ge 1$，扔掉它们让分母变小 → 分数变大 → 不等式方向正确。

$$\frac{(t x_i)^{2k}}{(2k)!} \le \frac{(t x_i)^{2k}}{k! \cdot 2^k} = \frac{(t^2 x_i^2/2)^k}{k!}$$

现在求和变成一个我们认识的形式：

$$\sum_{k \ge 0} \frac{(t x_i)^{2k}}{(2k)!} \le \sum_{k \ge 0} \frac{(t^2 x_i^2/2)^k}{k!} = e^{t^2 x_i^2/2}$$

**目的**：把 $\cosh$ 的泰勒级数放缩成指数的泰勒级数。这样连乘后就是一个简洁的指数函数，而不是一堆 $\cosh$ 的纠缠。

---

**第 6 步：连乘回来**

$$\mathbb{E}[e^{tX}] = \prod_i \mathbb{E}[e^{t\sigma_i x_i}] \le \prod_i e^{t^2 x_i^2/2} = \exp\left(\frac{t^2}{2}\sum_i x_i^2\right) = e^{t^2 \|x\|^2/2}$$

**目的**：d 个因子的乘积合并为一个指数——矩母函数的上界。

---

**第 7 步：参数最优化**

代回第 1 步的 Markov bound：

$$Pr[X \ge \lambda] \le e^{-t\lambda} \cdot e^{t^2\|x\|^2/2} = \exp\left(-t\lambda + \frac{t^2\|x\|^2}{2}\right)$$

这是 $t$ 的**二次函数**（开口向上）。在 $t = \lambda/\|x\|^2$ 处取极小值：

$$Pr[X \ge \lambda] \le \exp\left(-\frac{\lambda^2}{\|x\|^2} + \frac{\lambda^2}{2\|x\|^2}\right) = \exp\left(-\frac{\lambda^2}{2\|x\|^2}\right)$$

**下尾** $Pr[-X \ge \lambda]$ 完全对称（$\sigma_i$ 取 -1 等价于 $-\sigma_i$ 取 +1）→ 同样的 bound。合并：

$$\boxed{Pr[|\langle \sigma, x\rangle| \ge \lambda] \le 2\exp\left(-\frac{\lambda^2}{2\|x\|_2^2}\right)}$$

这就是 **Khintchine 不等式**。形式和高斯尾概率 $e^{-x^2/2}$ 完全一致——Rademacher 的集中性和高斯一样强。

---

##### 5.4.3 从 Khintchine 到 HD 的 $\ell_\infty$ 控制

现在回到 FJLT 管线。$y_i = \langle \sigma^{(i)}, z \rangle$，在 JL 场景中 $\|z\|^2 = 1$（归约到单位向量）。

取 $\lambda = \sqrt{2\ln(4d/\delta)}$，代 Khintchine：

$$Pr[|y_i| \ge \sqrt{2\ln(4d/\delta)}] \le 2\exp\left(-\frac{2\ln(4d/\delta)}{2}\right) = 2 \cdot \frac{\delta}{4d} = \frac{\delta}{2d}$$

**Union bound** 过所有 d 个坐标（$i = 1, \dots, d$）：

$$Pr[\|y\|_\infty \ge \sqrt{2\ln(4d/\delta)}] \le d \cdot \frac{\delta}{2d} = \frac{\delta}{2}$$

**结论**：定义事件 $\mathcal{E} = \{\|HDz\|_\infty \le \sqrt{2\ln(4d/\delta)}\}$，则 $Pr[\mathcal{E}] \ge 1 - \delta/2$。HD 把向量的峰值从可能高达 $\sqrt{d}$ 压到了 $O(\sqrt{\log d})$——均匀化完成。

---

#### 5.5 条件于低 $\ell_\infty$ 的采样分析 — 收尾

##### 5.5.1 为什么还需要这一步

HD 以概率 $\ge 1-\delta/2$ 保证了 $\ell_\infty$ 低，但这是**概率保证**，不是确定性的。采样矩阵 S 在 HD 之后执行——我们需要证明：**在 $\mathcal{E}$ 发生的条件下**，m 次稀疏采样的均值确实集中在真值 1 附近。这样才能完成整个 FJLT 的概率论证。

##### 5.5.2 采样变量的范围

采样过程：对每个 $i \in [m]$，独立均匀选 $j_i \sim [d]$，取 $Y_i = \sqrt{d} \cdot (HDz)_{j_i}$。

则 $\|\Pi z\|^2 = \frac{1}{m}\sum_{i=1}^m Y_i^2$（m 个独立采样取平均）。

**条件于 $\mathcal{E}$**：每个 $|(HDz)_{j_i}| \le \sqrt{2\ln(4d/\delta)}$，所以：

$$Y_i^2 = d \cdot (HDz)_{j_i}^2 \in \left[0,\; d \cdot 2\ln(4d/\delta)\right]$$

每个 $Y_i^2$ 是有界随机变量，范围上界 = $O(d \log d)$。

**无偏性**：$\mathbb{E}[Y_i^2] = d \cdot \mathbb{E}[(HDz)_j^2] = d \cdot \frac{1}{d}\sum_{k=1}^d (HDz)_k^2 = \|HDz\|^2 = \|z\|^2 = 1$（Hadamard 和 D 都是正交矩阵，保范数）。

所以 $\mathbb{E}[\|\Pi z\|^2] = \frac{1}{m} \cdot m \cdot 1 = 1$——无偏。

##### 5.5.3 Chernoff 收尾

m 个独立、有界 $[0, d \cdot 2\ln(4d/\delta)]$ 的随机变量，均值无偏为 1。Chernoff bound（有界随机变量版，范围上界记为 $U = d \cdot 2\ln(4d/\delta)$）：

$$Pr\left[\big| \|\Pi z\|^2 - 1 \big| \ge \epsilon \;\middle|\; \mathcal{E}\right] \le \exp\left(-\Omega\left(\frac{\epsilon^2 m}{U}\right)\right) = \exp\left(-\Omega\left(\frac{\epsilon^2 m}{\log(d/\delta)}\right)\right)$$

**为什么分母是 $U \propto \log d$？** Chernoff 的尾概率依赖"有界范围"这个参数——范围越大（$Y_i^2$ 可能取值的区间越宽），偏差相同的概率越大，需要的样本量越多。HD 把范围从 $[0, d]$ 压到 $[0, d\log d]$——实际上没改变数量级（仍是 $O(d)$），但常数因子从 d 变成了 $\log d$，这对后面的 m 取值至关重要。

##### 5.5.4 参数选取与总时间

取 $m = O(\epsilon^{-2}\log n \cdot \log(d/\delta))$，则上述尾概率 $< 1/n^3$。和 Gaussian JL 的 union bound 一样，覆盖所有 $O(n^2)$ 对点 → w.h.p. 所有 pairwise 距离保持。

**总时间**：
- D（符号翻转）：$O(d)$
- H（Hadamard 变换）：$O(d \log d)$
- S（稀疏采样）：$O(m) = O(\epsilon^{-2}\log n \cdot \log d)$

总计 $\tilde{O}(d)$（$\tilde{O}$ 隐藏对数因子），碾压 dense JL 的 $O(kd) = O(\epsilon^{-2}d\log n)$。

##### 5.5.5 完整推导链

```
D: δⱼ ∈ {±1} 随机符号翻转
    ↓
H: Hadamard 变换, y = HDz
    ↓
yᵢ = Σⱼ Hᵢⱼ·δⱼ·zⱼ = ⟨σ⁽ⁱ⁾, z⟩  (等价于 Rademacher 内积)
    ↓ Khintchine: Markov + 指数 + 泰勒展开/奇偶分离 + (2k)!放缩 + 参数最优化
Pr[|yᵢ| ≥ λ] ≤ 2exp(−λ²/(2||z||²))
    ↓ 取 λ = √(2ln(4d/δ)), Union bound over d 个坐标
||y||∞ ≤ √(2ln(4d/δ))  w.p. ≥ 1−δ/2
    ↓ 条件于 E, 每个 Yᵢ² ∈ [0, d·2ln(4d/δ)] 有界
    ↓ Chernoff (有界版)
Pr[ ||Πz||² 偏离 > ε | E ] ≤ exp(−Ω(ε²m/log(d/δ)))
    ↓ m = O(ε⁻²·log n·log d)
JL 保证完成。总时间 O(d log d) + O(m) = Õ(d)
```

**和 Gaussian JL 证明结构的对应**：

| 步骤 | Gaussian JL | FJLT |
|------|------------|------|
| 归约 | 单位向量 u | 单位向量 z |
| 分析中间量 | $(Au)_i \sim \mathcal{N}(0,1/k)$ | $(HDz)_i$ = Rademacher 内积 |
| 尾概率工具 | $\chi^2$ 的 Chernoff | Khintchine 不等式 |
| MGF 技巧 | $\mathbb{E}[e^{\lambda X^2}] = 1/\sqrt{1-2\lambda}$ | 泰勒展开 + 奇偶分离 + $(2k)!$ 放缩 |
| 收尾 | $k = O(\epsilon^{-2}\log n)$ | $m = O(\epsilon^{-2}\log n \cdot \log d)$ |

两条路不同的 MGF 处理方式，但底层逻辑完全相同：**Markov + 指数变换 → 分析 MGF → 取最优参数 → 目标维度对 $\log n$ 的依赖**。

---

### 6. Oblivious Subspace Embedding (OSE) — 嵌入整个子空间

#### 6.1 问题：从 JL 到 OSE — 从"有限个点"到"整个子空间"

##### 6.1.1 JL 的局限

JL 定理保证：n 个**离散点** $x_1, \dots, x_n$，随机投影后所有 pairwise 距离保持 $(1\pm\epsilon)$ 倍。

但这不能直接推出：这些点张成的 d 维**子空间**中，**所有**向量（无限个！）的范数也被保持。JL 只对那 n 个具体的点做了 union bound，子空间中的其他向量不在保证范围内。

**一个具体的失败场景**：假设 $n=3$ 个点 $(1,0,0), (0,1,0), (0,0,1)$ 张成整个 $\mathbb{R}^3$。JL 只保证这三个点两两之间的距离 OK——但这不意味着子空间中随便一个向量如 $(0.7, 0.3, 0.6)$ 投影后范数也 OK。

##### 6.1.2 为什么需要"保证整个子空间"？

很多应用中，我们关心的不只是一组离散点，而是这些点张成的**整个子空间**：

- **线性回归**（第 7.2 节）：残差向量 $X\beta - y$ 落在 $\text{span}(\text{cols}(X), y)$ 中（维度 $\le d+1$）。我们需要 $\|\Pi X\beta - \Pi y\| \approx \|X\beta - y\|$ 对**所有** $\beta$ 成立——这是一个连续无穷集合。
- **低秩近似**：SVD 的前 k 个奇异向量张成的子空间，我们需要投影后整个子空间被保持。
- **PCA**：主成分方向构成的子空间，降维后这些方向的方差应被保持。

**关键区别**：JL 保证"我认识的那 n 个点 OK"，OSE 保证"这个子空间里**不管什么点**都 OK"。

##### 6.1.3 OSE 的形式定义

随机矩阵 $\Pi \in \mathbb{R}^{m \times n}$ 是 $(\epsilon, \delta)$-**OSE for a d-dimensional subspace**，如果对**任意固定的** d 维子空间 $T \subset \mathbb{R}^n$，以概率 $\ge 1-\delta$：

$$\forall x \in T: \|\Pi x\|_2 = (1\pm\epsilon)\|x\|_2$$

**"任意固定"的含义**：$T$ 在 $\Pi$ 被采样**之前**就确定了——$\Pi$ 对 $T$ 没有"针对性"。这保证了 $\Pi$ 可以重复用于不同的 $T$（只要 $T$ 是在看到 $\Pi$ 之前选的）。

**"oblivious"（无感知）** 的含义**：$\Pi$ 的构造**不依赖** $T$。你只需要知道子空间维度 d，选好 $m = O(d/\epsilon^2)$，随机生成 $\Pi$。然后**任何** d 维子空间 $T$，$\Pi$ 都以高概率成为它的嵌入——$\Pi$ 对 $T$ 的具体方向"毫无感知"。

##### 6.1.4 等价矩阵表述

定义中写"任意 d 维子空间 $T$"，和写"任意固定矩阵 $A \in \mathbb{R}^{n \times d}$"是等价的——因为任何 d 维子空间就是某个 $A$ 的列空间 $\{Ax : x \in \mathbb{R}^d\}$。所以 OSE 也常写成：

$$\forall x \in \mathbb{R}^d: \|\Pi A x\|_2 = (1\pm\epsilon)\|A x\|_2$$

这是第 7.2 节 Sketch-and-Solve 中直接使用的形式。

##### 6.1.5 直觉：为什么"保证子空间"可能比"保证 n 个点"更省维度？

这听起来反直觉——保证无穷个点怎么可能比保证有限个点更便宜？答案藏在 **union bound 的对象**里：

- JL 对 $\binom{n}{2} \approx n^2/2$ 对离散点做 union bound → 目标维度含 $\log n$
- OSE 对 $\gamma$-net 上的 $\le 5^d$ 个锚点做 union bound → 目标维度含 $\log(5^d) = O(d)$

当 $d \ll \log n$ 时（特征数远小于样本数的对数），$O(d) \ll O(\log n)$。子空间的"几何复杂度"由维度 $d$ 决定，而离散点集的"组合复杂度"由点数 $n$ 决定——二者可以相差悬殊。

**具体对比**：

| | JL | OSE |
|--|-----|------|
| 保证对象 | n 个离散点 | 整个 d 维子空间（无限个点） |
| 目标维度 | $O(\epsilon^{-2}\log n)$ | $O(d/\epsilon^2)$ |
| Union bound 对象 | $\binom{n}{2}$ 对点 | $\le 5^d$ 个 net 锚点 |
| 何时更省 | $d \gg \log n$ | $d \ll \log n$ |

**数值例子**：$n=10^6$，$d=50$。JL 需要 $m_{\text{JL}} \propto \log(10^6) \approx 14$（常数因子），OSE 需要 $m_{\text{OSE}} \propto 50$。当 $\epsilon^{-2}$ 的常数因子很大时（如 $\epsilon=0.1$ 给出 100 倍），$m_{\text{JL}} \approx 1400$，$m_{\text{OSE}} \approx 5000$——JL 更省。但当 $d=5$，$m_{\text{OSE}} \propto 5 \ll 14 = m_{\text{JL}}$。所以 OSE 的优势在 $d$ 很小时尤为明显。

---

#### 6.2 $\gamma$-net Argument — 从"保证有限个锚点"到"保证整个子空间"

##### 6.2.1 核心挑战

OSE 要保证子空间中**所有**向量（无限个）。但我们的概率工具（Chernoff、Union bound）只能处理**有限**个事件。怎么跨过这个鸿沟？

**答案**：$\gamma$-net——用有限个"锚点"覆盖整个 d 维单位球面。证明分两阶段：
1. **在锚点上**：对 net 中每个点用 JL（有限个，union bound 可控）
2. **传递到球面**：球面上任意点 = 锚点的加权和（几何级数），用三角不等式把锚点上的保证"传递"过去

##### 6.2.2 $\gamma$-net 是什么？

**定义**：集合 $N \subset \mathbb{S}^{d-1}$（d 维单位球面）是 $\gamma$-net，如果球面上**任意**一点到 $N$ 中**某个**点的距离 $\le \gamma$。

$$\forall x \in \mathbb{S}^{d-1}, \exists y \in N: \|x-y\|_2 \le \gamma$$

**物理类比**：地球上布了 $|N|$ 个气象站。$\gamma$-net 保证地球上任意地点离最近气象站不超过 $\gamma$（弧度度量）。站不用太多——如果 $\gamma=0.1$（约 570 km），只需大约 $(3/0.1)^2 \approx 900$ 个站就能覆盖全球。

##### 6.2.3 Net 大小上界的推导（贪心构造 + 体积论）

**目的**：证明 $|N| \le (3/\gamma)^d$，即 net 的大小只指数依赖于 $d$，与 $n$ 无关。

**构造方法（贪心）**：
1. 从空集开始，反复在 $\mathbb{S}^{d-1}$ 上随便选一个点到 $N$ 中
2. 每次选完后，删除所有离新点距离 $\le \gamma$ 的区域
3. 当球面被完全覆盖时停止

**大小分析**：以 $N$ 中每个点为中心、$\gamma/2$ 为半径画小球。这些小球**互不相交**（否则两个中心的距离会 $< \gamma$，贪心过程不会同时保留它们）。所有小球都包含在半径 $1+\gamma/2$ 的大球内。

d 维球的体积 $\propto r^d$，所以：

$$|N| \cdot (\gamma/2)^d \le (1+\gamma/2)^d$$

$$\Rightarrow |N| \le \left(\frac{1+\gamma/2}{\gamma/2}\right)^d = \left(1 + \frac{2}{\gamma}\right)^d \le \left(\frac{3}{\gamma}\right)^d$$

取 $\gamma \le 1/2$，$|N| \le 5^d$。

##### 6.2.4 七步论证的完整推导

设 $A \in \mathbb{R}^{n \times d}$ 是列满秩矩阵，我们要证 OSE 保持 $\|Ax\|$ 对所有单位向量 $x \in \mathbb{S}^{d-1}$ 成立。以 A 的列空间为子空间 $T$。

---

**第 1 步：在子空间中建 net**

令 $N$ 是 $\mathbb{S}^{d-1}$ 上的 $\gamma$-net（$|N| \le 5^d$）。定义子空间中的对应锚点集：

$$M = \{Ax : x \in N\} \subset T$$

$|M| \le |N| \le 5^d$。这些就是在子空间中要直接施加 JL 保证的"锚点"。

**目的**：把球面上的 net 映射到实际的子空间 $T$ 中。JL 会直接保证这些 $M$ 中的点。

---

**第 2 步：球面上任意点用最近锚点近似**

对任意 $x^{(0)} = x \in \mathbb{S}^{d-1}$（这恰好是第 0 轮），由 net 定义存在 $x_1 \in N$ 满足：

$$\|x^{(0)} - x_1\|_2 \le \gamma$$

令 $y_1 = A x_1 \in M$（第 1 个锚点向量）。则 $\|Ax^{(0)} - y_1\|_2 = \|A(x^{(0)} - x_1)\|_2 \le \|A\| \cdot \gamma$。

**但** $x^{(0)} - x_1$ 不再是单位向量！设 $\alpha_1 = \|x^{(0)} - x_1\|_2 \le \gamma$。

---

**第 3 步：把"剩余向量"归一化，再用 net 近似**

令 $x^{(1)} = (x^{(0)} - x_1) / \alpha_1$。这是一个单位向量（在第 1 轮归一化）。由 net 定义存在 $x_2 \in N$ 满足 $\|x^{(1)} - x_2\|_2 \le \gamma$。

对应地 $y_2 = A x_2 \in M$，$\alpha_2 = \|x^{(1)} - x_2\|_2 \le \gamma$。

此时：
$$Ax^{(0)} = y_1 + \alpha_1 A x^{(1)} = y_1 + \alpha_1(y_2 + \alpha_2 A x^{(2)}) = y_1 + \alpha_1 y_2 + \alpha_1\alpha_2 A x^{(2)}$$

第 2 轮剩余 $\alpha_1\alpha_2 A x^{(2)}$ 的范数 $\le \gamma^2 \cdot \|A\|$。

**目的**：每轮把"剩余向量"归一化 → net 近似 → 产生一个新的锚点项 $y_i$ 和一个更小的剩余向量。剩余向量的范数以 $\gamma$ 倍指数衰减。

---

**第 4 步：迭代展开成几何级数**

重复上述过程：对 $i = 1, 2, 3, \dots$：

$$x^{(i-1)} \xrightarrow{\text{net}} x_i \in N \xrightarrow{} y_i = A x_i \in M$$

$$\alpha_i = \|x^{(i-1)} - x_i\|_2 \le \gamma$$

$$x^{(i)} = (x^{(i-1)} - x_i) / \alpha_i$$

展开 $i$ 轮后：

$$Ax = y_1 + \alpha_1 y_2 + \alpha_1\alpha_2 y_3 + \cdots + \left(\prod_{j=1}^{i} \alpha_j\right) A x^{(i)}$$

无穷级数展开（因为 $\alpha_j \le \gamma < 1$，剩余项 → 0）：

$$Ax = \sum_{i=1}^{\infty} \beta_i y_i, \quad \text{其中 } \beta_i = \prod_{j=1}^{i-1} \alpha_j \le \gamma^{i-1}, \;\; \beta_1 = 1$$

每个 $y_i \in M$ 都是 net 锚点。$\|y_i\|_2 \le \|A\|$（因为 $x_i$ 是单位向量）。

**目的**：把子空间中的**任意**向量 $Ax$ 写成 $M$ 中**有限个**锚点的加权和。权值 $\beta_i$ 以几何速度衰减（$\le \gamma^{i-1}$），确保级数收敛。

---

**第 5 步：对锚点施加 JL 保证**

对 $M$ 中的每个点 $y_i$，JL 保证（以高概率）：

$$\|\Pi y_i\|_2^2 = (1\pm\epsilon)\|y_i\|_2^2$$

同时，对任意一对 $y_i, y_j \in M$，内积也被近似保持：

$$\langle \Pi y_i, \Pi y_j \rangle = \langle y_i, y_j \rangle \pm 2\epsilon\|y_i\|\|y_j\|$$

Union bound 过所有 $|M| \le 5^d$ 个点 → 需要概率 $< \delta/5^d$ 每点 → $m = O(\epsilon^{-2}\log(5^d/\delta)) = O(\epsilon^{-2}(d + \log(1/\delta)))$。

**目的**：有限个锚点，标准 JL + union bound 即可。这也是 OSE 目标维度 $O(d/\epsilon^2)$ 的来源——$\log(5^d) = O(d)$。

---

**第 6 步：展开 $\|\Pi Ax\|^2$**

$$\|\Pi Ax\|^2 = \left\|\sum_i \beta_i \Pi y_i\right\|^2 = \sum_i \beta_i^2 \|\Pi y_i\|^2 + 2\sum_{i<j} \beta_i\beta_j \langle \Pi y_i, \Pi y_j \rangle$$

代入第 5 步的保证：

$$= \sum_i \beta_i^2 (1\pm\epsilon)\|y_i\|^2 + 2\sum_{i<j} \beta_i\beta_j (\langle y_i, y_j \rangle \pm 2\epsilon\|y_i\|\|y_j\|)$$

$$= \sum_i \beta_i^2 \|y_i\|^2 + 2\sum_{i<j} \beta_i\beta_j \langle y_i, y_j \rangle \;\pm\; \epsilon\left(\sum_i \beta_i^2 \|y_i\|^2 + 4\sum_{i<j} \beta_i\beta_j \|y_i\|\|y_j\|\right)$$

前面的无 $\epsilon$ 部分恰好是 $\|\sum_i \beta_i y_i\|^2 = \|Ax\|^2$。后面的 $\epsilon$ 误差项需要被 bound。

---

**第 7 步：bound 误差项（为什么几何衰减救了命）**

误差项 = $\epsilon \cdot \sum_{i,j} \beta_i\beta_j \|y_i\|\|y_j\|$（内积误差和平方误差合并）。

$\|y_i\| \le \|A\|$（因为 $x_i$ 是单位向量）。$\beta_i \le \gamma^{i-1}$。

$$\sum_{i,j} \beta_i\beta_j \le \sum_{i,j} \gamma^{i+j-2} = \left(\sum_{i=0}^{\infty} \gamma^i\right)^2 = \frac{1}{(1-\gamma)^2}$$

取 $\gamma \le 1/2$，$\frac{1}{(1-\gamma)^2} \le 4$。所以误差项 $\le 4\epsilon \cdot \|A\|^2 = O(\epsilon)$。

**结论**：$\|\Pi Ax\|^2 = \|Ax\|^2 \pm O(\epsilon)\|A\|^2 = (1 \pm O(\epsilon))\|Ax\|^2$。通过缩放 $\epsilon$ 的常数因子，得到标准的 $(1\pm\epsilon)$ 形式。

##### 6.2.5 为什么 $\gamma$-net 是 OSE 论证的灵魂

整个证明只有两个关键 idea：

1. **用有限个锚点覆盖无限球面**（$\gamma$-net）：球面虽然是连续的，但它的"复杂度"由 $d$ 维体积决定。贪心构造给出了 $5^d$ 的上界——虽是 $d$ 的指数，但是**有限**的。

2. **用几何级数传递保证**：剩余向量每轮缩 $\gamma$ 倍 → 锚点的权值 $\beta_i$ 几何衰减 → 级数有界 → 无穷多锚点上的误差求和收敛到 $O(\epsilon)$。

两者结合：JL 只需对 $5^d$ 个锚点做 union bound（$\to m = O(d/\epsilon^2)$），三角不等式完成剩下的传递。

---

#### 6.3 Count Sketch 作为 Faster OSE — 牺牲维度换速度

##### 6.3.1 动机

Dense OSE（Gaussian 矩阵）每次应用 $\Pi$ 到矩阵 $A$ 需要 $O(mnd)$ 时间——和 dense JL 一样慢。Count Sketch（$\Pi = S D$，第 3 章）只需要和 $A$ 的**非零元数量**成正比的时间。能不能用 Count Sketch 来实现 OSE？

**代价**：目标维度从 $O(d/\epsilon^2)$ 涨到 $\Theta(d^2/(\epsilon^2\delta))$——多了 d 倍。但对稀疏数据（非零元少），计算时间节省远超过维度增加带来的存储开销。

##### 6.3.2 为什么 Count Sketch 做 OSE 更困难？

回顾第 3 章：Count Sketch 作为 JL 矩阵时，**每个向量单独分析**——$(1\pm\epsilon)$ 保证对每个固定向量 $x$ 成立。但 OSE 要求**同时**对整个 d 维子空间中的所有向量成立。

问题的根源：Count Sketch 的每行只随机**采一个**坐标（$\Pi = S \cdot D$，S 的每行只有一个 1）。当多个向量共享同一个被采样的坐标时，它们会"碰撞"——两个不同方向投影后变成了相关变量，分析不再能逐个向量独立进行。

##### 6.3.3 分析策略：重列/轻列分解

设 $U \in \mathbb{R}^{n \times d}$ 是子空间 $T$ 的一组**正交**基（$U^T U = I_d$）。分析 $\|\Pi y\|^2$ 对任意 $y \in T$。

**关键观察**：$y = Uz$ 对某个 $z \in \mathbb{R}^d$（$\|z\|_2 = \|y\|_2$，因为 U 正交）。所以只需分析 $\|\Pi U z\|^2$。

**分解策略**：把 U 的 $d$ 列按 $\ell_2$ 范数从大到小排序：

$$\|U_{*,1}\|_2 \ge \|U_{*,2}\|_2 \ge \cdots \ge \|U_{*,d}\|_2$$

切分点 $s$：前 $s-1$ 列为"重列"（列范数大），第 $s$ 列及以后为"轻列"（列范数小）。

**目的**：重列数量少但贡献大，用无碰撞性确保它们被精确保持；轻列数量多但每列贡献小，用低负载的 Chernoff 控制它们的总误差。

##### 6.3.4 三个事件的联合控制

将 $y = Uz$ 拆成重部分和轻部分：

$$y = U_{\text{heavy}} \cdot z_{\text{heavy}} + U_{\text{light}} \cdot z_{\text{light}} \triangleq y_H + y_L$$

分析 $\|\Pi y\|^2 = \|\Pi(y_H + y_L)\|^2 = \|\Pi y_H\|^2 + \|\Pi y_L\|^2 + 2\langle \Pi y_H, \Pi y_L\rangle$ 中的三项：

| 项 | 控制手段 | 依赖事件 |
|---|---|---|
| $\|\Pi y_H\|^2$ | 重列被哈希到不同桶（无碰撞）→ 精确保持 | $\mathcal{E}_B$（桶碰撞事件） |
| $\|\Pi y_L\|^2$ | 轻列贡献小，Chernoff bound 控制总误差 | $\mathcal{E}_h$（桶负载事件） |
| $2\langle \Pi y_H, \Pi y_L\rangle$ | 交叉项在两个条件下受控 | $\mathcal{E}_C \subseteq \mathcal{E}_B \cap \mathcal{E}_h$ |

**$\mathcal{E}_B$**：哈希函数 $h$ 将所有重列映射到**不同的**桶。重列数量 = $s-1$，取 $m = \Omega(s^2)$ → 无碰撞以高概率成立。在此条件下，轻列和重列的交叉项因 Rademacher 符号的独立性而期望为零。

**$\mathcal{E}_h$**：每个桶中轻列的总 $\ell_2$ 负载不超过某个阈值（Chernoff bound）。轻列 $\ell_2$ 范数衰减 → 负载聚集程度受控。

**$\mathcal{E}_C$**：在 $\mathcal{E}_B \cap \mathcal{E}_h$ 下，交叉项 $|\langle \Pi y_H, \Pi y_L\rangle|$ 不超过 $O(\epsilon)(\|y_H\|^2 + \|y_L\|^2)$。

##### 6.3.5 维度 vs 速度权衡

| | Dense OSE (Gaussian) | Count Sketch OSE |
|---|---|---|
| 目标维度 m | $O(d/\epsilon^2)$ | $\Theta(d^2/(\epsilon^2\delta))$ |
| 应用到 $n \times d$ 矩阵 | $O(mnd)$ | $O(\text{nnz}(A))$（正比于非零元数） |
| 分析工具 | $\gamma$-net | 重列/轻列分解 + 负载分析 |
| 适用场景 | d 小、矩阵稠密 | 矩阵稀疏、非零元远小于 nd |

**核心 tradeoff**：Count Sketch 牺牲了 $d$ 倍维度，换来了"时间不依赖 $n$ 和 $d$ 的乘积，只依赖实际数据量"的快速计算。在第 7.2 节 Sketch-and-Solve 中，用 Count Sketch OSE 替代 Gaussian OSE 可直接加速整个管线。

---

### 7. 应用：从理论到实践

#### 7.1 k-means 聚类的 JL 加速

**场景**：你有 100 万张图片，每张用 1000 维特征表示。想用 k-means 把它们聚成 10 类。每次迭代需要计算每个点到 10 个聚类中心的距离——$10^6 \times 10 \times 1000 = 10^{10}$ 次浮点运算，一次迭代就要几十秒。能不能加速？

**问题**：k-means 反复计算点到聚类中心的距离。n 个 d 维点，每次迭代 $O(nkd)$ 时间。高维时这就是瓶颈——但注意到我们只需要**相对距离**来判定"哪个中心更近"，不需要距离的绝对精确值。JL 正好能在保持所有 pairwise 距离的前提下大幅降维。

**思路**：k-means 的目标函数可以重写成仅依赖 pairwise 距离的形式。JL 保持所有 pairwise 距离 → 先用 JL 降到 $k' = O(\epsilon^{-2}\log n)$ 维，再在低维空间做聚类。低维空间的聚类结果近似比几乎不变，但每轮迭代只需 $O(n \cdot k \cdot k')$ 时间。

**k-means 目标函数**：将 n 个点划分到 k 个簇 $\mathcal{P}_1, \dots, \mathcal{P}_k$，最小化每个点到其簇中心的距离平方和：

$$\min_{\mathcal{P}_1,\dots,\mathcal{P}_k} \sum_{j=1}^k \sum_{i \in \mathcal{P}_j} \|x_i - c_j\|^2, \quad c_j = \frac{1}{|\mathcal{P}_j|}\sum_{i \in \mathcal{P}_j} x_i \text{ 为簇心}$$

**等价重写（Voronoi 分区恒等式）**：下面这个恒等式是整个论证的关键——它说"各点到簇心的距离平方和"可以用"簇内所有点对的距离平方和"来等价表示：

$$\sum_{i \in \mathcal{P}_j} \|x_i - c_j\|^2 = \frac{1}{2|\mathcal{P}_j|}\sum_{i, i' \in \mathcal{P}_j} \|x_i - x_{i'}\|^2$$

**为什么？** 展开左边：$\sum_i \|x_i - c_j\|^2 = \sum_i \|x_i\|^2 - 2\langle \sum_i x_i, c_j \rangle + |\mathcal{P}_j| \cdot \|c_j\|^2$。因为 $c_j = \frac{1}{|\mathcal{P}_j|}\sum_i x_i$，中间项化简为 $-2|\mathcal{P}_j| \cdot \|c_j\|^2$。所以 $= \sum_i \|x_i\|^2 - |\mathcal{P}_j| \cdot \|c_j\|^2$。

展开右边：$\frac{1}{2|\mathcal{P}_j|}\sum_{i,i'} \|x_i - x_{i'}\|^2 = \frac{1}{2|\mathcal{P}_j|}\sum_{i,i'}(\|x_i\|^2 + \|x_{i'}\|^2 - 2\langle x_i, x_{i'}\rangle) = \frac{1}{2|\mathcal{P}_j|}(2|\mathcal{P}_j|\sum_i \|x_i\|^2 - 2\|\sum_i x_i\|^2) = \sum_i \|x_i\|^2 - |\mathcal{P}_j| \cdot \|c_j\|^2$。左边 = 右边 ✓

**这个恒等式的意义**：k-means 目标函数完全由 pairwise 距离决定，和具体坐标无关！而这正是 JL 保证的东西。

因此，总目标函数：
$$\min_{\mathcal{P}_1,\dots,\mathcal{P}_k} \sum_{j=1}^k \frac{1}{|\mathcal{P}_j|}\sum_{i \neq i' \in \mathcal{P}_j} \|x_i - x_{i'}\|^2$$

JL 保持所有 pairwise 距离在 $(1\pm\epsilon)$ 倍，所以降维后的目标函数值在 $(1\pm\epsilon)$ 倍原值以内：
$$\sum_{i\neq i'} \|\Pi x_i - \Pi x_{i'}\|^2 = (1\pm\epsilon)\sum_{i\neq i'} \|x_i - x_{i'}\|^2$$

**最终管线**：先在降维后的空间（$k' \approx 690$ 维，$\epsilon=0.1$, $n=10^6$）做聚类，结果的近似比几乎不变。时间从 $O(n^2 d) = 10^{15}$ 降为 $O(n^2 k' + nkd) = O(10^{12} + 6.9 \times 10^{11})$——快了约 500 倍。

#### 7.2 线性回归的 Sketch-and-Solve — OSE 的核心应用

##### 7.2.1 问题设定与几何视角

**输入**：数据矩阵 $X \in \mathbb{R}^{n \times d}$（n 个样本，d 个特征），标签向量 $y \in \mathbb{R}^n$。

**目标**：找系数向量 $\beta \in \mathbb{R}^d$，最小化残差平方和：

$$\beta^{LS} = \arg\min_{\beta} \|X\beta - y\|_2$$

**一个关键的几何分解**：将 $y$ 分解为 $y = y^\parallel + y^\perp$，其中：
- $y^\parallel$ 是 $y$ 在 $X$ 列空间上的正交投影（**列空间能表示的"最好版本"**）
- $y^\perp$ 正交于 $\text{cols}(X)$（**列空间永远无法触及的剩余**）

**目的**：把残差拆成"可优化部分"和"不可优化常数"。展开残差平方：

$$\|X\beta - y\|^2 = \|X\beta - y^\perp - y^\parallel\|^2 = \|X\beta - y^\parallel\|^2 - 2\langle X\beta - y^\parallel, y^\perp\rangle + \|y^\perp\|^2$$

因为 $X\beta$ 和 $y^\parallel$ 都在列空间内，$X\beta - y^\parallel \in \text{cols}(X)$。而 $y^\perp \perp \text{cols}(X)$ → 交叉项 $\langle X\beta - y^\parallel, y^\perp\rangle = 0$：

$$\|X\beta - y\|^2 = \underbrace{\|X\beta - y^\parallel\|^2}_{\text{可优化}} + \underbrace{\|y^\perp\|^2}_{\text{常数，与 β 无关}}$$

**结论**：最小化 $\|X\beta - y\|$ 等价于最小化 $\|X\beta - y^\parallel\|$。最优解 $\beta^{LS}$ 总能把残差压到列空间能表示的最好水平 $\|y^\perp\|$。

**标准解法**：$\beta^{LS} = (X^T X)^+ X^T y$（$+$ 为伪逆，$X^TX$ 不可逆时也能用）。时间 $O(nd^2)$（SVD）。

**瓶颈**：当样本数 $n$ 极大（百万级）时，$O(nd^2)$ 太慢。但特征数 $d$ 通常很小（几十到几百）——能不能把"大 n"压缩掉？

##### 7.2.2 核心思路：用 OSE 把 n 压到 m

**为什么 OSE 能解决这个问题？** 回顾 OSE 的定义（第 6.1 节）：一个随机矩阵 $\Pi \in \mathbb{R}^{m \times n}$ 是 $\epsilon$-OSE，如果对任意固定的 d 维子空间 $T$，$\Pi$ 保持 $T$ 中**所有**向量的范数在 $(1\pm\epsilon)$ 倍以内。

关键观察：线性回归的残差向量 $X\beta - y$ 始终落在 $\text{span}(\text{cols}(X), y)$ 中，这是一个维度 $\le d+1$ 的子空间。所以如果我们用一个 $\epsilon$-OSE 矩阵 $\Pi$ 去乘，对**所有** $\beta$ 同时有：

$$(1-\epsilon)\|X\beta - y\| \le \|\Pi X\beta - \Pi y\| \le (1+\epsilon)\|X\beta - y\|$$

**"同时"是核心**——不是对某一个 $\beta$ 成立，而是对整个 $\mathbb{R}^d$ 中所有 $\beta$ 同时成立。这意味着压缩后的最小化问题的最优解，在原问题上也近似最优。

##### 7.2.3 Sketch-and-Solve 的具体步骤

**第 1 步：压缩（Sketch）**

选取 $\epsilon$-OSE 矩阵 $\Pi \in \mathbb{R}^{m \times n}$，其中 $m = O(d/\epsilon^2)$。计算：

$$\tilde{X} = \Pi X \in \mathbb{R}^{m \times d}, \quad \tilde{y} = \Pi y \in \mathbb{R}^m$$

**目的**：把 $n \times d$ 的大矩阵变成 $m \times d$ 的小矩阵。$m$ 只依赖 $d$ 和 $\epsilon$，**不依赖 $n$**。当 $n \gg d$ 时（如 $n=10^6, d=50$），$m \approx 50/0.01 = 5000 \ll 10^6$。

**第 2 步：在小版本上求解（Solve）**

$$\tilde{\beta}^{LS} = \arg\min_{\beta} \|\tilde{X}\beta - \tilde{y}\|_2 = \arg\min_{\beta} \|\Pi X\beta - \Pi y\|_2$$

在 $m \times d$ 的小矩阵上求解，时间 $O(md^2) = O(d^3/\epsilon^2)$。

**第 3 步：直接使用 $\tilde{\beta}^{LS}$ 作为原问题的近似解。**

##### 7.2.4 近似比推导 — 为什么 $\tilde{\beta}^{LS}$ 足够好

设 $\beta^{LS}$ 是原问题的真正最优解，$\tilde{\beta}^{LS}$ 是压缩后的最优解。要证 $\tilde{\beta}^{LS}$ 的残差不超过 $\beta^{LS}$ 残差的 $\frac{1+\epsilon}{1-\epsilon} \approx 1+2\epsilon$ 倍。

**推导分三步，每步的目的不同**：

**步骤 (a)：从压缩残差恢复到原残差（用到 OSE 下界）**

由 OSE 定义，对所有 $\beta$（包括 $\tilde{\beta}^{LS}$）有下界保证：

$$\|\Pi X\tilde{\beta}^{LS} - \Pi y\| \ge (1-\epsilon)\|X\tilde{\beta}^{LS} - y\|$$

移项得：

$$\|X\tilde{\beta}^{LS} - y\| \le \frac{1}{1-\epsilon}\|\Pi X\tilde{\beta}^{LS} - \Pi y\|$$

**目的**：把"原空间中的残差"和"压缩空间中的残差"挂上钩。OSE 给了双向不等式，这里用的是下界方向（把压缩残差"放大"回原残差）。

**步骤 (b)：压缩版本的最优性（用到 $\tilde{\beta}^{LS}$ 的定义）**

$\tilde{\beta}^{LS}$ 是压缩空间中的**最优解**——任何其他 $\beta$（包括真正的 $\beta^{LS}$）在压缩空间中的残差都不会比它更小：

$$\|\Pi X\tilde{\beta}^{LS} - \Pi y\| \le \|\Pi X\beta^{LS} - \Pi y\|$$

**目的**：这是 trivial 的一步——"压缩版最优解在压缩空间中不差于任何其他解"。但它是把链从 $\tilde{\beta}^{LS}$ 转向 $\beta^{LS}$ 的关键转折。

**步骤 (c)：从原最优到压缩空间（用到 OSE 上界）**

由 OSE 定义，上界方向对 $\beta^{LS}$ 给出：

$$\|\Pi X\beta^{LS} - \Pi y\| \le (1+\epsilon)\|X\beta^{LS} - y\|$$

**目的**：把压缩空间中 $\beta^{LS}$ 的残差，用原空间中 $\beta^{LS}$ 的残差来 bound。

**串联**：(a) → (b) → (c)：

$$\|X\tilde{\beta}^{LS} - y\| \le \frac{1}{1-\epsilon} \cdot \|\Pi X\tilde{\beta}^{LS} - \Pi y\| \le \frac{1}{1-\epsilon} \cdot \|\Pi X\beta^{LS} - \Pi y\| \le \frac{1+\epsilon}{1-\epsilon}\|X\beta^{LS} - y\|$$

**近似比** $\frac{1+\epsilon}{1-\epsilon}$ 对小的 $\epsilon$ 用泰勒展开：$\frac{1+\epsilon}{1-\epsilon} = (1+\epsilon)(1+\epsilon+\epsilon^2+\dots) \approx 1+2\epsilon$。

##### 7.2.5 为什么 $m = O(d/\epsilon^2)$ 而不是 JL 的 $O(\epsilon^{-2}\log n)$？

这是 OSE 和 JL 最关键的差异。回顾 $\gamma$-net 论证：

- **JL**：需要对 $\binom{n}{2} = O(n^2)$ 对离散点做 union bound → 目标维度含 $\log(n^2) = O(\log n)$
- **OSE**：需要对 $\gamma$-net 上的 $\le 5^d$ 个"锚点"做 union bound → 目标维度含 $\log(5^d) = O(d)$

OSE 的维度只依赖子空间维度 $d$，不依赖样本数 $n$——因为一个 d 维子空间的"几何复杂度"由 $5^d$（有限！）而非 $n$（可以任意大）决定。

##### 7.2.6 时间和空间对比

| | 原始 | Sketch-and-Solve |
|---|---|---|
| 矩阵大小 | $n \times d$ | $m \times d$，$m = O(d/\epsilon^2)$ |
| 求解时间 | $O(nd^2)$ | $O(md^2) = O(d^3/\epsilon^2)$ |
| 依赖 $n$？ | 线性 | **不依赖** |

**数值例子**：$n=10^6, d=50, \epsilon=0.1$。原始方法 $O(10^6 \times 2500)$，压缩后 $O(5000 \times 2500)$——快约 200 倍，且差距随 $n \to \infty$ 无限拉大。

---

#### 7.3 用 OSE 加速梯度下降 — 预处理

##### 7.3.1 问题：为什么梯度下降需要预处理？

Sketch-and-Solve 给了近似闭式解。但如果想用**梯度下降（GD）**迭代求解呢？

GD 的收敛速度由 $X$ 的**条件数** $\kappa(X) = \sigma_{\max}(X) / \sigma_{\min}(X)$ 决定。直观：如果 $X$ 的奇异值从很小到很大都有（条件数大），误差函数的等高线是"又长又窄的峡谷"——GD 会在峡谷里 zigzag，收敛极慢。

**但我们可以预处理！** 找一个矩阵 $R \in \mathbb{R}^{d \times d}$，让 $XR$ 的奇异值全部集中在 $[1, 1/\sqrt{2}]$ 内（条件数 $\le 1/\sqrt{2} \approx 0.707$）。然后对 $XR$ 做 GD，每步误差减半。

##### 7.3.2 为什么 OSE 能做预处理？

**关键洞察**：如果我们能对 $X$ 做一次"廉价的 SVD 近似"，就能构造出 $R$。OSE 正好提供了这个能力——用一个很小的随机矩阵 $\Pi$ 压缩 $X$，然后在压缩后的小矩阵上做 SVD。

**具体步骤**：

**第 1 步：用一个 1/2-OSE 矩阵 $\Pi \in \mathbb{R}^{m \times d}$ 压缩**（$m = O(d)$）：

$$\tilde{X} = \Pi X \in \mathbb{R}^{m \times d}$$

**目的**：OSE 保证 $\|\tilde{X}z\| \approx \|Xz\|$ 对所有 $z \in \mathbb{R}^d$ 成立。$X$ 的奇异值信息被"编码"在 $\tilde{X}$ 中。

**第 2 步：对小矩阵 $\tilde{X}$ 做 SVD**（$m$ 小，便宜）：

$$\tilde{X} = U' \Sigma' V'^T$$

**目的**：得到 $V'$（右奇异向量）和 $\Sigma'$（奇异值对角矩阵）。因为 $\tilde{X}$ 只有 $m \times d$ 大（$m = O(d)$），这个 SVD 只需 $O(md^2) = O(d^3)$ 时间——远快于对原矩阵 $X$（$n \times d$）做 SVD 的 $O(nd^2)$。

**第 3 步：构造预处理矩阵**：

$$R = V'(\Sigma')^{-1}$$

**第 4 步：验证 $XR$ 的条件数**。对任意单位向量 $z \in \mathbb{R}^d$：

$$\|XRz\| = \|X \cdot V'(\Sigma')^{-1} z\|$$

由 OSE 保证，$\|Xw\| \approx \|\tilde{X}w\|$ 对所有 $w$。取 $w = V'(\Sigma')^{-1}z$：

$$\|XRz\| \approx \|\tilde{X}V'(\Sigma')^{-1}z\| = \|U'\Sigma'V'^T V'(\Sigma')^{-1}z\| = \|U'z\| = \|z\| = 1$$

因为 $U'$ 的列是正交的，$\|U'z\| = \|z\|$。由于 OSE 用的是 $1/2$-OSE（$\epsilon = 1/2$），近似区间是 $[1/2, 3/2]$，即：

$$\frac{1}{2} \le \|XRz\| \le \frac{3}{2}$$

通过适当的常数缩放，可以把所有奇异值夹在 $[1, 1/\sqrt{2}]$ 内。

**本质**：$\tilde{X}$ 的 SVD 是 $X$ 的 SVD 的一个"低精度预览"——精度够用来做预处理，但计算成本低了 $n/m$ 倍。

##### 7.3.3 预处理后的梯度下降 — 完整收敛性推导

**场景**：我们不做 Sketch-and-Solve 的一次性求解，而是想用梯度下降**迭代**逼近最优 $\beta$。问题是——如果 $X$ 的列有些"方向"很敏感（大奇异值）、有些很迟钝（小奇异值），梯度下降会在峡谷里 zigzag，收敛极慢。第 7.3.2 节的 OSE 预处理解决了这个问题——它把 $X$ 变成 $XR$，使所有方向的敏感度变得均匀（奇异值聚集在 1 附近）。现在要严格证明：预处理后的 GD 确实每步误差减半。

**梯度下降的更新规则**：对 $f(\beta) = \|X\beta - y\|^2$，梯度 $\nabla f(\beta) = 2X^TX\beta - 2X^Ty$。取步长 $\gamma = 1/2$：

$$\beta^{(t)} = \beta^{(t-1)} - \frac{1}{2}\nabla f(\beta^{(t-1)}) = \beta^{(t-1)} + X^Ty - X^TX\beta^{(t-1)}$$

**要证**：如果 $X$ 的奇异值全在 $1 \pm 1/\sqrt{2}$ 内，则 $\|X(\beta^{(t)} - \beta^{LS})\| \le \frac{1}{2}\|X(\beta^{(t-1)} - \beta^{LS})\|$。

---

**第 1 步：展开误差递推式**

$$X(\beta^{(t)} - \beta^{LS}) = X(\beta^{(t-1)} + X^Ty - X^TX\beta^{(t-1)} - \beta^{LS})$$

$$= (X - XX^TX)\beta^{(t-1)} + XX^Ty - X\beta^{LS}$$

**目的**：把 $\beta^{(t)}$ 的迭代式代入，分离出 $\beta^{(t-1)}$ 的系数和常数项。

**第 2 步：处理 $XX^Ty$ 项 — 用到"$X\beta^{LS} = y^\parallel$"**

在 7.2.1 的几何分解中，$\beta^{LS}$ 的残差 $X\beta^{LS} - y$ 与列空间正交 → $X\beta^{LS} = y^\parallel$（投影）。

由此 $\beta^{LS} = (X^TX)^+X^Ty$。关键代数恒等式（伪逆性质）：$XX^TX(X^TX)^+X^Ty = XX^Ty$，即 $XX^TX\beta^{LS} = XX^Ty$。

**目的**：把"与 $y$ 有关的常数项"转成"与 $\beta^{LS}$ 有关的项"，和 $X\beta^{LS}$ 合并。

**第 3 步：代入化简**

$$X(\beta^{(t)} - \beta^{LS}) = (X - XX^TX)\beta^{(t-1)} + XX^TX\beta^{LS} - X\beta^{LS}$$

$$= (X - XX^TX)(\beta^{(t-1)} - \beta^{LS})$$

**目的**：误差递推被干净地写成"上一轮误差左乘固定矩阵 $(X - XX^TX)$"。这一步是整个推导的结构性转折。

**第 4 步：用 SVD 分析 $X - XX^TX$**

**SVD 是什么？** SVD（奇异值分解）把任意矩阵 $X$ 拆成三个矩阵的乘积：$X = U\Sigma V^T$。其中 $U$ 和 $V$ 是正交矩阵（只做旋转/反射，不改变向量长度），$\Sigma$ 是对角矩阵（对角线上是奇异值 $\sigma_1, \dots, \sigma_d$，每个 $\sigma_i$ 表示 $X$ 在第 i 个"方向"上的拉伸/压缩倍数）。直观类比：任何线性变换 = 旋转 → 拉伸 → 旋转回来，SVD 就是把这三个动作拆开。

设 $X = U\Sigma V^T$ 是 $X$ 的 SVD（$U \in \mathbb{R}^{n \times d}$ 列正交，$\Sigma$ 为 $d \times d$ 对角奇异值矩阵，$V \in \mathbb{R}^{d \times d}$ 正交）。则：

$$X^TX = V\Sigma^2 V^T, \quad XX^TX = U\Sigma V^T \cdot V\Sigma^2 V^T = U\Sigma^3 V^T$$

所以：

$$X - XX^TX = U\Sigma V^T - U\Sigma^3 V^T = U \cdot \Sigma(I - \Sigma^2) \cdot V^T$$

**目的**：把晦涩的矩阵 $(X - XX^TX)$ 用 SVD 对角化——奇异向量 $U, V$ 只负责"旋转"，真正的"缩放"由对角矩阵 $\Sigma(I - \Sigma^2)$ 决定。

**第 5 步：代回递推式，逐个剥离正交矩阵**

$$\|X(\beta^{(t)} - \beta^{LS})\| = \|U \cdot \Sigma(I - \Sigma^2) \cdot V^T(\beta^{(t-1)} - \beta^{LS})\|$$

$U$ 列正交 → $\|Uw\| = \|w\|$（保范数）：

$$= \|\Sigma(I - \Sigma^2) \cdot V^T(\beta^{(t-1)} - \beta^{LS})\|$$

**目的**：$U$ 消失——因为正交矩阵不改变范数，误差的大小由 $\Sigma$ 决定。

**第 6 步：分离 $\Sigma$ 和 $(I - \Sigma^2)$（关键不等式）**

$\Sigma(I - \Sigma^2)$ 是对角矩阵（$\Sigma$ 和 $I-\Sigma^2$ 都是对角的，可交换）。令 $D = I - \Sigma^2$（$d \times d$ 对角），$w = \Sigma V^T(\beta^{(t-1)} - \beta^{LS}) \in \mathbb{R}^d$。

$$\|\Sigma(I - \Sigma^2)V^T(\beta^{(t-1)} - \beta^{LS})\| = \|D \cdot w\|$$

对对角矩阵 $D$：$\|Dw\|^2 = \sum_i d_i^2 w_i^2$。用 Cauchy-Schwarz 放缩：

$$\sum_i d_i^2 w_i^2 \le \left(\sum_i d_i^2\right) \cdot \left(\sum_j w_j^2\right) = \|D\|_F^2 \cdot \|w\|^2$$

所以：

$$\|D w\| \le \|D\|_F \cdot \|w\| = \|I - \Sigma^2\|_F \cdot \|\Sigma V^T(\beta^{(t-1)} - \beta^{LS})\|$$

**目的**：把 $I-\Sigma^2$ 和 $\Sigma$ 分离开——前者给出收缩因子 $\|I-\Sigma^2\|_F$，后者和 $V^T$ 组合回 $X$。

**第 7 步：$w$ 的范数 = 上一轮误差的范数**

$$\|\Sigma V^T(\beta^{(t-1)} - \beta^{LS})\| = \|U\Sigma V^T(\beta^{(t-1)} - \beta^{LS})\| = \|X(\beta^{(t-1)} - \beta^{LS})\|$$

（补上 $U$ 不改变范数，$U\Sigma V^T = X$）

**目的**：$w$ 的范数恰好就是上一轮误差，不需要额外 bound——得到纯倍增形式的递推。

**第 8 步：组装 — 干净的递推不等式**

$$\boxed{\|X(\beta^{(t)} - \beta^{LS})\| \le \|I - \Sigma^2\|_F \cdot \|X(\beta^{(t-1)} - \beta^{LS})\|}$$

**第 9 步：为什么 $\|I - \Sigma^2\|_F \le 1/2$？**

经过 $R$ 预处理（7.3.2 节）后，$XR$ 的所有奇异值 $\sigma_i$ 落在 $1 \pm 1/\sqrt{2}$ 附近。对每个 $\sigma_i$：

$$|1 - \sigma_i^2| = |(1-\sigma_i)(1+\sigma_i)| \le \frac{1}{\sqrt{2}} \cdot (2 + \frac{1}{\sqrt{2}}) \approx 1.9 \text{（这个bound太松）}$$

更精确的界来自直接验证：$\sigma_i \in [0.7, 1.3]$（1/2-OSE 的保证）→ $|1 - \sigma_i^2| \le 1/2$。

幻灯片中用**谱范数**（spectral norm，记为 $\|\cdot\|_2$）而非 Frobenius 范数给出更紧的 bound。两者的区别：Frobenius 范数 $\|D\|_F = \sqrt{\sum_i d_i^2}$ 是所有奇异值的"平方和开根"，谱范数 $\|D\|_2 = \max_i |d_i|$ 是"最大的那个奇异值"。显然 $\|D\|_2 \le \|D\|_F$，所以用谱范数能得到更小的收缩因子：

$$\|I - \Sigma^2\|_2 = \max_i |1 - \sigma_i^2| \le \frac{1}{2}$$

所以每步误差至少减半 —— $\frac{1}{2}$ 收缩因子。

---

**推导链总结**：

```
β^{(t)} = β^{(t-1)} + X^Ty - X^TXβ^{(t-1)}     (GD 更新)
    ↓ 代入 Xβ^{LS} = y∥, XX^Ty = XX^TXβ^{LS}
X(β^{(t)}−β^{LS}) = (X−XX^TX)(β^{(t-1)}−β^{LS})
    ↓ SVD: X = UΣV^T, XX^TX = UΣ³V^T
= U·Σ(I−Σ²)·V^T(β^{(t-1)}−β^{LS})
    ↓ 剥 U (保范数), 分离 Σ 和 I−Σ²
∥error^{(t)}∥ ≤ ∥I−Σ²∥_F · ∥ΣV^T(β^{(t-1)}−β^{LS})∥
    ↓ ∥ΣV^T(β^{(t-1)}−β^{LS})∥ = ∥X(β^{(t-1)}−β^{LS})∥
∥error^{(t)}∥ ≤ ∥I−Σ²∥_F · ∥error^{(t-1)}∥
    ↓ OSE 预处理保证 ∥I−Σ²∥₂ ≤ 1/2
∥error^{(t)}∥ ≤ (1/2) · ∥error^{(t-1)}∥
    ↓ O(log 1/ε) 轮收敛
```

**变量代换**：令 $\alpha = R^{-1}\beta$，原问题 $\min_\beta \|X\beta - y\|$ 等价于 $\min_\alpha \|XR\alpha - y\|$。每轮 GD 更新 $\alpha^{(t)} = \alpha^{(t-1)} + (XR)^Ty - (XR)^T(XR)\alpha^{(t-1)}$，每轮 $O(nd)$。收敛后 $\beta = R\alpha$ 恢复原变量。

##### 7.3.4 Sketch-and-Solve vs 预处理 GD

| | Sketch-and-Solve | 预处理 GD |
|---|---|---|
| 输出 | 近似闭式解 | 迭代序列 |
| OSE 用途 | 直接压缩数据矩阵 | 压缩后做 SVD → 预处理矩阵 |
| 核心时间 | $O(d^3/\epsilon^2)$ | $O(nd \log(1/\epsilon) + d^3)$ |
| 依赖 $n$？ | 不依赖（压缩后 $n$ 消失） | 每轮 $O(nd)$（仍要扫数据） |
| 适用场景 | $n$ 极大时碾压 | $n$ 适中且要更高精度时 |

两条路依赖同一个核心洞察：**OSE 让你在 $O(d/\epsilon^2)$ 维的小空间里"预览"原 d 维子空间的所有几何性质——范数、距离、奇异值——预览的代价远低于在原空间直接计算。**

---

## 难点突破

### 难点 1：JL 证明中 $\chi^2$ 分布的 Chernoff bound

**容易卡住的地方**：从 $\|Au\|^2 = \sum (Au)_i^2$ 跳到"这服从 $\chi^2(k)/k$"，再到"对 $\chi^2$ 用 Chernoff"，中间缺了一步。

**关键链**：
1. 每个 $(Au)_i \sim \mathcal{N}(0, 1/k)$ → $X_i = \sqrt{k}(Au)_i \sim \mathcal{N}(0,1)$
2. $\sum (Au)_i^2 = \frac{1}{k}\sum X_i^2$，且 $X_i$ 独立
3. $\sum X_i^2 \sim \chi^2(k)$，$\mathbb{E}[\chi^2(k)] = k$ → $\mathbb{E}[\|Au\|^2] = 1$
4. 对 $\chi^2(k)$ 的尾概率：$Pr[\chi^2(k) > (1+\epsilon)k] < e^{-\epsilon^2 k/8}$（通过 MGF $e^{\lambda X_i^2}$，利用 $\mathbb{E}[e^{\lambda X^2}] = 1/\sqrt{1-2\lambda}$ 对 $\lambda<1/2$，选 $\lambda=\epsilon/4$ 或 $\epsilon/(2(1+\epsilon))$）

**类比**：这和普通 Chernoff（独立伯努利和）的逻辑完全相同，只是矩母函数换成了 $X^2$ 而非 X 的 MGF。

### 难点 2：$\gamma$-net — 为什么把无限的子空间变有限

**为什么卡住**：JL 只保证**有限**个点，子空间有**无限**个点。怎么说 OSE 比 JL"更容易"？

**突破思路**：
1. 子空间是 d 维 → 所有信息在 d 个基向量中。但基向量不一定在单位球面上。
2. 类比：不必数清沙滩上每粒沙——用网格覆盖。$\gamma$-net 就是这个网格。
3. d 维球的"复杂度"由 net 大小 $5^d$ 量度——仍是指数，但**有限**。
4. 对 net 中每个点用 JL → union bound 只需 $5^d$ 次 → $O(d/\epsilon^2)$ 维。
5. net 以外的点通过级数分解为 net 点之和 → 三角不等式传递误差。

**关键对比**：
|  | JL | OSE |
|--|-----|------|
| 保证对象 | n 个点 | 整个 d 维子空间 |
| 复杂度量度 | 点对数 $O(n^2)$ | net 大小 $5^d$ |
| 目标维度 | $O(\epsilon^{-2}\log n)$ | $O(d/\epsilon^2)$ |
| 谁更省维度 | 当 $d \gg \log n$ 时 JL 胜 | 当 $d \ll \log n$ 时 OSE 胜 |

---

## 与前章关联

- **[[02-Hashing]]**：Chernoff Bound（JL 证明、Hamming 空间降维、LSH 分析的核心工具）；Universal Hashing（LSH 哈希族的随机性来源）；$\chi^2$ 的 Chernoff 和第 2 章伯努利和的 Chernoff 共享相同的 MGF 技术路线
- **[[03-Sketching]]**：Count Sketch 作为 ±1 矩阵（第 32-33 页证明其"不比 Gaussian 差"）→ 是 JL 的特例；且 Count Sketch 作为 OSE（第 88-90 页）速度快于 dense JL；第 3 章的"基本版→+版→++版"模式在本章 LSH 的 tensorization + multiple hash tables 中再次出现

**跨章技术线**：
- Markov → Chebyshev → Chernoff → Hoeffding → Khintchine → Azuma 构成了"概率集中不等式"的完整升级路径
- "随机化 + 独立副本 + Union bound / Boosting"是第 1-4 章共用的设计范式

---

## 记忆卡片

**Q1**: JL 定理的核心结论？
**A**: n 个任意维度的点可嵌入 $k = O(\epsilon^{-2}\log n)$ 维，所有 pairwise 距离保持 $(1\pm\epsilon)$ 倍。k 不依赖原始维度 d。

**Q2**: Gaussian JL 证明的四步？
**A**: (1) 归约到单位向量 → (2) $(Au)_i \sim \mathcal{N}(0,1/k)$ → (3) $\|Au\|^2 \sim \chi^2(k)/k$ → (4) $\chi^2$ 的 Chernoff bound + Union bound。

**Q3**: LSH 的参数 $\rho = \log p / \log q$ 决定什么？
**A**: 空间 $O(n^{1+\rho})$，查询时间 $O(n^\rho \log n)$。$\rho$ 越小越好。汉明空间简单 LSH 有 $\rho \approx 1/c$。

**Q4**: FJLT 中为什么需要 Hadamard 变换？
**A**: Hadamard + Rademacher (HD) 将向量"均匀化"——通过 Khintchine 不等式保证 $\ell_{\infty}$ 范数低，从而使后续随机采样方差可控。没有这步，$(0,...,\sqrt{d},...)$ 类峰值向量的采样方差爆炸。

**Q5**: OSE 和 JL 的区别？
**A**: JL 保证 n 个点，目标维度 $O(\epsilon^{-2}\log n)$；OSE 保证整个 d 维子空间，目标维度 $O(d/\epsilon^2)$。OSE 通过 $\gamma$-net argument 证明：只需嵌入约 $5^d$ 个"骨架"点即可保证整个子空间。

**Q6**: $\gamma$-net 的大小为什么是 $O(5^d)$？
**A**: d 维单位球面上最多容纳 $(3/\gamma)^d$ 个互不重叠的 $\gamma/2$-球。取 $\gamma \le 1/2$ 得 $\le 5^d$。

**Q7**: LSH 的 tensorization 原理？
**A**: 1 个 $(r,cr,p,q)$-LSH → k 个独立副本组合成 $g(x) = (h_1(x),...,h_k(x))$ → $(r,cr,p^k,q^k)$-LSH。取 $k = \log_{1/q}n$ 使远端碰撞概率 $\le 1/n$，近端碰撞概率 $= n^{-\rho}$。

---

## 💬 学习对话补充

### 2026-05-18：全章重组与基础概念澄清 — 从"看懂公式"到"理解每步的物理意义"

**类型：** 深化 + 澄清

**背景：** 用户在第 4 章学习中发现了两个层面的需求。第一是笔记结构层面：原笔记只有简要概述，缺少从 PDF 课件中提取的完整推导（JL 证明、LSH 分析、FJLT 的 Khintchine 论证、OSE 的 γ-net 论证等）。第二是基础符号层面：用户在阅读过程中主动追问了多个"看起来简单但如果不搞懂就卡住"的符号问题——$\|\cdot\|$ 到底是什么、pairwise 是什么、$\mathcal{N}(0,1/k)$ 的 $\mathcal{N}$ 指什么、$A_{ij}$ 是一个数还是一个矩阵、$Au$ 是向量还是映射。

**讨论过程：**

全章重组采用了和第 3 章相同的整合策略——将"前置知识 + 核心概念 + 完整推导"合并到一个位置。新增了约 60 行的前置知识部分，从度量空间的公理化定义出发，引入欧氏空间和汉明空间作为本章两个主要场景，然后补上范数的定义和三种常用范数（$\ell_2$、$\ell_2^2$、$\ell_{\infty}$）及其在笔记中的具体含义。降维问题的形式化中补充了 pairwise 的解释（n 个点共 $n(n-1)/2$ 对），Metric Embedding 视角补充了失真的严格定义。

核心概念部分将原来 12 个简要小节合并重组为 7 个完整小节，每个都包含完整推导：JL 定理补充了 Gaussian 的完整五步证明（归约→分布→$\chi^2$→Chernoff→Union bound）和 Random Subspace 的对称性论证；Hamming 空间降维补充了 Bernoulli 矩阵的单行碰撞概率引理和 s 阈值的构造；LSH 框架补充了 tensorization、$\rho$ 参数推导、完整数据结构的空间/时间分析和正确性证明；FJLT 补充了朴素采样失败的原因（峰值向量的四阶矩爆炸）、Khintchine 不等式的完整证明、以及条件于低 $\ell_{\infty}$ 范数的 Chernoff 收尾；OSE 补充了 $\gamma$-net 的贪心构造、大小上界、级数分解和交叉项控制的全流程；最后新增了 k-means 加速、线性回归 Sketch-and-Solve、梯度下降预处理三个应用场景。

符号澄清方面，用户问了四个问题：(1) $\|\cdot\|$ 是范数符号，$\|x\|_2$ = 欧氏长度，$\|x\|_2^2$ = 长度的平方；(2) pairwise = 两两之间，JL 保证的是所有 $n(n-1)/2$ 对距离都保持；(3) $\mathcal{N}$ 是正态分布的标准记号，$\mathcal{N}(0,1/k)$ = 均值 0、方差 $1/k$；(4) $A_{ij}$ 是矩阵的一个标量元素，$A$ 整体是从 $\mathbb{R}^d$ 到 $\mathbb{R}^k$ 的线性映射，$Au$ 是映射后的 k 维输出向量。这些澄清都已直接补入笔记正文中对应符号首次出现的位置。

**核心收获：** 用户从依赖"别人整理好的笔记"进入到能独立阅读原始证明的层次。关键认知跃迁包括：JL 证明不是魔法而是一条清晰的五步链；$\chi^2$ 的 Chernoff 和第 2 章伯努利和的 Chernoff 本质是同一技术换了个 MGF；$\gamma$-net 是"用有限覆盖无限"的经典分析技巧，在算法理论中反复出现；LSH 的 $\rho$ 参数本质上是哈希碰撞概率在 log 尺度下的比值，决定了近点和远点在哈希空间中的分离度。

**延伸思考：** 第 4 章和第 3 章共享同一个概率工具箱（Markov → Chebyshev → Chernoff → Hoeffding → Khintchine）。FJLT 中 Khintchine 不等式的证明和第 2 章 Chernoff 的证明使用了相同的"指数变换 + MGF bound + 参数最优化"三步走技术。LSH 的 boosting（多个 hash table）和第 3 章的 Morris++（median-of-means）是同一设计模式在不同问题上的体现——独立副本 + 取最优 → 失败概率指数衰减。

### 2026-05-25：FJLT 后半 + OSE + 线性回归 — 逐行推导与几何直觉

**类型：** 深化 + 推导补充

**讨论过程：**

本次复习聚焦于第四章后半部分：FJLT 的概率保证（Khintchine 不等式）、OSE 的 $\gamma$-net 论证、以及线性回归的两个应用（Sketch-and-Solve 和 GD 预处理）。用户多次要求"写出每一步的目的"，由此形成了与前几章一致的"带目的标注的逐步推导"风格。

**FJLT 部分**的核心突破是 Khintchine 不等式的完整证明。此前笔记中只有三行压缩版（"$\cosh \le \exp$ + 取最优 t"），本次补充了七步推导——从 Markov + 指数起手，经泰勒展开和奇偶项分离（奇数抵消、偶数翻倍），用 $(2k)! \ge k! \cdot 2^k$ 放缩回指数形式，最后参数最优化得到 $e^{-\lambda^2/(2\|x\|^2)}$ 的尾概率。用户认识到 Khintchine 和 Gaussian Chernoff 的结构完全对应：都是"Markov + MGF + 参数最优化"，差别只在 MGF 的处理方式（Gaussian 用 $\mathbb{E}[e^{\lambda X^2}] = 1/\sqrt{1-2\lambda}$，Rademacher 用泰勒展开）。

**OSE 部分**的核心认知跃迁是从"保证 n 个点"到"保证整个子空间"的桥梁——$\gamma$-net。用户理解了为什么 OSE 的 $m = O(d/\epsilon^2)$ 不含 $\log n$：union bound 的对象从 $\binom{n}{2}$ 对离散点变成了 $\le 5^d$ 个锚点。七步 $\gamma$-net 论证中，最关键的是"级数分解 + 几何衰减 + 三角不等式传递"三步——任意向量被写成锚点的加权和，权值以 $\gamma^{i-1}$ 指数衰减，保证误差项求和收敛到 $O(\epsilon)$。

**线性回归部分**补充了两个关键推导：(1) 几何分解 $y = y^\parallel + y^\perp$ 解释为什么残差 = 可优化部分 + 不可优化常数；(2) GD 收敛的九步 SVD 推导——从 $\beta^{(t)} = \beta^{(t-1)} + X^Ty - X^TX\beta^{(t-1)}$ 展开，经 $XX^Ty = XX^TX\beta^{LS}$ 恒等式化简为 $(X - XX^TX)(\beta^{(t-1)} - \beta^{LS})$，SVD 对角化得 $U\Sigma(I-\Sigma^2)V^T$，用 $\|Dw\| \le \|D\|_F\|w\|$ 分离出收缩因子 $\|I-\Sigma^2\|$，最后 OSE 预处理保证 $\|I-\Sigma^2\|_2 \le 1/2$。

**核心收获：** 用户能从原始课件（带符号的幻灯片）出发，追问推导目的并逐步填充笔记。关键认知包括：$(2k)! \ge k! \cdot 2^k$ 不是魔法而是"扔掉奇数因子"；$\gamma$-net 是"比 JL 更便宜地保证更多东西"的反直觉结论——子空间的连续无穷集合比离散有限点集在 union bound 意义上更"小"；GD 收敛速度的 SVD 推导本质是 $X - XX^TX$ 的谱分析——收缩因子恰好是 $|1-\sigma_i^2|$。

**课件进度：** 读到第 6.3 节（OSE / 线性回归），剩余 7.1（k-means）及全章收尾未读，计划 5.26 完成。
