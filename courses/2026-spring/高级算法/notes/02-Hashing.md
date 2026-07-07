---
title: "Hashing — 哈希、负载均衡与字典数据结构"
course: "高级算法"
tags: ["hashing", "balls-into-bins", "Chernoff", "Cuckoo", "perfect-hashing", "universal-hashing"]
created: 2026-05-15
source: "Hashing.pdf"
status: reviewed
related: ["01-Fingerprinting", "03-Sketching", "04-Dimension"]
chapter: 2
---

## 一句话总结

哈希不止是"算个地址存数据"——从 Balls into Bins 的概率分析出发，逐步构建出完美哈希（FKS）、布谷鸟哈希（Cuckoo）、简洁字典等一套完整的数据结构理论体系。

## 知识地图

```mermaid
flowchart TD
    BIB[Balls into Bins] --> OP[Occupancy Problem<br>最大负载]
    BIB --> BP[Birthday Paradox<br>碰撞概率]
    BIB --> P2C[Power of Two Choices]

    OP --> CH[Chaining 链地址法]
    OP --> CB[Chernoff Bound]

    CB --> UPPER[上尾界 1+δ]
    CB --> LOWER[下尾界 1-δ]
    CB --> GEN[广义Chernoff<br>k-wise独立版本]

    BP --> PH1[1-level Perfect Hashing<br>m=n², 无碰撞]
    PH1 --> FKS[FKS 2-level Perfect Hashing<br>O(n) space, O(1) query]

    P2C --> CUCKOO[Cuckoo Hashing<br>布谷鸟哈希]
    CUCKOO --> CG[Cuckoo Graph 分析]
    CUCKOO --> RES[O(1) expected amortized update<br>2 probes query]

    PH1 --> UH[Universal Hashing<br>k-universal family]
    UH --> LC[Linear Congruential<br>2-wise independent]
    UH --> TAB[Tabulation Hashing<br>3-universal, fast in practice]

    FKS --> SD[Succinct Dictionary<br>(1+o(1))n space]
```

## 核心概念

### 1. Balls into Bins（球与桶模型）

**是什么**：将 m 个球独立均匀随机地投入 n 个桶。这是分析所有哈希数据结构的统一数学模型。

**关键结论**（通过 Chernoff + Union Bound）：
- m = n 时，最大负载 = **O(log n / log log n)** w.h.p.
- m ≥ n ln n 时，最大负载 = **O(m/n)** w.h.p.

**边际分布**：每个桶 i 接收的球数 Xᵢ ~ Bin(m, 1/n)，𝔼[Xᵢ] = m/n。

### 2. Chernoff Bound（切尔诺夫界）

**是什么**：对独立 0-1 随机变量之和的集中不等式，比 Markov/Chebyshev 强得多。

**上尾界**（δ > 0）：$$Pr[X \geq (1+\delta)\mu] \leq \left(\frac{e^\delta}{(1+\delta)^{1+\delta}}\right)^\mu$$

**下尾界**（0 < δ < 1）：$$Pr[X \leq (1-\delta)\mu] \leq \left(\frac{e^{-\delta}}{(1-\delta)^{1-\delta}}\right)^\mu$$

**常用简化形式**：
- 0 < δ < 1：$Pr[X \geq (1+\delta)\mu] \leq e^{-\mu\delta^2/3}$
- 0 < δ < 1：$Pr[X \leq (1-\delta)\mu] \leq e^{-\mu\delta^2/2}$
- L ≥ 2eμ：$Pr[X \geq L] \leq 2^{-L}$

**证明核心**：Chernoff 技巧 = Markov 不等式 + 矩母函数（MGF）
$$Pr[X \geq a] = Pr[e^{tX} \geq e^{ta}] \leq e^{-ta} \cdot \mathbb{E}[e^{tX}]$$

MGF 上界：$\mathbb{E}[e^{tX}] \leq e^{(e^t-1)\mu}$

取 t = ln(1+δ) 最小化上界即得上尾界。

### 3. Power of Two Choices（双选择的力量）

**核心结果**：放球时随机选两个桶，将球放入负载较小的那个 → 最大负载从 O(log n / log log n) 降到 **O(log log n)**。

**直观理解**：设 Bᵢ = #{桶的负载 ≥ i}，则 Bᵢ ≈ B_{i-1}²/n。这个二次下降导致负载只能堆到 log log n 层。

**这解释了为什么 Cuckoo Hashing 和 Chaining with two choices 效果这么好。**

### 4. Universal Hashing（全域哈希）

**k-universal 定义**（Carter & Wegman 1979）：对任意 k 个不同元素 x₁,...,xₖ，
$$Pr[h(x₁) = \cdots = h(xₖ)] \leq \frac{1}{m^{k-1}}$$

**k-wise independent**（更强）：对任意 k 个不同元素和任意 k 个目标值，
$$Pr\left[\bigwedge_{i=1}^k h(x_i) = y_i\right] = \frac{1}{m^k}$$

**构造 — Linear Congruential**（2-wise independent）：
$$h_{a,b}(x) = ((ax + b) \bmod p) \bmod m, \quad a \in \mathbb{Z}_p\setminus\{0\}, b \in \mathbb{Z}_p$$

### 5. Birthday Paradox（生日悖论）

n 个球投入 m 个桶，无碰撞（每个桶 ≤ 1 个球）的概率：

$$Pr[\mathcal{E}] = \prod_{i=0}^{n-1}\left(1 - \frac{i}{m}\right) \approx e^{-n^2/2m}$$

- m = n² 时，完美的概率 > 1/2 → **这就是 1-level Perfect Hashing 选 m=n² 的原因**
- 使用 2-universal hashing 同样成立（只需 pairwise independence）

### 6. FKS Perfect Hashing（两级完美哈希）

**Fredman, Komlós, Szemerédi (1984)** — 静态集合的完美哈希方案：

1. **第一级**：用 2-universal hash 将 n 个元素分到 n 个桶
2. **第二级**：对桶 i（大小 |Bᵢ|），分配 |Bᵢ|² 空间，再次用 2-universal hash 做到该桶内无碰撞

**空间分析**：$\mathbb{E}[\sum |B_i|^2] = \frac{n(n-1)}{m} + n$，取 m=n 时期望 < 2n。总空间 O(n)，最坏情况 O(1) 查询（5 次内存访问）。

### 7. Cuckoo Hashing（布谷鸟哈希）

**思想**：两个哈希函数 h, g。元素 x 只能放在位置 h(x) 或 g(x)。插入时如果两个位置都满，踢出一个已存在的元素，让它去另一个位置。

**Cuckoo Graph**：节点 = 哈希表槽位，边 = (h(x), g(x)) 对每个元素 x。
- 插入成功 ⟺ 图中无"双循环"且路径不长
- 一条固定插入路径长度 ≥ k 的概率 ≤ m^{-k}（指数衰减）
- 期望插入时间 O(1)（amortized），查询精确 2 次内存访问

### 8. Succinct Dictionary（简洁字典）

**目标**：在接近信息论下界 (1+o(1))n 的空间内支持 O(1) 查询。

**关键技术**：
- 用大桶 + Elias-Fano/Trie 编码小字典
- 允许少量溢出桶（overflow），大小 n/poly log n
- 重构时平衡负载，整体冗余 o(n log U) bits

### 9. Tabulation Hashing（查表哈希）

**实用中最快的哈希方案**：将 key 分解为 c 个字符 x = (x₁,...,x_c)，查 c 个随机表后 XOR：
$$h(x) = T_1[x_1] \oplus \cdots \oplus T_c[x_c]$$

- 仅 3-universal（不是 4-universal），但足以支持链地址法、线性探测、Cuckoo、F₂ 估计等几乎所有应用
- 空间 cu（c=4, u=256 时极小），时间 O(c)，完全适配 CPU cache

## 难点突破

### 难点 1：Chernoff Bound 证明中 MGF 的来龙去脉

**为什么会卡住**：Chernoff 证明里突然冒出 $e^{tX}$ 和矩母函数，感觉像魔术。

**突破方法**：Chernoff 的思想本质是"用指数函数放大偏差"：
- Markov 不等式：$Pr[X \geq a] \leq \mathbb{E}[X]/a$，但对尾部控制太弱
- 取 $e^{tX}$ 再 Markov：$Pr[X \geq a] \leq \mathbb{E}[e^{tX}]/e^{ta}$，指数放大了大偏差的权重
- 为什么是 $e^{tX}$ 而不是别的？因为独立随机变量之和的指数 = 指数的乘积：$\mathbb{E}[e^{t\sum X_i}] = \prod \mathbb{E}[e^{tX_i}]$，计算干净
- MGF 的展开：$\mathbb{E}[e^{tX}] = \sum t^k \mathbb{E}[X^k]/k!$，包含了所有阶矩的信息

**类比**：普通 Markov 像用放大镜看偏差，Chernoff 像用显微镜——指数函数把微小的概率差异放大到肉眼可见。

### 难点 2：Cuckoo Graph 中插入失败的条件

**关键理解**：在 Cuckoo Graph 中，一次插入沿路径踢元素。失败发生在：
- **双循环（double cycle）**：插入 x = (u,v) 后发现 u→...→v 和 v→...→u 两条边都形成环，踢不动了
- **长路径**：一直踢下去，踢了太长还没找到空位

为什么踢的过程对应图中的路径？每次踢出一个元素就是沿边走到图的另一边（从 h(x) 踢到 g(x) 或反过来）。如果图中没有双循环，踢的过程要么找到空位（成功），要么走成一个简单循环再回来（单循环并不致命——你会发现最初的元素可以塞进空位）。

## 与前章关联

- 依赖 01-Fingerprinting 中建立的"随机化 = 概率分析 + 可控错误"范式
- Chernoff Bound 的矩母函数方法与 Fingerprinting 中 Fingerprint 函数的设计共享"将确定性计算转化为概率估计"的核心哲学
- 为 03-Sketching 的 Morris 算法等概率分析提供工具（Chernoff + occupancy bounds）

## 记忆卡片

**Q1**: m=n 时 Balls into Bins 的最大负载是多少？
**A**: O(log n / log log n)，通过 Chernoff + Union Bound 证明。单个桶负载超过 L 的概率 ≤ e^L/L^L，取 L = O(log n / log log n) 使该概率 < 1/n。

**Q2**: Power of Two Choices 为什么能把最大负载降到 O(log log n)？
**A**: 负载 ≥ i 的桶数 Bᵢ 以二次速度收缩：Bᵢ ≈ B_{i-1}²/n。O(log n) 层后 Bⱼ < 1。

**Q3**: FKS Perfect Hashing 的总空间为什么是 O(n)？
**A**: 用 2-universal hash 分桶，桶 i 分配 |Bᵢ|² 空间。$\mathbb{E}[\sum |B_i|^2] = \frac{n(n-1)}{m} + n = 2n-1$（取 m=n）。每个桶内再用 2-universal hash 做到无碰撞。

**Q4**: Cuckoo Hashing 查询为什么精确是 2 次内存访问？
**A**: 元素 x 只可能在 h(x) 或 g(x) 两个位置之一。检查这两个位置是否存有 x 即可。不需要遍历链表。

**Q5**: Tabulation Hashing 是几-universal 的？
**A**: 3-universal，但不是 4-universal（因为有恒等式 $h(a_1,a_2) \oplus h(a_1,b_2) \oplus h(b_1,a_2) \oplus h(b_1,b_2) = 0$）。不过对于实际中几乎所有哈希应用都足够好。

---

## 📐 课件完整推导（按 Issue 整理）

以下对照 Hashing.pdf 的每个 Issue（主题），给出课件中出现过的所有推导步骤。标注了页码方便回溯原文。

---

### A. Chernoff Bound — 从 Markov 到最终形式的完整推导

**对应课件：第 9, 12-16, 56 页**

#### A.1 起点：Markov 不等式（第 12 页）

Chernoff 的起点永远是 Markov。对非负随机变量 Y 和任意 a > 0：

$$Pr[Y \geq a] \leq \frac{\mathbb{E}[Y]}{a}$$

问题在于直接对 X = ΣXᵢ 用 Markov 太弱。Chernoff 的洞察：**先用单调变换放大偏差，再套 Markov**。

#### A.2 指数变换 + MGF（第 12-13 页）

对任意 t > 0：

$$Pr[X \geq (1+\delta)\mu] = Pr[e^{tX} \geq e^{t(1+\delta)\mu}] \leq e^{-t(1+\delta)\mu} \cdot \mathbb{E}[e^{tX}] \quad \text{(Markov)}$$

现在需要 bound MGF：M_X(t) = 𝔼[e^{tX}]。对独立伯努利和：

$$\mathbb{E}[e^{tX}] = \mathbb{E}\left[\prod_{i=1}^n e^{tX_i}\right] = \prod_{i=1}^n \mathbb{E}[e^{tX_i}] \quad \text{(独立性)}$$

对每个 Xᵢ ~ Bernoulli(pᵢ)：

$$\mathbb{E}[e^{tX_i}] = p_i e^t + (1-p_i) = 1 + p_i(e^t - 1) \leq e^{p_i(e^t-1)} \quad \text{(因为 } 1+x \leq e^x\text{)}$$

因此：

$$\mathbb{E}[e^{tX}] \leq \prod_{i=1}^n e^{p_i(e^t-1)} = e^{\mu(e^t-1)} \quad \text{其中 } \mu = \sum p_i$$

#### A.3 上尾界 — t 的最优选择（第 14 页）

代回 Markov：

$$Pr[X \geq (1+\delta)\mu] \leq e^{-t(1+\delta)\mu} \cdot e^{\mu(e^t-1)} = \left[e^{e^t-1-t(1+\delta)}\right]^\mu$$

现在这个界对**任意 t > 0** 成立。我们要选最优的 t 最小化右端。对指数内部求导：

$$\frac{d}{dt}[e^t - 1 - t(1+\delta)] = e^t - (1+\delta)$$

令导数 = 0 → t = ln(1+\delta)。代回：

$$Pr[X \geq (1+\delta)\mu] \leq \left[e^{\delta - (1+\delta)\ln(1+\delta)}\right]^\mu = \left(\frac{e^\delta}{(1+\delta)^{1+\delta}}\right)^\mu$$

这就是 **Chernoff 上尾界的最紧乘法形式**。

课件第 14 页的图示说明了为什么这个 t 是最优的：函数 e^t - 1 - t(1+δ) 在 t = ln(1+δ) 处取极小值（导数为 0，二阶导 e^t > 0）。

#### A.4 下尾界（第 15 页）

下尾思路完全对称，但取 t < 0（因为要 bound 下尾，指数要朝另一边放大）：

$$Pr[X \leq (1-\delta)\mu] = Pr[e^{tX} \geq e^{t(1-\delta)\mu}] \leq e^{-t(1-\delta)\mu} \cdot \mathbb{E}[e^{tX}]$$

MGF 的界对任意 t（包括负数）都成立：

$$\mathbb{E}[e^{tX}] \leq e^{\mu(e^t-1)}$$

因此：

$$Pr[X \leq (1-\delta)\mu] \leq \left[e^{e^t-1-t(1-\delta)}\right]^\mu$$

令 t = ln(1-\delta) < 0（对 0 < δ < 1），代回：

$$Pr[X \leq (1-\delta)\mu] \leq \left(\frac{e^{-\delta}}{(1-\delta)^{1-\delta}}\right)^\mu$$

#### A.5 简化形式（第 16 页）

对 0 < δ < 1，用 Taylor 展开 ln(1+δ) = δ - δ²/2 + δ³/3 - ...：

$$\ln(\text{bound}) = \mu[\delta - (1+\delta)\ln(1+\delta)] = \mu\left[\delta - (1+\delta)\left(\delta - \frac{\delta^2}{2} + \frac{\delta^3}{3} - \cdots\right)\right]$$

展开后 δ 项消掉，主项 = -μδ²/2 + μ(δ³/6 - ...)。取上界 -μδ²/3（对 δ < 1 时更保守但简洁）：

$$Pr[X \geq (1+\delta)\mu] \leq e^{-\mu\delta^2/3}$$

下尾简化（同理，ln(1-δ) = -δ - δ²/2 - δ³/3 - ...）：

$$Pr[X \leq (1-\delta)\mu] \leq e^{-\mu\delta^2/2}$$

**为什么上尾和下尾常数不同**：因为 ln(1+δ) 展开的奇次项符号交替，而上尾需要展开 (1+δ)ln(1+δ)，奇次项的部分抵消使得衰减略慢 → 用 3 而非 2。

#### A.6 大偏差形式（第 11 页）

当 L ≥ 2eμ 时：

$$Pr[X \geq L] = Pr[X \geq (1+\delta)\mu] \quad \text{其中 } \delta = L/\mu - 1 \geq 2e-1 > 1$$

代回原式，利用 (1+δ)^{1+δ} ≥ (1+δ)^L/μ·e^δ 在 δ 大时的特性，课件给出：

$$Pr[X \geq L] \leq 2^{-L} \quad \text{当 } L \geq 2e\mu$$

**推导直觉**：当 δ 很大时，(1+δ) 的增长主导 e^δ，使得分数 e^δ/(1+δ)^{1+δ} 被 (1+δ) 压到极小，在大偏差下 2^{-L} 是一个方便的形式。

---

### B. Occupancy Problem — 用 Chernoff 解最大负载

**对应课件：第 7-11, 17 页**

#### B.1 设置

m 个球均匀随机放入 n 个桶。第 i 个桶的负载 Xᵢ ~ Bin(m, 1/n)（边际分布）。μ = 𝔼[Xᵢ] = m/n。

注意：Xᵢ 之间不独立（多项分布），但 Chernoff 对每个单独的 Xᵢ 成立（它是 m 个独立伯努利的和）。

#### B.2 m = n 场景（μ = 1）（第 10 页）

对单个桶，用 Chernoff 上尾：

$$Pr[X_i \geq L] = Pr[X_i \geq (1+\delta)\mu] \quad \delta = L-1$$

$$\leq \left(\frac{e^{L-1}}{L^L}\right)^1 = \frac{e^{L-1}}{L^L} \leq \left(\frac{e}{L}\right)^L$$

取 L = 2 ln n / ln ln n（课件的选择，保证足够小）：

$$Pr[X_i \geq L] \leq \left(\frac{e}{L}\right)^L = \exp(L \ln(e/L))$$

当 L = O(log n / log log n) 时，L ln(e/L) ≈ -L ln L，令其 ≤ -2 ln n：

- 需要 L ln L ≥ 2 ln n
- 取 L = 3 ln n / ln ln n 则 L ln L ≈ 3 ln n · (1 - ln ln ln n / ln ln n) ≥ 2 ln n（对充分大的 n）

于是 Pr[Xᵢ ≥ L] ≤ 1/n²。用 Union Bound 过所有 n 个桶：

$$Pr[\max_i X_i \geq L] \leq n \cdot \frac{1}{n^2} = \frac{1}{n}$$

所以 w.h.p. max load = O(log n / log log n)。

#### B.3 m ≥ n ln n 场景（μ ≥ ln n）（第 11 页）

此时用大偏差形式：对 L = 2eμ ≥ 2e ln n：

$$Pr[X_i \geq L] \leq 2^{-L} \leq 2^{-2e\ln n} = n^{-2e\ln 2} \leq \frac{1}{n^2}$$

Union bound 同样给出 1/n。此时 L = 2e·m/n，所以：

$$\max_i X_i = O(m/n) \quad \text{w.h.p.}$$

即所有桶负载均匀，偏差不超过常数倍。

**课件中的不等式选择逻辑**（第 8 页也展示了为什么不用 Markov/Chebyshev）：
- Markov：Pr[Xᵢ ≥ k] ≤ 1/k，Union bound 后 Pr[max ≥ k] ≤ n/k，要得到 1/n 需要 k = n²，太松。
- Chebyshev：Var(Xᵢ) ≤ 1，Pr[|Xᵢ-1| ≥ n] ≤ 1/n² → 只能保证偏离 n 以内的界，对最大负载（需要 O(log n) 量级）无能为力。
- 二项式直接求和：Pr[Xᵢ ≥ k] = Σ_{j≥k} C(n,j)(1/n)^j(1-1/n)^{n-j} ≤ C(n,k)(1/n)^k ≤ (e/k)^k，恰好和 Chernoff 给的一样紧——但 Chernoff 的推导更系统。

---

### C. Power of Two Choices — 逐层归纳证明

**对应课件：第 18-20 页**

#### C.1 基本设置（第 18-19 页）

定义 Bᵢ = #{负载 ≥ i 的桶}。一个球要进入"负载 ≥ i"的桶，必须它选的两个桶负载都 ≥ i-1：

$$B_i \leq \#\{球的两个选择都在负载 \geq i-1 的桶中\}$$

每个球的两个选择独立均匀随机，所以一个球"见证"两个都 ≥ i-1 的概率 ≤ (B_{i-1}/n)²。n 个球：

$$\mathbb{E}[B_i \mid B_{i-1}] \leq n \cdot \left(\frac{B_{i-1}}{n}\right)^2 = \frac{B_{i-1}^2}{n}$$

所以 E[Bᵢ] ≤ E[B_{i-1}²]/n。

直觉（第 19 页）：Bᵢ/n ≈ (B_{i-1}/n)²。从 B₁/n ≤ 1 开始，平方递归让占比指数级衰减。

**指数塔视角**：B_i/n ≤ (B_{i}/n)^{2^i} ≤ (1)^{2^i} 不会衰减，但实际 B₃ 已经 < n/2e，从那开始每步翻倍指数缩到 1/n 只需 O(log log n) 步。

#### C.2 分层归纳的严格版本（第 20 页）

课件给出了严谨的事件链分析。设置阈值序列：

$$\beta_6 = n/2e, \quad \beta_{i+1} = 2e\beta_i^2/n$$

即 βᵢ 是第 i 层负载 ≥ i 的桶数上界。定义事件 ℰᵢ = {νᵢ ≤ βᵢ}，其中 νᵢ 是实际负载 ≥ i 的桶数。

**目标**：Pr[∧ᵢ ℰᵢ] = Πᵢ Pr[ℰᵢ | ℰ_{<i}] ≥ 1 - O(1/n)。

**关键观察**：给定 ℰᵢ（即 νᵢ ≤ βᵢ），"负载变为 ≥ i+1 的球"的数量 ⪅ Bin(n, βᵢ²/n²)。

原因：一个球要使其桶从负载 i 变成 i+1，必须两个选择都落在负载 ≥ i 的桶中。条件于 νᵢ ≤ βᵢ，这个概率至多为 (βᵢ/n)²。

**情况 1**：βᵢ²/n ≥ ln n（即层还比较低，桶还不少时）

此时 Bin(n, βᵢ²/n²) 的期望 ≥ ln n。取 L = β_{i+1} = 2e·𝔼[Bin]，用大偏差 Chernoff：

$$Pr[\nu_{i+1} \geq \beta_{i+1} \mid \mathcal{E}_i] \leq 2^{-\beta_{i+1}} \leq 1/n^3$$

**情况 2**：νᵢ < n log n（即 βᵢ 已经掉到很小，开始剧烈收缩）

此时 Bin(n, 36 log²n / n²) 的期望很小，取 6 log n 为界：

$$Pr[\nu_{i+1} \geq 6\log n] \leq 1/n^3$$

**最终步**：当 ν_{i+1} < 6 log n 时：

$$Pr[\nu_{i+2} \geq 1] \leq Pr[Bin(n, 6\log n/n)^2 \geq 1] = O(\log^2 n)/n \ll 1/n$$

即最多再 2 层就没有负载 ≥ i+2 的桶了。所以最大负载 = O(log log n)。

---

### D. Birthday Paradox — 精确公式与近似

**对应课件：第 22-25, 31-32 页**

#### D.1 精确公式（第 23-24 页）

n 个球放入 m 个桶。事件 ℰ = {每个桶 ≤ 1 个球}。

课件用链式法则给出精确形式：

$$Pr[\mathcal{E}] = \prod_{i=1}^n Pr[\text{第 }i\text{ 个球落入空桶} \mid \text{前 }i-1\text{ 个球全在空桶}]$$

$$= \prod_{i=1}^n \left(1 - \frac{i-1}{m}\right) = \prod_{i=0}^{n-1} \left(1 - \frac{i}{m}\right) = \frac{m(m-1)\cdots(m-n+1)}{m^n}$$

另一个视角：所有 n!·C(m,n) 种无碰撞配置 ÷ 总共 mⁿ 种配置 = m(m-1)...(m-n+1)/mⁿ。一致。

#### D.2 1 - x ≤ e^{-x} 近似（第 25 页）

用 1 - x ≤ e^{-x}（对所有实数 x）：

$$Pr[\mathcal{E}] = \prod_{i=0}^{n-1} \left(1 - \frac{i}{m}\right) \leq \prod_{i=0}^{n-1} e^{-i/m} = \exp\left(-\frac{n(n-1)}{2m}\right)$$

当 n ≪ m 时，1 - x ≈ e^{-x}（Taylor：1 - x = e^{-x - x²/2 - ...}），所以近似是紧的。

**课件中的形式化双边不等式**（第 25 页下方）：

$$e^{-(1+o(1))n^2/2m} \leq \prod_{i=0}^{n-1} \left(1 - \frac{i}{m}\right) \leq e^{-(1-o(1))n^2/2m}$$

这来自更精细的界：对 x ∈ [0, 1/2]，有 e^{-x-x²} ≤ 1-x ≤ e^{-x}（由 ln(1-x) = -x - x²/2 - x³/3 - ... 得到）。所以：

$$\ln Pr[\mathcal{E}] = \sum_{i=0}^{n-1} \ln\left(1 - \frac{i}{m}\right) = -\sum_{i=0}^{n-1} \frac{i}{m} - \Theta\left(\sum_{i=0}^{n-1} \frac{i^2}{m^2}\right)$$

$$= -\frac{n(n-1)}{2m} - O\left(\frac{n^3}{m^2}\right)$$

当 n ≪ m^{2/3} 时余项可忽略。

**应用**：$$n = \sqrt{2m\ln(1/p)}$$ 时，Pr[ℰ] ≈ p。取 p = 1/2，m = 365，n ≈ 22.5（生日悖论）。

#### D.3 2-universal 版本的 Birthday Paradox（第 31-32 页）

球的位置 Xᵢ = h(xᵢ)，由 2-universal 哈希决定。总碰撞数：

$$Y = \sum_{i<j} \mathbf{1}[X_i = X_j]$$

由 linearity of expectation 和 2-universal 性质：

$$\mathbb{E}[Y] = \sum_{i<j} Pr[X_i = X_j] \leq \binom{n}{2} \cdot \frac{1}{m} = \frac{n(n-1)}{2m}$$

**注意**：这里只需要 pairwise independence（2-universal），不需要完全随机！

然后用 Markov：

$$Pr[\neg\mathcal{E}] = Pr[Y \geq 1] \leq \mathbb{E}[Y] \leq \frac{n(n-1)}{2m} \leq \epsilon \quad \text{当 } n \leq \sqrt{2m\epsilon}$$

取 m = n² → Pr[不完美] ≤ 1/2。对 FKS 第一层，取 m = n → Pr[碰撞] ≤ (n-1)/(2n) < 1/2。但我们不关心单桶——我们要所有桶都好（见下文 FKS）。

---

### E. Collision Number 与 FKS 空间分析

**对应课件：第 33-39 页**

#### E.1 碰撞数与桶大小平方和的关系（第 37 页）

这是 FKS 空间分析的核心恒等式：

$$Y = \sum_{i<j} \mathbf{1}[X_i = X_j] = \sum_{i=1}^n \binom{|B_i|}{2} = \frac{1}{2}\sum_{i=1}^n |B_i|(|B_i|-1)$$

**推导**：每对碰撞的球 (i,j) 在某个桶中相遇。左边按球对计数，右边按桶汇总。同桶中 |Bᵢ| 个球有 C(|Bᵢ|,2) 对碰撞。

由此推出：

$$\sum_{i=1}^n |B_i|^2 = 2Y + \sum_{i=1}^n |B_i| = 2Y + n$$

取期望，用 E[Y] ≤ n(n-1)/(2m)（2-universal）：

$$\mathbb{E}\left[\sum |B_i|^2\right] = 2\mathbb{E}[Y] + n \leq \frac{n(n-1)}{m} + n$$

**这就是为什么 FKS 取 m = n 时期望总空间 < n + n = 2n。**

课件第 37 页还给出了精确推导：

$$\mathbb{E}[|B_i|^2] = \sum_j Pr[h(x_j)=i] + \sum_{j\neq k} Pr[h(x_j)=h(x_k)=i]$$

$$= \frac{n}{m} + \frac{n(n-1)}{m^2}$$

第一项来自 j=k（每个球自己），第二项来自 2-universal。对所有 i 求和得 n/m·n + n(n-1)/m = n²/m + n(n-1)/m = n(n-1+m)/m。

#### E.2 FKS 存在性论证（第 33-34, 38 页）

课件（第 33 页）首先论证 1-level：取 m ≥ C(n,2)，2-universal 族中 ∃ h 使 S 上无碰撞。

证明：对每个 h ∈ ℋ，指示"h 对 S 不完美"的变量期望 < 1/2（当 m > C(n,2) 时），所以 ∃ h 完美。

然后 FKS（第 34 页来自原论文）：两级构造。
1. 第一层 h: [N]→[n]，用 2-universal
2. 第二层：桶 i 有 |Bᵢ| 个元素，分配 |Bᵢ|² 空间，用另一个 2-universal hᵢ 在该桶内实现完美

空间 ≤ Σ(|Bᵢ|²+2) = 2+2n+Σ|Bᵢ|²。期望 ≤ 2+2n+2n = O(n)。

查询：5 次内存访问（T[0]→h→T[j]→|Bⱼ|→k'→Tⱼ[hⱼ(x)]）。

---

### F. Cuckoo Hashing — Cuckoo Graph 与插入分析

**对应课件：第 40-46 页**

#### F.1 Cuckoo Graph 模型（第 42-43 页）

将哈希表槽位视为节点 V = [m]，每个元素 x 对应一条边 e = (h(x), g(x))。

- **插入成功**：沿着边交替踢元素，形成一条**路径**最终找到空位，或遇到**单循环**（single cycle）回到起点发现起点可以空出来。
- **插入失败** ⇔ **双循环**（double cycle）或**长路径**（超过合理长度）。

课件第 43 页用图示区分了这三种情况。

#### F.2 路径长度概率（第 44 页）

**Claim**：固定长度为 k 的插入路径存在的概率 ≤ m^{-k}。

路径结构：x, slot₁, y, slot₂, z, ...（key-slot-key-slot 交替）。2k+1 个对象的特定排列。数量的界：

$$\text{#possible paths of length }k \leq n^k \cdot m^{k+1}$$

其中 nᵏ 是选 k 个不同 key，m^{k+1} 是选 k+1 个 slot。

每个具体路径的所有哈希值匹配的概率 ≤ 1/m^{2k+1}（每步需要特定的 h 或 g 值）。

因此：

$$Pr[\text{存在长度} \geq k \text{ 的路径}] \leq \frac{n^k \cdot m^{k+1}}{m^{2k+1}} = \frac{n^k}{m^k} = \left(\frac{n}{m}\right)^k$$

当 m = (1+ε)n（表稍大）时，概率 = (1+ε)^{-k} = e^{-Ω(k)}。

**推论**：
- Pr[路径长度 ≥ 2 log n] ≤ 1/n²
- E[路径长度] = Σ_{k≥1} Pr[length ≥ k] ≤ Σ e^{-Ω(k)} = O(1)

#### F.3 双循环分析（第 45 页）

**最简单的情况** (⦶)：4 条边 a,b,c,d，满足 h(a)=h(b), g(a)=g(c), h(c)=h(d), g(b)=g(d)。课件给出的概率：

$$Pr[\text{最简单双循环}] \leq \frac{n^4 \cdot m^2}{m^6} = \frac{n^4}{m^4}$$

**一般情况** (⧟)：k 条边、k 个节点（#edges = #nodes），形成双循环。概率 ≤ nᵏ mᵏ / m^{2k} = (n/m)ᵏ。

**d-cycle 的总概率**（用 union bound 汇总所有可能的 k）：

$$Pr[\text{d-cycle}] \leq \sum_{k\geq 2} \left(\frac{n}{m}\right)^k \leq \frac{n^2/m^2}{1-n/m} = O(1/n^2) \quad \text{当 } m = (1+\epsilon)n$$

#### F.4 期望插入时间（第 44-46 页）

设 T 为插入时间。课件给出递推：

$$\mathbb{E}[T] \leq \mathbb{E}[\text{len(path)}] + \mathbb{E}[\text{len(cycle)}] + Pr[\text{d-cycle} \cup \text{long path}] \cdot n \cdot \mathbb{E}[T]$$

前两项都是 O(1)（期望路径和单循环长度都是 O(1)）。第三项：

$$Pr[\text{d-cycle}] \cdot n \cdot \mathbb{E}[T] + Pr[\text{long path}] \cdot n \cdot \mathbb{E}[T]$$

$$= O(1/n^2) \cdot n \cdot \mathbb{E}[T] + 1/n^2 \cdot n \cdot \mathbb{E}[T] = o(1) \cdot \mathbb{E}[T]$$

因此 E[T] ≤ O(1) + o(1)·E[T] → E[T] = O(1)。查询严格 2 次。

---

### G. Succinct Dictionary — 冗余分析与 Trie 压缩

**对应课件：第 47-54 页**

#### G.1 冗余分析概览（第 48 页对比表）

| 结构 | 空间 | 查询 | 更新 |
|------|------|------|------|
| 二分搜索树 | O(n) | O(log n) | O(log n) |
| Chaining | O(n) expected | O(1) expected | O(1) |
| 1-level Perfect | O(n²) | O(1) | — |
| 2-level FKS | O(n) | O(1) | O(1)（静态） |
| Cuckoo | O(n) | 2 | O(1) expected amortized |
| **Succinct** | **(1+o(1))n** | O(1) | O(1) |

信息论下界：log C(N, n) ≈ n log(N/n) bits。Succinct dictionary 目标：在这个下界的 (1+o(1)) 倍内。

#### G.2 FKS 的冗余来源（第 49 页）

FKS 一级指针 + 哈希参数 = n log n bits，原始数据 = nv bits（v = log U）。总共 n log n + nv bits。

**观察**：如果 log n ≪ v（即 key 本身很大），则 n log n 是 o(nv)，即冗余是 o(nv) → FKS 本身就是 succinct 的！例如 v = log U，当 n = poly log U 时（小集合大宇宙）满足条件。

#### G.3 大桶策略（第 50-51 页）

**第一次尝试**：放 n 个球到 n/log³n 个桶中。用 Chernoff bound：

- m = n/log³n，δ = 2/log n
- Pr[负载 ≥ (1+δ)m] ≤ exp(-μδ²/2) = exp(-log³n · (4/log²n)/2) = exp(-2 log n) = 1/n²

每个小桶最多 (1+2/log n)log³n 个元素。每个小桶用 log(桶大小) bits 编码索引 → 冗余 o(n log U)。

**更好的做法：让桶溢出！**（第 51 页）

取 m = log n / log log n 个大桶，δ = Ω(log log n / log n)：

- 正常桶负载 ≤ (1+δ)m
- 溢出元素 ≈ n / poly log n（Chernoff 尾概率 × n）
- 对溢出元素单独建字典（只有 poly log n 量级）

冗余 = O(δn) words = o(n) words。总空间 (1+o(1))n log(U/n) bits。这就是 Feistel 的构造。

#### G.4 Trie 压缩（第 52-53 页）

对溢出字典（约 n/log⁹n 个 key），用 Trie（或 Elias-Fano）：

- 假设 key 随机，插入 n' 个 key 建 Trie → 期望 O(n') 节点
- 每个节点编码用 O(log n) bits → 总空间 O(n' log n) = o(n) bits

**Trie 的增长分析**（第 52 页）：一次插入沿 Trie 走，每步以 1/2 概率需要分裂（grow），分裂次数是几何分布 → 期望 O(n') 个节点。高概率下节点数 ≤ O(n')。每个节点只需 O(log n) bits（指针/标记），总冗余 o(n)。

---

### H. Generalized Chernoff — 参数化 αᵢ 替代 t

**对应课件：第 57-66 页**

#### H.1 矩视角（第 58-59 页）

课件从一个新角度审视 Chernoff：不再用指数变换 e^{tX}，而是直接展开幂次。

对伯努利和 X = ΣXᵢ，k 次幂展开：

$$X^k = \left(\sum X_i\right)^k = \sum_{i \leq \min\{k,n\}} \alpha_i \sum_{1 \leq j_1 < \cdots < j_i \leq n} X_{j_1}\cdots X_{j_i}$$

其中 αᵢ 是组合系数。例如：
- k=1：ΣXᵢ
- k=2：ΣXᵢ + Σ_{i≠j} XᵢXⱼ
- k=3：ΣXᵢ + 2Σ_{i≠j} Xᵢ²Xⱼ + Σ_{i≠j≠k} XᵢXⱼXₖ

#### H.2 参数化 αᵢ（第 60-64 页）

Chernoff 的做法等价于固定 αᵢ = tⁱ/i!（来自 e^{tX} 的 Taylor 展开）。Generalized Chernoff 的核心思想：**αᵢ 可以自由选择**，不必局限在指数函数的 Taylor 系数。

从 Markov 出发：

$$Pr[X \geq a] \leq \frac{\mathbb{E}\left[\sum_{i=0}^n \alpha_i \sum_{j_1<\cdots<j_i} X_{j_1}\cdots X_{j_i}\right]}{\sum_{i=0}^a \alpha_i \binom{a}{i}}$$

**关键观察**（第 61 页）：
1. 对于 i > a，αᵢ 应设为 0（因为分母的 C(a,i) = 0，分子中的项没有对应）
2. 应选 αᵢ 最小化 (μ/n)ⁱ / C(a,i)（因为 𝔼[X_{j₁}...X_{jᵢ}] ≤ (μ/n)ⁱ 对独立伯努利）

**最优 αᵢ 的选择**（第 63 页）：由比值

$$\frac{\binom{n}{i+1}(\mu/n)^{i+1} / \binom{a}{i+1}}{\binom{n}{i}(\mu/n)^i / \binom{a}{i}} = \frac{n-i}{i+1} \cdot \frac{\mu}{n} \cdot \frac{a-i}{i+1}$$

在每个 i 处比较相邻两项。令比值为 1 解得最优点：

$$i^* = \frac{a - \mu}{1 - \mu/n}$$

取 α_{i*} = 1，其余 αᵢ = 0，得到：

$$Pr[X \geq a] \leq \frac{\binom{n}{i^*}(\mu/n)^{i^*}}{\binom{a}{i^*}}$$

这个界在特定场景下比标准 Chernoff 更紧。

#### H.3 k-wise 独立版本（第 57, 65-66 页）

当 Xᵢ 只有 k-wise 独立（而非完全独立）时：

- 𝔼[X_{j₁}...X_{jₖ}] ≤ (μ/n)ᵏ（k-wise 独立保证了 1~k 阶联合矩与完全随机相同）
- 对于 i > k 的交叉项，k-wise 独立不保证矩的上界
- 但我们可以**只用到 α₁,...,αₖ**（即只取 i ≤ k），因为 i > a 的 αᵢ = 0，且如果 i* ≤ k，截断到 k 无损

**最终 k-wise Chernoff**（第 57, 66 页）：

当 k ≤ μδ/(1-μ/n) 时：

$$Pr[X \geq (1+\delta)\mu] \leq \frac{\binom{n}{k}(\mu/n)^k}{\binom{(1+\delta)\mu}{k}} = \frac{\mu}{n} \cdot \frac{\mu-1/n}{n-1} \cdots = \prod_{i=0}^{k-1} \frac{\mu}{(1+\delta)\mu-i}$$

这意味着：**要得到指数衰减的尾界，只需要 O(μδ) 阶独立性**，而非完全独立。对 Chaining（μ = O(log n / log log n)），所需独立度数远小于 n。这就是为什么 Tabulation（仅 3-universal）在实践中也够用的深层原因。

---

### I. Tabulation Hashing — 构造、性质与 Peeling

**对应课件：第 69-79 页**

#### I.1 构造（第 69 页）

将 key x 分解为 c 个字符：x = (x₁, ..., x_c) ∈ [u]^c。维护 c 张完全随机的查找表 T₁, ..., T_c : [u] → [m]。哈希值：

$$h(x) = T_1[x_1] \oplus T_2[x_2] \oplus \cdots \oplus T_c[x_c]$$

- 空间：cu（每个表 u 条目），当 c=4, u=256 时仅 1024 条
- 时间：O(c)，完全适配 L1 cache

#### I.2 3-universal 但不是 4-universal（第 70 页）

**3-universal 证明概要**：对 3 个不同 key x,y,z，需要某个字符位置使三者在该位置的值不全相同。利用 XOR 结构和真随机查找表，可证 Pr[h(x)=h(y)=h(z)] ≤ 1/m²。（详见原文引用的 Patrascu-Thorup 论文）

**4-universal 的反例**（第 70 页）：

$$h(a_1,a_2) \oplus h(a_1,b_2) \oplus h(b_1,a_2) \oplus h(b_1,b_2) = 0$$

**推导**：展开每一项：
- h(a₁,a₂) = T₁[a₁] ⊕ T₂[a₂]
- h(a₁,b₂) = T₁[a₁] ⊕ T₂[b₂]
- h(b₁,a₂) = T₁[b₁] ⊕ T₂[a₂]
- h(b₁,b₂) = T₁[b₁] ⊕ T₂[b₂]

XOR 全部 4 项，每个 T₁[a₁] 出现 2 次（相消），同理 T₂[a₂]、T₁[b₁]、T₂[b₂] 都各出现 2 次 → 总和恒为 0。

这意味着 4 个 key 的哈希值不可能是独立的——它们满足线性关系。所以 Tabulation 不是 4-universal。

#### I.3 Position Character 与 Peelability（第 72-76 页）

**定义**：对 key x，position character (i, x_i) 是好的，如果对所有其他 key y∈S，y_i ≠ x_i（即 x 在位置 i 的字符是唯一的）。

如果 x 有好的 position character，则 h(x) = T_i[x_i] ⊕ (与 x 无关的项)，而 T_i[x_i] 是真随机的且独立于其他所有 key 的哈希值 → h(x) 独立于 {h(y): y∈S, y≠x}。

**Peelability**（第 73-74 页）：集合 S 可剥（peelable），如果能逐层找到具有好的 position character 的元素。具体地：

**Claim**（第 73 页）：对任意 |S|=d，∃ 可剥子集大小 t ≥ max{d^{1/c}, log d}。

这意味着任何大集合可以分解为若干"可独立分析"的子集，每个子集内部元素有好的 position character。这是 Tabulation 能用于负载均衡、Cuckoo、线性探测等应用的理论基础。

**Peeling 算法**（第 75-76 页）：
1. 找 α∈S 有好的 PC(i, αᵢ) → h(α) 独立于 S\{α}
2. 重复，得集合序列 S_α, S_β, ...，每个元素的条件期望独立
3. 对每个子集分别应用集中不等式（Chernoff with peeling）
4. 所有子集的界合并 → 整体尾界

第 79 页给出最终应用：max-load 分析中，每个 bin 中来自 S_α 的球以概率 d·m^{-1+t/c} 集中，用 union bound over n^t 个可能集合 → w.h.p. 每个 bin 的负载有界。这就是 Tabulation 替代完全随机性仍保持 O(log n / log log n) 最大负载的原理。

---

### J. 不等式使用决策树（汇总）

回顾全部推导中用到的核心不等式及其依赖关系：

```
1 + x ≤ eˣ  ───────────────────────────────────────────┐
    ↓                                                    │
Markov: Pr[Y≥a] ≤ E[Y]/a ──→ Chernoff ──→ 简化形 e^{-μδ²/3}  │
    ↓                           ↓                    ↓     │
MGF: E[e^{tX}] ≤ e^{μ(e^t-1)}   大偏差 2^{-L}      k-wise │
    ↓                                                    │
最优 t = ln(1±δ) ──→ 乘法形 (e^δ/(1+δ)^{1+δ})^μ        │
    ↓                                                    │
Union Bound ──→ max load ≤ O(log n / log log n)          │
    ↓                                                    │
Linearity of Expectation ──→ E[Σ|B_i|²] ≤ n(n-1)/m + n  │
    ↓                                                    │
Markov (again) ──→ Pr[Y≥1] ≤ E[Y] (birthday w/ 2-univ)  │
    ↓                                                    │
Azuma-Hoeffding ──→ Power of Two Choices 严格版          │
    ↓                                                    │
Hoeffding / Generalized Chernoff ──→ Tabulation peeling  │
```

## 💬 学习对话补充

### 2026-05-18：不等式选择决策框架 — 从"知道公式"到"知道该用哪个"

**类型：** 深化 + 关联

**背景：** 用户在第 2 章复习中注意到课件大量使用 Markov、Chebyshev、Chernoff、Hoeffding 等不等式，但原笔记只孤立地列出了 Chernoff 的公式和记忆卡片，没有解释"面对一个具体问题该选哪个不等式"以及"为什么某些地方用 Chebyshev 就够了，某些地方必须上 Chernoff"。用户的原话是"从数学的角度帮我区分一下，使用markov，切比雪夫，切尔诺夫等经典结论的场景"——这是在寻求一个系统化的选择框架，而非单个不等式的推导。

**讨论过程：**

我们从"不等式升级路径"这个核心比喻开始：Markov（最弱前提，最松界）→ Chebyshev（有方差，多项式衰减）→ Chernoff（独立伯努利和，指数衰减）→ Hoeffding（有界变量通用版）→ Azuma-Hoeffding（鞅差有界版）。每一级"升级"的代价是更强的假设条件，回报是指数级更紧的尾界。

我们深入讨论了 Chebyshev 和 Chernoff 在同一个问题上（估计 ∥x∥²）的定量差异：用 Chebyshev 分析 Count Sketch 需要 k = O(1/ε²δ)（样本量对 1/δ 是多项式依赖），而用 Chernoff 分析 Gaussian JL 只需 k = O(log(1/δ)/ε²)（对数依赖）。这意味着把 δ 从 0.1 压到 10⁻⁶，Chebyshev 方案需要 10⁵ 倍空间，Chernoff 方案只需约 60 倍。这个具体的数量级对比让用户直观理解了"指数衰减 vs 多项式衰减"在算法设计中的实际含义。

我们还辨析了"为什么是指数函数 e^{tX} 而不是 x² 或 xᵏ"：因为独立随机变量之和的指数 = 指数之积，即 E[e^{tΣXᵢ}] = ΠE[e^{tXᵢ}]，这是能把"加法变乘法"从而充分拆解独立性的唯一变换。如果取 x²，交叉项 E[XᵢXⱼ] 虽然独立性帮助简化但不会像乘积那样干净分解。

此外，讨论了 Union Bound 为什么能和 Chernoff 形成"组合技"：Chernoff 把每个事件的概率压到 1/poly(n)（指数小），Union Bound 乘以 n 后仍然是 1/poly(n)。如果单事件只能压到常数概率（比如用 Markov），乘以 n 就炸了——这就是为什么 Markov/Chebyshev 解决不了 occupancy problem，必须上 Chernoff。

我们还建立了跨章节的不等式应用对比：第 2 章用 Chernoff 解最大负载，第 3 章用 Chebyshev 分析 Count Sketch，第 4 章用 Hoeffding（汉明空间降维）和 χ²-Chernoff（JL 证明），以及 Khintchine 不等式（FJLT）。这种跨章节的横向对比帮助用户建立了"不等式工具箱"的统一视角。

**核心收获：** 用户从"每个不等式各自为战"进入到了一个系统化的决策框架：面对一个尾概率问题，按"前提条件 → 可选不等式 → 界的衰减速度 → 能否满足要求"的链条来判断。关键的决策节点是：（1）只知道期望 → Markov；（2）有方差 → Chebyshev；（3）独立伯努利和 → Chernoff；（4）有界但非伯努利 → Hoeffding；（5）有依赖但鞅差有界 → Azuma。最重要的选择标准是"衰减速度"——多项式衰减导致对精度参数 δ 的多项式依赖，指数衰减导致对数依赖，这在高维和大数据场景下是质的区别。

**延伸思考：** Generalized Chernoff（通过参数化 αᵢ 替代单参数 t）提供了一条超越标准 Chernoff 的路——在某些特定场景（如伯努利参数不均匀、k-wise 独立）下可以获得更紧的界。课程后续章节的 LSH 和 OSE 分析中，不等式选择同样是核心技能。

---

### 2026-05-18：Power of Two Choices 的平方递归 — 从直觉到严格证明

**类型：** 深化

**背景：** 用户询问 Power of Two Choices 的具体推导和为什么能成立，说明已经理解了"结果是什么"（O(log log n)），但想搞清楚"为什么会这样"，特别是为什么从 O(log n / log log n) 能降到 O(log log n)，以及中间的推导逻辑。

**讨论过程：**

我们从定义"见证变量" Bᵢ = {负载 ≥ i 的桶数} 开始，这是理解整个推导的关键。一个球要进入负载 ≥ i 的桶，它随机选的两个桶的负载都必须 ≥ i-1（否则会选负载更低的那一个）。这给出了核心不等式：一个球增加 Bᵢ 的概率 ≤ (B_{i-1}/n)²。乘以 n 个球得到 E[Bᵢ] ≤ E[B_{i-1}²]/n。

接下来是关键的一步——定义 bᵢ = E[Bᵢ]/n（负载 ≥ i 的桶的期望占比），并假设 B_{i-1} 集中在期望附近（需要 Azuma-Hoeffding 鞅论证，因为球有依赖）。在这个假设下，B_{i-1}² ≈ (n·b_{i-1})²，于是 bᵢ ≤ (n·b_{i-1})²/n² = b_{i-1}²。这就是平方递归的核心。

我们讨论了为什么 b₀ = 1 不能直接启动递归（因为 1² = 1，不会衰减），并解释了常数层和平方递归层的分界：前面的层（常数数量级内）bᵢ 降到某个小于 1 的常数（如 1/4），然后平方递归开始发力——每步把占比平方，O(log log n) 步后 < 1/n。

最后用指数塔的直观解释收敛：b_{i₀+k} ≤ (b_{i₀})²^k，设 b_{i₀} = 1/4，解 (1/4)²^k < 1/n → ²^k > log₄ n → k > log₂ log₄ n = O(log log n)。

**核心收获：** 用户从"记住了 O(log log n) 的结果"进入到了理解"为什么是平方下降、为什么是 log log n 而不是其他"的层面。平方递归是这个结果的核心——随机选两个桶把线性衰减（bᵢ ≈ b_{i-1}·const → O(log n)）变成了平方衰减（bᵢ ≈ b_{i-1}² → O(log log n)）。选 d 个桶会得到 bᵢ ≈ b_{i-1}^d → O(log log n / log d)，收益递减。
