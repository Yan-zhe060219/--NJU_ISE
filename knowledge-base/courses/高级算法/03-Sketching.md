---
title: "Sketching — 数据流草图与近似计数"
course: "高级算法"
tags: ["sketching", "Morris", "Count-Min", "Flajolet-Martin", "Bloom-filter", "数据流"]
created: 2026-05-15
source: "Sketching.pdf"
status: reviewed
related: ["01-Fingerprinting", "02-Hashing"]
chapter: 3
---

## 一句话总结

在数据只能扫一遍、内存远小于数据量的约束下，用随机化技术把"精确答案"压缩为"高概率近似"——空间从 O(n) 降到 O(log log n) 甚至常数，这是 Sketching 的核心魔法。

## 知识地图

```mermaid
flowchart TD
    SKETCH[Sketching 草图] --> AC[近似计数 Morris]
    SKETCH --> DE[去重估计 Distinct Elements]
    SKETCH --> PQ[点查询 Point Query]
    SKETCH --> FM[频率矩估计 F₂]
    SKETCH --> BF[布隆过滤器]

    AC --> MORRIS[Morris: X+1 w.p. 2^{-X}<br>空间 O(log log n)]
    MORRIS --> MORRISP[Morris+: k个副本取平均]
    MORRISP --> MORRISPP[Morris++: ℓ个Morris+取中位数]

    DE --> MINSKETCH[Min Sketch: 1/min - 1]
    MINSKETCH --> FMALGO[Flajolet-Martin: 2^{max zeros}]
    FMALGO --> BOTTOMK[Bottom-k: kM/Y_k]

    PQ --> BUCKET[Bucket Sketch: 基本计数]
    BUCKET --> CMS[Count-Min Sketch: min over k hashes]

    FM --> TOW[Tug-of-War: Σ σ(x)]
    TOW --> TOWP[Count Sketch+: 平均降方差]
    TOWP --> TOWPP[Count Sketch++: CMS + sign]

    BF --> BF1[基本Bloom: 1个哈希]
    BF1 --> BFK[Bloom Filter+: k个哈希<br>误报率 = 0.6185^c]
```

## 核心概念

### 1. Morris 近似计数 — 从 O(log n) 到 O(log log n) 的空间压缩

**问题**：在 $O(\log\log n)$ 空间内维护一个计数器，允许近似。确定性方法需 $\lceil\log_2 n\rceil$ bits，而 $\log\log n$ 只存"n 的量级"——n=10⁹ 时 $\log n \approx 30$，$\log\log n \approx 5$。

**核心洞察**：让计数器增长越来越慢。n 很大时再加 1 对数量级几乎没影响——计数器应该"懒得动"。

#### 1.1 Morris 基本算法

```
init: X ← 0
increment: 以概率 2^{-X} 执行 X ← X+1，否则什么都不做
query: 返回 n̂ = 2^X - 1
```

**参数直觉**：X=0 时概率=1（每次都动）；X=10 时概率=2⁻¹⁰≈1/1024（约每 1024 次动一次）。估算值 $2^X$ 以指数速度增长 → X 以对数速度增长。

#### 1.2 无偏性证明

**命题**：$\mathbb{E}[2^{X_n}] = n + 1$，其中 $X_n$ 是 n 次增量后的 X。

**基始**：n=0，$X_0=0$，$\mathbb{E}[2^0]=1=0+1$。

**归纳步**：假设 $\mathbb{E}[2^{X_n}] = n+1$。给定 $X_n=j$：
$$\mathbb{E}[2^{X_{n+1}} \mid X_n=j] = (1-2^{-j}) \cdot 2^j + 2^{-j} \cdot 2^{j+1} = 2^j - 1 + 2 = 2^j + 1$$

全期望公式：
$$\mathbb{E}[2^{X_{n+1}}] = \sum_j Pr[X_n=j] \cdot (2^j+1) = \mathbb{E}[2^{X_n}] + 1 = n+2$$

**证明精妙之处**：不关心 $X_n$ 的复杂分布，只关心 $\mathbb{E}[2^X]$。概率 $2^{-X}$ 被精确设计成让不动项和动项的和恰好是 $2^j+1$，常数 1 完美提出。

#### 1.3 空间分析

**Jensen 不等式**（$f(x)=2^x$ 凸）：$2^{\mathbb{E}[X]} \leq \mathbb{E}[2^X] = n+1$，得 $\mathbb{E}[X] \leq \log_2(n+1)$。

**Markov 不等式**（对非负 Y，$Pr[Y \geq a] \leq \mathbb{E}[Y]/a$）：
$$Pr[\hat{n} \geq 10n] \leq \frac{\mathbb{E}[\hat{n}]}{10n} = \frac{n}{10n} = 0.1$$

以 90% 概率 $2^X \leq 10n+1$，$X \leq \log_2(10n+1)$。编码 X 只需 $\log_2\log_2(10n+1) = \log\log n + O(1)$ bits。

#### 1.4 Chebyshev 分析：方差问题

基本版方差太大。需要 bound $\mathbb{E}[2^{2X}]$。

**归纳证明** $\mathbb{E}[2^{2X_n}] \leq 3n(n+1)/2 + 1$：
$$\mathbb{E}[2^{2X_{n+1}}] = \mathbb{E}[(1-2^{-X_n})2^{2X_n} + 2^{-X_n} \cdot 2^{2(X_n+1)}] = \mathbb{E}[2^{2X_n} + 3\cdot 2^{X_n}]$$
$$\leq 3n(n+1)/2 + 1 + 3(n+1) \leq 3(n+1)(n+2)/2 + 1$$

最终 $\text{Var}[\hat{n}] \approx n^2/2$。Chebyshev 给出 $Pr[|\hat{n}-n| \geq \epsilon n] \leq 1/(2\epsilon^2)$——当 $\epsilon<1$ 时无意义。

#### 1.5 Morris+：Mean Trick 降方差

维护 k 个独立 Morris 计数器，返回平均 $\hat{n} = \frac{1}{k}\sum \hat{n}_i$。

由独立性：$\text{Var}[\hat{n}] = \text{Var}[\hat{n}_1]/k \leq n^2/(2k)$。

$$Pr[|\hat{n}-n| \geq \epsilon n] \leq \frac{1}{2k\epsilon^2} = \delta \quad\Rightarrow\quad k = O(1/\epsilon^2\delta)$$

#### 1.6 Morris++：Median-of-Means 降失败概率

维护 ℓ 个独立 Morris+（每个失败概率 ≤ 1/3），返回**中位数**。

只要超过半数 Morris+ 正确，中位数就正确。$Y_i \sim \text{Bernoulli}(1/3)$ 独立，$\mathbb{E}[\sum Y_i] = \ell/3$。

$$Pr[\text{中位数错误}] = Pr\left[\sum Y_i \geq \frac{\ell}{2}\right]$$

Chernoff-Hoeffding：
$$Pr\left[\sum Y_i - \frac{\ell}{3} \geq \frac{\ell}{6}\right] \leq \exp\left(-\frac{2(\ell/6)^2}{\ell}\right) = \exp\left(-\frac{\ell}{18}\right) = \delta$$

取 $\ell = \lceil 18\ln(1/\delta) \rceil$。**关键对比**：Morris+ 对 $\delta$ 多项式依赖（$k=O(1/\delta)$），Morris++ 对数依赖（$\ell=O(\log(1/\delta))$）。

总空间：$k\ell = O(\epsilon^{-2}\log(1/\delta)) \cdot \log\log n$。

**推广（Flajolet 1985）**：增量概率为 $1/(1+\alpha)$，估计 $\hat{n}=((1+\alpha)^X-1)/\alpha$。$\alpha = \Theta(\epsilon^2\delta)$ 时最优。

---

### 2. Min Sketch 与 Flajolet-Martin（F₀ 估计 / 去重计数）

**问题**：数据流 $x_1,...,x_n \in [N]$，估计不同元素个数 z。流只能扫一遍，内存远小于 z。

#### 2.1 Min Sketch：对称性论证

**理想化假设（SUHA）**：存在真均匀哈希 $h: U \to [0,1]$（连续）。维护 $Y = \min_i h(x_i)$。z 个不同元素产生 z 个 i.i.d. Uniform(0,1) 值。$Y = \min(H_1,...,H_z)$。

**直觉**：z 个点把 [0,1] 分成 z+1 个区间，由对称性每个等长 → $\mathbb{E}[Y] = 1/(z+1)$。

**严格推导**：CDF $Pr[Y > y] = (1-y)^z$，PDF $p(y) = z(1-y)^{z-1}$。
$$\mathbb{E}[Y] = \int_0^1 y \cdot z(1-y)^{z-1} dy = \frac{1}{z+1}, \quad \mathbb{E}[Y^2] = \frac{2}{(z+1)(z+2)}$$
$$\text{Var}[Y] \leq \frac{1}{(z+1)^2}$$

估计器 $\hat{Z} = 1/Y - 1$。但 Chebyshev 给出常数失败概率，需改进。

#### 2.2 Min Sketch+：Mean Trick

k 个独立哈希 $h_1,...,h_k$，$Y_j = \min_i h_j(x_i)$，$\bar{Y} = \frac{1}{k}\sum Y_j$。

由 pairwise independence（交叉项 Cov=0）：$\text{Var}[\bar{Y}] \leq 1/(k(z+1)^2)$。

$$Pr[|\hat{Z}-z| \geq \epsilon z] \leq \frac{4}{k\epsilon^2} \leq \delta \quad\Rightarrow\quad k = \lceil 4/(\epsilon^2\delta) \rceil$$

#### 2.3 Flajolet-Martin：离散化后的实用方案

Min Sketch 需要连续哈希（不可实现）。FM 用离散技巧达到相同效果。

**核心定义**：$\text{zeros}(y) = \max\{i : 2^i \mid y\}$，即尾部连续 0 的个数。均匀随机 w-bit 数的 zeros 服从几何分布：$Pr[\text{zeros} \geq r] = 2^{-r}$。这和连续情况下最小值的结构相同。

**算法**（2-wise independent h: $[2^w] \to [2^w]$）：
```
R = max_i zeros(h(x_i))
返回 ẑ = 2^R
```

**直觉**：z 个不同元素，期望 $z\cdot 2^{-r}$ 个满足 zeros ≥ r。当 $2^r \gg z$ 时几乎没有；当 $2^r \ll z$ 时有很多。R 恰好捕获 $r \approx \log_2 z$ 附近的相变阈值。

**严格分析**（引入辅助变量 $Y_r$）：

定义 $Y_r = \sum_{x \text{ distinct}} \mathbf{1}[\text{zeros}(h(x)) \geq r]$。

由 linearity of expectation + 2-wise independence：
$$\mathbb{E}[Y_r] = z \cdot 2^{-r}, \quad \text{Var}[Y_r] \leq z \cdot 2^{-r} = \mathbb{E}[Y_r]$$

注意 $R = \max\{r : Y_r > 0\}$。

- **高估控制**（Markov）：令 $r^* = \lceil \log_2(Cz) \rceil$。$Pr[\hat{Z} > Cz] \leq Pr[Y_{r^*} > 0] \leq \mathbb{E}[Y_{r^*}] = z/2^{r^*} \leq 1/C$。
- **低估控制**（Chebyshev）：令 $r^{**} = \lceil \log_2(z/C) \rceil$。$Pr[\hat{Z} < z/C] \leq Pr[Y_{r^{**}} = 0] \leq \text{Var}[Y_{r^{**}}]/\mathbb{E}[Y_{r^{**}}]^2 \leq 2^{r^{**}}/z \leq 2/C$。

合并：总失败概率 ≤ 3/C。**空间**：$O(\log\log N)$ bits（存 R）+ $O(\log N)$ bits（存哈希函数）。

**关键技巧**：$Y_r$ 是分析工具而非算法本身——"引入合适的中间随机变量承载分析"贯穿全课程。

#### 2.4 Bottom-k 算法（第 41-44 页）— 完整推导

**直觉**：z 个均匀分布在 [1,M] 上的点，平均间距约 M/z。第 k 小约在 k·M/z 处 → $z \approx kM/Y_k$。

```
h: [N] → [M]
维护 k 个最小哈希值 Y_1 ≤ Y_2 ≤ ... ≤ Y_k
查询：返回 Ẑ = kM / Y_k
```

**为什么比单看最小值好？** $Y_1$ 只用 1 个样本，方差 $\approx 1/z^2$。$Y_k$ 用 k 个样本，方差 $\approx 1/(kz^2)$。和 Min Sketch+（k 个独立哈希各自取 min）精神相同，但 Bottom-k 用**一个哈希函数下的多个次序统计量**——实现更简单、常数更好。

**严格分析框架**：设 z 个哈希值 $X_1,...,X_z \in [M]$，均匀且 pairwise independent。排序 $Y_1 \leq ... \leq Y_z$。目标 $Pr[|\hat{Z}-z| \geq \epsilon z] \leq \delta$（$\epsilon \leq 1/2$）。

**从估计误差到次序统计量偏离**：
- 高估 $\hat{Z} > (1+\epsilon)z \iff Y_k < kM/[(1+\epsilon)z]$
- 低估 $\hat{Z} < (1-\epsilon)z \iff Y_k > kM/[(1-\epsilon)z]$

**阈值简化技巧**（核心！）：对 $\epsilon \in (0,1)$ 有不等式 $1/(1+\epsilon) \leq 1-\epsilon/2$ 和 $1/(1-\epsilon) \geq 1+\epsilon/2$。因此：
$$Y_k < \frac{kM}{(1+\epsilon)z} \implies Y_k < \left(1-\frac{\epsilon}{2}\right)\frac{kM}{z}$$
$$Y_k > \frac{kM}{(1-\epsilon)z} \implies Y_k > \left(1+\frac{\epsilon}{2}\right)\frac{kM}{z}$$

证明（第一个）：$\frac{1}{1+\epsilon} - (1-\frac{\epsilon}{2}) = \frac{\epsilon(\epsilon-1)}{2(1+\epsilon)} \leq 0$。

所以只需控制更宽松的阈值条件。

**引入指示变量 V 和 W**：
$$V = \sum_{i=1}^{z} \mathbf{1}\left[X_i \leq \left(1-\frac{\epsilon}{2}\right)\frac{kM}{z}\right], \quad W = \sum_{i=1}^{z} \mathbf{1}\left[X_i \leq \left(1+\frac{\epsilon}{2}\right)\frac{kM}{z}\right]$$

**关键对应**：
- $Y_k < (1-\epsilon/2)kM/z \iff V \geq k$（至少 k 个元素 ≤ 该阈值）
- $Y_k > (1+\epsilon/2)kM/z \iff W < k$（不足 k 个元素 ≤ 该阈值）

**期望与方差**：
$$\mathbb{E}[V] = z \cdot \frac{(1-\epsilon/2)kM/z}{M} = \left(1-\frac{\epsilon}{2}\right)k, \quad \mathbb{E}[W] = \left(1+\frac{\epsilon}{2}\right)k$$

展开方差：$\text{Var}[V] = \sum\text{Var}[\mathbf{1}_i] + \sum_{i\neq j}\text{Cov}(\mathbf{1}_i,\mathbf{1}_j)$。由 2-wise independence，$\text{Cov}=0$。故 $\text{Var}[V] \leq \mathbb{E}[V] \leq k$。同理 $\text{Var}[W] \leq k$。

**Chebyshev 收尾**：
$$Pr[V \geq k] \leq \frac{\text{Var}[V]}{(\epsilon k/2)^2} \leq \frac{4}{\epsilon^2 k}, \quad Pr[W < k] \leq \frac{4}{\epsilon^2 k}$$
$$Pr[|\hat{Z}-z| \geq \epsilon z] \leq \frac{8}{\epsilon^2 k} \leq \delta \quad\Rightarrow\quad k = \lceil 16/(\epsilon^2\delta) \rceil$$

**关于独立性**：课件从 2-wise 切换为 3-wise。Chebyshev 层面 2-wise 足够（仅需 Cov=0），但 BJKST 更精细分析（如用 Chernoff 替代 Chebyshev）需要 $O(\log(1/\delta))$ 阶独立性。实践中 $M=N^3$ 保证哈希冲突可忽略。

|  | Min Sketch+ | Flajolet-Martin | Bottom-k |
|--|------------|-----------------|----------|
| **核心统计量** | k 个独立最小值 | 最大 tail zeros | 第 k 小哈希值 |
| **哈希需求** | k 个独立哈希 | 1 个 2-wise 哈希 | 1 个 2-wise 哈希 |
| **空间** | k 个实数（不可实现） | $\log\log N$ bits | $k\log M$ bits |
| **k 取值** | $O(1/\epsilon^2\delta)$ | 无此参数 | $O(1/\epsilon^2\delta)$ |
| **误差** | $(\epsilon,\delta)$ | 常数失败概率 | $(\epsilon,\delta)$ |
| **实现复杂度** | 需连续哈希 | 极简 | 需维护小顶堆 |

Bottom-k 的核心优势：用一个哈希函数达到 Min Sketch+ 用 k 个哈希函数的效果。HyperLogLog 等工业级算法由此思路发展而来。

---

### 3. Count-Min Sketch（频率估计 / 点查询）

**问题**：数据流 $x_1,...,x_n \in [N]$，对任意 x 查询频率 $f_x$，允许 $\pm \epsilon n$ 加性误差。

#### 3.1 Bucket Sketch（基本版）

```
h: [N] → [m], S[1..m] = 0
update(x): S[h(x)]++
query(x): 返回 f̂_x = S[h(x)]
```

**性质**：$\hat{f}_x \geq f_x$（碰撞只增不减——永不高估真值，这里指永不低于真值）。碰撞带来正偏差。

**期望分析**（2-universal h）：
$$\mathbb{E}[S[h(x)]] = f_x + \sum_{y\neq x} f_y \cdot Pr[h(y)=h(x)] \leq f_x + \frac{n}{m}$$
$$Pr[\hat{f}_x - f_x \geq \epsilon n] \leq \frac{1}{\epsilon m} \quad\text{(Markov)}$$

需 $m = 1/(\epsilon\delta)$，对 $\delta$ 多项式。

#### 3.2 Count-Min Sketch：取 min 的魔法

**洞察**：每个 counter 估计 ≥ 真值，但不同哈希函数的碰撞模式不同。取 min → 选碰撞最少、最接近真值的那个。

```
k 个独立 2-universal 哈希 h_1,...,h_k: [N] → [m]
CMS[k][m] = 0
update(x): for all j, CMS[j][h_j(x)]++
query(x): f̂_x = min_j CMS[j][h_j(x)]
```

**分析**：对每行 j，$\mathbb{E}[CMS[j][h_j(x)]] \leq f_x + n/m$。Markov：
$$Pr[CMS[j][h_j(x)] - f_x \geq \epsilon n] \leq \frac{1}{\epsilon m}$$

k 行独立：
$$Pr[\hat{f}_x - f_x \geq \epsilon n] \leq \left(\frac{1}{\epsilon m}\right)^k$$

取 $m = \lceil e/\epsilon \rceil$，$k = \lceil \ln(1/\delta) \rceil$：
$$\leq (1/e)^k = e^{-\ln(1/\delta)} = \delta$$

**空间**：$km = O(\epsilon^{-1}\log(1/\delta))$ 计数器，每个 $O(\log n)$ bits。

**为什么取 min 而非 mean？** 碰撞只使估计偏大（安全方向），取 min 得最接近真值。取 mean 被碰撞"污染"，无法消除偏差。

#### 3.3 线性性质与 Heavy Hitters

CMS 是线性的：$CMS_{all} = CMS_1 + CMS_2$（逐元素相加）。分布式流处理核心性质。

**Heavy Hitters**：找频率 $> \epsilon n$ 的元素。对值域二分：维护 CMS 树，每层检查左右子区间频率估计，只深入 $> \epsilon n$ 的分支 → $O(k\log N)$ 时间。

---

### 4. Tug-of-War / Count Sketch（F₂ 估计）

**问题**：估计 $F_2 = \sum_x f_x^2$。CMS 做不了——误差 $\pm\epsilon n$ 是加性的，平方后累积不可控。

例：$f=(1,1,...,1)$ 时 $F_2=n$，$f=(1,1,...,1,\sqrt{n})$ 时 $F_2=2n-1$。两者 $F_2$ 差常数倍，但 CMS 误差 $\pm\epsilon n$ 级别，无法区分。

#### 4.1 Tug-of-War 基本版

给每个元素分配随机 ±1 符号 $\sigma(x)$（2-wise independent）。$z = \sum_i \sigma(x_i) = \sum_x f_x \sigma(x)$。查询返回 $z^2$。

**无偏性**：
$$\mathbb{E}[z^2] = \sum_{x,y} f_x f_y \cdot \mathbb{E}[\sigma(x)\sigma(y)]$$
- $x=y$：$\mathbb{E}[\sigma(x)^2]=1$（平方恒为 1）
- $x\neq y$：$\mathbb{E}[\sigma(x)\sigma(y)]=0$（2-wise independence）

$$\mathbb{E}[z^2] = \sum_x f_x^2 = F_2$$

**直觉**：不同元素的符号正负相消，只有同元素的 $f_x^2$ 保留——这就是"Tug-of-War"（拔河）名字的由来。

#### 4.2 方差分析

$\text{Var}(z^2) = \mathbb{E}[z^4] - F_2^2$。展开 $z^4 = \sum_{a,b,c,d} f_a f_b f_c f_d \cdot \sigma(a)\sigma(b)\sigma(c)\sigma(d)$。

由于 σ 取值 ±1 且 2-wise independent，只有每个元素出现**偶数次**的项非零：
- **4-0-0-0**（四个位置同元素）：$\mathbb{E}[\sigma(a)^4]=1$。贡献 $\sum f_a^4$
- **2-2-0-0**（两对相等）：$\mathbb{E}[\sigma(a)^2\sigma(c)^2]=1$。3 种排列。贡献 $3\sum_{a\neq c} f_a^2 f_c^2$
- 其他模式（2-1-1-0, 1-1-1-1）→ 奇次出现 → 期望 0

$$\mathbb{E}[z^4] \leq F_2^2 + 3F_2^2 = 4F_2^2, \quad \text{Var}(z^2) \leq 3F_2^2$$

Chebyshev：$Pr[|z^2-F_2| \geq \epsilon F_2] \leq 3/\epsilon^2$。常数失败概率。

#### 4.3 Tug-of-War+（Mean Trick）

k 个独立副本取平均：$\text{Var} \leq 4F_2^2/k$。取 $k = 4/(\epsilon^2\delta)$。

#### 4.4 Count Sketch++（完整版：哈希分桶 + 符号）

融合 CMS 的分桶和 Tug-of-War 的符号：k×m 矩阵，每行独立哈希 $h_j$ 和符号 $\sigma_j$。

```
update(x): CS[j][h_j(x)] += σ_j(x)  for all j
query(x): median_j { σ_j(x) · CS[j][h_j(x)] }
```

**单行误差**：$E_j = \sigma_j(x)CS[j][h_j(x)] - f_x = \sum_{y\neq x} \sigma_j(x)\sigma_j(y)\mathbf{1}[h_j(x)=h_j(y)]f_y$。

展开 $\mathbb{E}[E_j^2]$（利用 σ 和 h 的 2-wise independence，交叉项消去）：
$$\mathbb{E}[E_j^2] = \sum_{y\neq x} f_y^2 \cdot Pr[h_j(x)=h_j(y)] \leq \frac{F_2}{m}$$

取 $m = \lceil 9/\epsilon^2 \rceil$：$\mathbb{E}[|E_j|] \leq \epsilon\sqrt{F_2}/3$。Markov → 单行失败 ≤ 1/3。k 行取中位数 + Chernoff-Hoeffding → $k = \lceil 18\ln(1/\delta) \rceil$。

**空间** $O(\epsilon^{-2}\log(1/\delta))$，误差 $\pm \epsilon\sqrt{F_2}$（相对于 $F_2$ 的 $\epsilon$ 倍，与 CMS 的 $\pm\epsilon n$ 不同）。

---

### 5. Bloom Filter（近似成员查询）

**问题**：维护集合 S（大小 n），回答"x ∈ S?"。允许假阳性，不允许假阴性。信息论下界 $\log\binom{N}{n} \approx n\log(N/n)$ bits，Bloom Filter 用远小于此的空间换取可控假阳性。

#### 5.1 基本 Bloom Filter

```
m 位比特数组 A，初始全 0
insert(x): A[h(x)] = 1
query(x): 检查 A[h(x)] == 1
```

n 次插入后某位仍为 0 的概率 = $(1-1/m)^n \approx e^{-n/m}$。假阳性 ≈ $1-e^{-n/m}$。m=n 时 ≈ 63%，太高。

#### 5.2 Bloom Filter+：k 个哈希

```
insert(x): 对所有 j, A[h_j(x)] = 1
query(x): 检查所有 j, A[h_j(x)] == 1
```

n 次插入后某位仍为 0 ≈ $(1-1/m)^{kn} \approx e^{-kn/m}$。假阳性 ≈ $(1 - e^{-kn/m})^k$。

#### 5.3 最优参数推导

令 $m = cn$, $k = c\ln 2$：
$$\text{FPR} = (1 - e^{-c\ln 2 \cdot n/(cn)})^k = (1 - e^{-\ln 2})^k = (1/2)^{c\ln 2} = (0.6185)^c$$

**导数验证 k 的最优性**：$\ln\text{FPR} = k\ln(1-e^{-k/c})$。令导数 = 0 → $e^{-k/c} = 1/2$ → $k = c\ln 2$。

c=10 → FPR ≈ 1/122，每元素约 10 bits。c=20 → FPR ≈ 6.8×10⁻⁵，每元素约 20 bits。

#### 5.4 Azuma 不等式的严格分析

启发式用"期望 0 的个数"替代"实际 0 的个数"。需要验证集中性。

$q_i$ = 插入 i 个元素后 0 的个数。$\{q_i\}$ 是鞅，$|q_i-q_{i-1}| \leq k$（每次最多翻转 k 个比特）。

Azuma：$Pr(|q_n - \mathbb{E}[q_n]| \geq t) \leq 2\exp(-2t^2/(nk^2))$。

取 $t = O(k\sqrt{n})$ → 概率可忽略。所以 #0 ≈ $\mathbb{E}[\#0] \pm O(k\sqrt{n})$，启发式近似渐近严格。

#### 5.5 与 Fingerprinting 的统一视角

Bloom Filter 是第 1 章 Fingerprinting 思想的直接应用：小空间"指纹"（k 个比特位的模式）替代完整集合，接受假阳性换取空间指数压缩。和 EQ 问题中 Alice 发 $f(r) \bmod p$ 而非 n-bit 串是同一哲学。

---

### 6. 贯穿全章的设计模式：基本版 → +版 → ++版

整个 Sketching 章节反复出现同一配方。这不是三个算法拼凑，而是同一套数学在三个问题上的应用：

| 版本 | 操作 | 数学效果 |
|------|------|----------|
| **基本版** | 一个 sketch | 期望正确，方差大 / 失败概率常数 |
| **+版** | k 个独立副本取**平均** | 方差 ÷ k（Chebyshev）；对 $\epsilon$ 多项式，对 $\delta$ 多项式 |
| **++版** | ℓ 个 +版取**中位数** | 失败概率指数衰减（Chernoff-Hoeffding）；对 $\delta$ 从多项式 → 对数 |

**出现位置**：
- Morris → Morris+ (mean) → Morris++ (median-of-means)
- Min Sketch → Min Sketch+ (mean) → FM (不同的降方差路径)
- Tug-of-War → Tug-of-War+ (mean) → Count Sketch++ (median + hashing)

**核心数学**：
1. **Mean Trick**：$\text{Var}(\bar{X}) = \text{Var}(X_1)/k$，只需 pairwise independence（Cov=0）
2. **Median Trick**：超过半数正确则中位数正确，Chernoff-Hoeffding 将失败概率从常数压到 $\exp(-\Omega(\ell))$

**关键收益**：从 $\delta$ 多项式依赖变成对数依赖。把 δ 从 0.1 压到 10⁻⁶，median trick 只需约 60 倍空间（$\ln(10^5) \approx 11.5$），mean trick 需要 10⁵ 倍。这个模式在第 4 章（JL 降维 + LSH boosting）会再次出现。

## 难点突破

### 难点 1：Morris 算法为什么是无偏的？

**容易迷惑的地方**：X 的值取决于前面所有增量的随机决策，感觉很复杂。但无偏性证明的魔法在于——我们不关心 X 本身的分布，只关心 $\mathbb{E}[2^X]$。

**推导**：
$$\mathbb{E}[2^{X_{n+1}}] = \sum_j Pr[X_n = j] \cdot \left[(1-2^{-j}) \cdot 2^j + 2^{-j} \cdot 2^{j+1}\right]$$
$$= \sum_j Pr[X_n = j] \cdot (2^j - 1 + 2) = \sum_j Pr[X_n = j] \cdot (2^j + 1) = \mathbb{E}[2^{X_n}] + 1$$

每一项中，以概率 1-2^{-j} 不变（贡献 2^j），以概率 2^{-j} 加一（贡献 2^{j+1}），总和恰好是 2^j + 1。设计 2^{-X} 的概率就是为了让这两项完美抵消。

### 难点 2：Flajolet-Martin 中 zeros(y) 的作用

**直觉**：均匀随机数的二进制尾部连续 0 的个数服从几何分布——Pr[zeros ≥ r] = 2^{-r}。z 个不同元素，期望有 z·2^{-r} 个元素的尾部 0 数 ≥ r。

- 当 2^r ≫ z 时，Y_r ≈ 0（大概率没有 ≥ r 个零的元素）
- 当 2^r ≪ z 时，Y_r > 0（大概率有）
- R = max zeros 在 $\log_2 z$ 附近切换

这就是为什么 $2^R$ 在 z 的量级附近——它捕捉了"从有到无"的阈值。

## 与前章关联

- 依赖 01-Fingerprinting 的 Fingerprint 概念（用小空间代表大信息）
- 大量使用 02-Hashing 中的 Chernoff Bound、Markov、Chebyshev 进行概率分析
- Count-Min 中的哈希碰撞分析直接使用 02 中 Universal Hashing 的性质
- Bloom Filter 是 Fingerprinting 的"假阳性可接受"哲学的直接应用
- 三个主题共享同一核心范式：**随机化 + 独立副本 + 中位数/平均 → (ε,δ)-估计**

## 记忆卡片

**Q1**: Morris 算法用了多少空间？
**A**: O(log log n) bits。因为 $X \approx \log_2 n$，$\log_2 X \approx \log_2\log_2 n$ bits。

**Q2**: Flajolet-Martin 为什么用"尾部连续 0 的个数"？
**A**: 均匀随机数的 zeros 服从几何分布：Pr[zeros ≥ r] = 2^{-r}。z 个不同元素中 ≥ r 个零的期望数 = z/2^r，在 r ≈ log₂ z 处发生相变，R 恰捕获这个阈值。

**Q3**: Count-Min Sketch 为什么取 min 而不是 mean？
**A**: 每个 counter 的估计 ≥ 真实值（因为哈希碰撞只会增加计数）。取 min 得到最接近真实值的下界估计。取 mean 会被碰撞"污染"。

**Q4**: Bloom Filter 最优参数？
**A**: m = cn, k = c·ln 2，假阳性 = (0.6185)^c。c=10 时约 1% 误报。

**Q5**: Morris++ 和 Morris+ 的区别？
**A**: Morris+ 取 mean 降方差。Morris++ 取 median-of-means：ℓ 个 Morris+ 中超过半数正确即可，用 Chernoff 将失败概率从常数降到 δ（指数衰减）。


## 💬 学习对话补充

### 2026-05-18：全章完整推导整理 — 从"知道算法"到"理解每一步为什么成立"

**类型：** 深化

**背景：** 用户已完成第 3 章笔记的初稿（涵盖 Morris、Min Sketch、Flajolet-Martin、Count-Min、Tug-of-War、Bloom Filter 六大主题），但在复习时发现原笔记只给出了算法的"结论"和"核心公式"，缺少从问题设定到最终结果之间的完整推导链路。用户明确要求"仔细整理每个小 issue 的完整推导过程并配上足够的思路讲解"，目的是建立从"知道这个算法"到"理解每一步为什么成立、为什么概率这样设计、为什么空间是这个量级"的深层理解。

**讨论过程：**

我们按课件顺序逐一展开每个 Issue 的推导。Morris 部分从"为什么 $2^{-X}$ 这个概率"开始——关键在于设计概率使得不动项和动项的和恰好提出常数 1，从而归纳成立。这解释了一个常见的困惑：学生通常能背下 Morris 算法但不知道为什么是这个概率。接着通过 Markov → Chebyshev 的递进揭示了基本版方差太大的致命缺陷，再自然地引出 Morris+（mean trick：方差 ÷ k）和 Morris++（median-of-means：失败概率指数衰减）的设计动机。

Min Sketch 部分重点展开了"对称性论证"的严格版本——不依赖直觉"z+1 个区间等长"，而是通过 CDF → PDF → Beta 积分得到 $\mathbb{E}[Y]=1/(z+1)$ 和 $\text{Var}[Y] \leq 1/(z+1)^2$ 的精确表达式。

Flajolet-Martin 的分析是整个推导中技巧性最强的部分。关键是引入"中间变量" $Y_r$ ——计数有多少元素的 zeros ≥ r——然后发现 $R = \max\{r: Y_r > 0\}$ 的尾概率可以通过 $Y_r$ 的期望（Markov 控制高估）和方差（Chebyshev 控制低估）来分析，而 $Y_r$ 的期望/方差在 2-wise independence 下精确可算。这种"引入合适的中间随机变量来承载分析"的技术贯穿了整个课程。

Count-Min Sketch 部分着重解释了"为什么取 min 而不是 mean"——这是最容易困扰初学者的设计选择。核心在于碰撞总是使计数偏大（安全方向），取 min 选最干净的那个。如果取 mean，碰撞带来的正偏差会污染所有副本，无法通过平均消除。

Tug-of-War 的 $\mathbb{E}[z^4]$ 分析是另一个技术高峰：将 $(∑σ(x)f_x)^4$ 展开，然后利用 σ 的 2-wise independence 和 ±1 取值性质，只有"每个元素出现偶数次"的项（4-0-0-0 和 2-2-0-0）才非零。这个计数技巧和后面第 4 章 Khintchine 不等式的证明共享同样的数学结构。

Bloom Filter 部分补充了最优参数 $k = c\ln 2$ 的导数推导，以及 Azuma 不等式为什么能用来严格化启发式近似——0 的个数是鞅，每次插入最多翻转 k 个位，从而尾概率指数衰减。

最后强调贯穿全章的"基本版 → +版 → ++版"设计模式不是三个独立算法的拼凑，而是同一套数学技术在三个不同问题上的应用：mean trick（方差 ÷ k，只需 pairwise independence）+ median trick（Chernoff-Hoeffding，失败概率指数衰减）。理解这个模式就等于掌握了数据流算法设计的核心方法论。

**核心收获：** 用户从"知道每个算法是什么"进入到"理解每个算法的完整推导链路和设计动机"。关键认知跃迁包括：(1) Morris 的 $2^{-X}$ 不是随便选的，是精心设计使归纳步恰好提出常数 1；(2) FM 的 $Y_r$ 是分析工具而非算法本身，这种"引入辅助变量分析"的技术会反复出现；(3) CMS 取 min 的关键前提是碰撞的**单向性**（只增不减）；(4) Tug-of-War 的 $\mathbb{E}[z^4]$ 中交叉项消去只依赖 2-wise independence，不需要 4-wise independence；(5) median-of-means 的威力在于将失败概率的依赖从 $1/\delta$ 降为 $\log(1/\delta)$。

**延伸思考：** 本章的 mean trick 和 median trick 在第 4 章（JL 降维和 LSH）中会继续出现——JL 证明用 Union Bound 过 $O(n^2)$ 对距离，LSH 用多个 hash table 做 boosting。三章共享的概率工具箱（Markov → Chebyshev → Chernoff → 鞅不等式）构成了整个随机化算法分析的基石。

---

### 2026-05-18：Bottom-k 完整推导 + 笔记结构整合

**类型：** 深化

**背景：** 在第 2 轮学习中，用户发现 Bottom-k 在原始笔记中只有一句话概括，缺失了完整的推导链路——特别是课件中 V/W 指示变量的引入逻辑、阈值简化的依据、以及 Chebyshev 方差展开的细节。同时用户注意到笔记存在结构性问题：每个算法的"概述"和"详细推导"被分散在两个独立区域（核心概念 vs 课件完整推导附录），阅读时需要反复跳转，不利于建立完整的思维链条。

**讨论过程：**

Bottom-k 推导的核心技术点有三个。第一是阈值简化：估计误差 $\hat{Z} > (1+\epsilon)z$ 等价于 $Y_k < kM/((1+\epsilon)z)$，但 $1/(1+\epsilon)$ 的分析不对称。技巧是用更宽松但对称的阈值 $(1\mp\epsilon/2)$ 来 bounding，严格证明 $1/(1+\epsilon) \leq 1-\epsilon/2$（对 $\epsilon \in (0,1)$），这样分析只用处理对称的偏离量 $\pm\epsilon k/2$。第二是次序统计量与指示变量的对应：$Y_k < T \iff \#\{i: X_i \leq T\} \geq k$，这个等价关系把"第 k 小的值落在哪里"转化为了"多少个元素落在阈值以下"——后者的期望和方差直接可算。第三是方差展开中交叉项的消除：$\text{Cov}(\mathbf{1}_i, \mathbf{1}_j) = 0$ 只依赖 2-wise independence，这意味着 Bottom-k 的 Chebyshev 分析不需要完全随机哈希。

笔记结构整合方面，用户明确要求"直接将后面的分析和原有的简单版的笔记合并，以便于查看每个部分的时候都能看到完整的 issue、算法思路、和对应的分析"。执行方式是：将原来分散的"核心概念（简要版）"和"📐 课件完整推导（详细版）"合并为统一的"核心概念（完整版）"，每个算法一节内包含问题表述→直觉→伪代码→完整推导→分析总结，删除冗余的附录区域。

**核心收获：** Bottom-k 的推导补齐了一个重要缺口——理解了它和 Min Sketch+ 的本质联系（都用 k 个统计量降方差，但 Bottom-k 用单个哈希函数的次序统计量替代 k 个独立哈希，实现更简单）。阈值简化技巧（用对称阈值替代非对称的 $1/(1\pm\epsilon)$）是一个通用的分析套路，不仅限于 Bottom-k。笔记结构上，现在读任何一个算法都可以在不跳转的情况下看到完整的推导链路，符合"由浅入深"的认知流程。

**延伸思考：** Bottom-k 是 HyperLogLog 的前身。HLL 将"保留 k 个最小哈希值"进一步压缩为"只保留每个寄存器的最大值（按前导零分组）"，在工程上达到了每寄存器 6 bits 的极致空间效率。这条演化路线（Min Sketch → Bottom-k → Flajolet-Martin → HyperLogLog）展示了理论研究如何通过逐步离散化和工程优化落地为工业级系统。
