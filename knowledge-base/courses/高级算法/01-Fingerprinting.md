---
title: "Fingerprinting — 指纹与随机化身份检测"
course: "高级算法"
tags: ["fingerprinting", "PIT", "Schwartz-Zippel", "随机化算法", "Freivald", "Karp-Rabin"]
created: 2026-05-15
source: "Fingerprinting.pdf"
status: draft
related: ["02-Hashing", "04-Dimension"]
chapter: 1
---

## 一句话总结

用随机采样生成"指纹"替代逐位比对，以极小的错误概率换取时间或空间上的指数级节省——这是随机化算法在大数据场景下最核心的思想。

## 知识地图

```mermaid
flowchart TD
    FP[Fingerprint 指纹] --> PIT[多项式恒等测试 PIT]
    FP --> CM[通信复杂度 EQ]
    FP --> MM[矩阵乘法验证 Freivald]
    FP --> PM[模式匹配 Karp-Rabin]
    FP --> ME[多重集判等 Lipton]

    PIT --> SZ[SZ单变量: 选r∈S, |S|=2d]
    PIT --> Mv[SZ多变量: Schwartz-Zippel 定理]

    SZ --> APP1[二分图完美匹配]
    SZ --> APP2[Reed-Muller码距离]
    Mv --> APP1

    PM --> RH[滚动哈希 rolling hash]
    ME --> DS[数据流算法 data stream]
```

## 核心概念

### 1. Fingerprint（指纹）

**是什么**：用一个简短的"摘要"代表一个大型对象，通过比较指纹来判断两个对象是否相同。好比人的指纹远小于全身信息，但足以唯一标识一个人。

**为什么**：直接比较两个对象需要 O(n) 时间/空间，如果对象在网络上分处两地（通信复杂度），或者有大量对象需要两两比较，直接比较太昂贵。

**怎么用**：设计一个随机函数 FING(·)，使得 `x = y ⟹ FING(x) = FING(y)`（必然），而 `x ≠ y ⟹ Pr[FING(x) = FING(y)]` 很小（高概率不误判）。这是 **one-sided error**（单向错误）：可能假阳性，不会假阴性。

### 2. Polynomial Identity Testing（PIT，多项式恒等测试）

**问题**：给定多项式 f(x)，判断 f ≡ 0？

**确定性算法**：选 d+1 个不同点，逐一验证 f(x_i) = 0。需要 d+1 次求值。

**随机化算法（Fingerprinting）**：从 S ⊆ 𝔽 中均匀随机选一个 r，检查 f(r) = 0。
- 若 f ≡ 0：一定输出 0（不会出错）
- 若 f ≢ 0：出错概率 ≤ d/|S|（由代数学基本定理：d 次多项式最多 d 个根）
- 取 |S| = 2d，错误概率 ≤ 1/2

**核心技巧**：用随机采样替代确定性遍历，从 O(d) 次求值降为 O(1) 次。

### 3. Schwartz-Zippel 定理（多变量 PIT）

**定理**：对于 𝔽[x₁, ..., xₙ] 上的 d 次多项式 f ≢ 0，从任意 S ⊆ 𝔽 独立均匀随机选取 r₁, ..., rₙ：

$$Pr[f(r₁, ..., rₙ) = 0] \leq \frac{d}{|S|}$$

**证明思路**（对 n 归纳）：
- n=1 时即代数学基本定理
- 归纳步：将 f 按 xₙ 的最高次幂 k 重写为 $f = x_n^k \cdot f_k(x_1,...,x_{n-1}) + \bar{f}$，其中 $\bar{f}$ 中 xₙ 的次数 < k
- 利用全概率公式 + 归纳假设，得错误概率 ≤ (d-k)/|S| + k/|S| = d/|S|

**应用**：完美匹配检测（Edmonds 矩阵行列式）、Reed-Muller 码距离、PCP 构造、hardness vs randomness 等。

### 4. 通信复杂度与 EQ 问题

**问题（EQ）**：Alice 有 a ∈ {0,1}ⁿ，Bob 有 b ∈ {0,1}ⁿ，判断 a = b？最少需要通信多少 bits？

**Yao 定理（1979）**：任何确定性协议最坏情况下需要 n bits 通信。

**随机化 Fingerprinting 解法**：
- 将 a, b 视为多项式系数：$f(x)=\sum a_i x^i$, $g(x)=\sum b_i x^i$
- 选素数 p ∈ [n², 2n²]，在 ℤ_p 上计算
- Alice 发送 (r, f(r) mod p) 给 Bob，仅需 O(log n) bits
- Bob 计算 g(r) mod p 比较
- 错误概率 O(1/n)（w.h.p. 正确）

### 5. Freivald 算法（矩阵乘法验证）

**问题**：验证 A × B = C？（三个 n×n 矩阵）

**直接验证**：计算 A×B 需要 O(n^ω) 时间（当前最优 ω ≈ 2.37）

**Freivald 算法**：
- 随机选 r ∈ {0,1}ⁿ
- 验证 A(Br) = Cr
- 计算 A(Br) 仅需 O(n²)：先算 Br（O(n²)），再算 A(Br)（O(n²)）
- 若 AB ≠ C，错误概率 ≤ 1/2
- 重复 O(log n) 次，总时间 O(n² log n)，w.h.p. 正确

**证明关键**：令 D = AB - C ≠ 0，若 Dr = 0，考虑 D 中非零行 D_i，有 $\sum_k D_{ik} r_k = 0$，解出 r_j 的表达式，利用 r_j 独立于其他 r_k，概率 ≤ 1/2。

### 6. Karp-Rabin 算法（模式匹配）

**问题**：在文本 x ∈ {0,1}ⁿ 中找到模式 y ∈ {0,1}ᵐ 的所有出现位置。

**指纹函数**：FING(a) = a mod p（将比特串视为二进制整数取模素数 p）

**算法**：
1. 随机选素数 p ∈ [mn³]
2. 对每个位置 i，比较 FING(x[i, i+m-1]) = FING(y) mod p
3. **滚动哈希**：FING(x[i+1, i+m]) 可从 FING(x[i, i+m-1]) 在 O(1) 时间更新

$$FING(x[i+1, i+m]) = \left(x_{i+m} + 2 \cdot FING(x[i, i+m-1]) - 2^m \cdot x_i\right) \bmod p$$

- 总时间 O(n)，空间 O(1)
- 单次比较错误概率 o(1/n²)，整体错误概率 o(1/n)

### 7. Lipton 算法（多重集判等 / 数据流）

**问题**：判断多重集 A = {a₁,...,aₙ} 和 B = {b₁,...,bₙ}（元素范围 1~n）是否相等？

**数据流场景**：输入逐个到达，只能用 O(log n) 空间

**指纹函数**：$FING(A) = \prod_{i=1}^n (r - a_i) \bmod p$

- 随机选素数 p ∈ [(n log n)²/2, (n log n)²] 和随机数 r ∈ ℤ_p
- 若 A ≠ B：多项式 $f_A - f_B \not\equiv 0$（在 ℝ 上），在 ℤ_p 上碰巧相等需要素数 p 整除 f_A - f_B 的某个非零系数 → 由素数定理，错误概率 O(1/n)
- 时间 O(n)，空间 O(log n)

## 难点突破

### 难点 1：Schwartz-Zippel 证明中的归纳步

**为什么会卡住**：证明用全概率公式拆成"f_k = 0"和"f_k ≠ 0"两个条件分支，第一次看到容易跟丢。

**突破方法**：关键是"固定 x₁,...,x_{n-1} 后，f 变成 xₙ 的单变量多项式"。如果 f_k(r₁,...,r_{n-1}) ≠ 0，那么这个单变量多项式次数恰好是 k，用单变量版本的结论（最多 k 个根），错误概率 ≤ k/|S|。如果 f_k = 0 但 f ≠ 0，则必有某个低次项的系数非零（即 f̄ 中的非零系数），这归结到对 n-1 个变量的归纳假设。

**类比**：就像拆一个"套娃"——把最外层变量 xₙ 剥离后，要么 xₙ 部分的最高次系数还活着（用单变量结论杀），要么问题下降到少一个变量的情况（递归杀）。

### 难点 2：为什么 Freivald 算法只验证 A(Br) = Cr 而不是直接验证 AB = C

**关键理解**：直接比较 AB 和 C 需要先算出 AB，那就已经 O(n^ω) 了。验证 A(Br) = Cr 的精妙在于**计算顺序**：
- 先算 Br → 一个 n 维向量（O(n²)）
- 再算 A(Br) → 另一个 n 维向量（O(n²)）
- 总计算量 O(n²)，而非 O(n^ω)

**为什么随机向量 r 能"代表"整个矩阵**：如果 AB ≠ C，则 D = AB - C 至少有一个非零元素。将 D 作用于均匀随机的 r ∈ {0,1}ⁿ，输出为 0 的概率 ≤ 1/2（因为对于 D 的每个非零行，只有一个特定的 r_j 值能让该行点积为 0，而 r_j 以 1/2 概率取该值）。

## 与前章关联

这是课程第一章，建立了"随机化指纹"的核心范式，为后续所有内容打基础：
- Hashing（02 章）将指纹思想延伸到负载均衡和哈希表理论
- Sketching（03 章）将"用小空间估算大信息"的思想进一步推到近似计数场景
- 课程后面的 JL 变换、LSH 等是 Schwartz-Zippel 思想在高维空间的推广

## 记忆卡片

**Q1**: Fingerprinting 的单向错误（one-sided error）指什么？
**A**: 如果两个对象相同，指纹一定相同（no false negative）；如果两个对象不同，指纹可能碰巧相同但概率可控（small false positive）。所以算法只会错在"误报相同"。

**Q2**: Schwartz-Zippel 定理的核心结论是什么？
**A**: n 变量 d 次非零多项式，在大小为 |S| 的集合中随机选点求值，得到 0 的概率 ≤ d/|S|。

**Q3**: Karp-Rabin 滚动哈希的递推公式为什么要加 2^m 项？
**A**: 滑动窗口时，最左边的字符移出、最右边的新字符移入。减去 2^m·x_i（移出旧字符的贡献），乘以 2（整体左移一位），加上 x_{i+m}（新字符的贡献）。

**Q4**: 从 D = AB - C ≠ 0 到 Pr[Dr = 0] ≤ 1/2 的关键一步是什么？
**A**: 考虑 D 的某个非零元素 D_{ij}，在等式 (Dr)_i = 0 中，r_j = -\frac{1}{D_{ij}}\sum_{k\neq j} D_{ik} r_k。固定其他 r_k 后，r_j 恰取该特定值的概率 ≤ 1/2。

## 💬 学习对话补充

### 2026-05-18：Private coin vs Public coin — 随机化协议中随机性的两种来源

**类型：** 澄清 + 关联

**背景：** 用户在复习第 1 章时注意到笔记中通信复杂度 EQ 问题涉及了随机化协议，但原笔记没有区分"Private coin"和"Public coin"这两种不同的随机性模型。用户直觉到这不是同一个概念，主动追问两者的区别、各自对应的原理和公式层面的差异。

**讨论过程：**

我们从最根本的定义开始区分——Private coin 是每个参与方各自独立抛硬币（对方不可见），Public coin 是所有参与方共享一条公共随机串（全都看得见）。在 Fingerprinting 解决 EQ 问题的场景中，这个区分的实际影响非常直接：如果用 Public coin，Alice 和 Bob 可以同时看到同一个素数 p 和随机数 r ∈ ℤ_p，Alice 只需发送 f(r) mod p 给 Bob（O(log n) bits），Bob 用自己的数据算 g(r) mod p 即可比较。但如果用 Private coin，Alice 自己选了 p 和 r 算完指纹后，Bob 根本不知道她用的是什么随机性——所以 Alice 必须额外把 r（或 p 和 r）也发给 Bob，通信量因此多了一截。

这里的关键洞察是：在随机化通信协议中，"同步随机性"本身是需要通信代价的。Public coin 相当于第三方免费提供了这个同步，Private coin 则要自己花钱（bits）同步。我们引入了一个直观类比：Public coin 是教室黑板——老师写一个随机数，全班都看见；Private coin 是每个人在自己的草稿纸上抛硬币——要同步就必须站起来喊出来。

更进一步，我们讨论了 Newman 定理，它给出了 public → private 转换的精确代价：额外 O(log n + log 1/ε) bits 通信，错误概率最多翻倍。证明的核心思路是：公共随机串空间虽然巨大（通常是指数级），但真正能"区分不同输入"的关键随机串其实很少——可以通过采样一个多项式大小的"好集合"来替代完整空间，然后 Alice 只需要发送这个集合中的索引（O(log n) bits）给 Bob。这意味着在绝大多数 Fingerprinting 应用中（n 很大时），public coin 到 private coin 的转换开销被大 O 记号吸收了，两者在大 n 渐近下可以视为等价——这也是为什么很多论文不刻意区分的原因。

从公式层面，我们还辨析了 Schwartz-Zippel 定理表述中的概率究竟是 public 还是 private：定理写的 Pr_{r∈_R S}[f(r)=0] ≤ d/|S|，这里的随机性来自单一源 r，本质上是一个 public coin 设定——因为 Alice 和 Bob 是对同一个 r 在比较。如果强行用 private coin（Alice 选 r_A、Bob 选 r_B 且 r_A ≠ r_B），协议本身无法成立，因为 f(r_A) 和 g(r_B) 在不同的点上求值不能直接比较。所以 private coin 协议必须包含一个"同步随机性"的步骤，同步完之后执行的仍是 public coin 逻辑。

**核心收获：** 用户从"以为随机化协议就是随便随机"进入到了理解随机性来源有两种架构选择的层次。Private vs Public 不是实现细节，而是影响通信复杂度下界和协议设计的核心维度。同时建立了与后续章节的关联——第 4 章 LSH 的哈希函数族本质上也是一种 public coin 设计：数据结构的构建者和查询者共享同一组哈希函数的随机选择，不需要在每次查询时重新协商。这个理解帮助统一了课程中多个看似独立的随机化技术背后的共同架构。

**延伸思考：** Newman 定理只是给出了 public → private 转换的通信上界，但某些问题（如 EQ）public coin 和 private coin 的确定性复杂度之间是否存在严格分离？在更复杂的多方通信模型中（如 SMP 模型），这个差异会如何放大？这些都是可以继续深挖的方向。
