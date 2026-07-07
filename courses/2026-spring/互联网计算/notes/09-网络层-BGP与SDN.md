---
title: "网络层：BGP、SDN、ICMP 与网络管理"
course: "互联网计算"
tags: ["BGP", "eBGP", "iBGP", "AS-PATH", "Hot Potato Routing", "策略路由", "SDN", "OpenFlow", "ICMP", "SNMP", "NETCONF", "YANG", "控制平面"]
created: 2026-05-18
source: "5-网络层(控制平面)-2.pdf"
source_lang: "en"
status: draft
related: ["08-网络层-路由协议", "07-网络层-IP寻址与SDN", "06-网络层-路由器与IP"]
chapter: 5
---

## 一句话总结

BGP 用路径向量 + 商业策略在 AS 之间选路（生意逻辑优先于性能）；SDN 把控制平面从每个路由器中抽出来交给集中控制器编程，实现任意路由需求；ICMP 是网络层诊断工具（ping/traceroute）；SNMP 管监控、NETCONF/YANG 管配置。

---

## 叙事主线

> 上节课（08）我们解决了 AS **内部**的路由——OSPF 用 Dijkstra 算最短路径。但互联网由成千上万个 AS 组成，AS **之间**怎么路由？这就是 BGP 要解决的问题。然后我们会问：控制平面非得分散在每个路由器上吗？SDN 给出了另一种答案——集中编程。最后，网络建好了，出问题怎么诊断？几千台设备怎么管理？ICMP 和 SNMP/NETCONF 收尾。

---

## 第一部分：BGP — AS 之间的路由

### 1.1 为什么需要 BGP？

互联网不是一家公司建的——它由成千上万个**自治系统（AS）**互联而成。每个 AS 由一家机构（ISP、大学、企业）管理，内部运行 OSPF 等协议。但 AS 之间必须交换"我能到达哪些网络"的信息——没有这个，Google 的 AS 就不知道如何把包发到微软的 AS，互联网就不存在了。

这就是 BGP 的角色：**"将因特网粘合在一起的胶水"（"glue that holds the Internet together"）**。BGP 是事实上的**域间路由协议（inter-domain routing protocol）**。

**BGP 为一个 AS 提供了四种能力**：
1. 从邻居 AS **获取**目的地网络的可达性信息（eBGP）
2. 根据可达性信息和策略**确定**到其他网络的路径
3. 将可达性信息**传播**到 AS 内部所有路由器（iBGP）
4. 向邻居 AS **通告**自己能到达的目的地

### 1.2 eBGP 与 iBGP：两种会话，一个目标

BGP 的通信分两层：

| 类型 | 全称 | 通信对象 | 作用 |
|------|------|----------|------|
| **eBGP** | External BGP | 不同 AS 的**网关路由器**之间 | 跨 AS 交换路由信息 |
| **iBGP** | Internal BGP | 同一 AS 内的**所有路由器**之间 | 把 eBGP 学到的外部路由扩散到整个 AS |

**关键角色——网关路由器（gateway router）**：位于 AS 边界的路由器，同时运行 eBGP 和 iBGP。它通过 eBGP 从邻居 AS 学习外部路径，再通过 iBGP 在 AS 内部扩散，确保 AS 内每台路由器都知道如何到达外部目的地。

```
        AS1                         AS2
   ┌──────────┐              ┌──────────┐
   │  1b  1d  │              │  2b  2d  │
   │          │   eBGP       │          │
   │  1a←─────┼──────────────┼→2c       │
   │          │              │          │
   │  1c      │              │  2a      │
   └──────────┘              └──────────┘
        ↑ iBGP 扩散               ↑ iBGP 扩散
   (1a学到外部路径后          (2c学到外部路径后
    告诉1b,1c,1d)              告诉2a,2b,2d)
```

### 1.3 BGP 消息：跑在 TCP 上的路径向量协议

BGP 的两台路由器（"对等体"，peers）通过**半永久的 TCP 连接**交换消息。BGP 是**路径向量（path vector）协议**——它通告的不是链路状态，而是"到达目标 X 需要经过哪些 AS"的完整路径。

**四种 BGP 消息**（RFC 4371）：

| 消息 | 作用 |
|------|------|
| `OPEN` | 打开到远程 BGP 对等体的 TCP 连接并认证 |
| `UPDATE` | 通告新路径，或撤销旧路径 |
| `KEEPALIVE` | 在没有 UPDATE 时保持连接活跃；同时确认 OPEN |
| `NOTIFICATION` | 报告错误，或者关闭连接 |

### 1.4 BGP 路由通告：前缀 + 属性

BGP 通告的路由 = **前缀（prefix）** + **属性（attributes）**。

- **前缀**：被通告的目的地网络（如 `192.168.0.0/24`）
- **两个关键属性**：
  - **AS-PATH**：通告前缀经过的 AS 编号序列。两个作用：(1) **防环路**——路由器收到包含自己 AS 号的路径就丢弃；(2) **选路依据**——优先选 AS-PATH 较短的路径。
  - **NEXT-HOP**：指向下一跳 AS 的具体路由器内部 IP 地址。AS 内其他路由器通过 iBGP 学到 NEXT-HOP，再结合 OSPF 等协议找到去该 NEXT-HOP 的出口接口。

**路径通告的具体过程**（以 AS3 向 AS2 通告目的地 X 为例）：

```
1. AS3 网关路由器 3a 通过 eBGP 向 AS2 网关路由器 2c 通告：AS3, X
   含义："我 AS3 承诺——发往 X 的包我可以帮你转发"

2. AS2 的 2c 根据进口策略（import policy）决定接受这个通告
   然后通过 iBGP 向 AS2 内所有路由器扩散：AS2, AS3, X
   （在路径前面加上自己的 AS 号）

3. AS2 根据出口策略（export policy）决定是否继续向外通告
   如果决定通告，AS2 网关 2a 通过 eBGP 向 AS1 通告：AS2, AS3, X
```

**多条路径时的选择**：AS1 的网关路由器 1c 可能同时学到两条到 X 的路径（AS2,AS3,X 和 AS3,X）。1c 根据策略选择一条（比如 AS3,X 更短），然后通过 iBGP 在 AS1 内只通告选中的那条。

### 1.5 转发表是如何填出来的？BGP + OSPF 协作

以上整个过程回答了"AS1 内部的路由器怎么知道去 X 走哪个接口"：

1. **iBGP** 告诉 1d："到 X 的包要先到 1c"
2. **OSPF**（AS 内部路由协议）告诉 1d："到 1c，走接口 1"
3. **结论**："到 X，走接口 1" → 写入转发表

> **BGP 管方向，OSPF 管走法。** BGP 告诉你"出门往哪走"（去哪个网关），OSPF 告诉你"怎么走到门口"（用哪个接口）。

### 1.6 热土豆路由（Hot Potato Routing）

当 AS 内路由器学到多条到同一外部目的地的路径（比如 2d 学到经 2a 和经 2c 都能到 X），怎么选？

**热土豆路由**：选 AS **内部**代价（intra-domain cost）最小的出口网关——不管出了 AS 之后要绕多少个 AS。

类比：手里捧着滚烫的土豆，赶紧扔给最近的接盘者，不在乎对方之后要递多少次。

**但这只是第三优先级**。BGP 完整的路由选择优先级：

1. **Local Preference（本地偏好值）**——策略决定，优先级最高
2. **Shortest AS-PATH（最短 AS 路径）**——经过最少的 AS
3. **Closest NEXT-HOP（最近下一跳）**——热土豆路由
4. 其他标准

> **策略 > 路径长度 > 内部代价**

### 1.7 策略路由：为什么 IP 包不总走"最优"路径？

**根本原因**：ISP 之间是商业关系，路由决策基于生意逻辑。

**核心规则**：ISP 只愿意路由去往/来自其**客户网络**的流量，**不愿意**为其他 ISP 承担中转流量（transit traffic）——这赚不到钱。

**经典例子**（课件原图）：

```
        B
       / \
      /   \
     A     C
     |     |
     w     y
     |
     x
```

- A 向 B 和 C 通告路径 Aw（"我能到 w"）
- B **选择不同 C 通告 BAw**——因为 C、A、w 都不是 B 的客户，B 从这条路径赚不到钱
- 结果：C 只能通过 CAw 到达 w，不会经过 B

**另一个例子（dual-homed x）**：x 同时接入 B 和 C 两个提供商网络。x 的策略是"不想帮 B 转发到 C 的流量"——所以 x 不会向 B 通告到 C 的路由。

### 1.8 为什么 AS 内部和 AS 之间的路由要分开？

课件总结三个原因：

| 维度 | Intra-AS（OSPF等） | Inter-AS（BGP） |
|------|-------------------|-----------------|
| **策略（Policy）** | 单一管理员，策略不重要 | 管理员要控制流量走谁的网络 |
| **规模（Scale）** | 分层路由节省表空间 | 同上，BGP 聚合前缀减少条目 |
| **性能（Performance）** | 可以专注性能优化 | **策略主导**，性能次要 |

---

## 第二部分：SDN — 重新思考控制平面

### 2.1 传统控制平面的痛点

传统网络中，每台路由器都是一个"黑箱"——交换硬件 + 私有的路由协议实现（如 Cisco IOS）。控制平面**分散**在每台路由器中，通过分布式协议（OSPF、BGP）协同计算转发表。

这带来三个问题：

**问题一：流量工程太难了**（课件用了三页 PPT 展示）

- **场景 1**：想让 u→z 的流量走 `uvwz` 而不是 `uxyz`？→ 只能调整链路权重碰运气，或者写新路由算法
- **场景 2**：想让 u→z 的流量**分流**（一部分走 uvwz，一部分走 uxyz）做负载均衡？→ **做不到**（目的地址相同的包只能走同一条路）
- **场景 3**：想根据流量类型（蓝/红）让 w→z 走不同路径？→ **做不到**（基于目的的转发 + LS/DV 路由不支持）

链路权重是**唯一的控制旋钮**——操控空间太小了。

**问题二：误配置风险**。每台路由器独立配置，一个错误就能搞垮局部网络。

**问题三：创新缓慢**。私有实现 + 封闭系统 = 新协议难以部署（"let 1000 flowers bloom"）。

### 2.2 SDN 的核心思想：控制平面独立出来

SDN 做了一件事：把控制平面从每台路由器中**抽离**，交给**逻辑上集中的控制器**。

```
传统模式（Per-router control plane）：
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 路由算法      │   │ 路由算法      │   │ 路由算法      │
│ (控制平面)    │   │ (控制平面)    │   │ (控制平面)    │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ 转发表        │   │ 转发表        │   │ 转发表        │
│ (数据平面)    │   │ (数据平面)    │   │ (数据平面)    │
└──────────────┘   └──────────────┘   └──────────────┘
      路由器              路由器              路由器
    各自为政            各自为政            各自为政

SDN 模式（Logically centralized control plane）：
┌─────────────────────────────────────────────────┐
│             Remote Controller                    │
│          (控制平面集中在这里)                      │
│    ┌──────┐  ┌──────────┐  ┌───────────┐        │
│    │路由   │  │访问控制   │  │负载均衡    │        │
│    └──────┘  └──────────┘  └───────────┘        │
└──────┬──────────────┬──────────────┬─────────────┘
       │ 安装转发表    │              │
  ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
  │ 交换机1  │    │ 交换机2  │    │ 交换机3  │
  │ (纯数据) │    │ (纯数据) │    │ (纯数据) │
  └─────────┘    └─────────┘    └─────────┘
```

**SDN 的四个特征**：
1. **基于流的广义转发**（如 OpenFlow API）——不只是按目的地转发，可以按任意头部字段组合匹配
2. **数据平面与控制平面分离**
3. **控制平面功能外置于数据平面交换机**
4. **可编程的控制应用**——路由、访问控制、负载均衡都可以写成程序

**类比——大型机到 PC 的革命**：传统路由器 = 垂直整合的大型机（硬件+OS+应用一体，封闭）；SDN = PC 革命（硬件标准化 + 开放 OS + 第三方应用），带来快速创新。

### 2.3 SDN 三层架构

```
┌───────────────────────────────────────┐
│  Network Control Apps                 │  ← "大脑"
│  (routing, load balancing, firewall) │    实现控制逻辑，可第三方提供
├───────────────────────────────────────┤
│  Northbound API（北向接口）             │    RESTful API / Intent API
├───────────────────────────────────────┤
│  SDN Controller / Network OS          │  ← "操作系统"
│  · 维护全网状态（链路、交换机、主机）    │    分布式系统：
│  · 为上层提供网络抽象                  │    高性能、可扩展、
│  · 与下层交换机通过 OpenFlow 通信      │    容错、健壮
├───────────────────────────────────────┤
│  Southbound API（南向接口）             │    OpenFlow / SNMP
├───────────────────────────────────────┤
│  Data-plane Switches                  │  ← "硬件"
│  (fast, simple, commodity switches)   │    实现广义转发，流表由控制器下发
└───────────────────────────────────────┘
```

**SDN 控制器内部三大组件**（以 OpenDaylight/ONOS 为例）：

| 组件 | 英文 | 功能 |
|------|------|------|
| **通信层** | Communication to/from controlled devices | 通过 OpenFlow、SNMP 与交换机交互 |
| **网络状态管理层** | Network-wide state management | 分布式数据库，维护链路状态、主机信息、交换机信息、流表、统计数据 |
| **接口层** | Interface to network control apps | 为上层应用提供网络图抽象、RESTful API、Intent API |

### 2.4 OpenFlow 协议

OpenFlow 是控制器与交换机之间的通信协议，运行在 TCP 之上（可选加密）。

**注意区分**：OpenFlow **API** 定义了广义转发的编程接口（能匹配哪些字段、执行哪些动作）；OpenFlow **协议** 负责传输这些指令和消息。

**三类消息**：

| 方向 | 消息 | 作用 |
|------|------|------|
| **控制器→交换机** | `features` | 查询交换机能力 |
| | `configure` | 查询/设置交换机配置参数 |
| | `modify-state` | 增/删/改流表中的流表项 |
| | `packet-out` | 让交换机从指定端口发出数据包 |
| **交换机→控制器**（异步） | `packet-in` | 将收到的包转交控制器处理 |
| | `flow-removed` | 流表项被删除时通知控制器 |
| | `port-status` | 端口状态变化时通知控制器 |
| **双向（对称）** | Hello, Echo 等 | 连接建立与保活 |

> 网络管理员通常**不直接发 OpenFlow 消息**——而是通过控制器提供的高层抽象（如 REST API、Intent API）来编程。

### 2.5 SDN 控制/数据平面交互示例：链路故障

课件给出一个完整的工作流（当交换机 S1 发现链路故障时）：

1. S1 通过 OpenFlow `port-status` 消息通知控制器
2. SDN 控制器接收消息，更新链路状态数据库
3. Dijkstra 路由应用之前已注册"链路状态变化时通知我"——它被唤醒
4. 路由应用从控制器获取网络图和链路状态，**重新计算路由**
5. 路由应用与控制器中的"流表计算"组件协作，算出需要更新的流表项
6. 控制器通过 OpenFlow `modify-state` 向受影响交换机**安装新流表**

→ 整个过程自动完成，不需要人工登入每台交换机改配置。

### 2.6 SDN 的现实部署与挑战

**Google ORION**（NSDI'21）：在 Google 数据中心（Jupiter）和广域网（B4）上大规模运行 SDN 控制平面。核心应用包括域内路由、iBGP、流量工程、CoFlow 调度以满足 SLA。

**主流开源控制器**：
- **OpenDaylight (ODL)**：服务抽象层（SAL）连接内部/外部应用和服务
- **ONOS**：强调分布式核心（服务可靠性、复制、性能扩展），支持 Intent 框架（"我要什么"而非"怎么做"）

**当前挑战**：控制平面加固（可靠性、安全）、满足特定任务需求（实时、超可靠）、互联网级扩展（跨多 AS）、5G 中的 SDN。

---

## 第三部分：ICMP — 网络层的诊断工具箱

### 3.1 什么是 ICMP？

ICMP（Internet Control Message Protocol）由主机和路由器用于交换**网络层**的控制信息。它封装在 IP 数据报中传输（技术上在 IP "之上"）。

**两大功能**：
1. **错误报告**：目的网络/主机/端口/协议不可达、TTL 过期、IP 头部错误
2. **诊断**：Echo Request/Reply（即 ping）

### 3.2 常用 ICMP 消息类型

| Type | Code | 含义 | 谁在用 |
|------|------|------|--------|
| 0 | 0 | Echo Reply | ping 回复 |
| 3 | 0 | 目的网络不可达 | 路由器报告 |
| 3 | 1 | 目的主机不可达 | 路由器报告 |
| 3 | 2 | 目的协议不可达 | 主机报告 |
| 3 | 3 | 目的端口不可达 | 主机报告（traceroute 终止信号） |
| 8 | 0 | Echo Request | ping 请求 |
| 11 | 0 | TTL Expired | 路由器报告（traceroute 中间跳信号） |

### 3.3 traceroute 原理

traceroute 利用 TTL 机制逐跳探测路径：

1. 源端发送一系列 UDP 段到目标，**第 n 组 TTL=n**
2. 第 n 组的数据报到第 n 跳路由器时 TTL 减为 0 → 路由器丢弃 → 返回 ICMP **"TTL Expired" (type 11, code 0)**
3. 当数据报最终到达目标主机 → 目标端口无应用监听 → 返回 ICMP **"Port Unreachable" (type 3, code 3)** → 源端知道到达了，停止发送
4. 源端记录每跳 IP 和 RTT（往返时间）

---

## 第四部分：网络管理与配置

### 4.1 为什么需要网络管理？

一个自治系统包含**上千个交互的硬件/软件组件**——路由器、交换机、防火墙、负载均衡器。没人能手动一台台管。

> "网络管理包括硬件、软件和人员要素的部署、集成和协调，以监控、测试、轮询、配置、分析、评估和控制网络及网元资源，从而以合理的成本满足实时性、运营性能和服务质量要求。"

### 4.2 网络管理架构

```
┌──────────────────┐
│ Managing Server  │  ← 管理服务器（有网络管理员在回路中）
│ (with humans)    │
└────┬──┬──┬──┬───┘
     │  │  │  │  网络管理协议（SNMP / NETCONF / CLI）
  ┌──┴──┴──┴──┴──┐
  │  M  M  M  M  │  ← 被管设备（Managed devices）
  │  各自包含 agent + data（配置、运行状态、统计数据）
  └──────────────┘
```

### 4.3 三种管理方式

| 方式 | 手段 | 特点 |
|------|------|------|
| **CLI** | 管理员直接 SSH 到每台设备敲命令、跑脚本 | 原始，一台台操作 |
| **SNMP/MIB** | 通过 SNMP 协议查询/设置设备的 MIB 数据 | 侧重**监控**，广泛部署 |
| **NETCONF/YANG** | 更抽象、网络级、整体性。YANG 定义数据模型，NETCONF 传输 | 侧重**多设备配置管理**，支持原子提交和回滚 |

### 4.4 SNMP 协议

**两种通信模式**：

- **请求/响应模式**：管理服务器主动查询设备 MIB 数据
- **Trap 模式**：设备主动向管理服务器报告异常事件

**五种消息类型**：

| 消息 | 方向 | 功能 |
|------|------|------|
| `GetRequest` | Manager→Agent | 读取单个 MIB 值 |
| `GetNextRequest` | Manager→Agent | 遍历 MIB 树的下一个值 |
| `GetBulkRequest` | Manager→Agent | 批量读取 MIB 数据块 |
| `SetRequest` | Manager→Agent | 设置 MIB 值 |
| `Response` | Agent→Manager | 对请求的响应 |
| `Trap` | Agent→Manager | 主动通知异常事件 |

**MIB（Management Information Base）**：被管设备的运行数据和部分配置数据，用 SMI 语言定义。RFC 定义了 400+ 标准 MIB 模块，还有大量厂商私有 MIB。每个变量有唯一的 OID（如 `1.3.6.1.2.1.7.1` = UDP 接收数据报总数）。

### 4.5 NETCONF/YANG

SNMP 管监控很好，但**配置管理**（尤其是多设备协同配置）是它的弱项。NETCONF 填补这块。

**NETCONF 核心能力**：
- 检索、设置、修改、**激活**配置
- **多设备原子提交**（要么全成功，要么全回滚）
- 查询运行数据和统计
- 订阅设备通知

**通信模式**：RPC（远程过程调用），消息用 XML 编码，跑在安全可靠传输（如 TLS）上。

**操作示例**：

| NETCONF 操作 | 功能 |
|-------------|------|
| `<get-config>` | 读取配置（设备可能有多份配置） |
| `<get>` | 读取配置 + 运行状态 |
| `<edit-config>` | 修改配置，支持回滚（`<ok>` 或 `<rpcerror>`） |
| `<lock>` / `<unlock>` | 锁定/解锁配置存储（排他） |
| `<create-subscription>` | 订阅事件通知 |

**YANG**：NETCONF 的数据建模语言，定义网络管理数据的结构、语法、语义。可以表达约束条件，确保 NETCONF 配置满足正确性和一致性。YANG 描述可以自动生成对应的 XML 文档。

| | SNMP | NETCONF/YANG |
|------|------|------|
| **定位** | 监控为主 | 配置管理为主 |
| **通信** | 请求/响应 + Trap，走 UDP | RPC，XML 编码，走 TLS |
| **数据模型** | MIB + SMI | YANG |
| **多设备操作** | 逐个设备 | 原子提交 + 回滚 |
| **亮点** | 简单、广泛部署 | 多设备一致性配置 |

---

## 与前章关联

本章是**网络层控制平面的下半场**：

- **接 08（OSPF/路由协议）**：08 讲 AS 内部（intra-domain）路由，本章讲 AS 之间（inter-domain）路由——BGP。两者协作填转发表：BGP 的 NEXT-HOP 依赖 OSPF 找到具体出口
- **接 07（IP 寻址与 SDN）**：07 讲了广义转发和 OpenFlow API（数据平面"能做什么"），本章讲 SDN 控制平面（"怎么决策"）和 OpenFlow 协议（传输实现）
- **接 06（路由器与 IP）**：ICMP 封装在 IP 数据报中，BGP 路径通告以 IP 前缀为单位

**网络层全景**至此完结：数据平面（转发、IP、路由器硬件）→ 控制平面（路由算法、OSPF、BGP、SDN）→ 诊断（ICMP）→ 管理（SNMP/NETCONF）。下一站：链路层。

---

## 术语对照

| English | 中文 | 说明 |
|---------|------|------|
| BGP (Border Gateway Protocol) | 边界网关协议 | AS 间路由协议，因特网的"胶水" |
| eBGP (External BGP) | 外部 BGP | 不同 AS 网关路由器之间交换路由信息 |
| iBGP (Internal BGP) | 内部 BGP | AS 内部传播从 eBGP 学到的外部路由 |
| AS-PATH | AS 路径属性 | 路由经过的 AS 序列，防环 + 选路 |
| NEXT-HOP | 下一跳属性 | 指向下一跳 AS 的具体路由器 IP |
| Hot Potato Routing | 热土豆路由 | 选 AS 内部代价最小的出口网关 |
| Local Preference | 本地偏好值 | 策略决定的最高优先级选路属性 |
| Policy-based Routing | 策略路由 | 基于商业关系而非性能的选路 |
| SDN (Software-Defined Networking) | 软件定义网络 | 控制平面集中化、可编程的网络架构 |
| OpenFlow | OpenFlow 协议 | SDN 控制器与交换机之间的南向接口协议 |
| Northbound API | 北向接口 | 控制器与网络应用之间的接口 |
| Southbound API | 南向接口 | 控制器与数据平面设备之间的接口 |
| ICMP (Internet Control Message Protocol) | 因特网控制报文协议 | 错误报告与诊断协议 |
| SNMP (Simple Network Management Protocol) | 简单网络管理协议 | 基于 MIB 的设备监控协议 |
| NETCONF | 网络配置协议 | 基于 XML-RPC 的设备配置管理协议 |
| YANG | YANG 数据建模语言 | NETCONF 的数据模型定义语言 |
| MIB (Management Information Base) | 管理信息库 | 设备可管理状态和配置数据的集合 |

---

## 关键原句

> "BGP (Border Gateway Protocol): the de facto inter-domain routing protocol — 'glue that holds the Internet together'"
> BGP 是事实上的域间路由协议——"将因特网粘合在一起的胶水"。

> "ISP only wants to route traffic to/from its customer networks (does not want to carry transit traffic between other ISPs – a typical 'real world' policy)."
> ISP 只想路由去往/来自其客户网络的流量（不希望在其他 ISP 之间承运中转流量——典型的"现实世界"策略）。

> "Hot potato routing: choose local gateway that has least intra-domain cost — don't worry about inter-domain cost!"
> 热土豆路由：选 AS 内部代价最小的本地网关——不关心 AS 间代价！

> "Why a logically centralized control plane? Easier network management: avoid router misconfigurations, greater flexibility of traffic flows."
> 为什么要逻辑集中的控制平面？更简单的网络管理：避免路由器误配置、更大的流量调度灵活性。

> "Generalized forwarding and SDN can be used to achieve any routing desired."
> 广义转发和 SDN 可用于实现任何所需的路由。

> "ICMP: used by hosts and routers to communicate network-level information. Error reporting: unreachable host, network, port, protocol. Echo request/reply (used by ping)."
> ICMP 由主机和路由器用于通信网络层信息。错误报告：不可达的主机、网络、端口、协议。Echo 请求/回复（用于 ping）。

> "Network management includes the deployment, integration and coordination of the hardware, software, and human elements to monitor, test, poll, configure, analyze, evaluate, and control the network and element resources to meet the real-time, operational performance, and Quality of Service requirements at a reasonable cost."
> 网络管理包括硬件、软件和人员要素的部署、集成和协调，以监控、测试、轮询、配置、分析、评估和控制网络及网元资源，从而以合理的成本满足实时性、运营性能和服务质量的要求。

---

## 难点突破

### 难点1：BGP 策略路由为什么不让包走"最短"路径？

**本质**：互联网不是一家公司，而是成千上万个 AS 通过**商业关系**（客户-提供商、对等互联）连接而成。BGP 必须把这些商业协议编码进路由决策。

类比快递公司：顺丰不会免费帮圆通转运包裹——除非圆通付了钱。BGP 也是一样——每个 AS 根据自己的经济利益决定：(1) 接受哪些路径、(2) 选哪条路径、(3) 向谁通告路径。

> IP 包走的路 = 商业上允许的路径中最好的那条，不一定是延迟最低的那条。

### 难点2：SDN 集中控制器是单点故障吗？

不是。SDN 控制器是**逻辑上集中、物理上分布**的分布式系统。Google ORION、ONOS 等实际部署的 SDN 控制器都内置了状态复制、故障转移和一致性机制，保证了性能、可扩展性和容错性。

类比：Google 搜索看起来是一个网站，背后是几十万台服务器。SDN 控制器同理——"集中"是逻辑抽象，分布式是物理实现。

---

## 记忆卡片

**Q1: eBGP 和 iBGP 的区别？**
A1: eBGP 在不同 AS 的网关路由器之间交换路由可达性信息；iBGP 在同一 AS 内部将 eBGP 学到的外部路由传播给所有路由器。网关路由器同时运行两者。

**Q2: BGP 路由选择的优先级顺序？**
A2: (1) Local Preference（本地偏好值，策略决定）→ (2) Shortest AS-PATH（最短 AS 路径）→ (3) Closest NEXT-HOP（热土豆路由）→ (4) 其他。策略 > 路径长度 > 内部代价。

**Q3: 什么是热土豆路由？**
A3: 路由器学到多条到同一外部目的地的路径时，选 AS 内部代价最小的出口网关，不关心 AS 外路径长短。像扔烫手土豆，尽快脱手。

**Q4: SDN 三层架构及各层职责？**
A4: 上层（Network Control Apps）→"大脑"，实现路由/负载均衡/防火墙；中层（SDN Controller/Network OS）→"操作系统"，维护全网状态和拓扑；下层（Data-plane Switches）→"硬件"，实现广义转发。上下层之间分别是北向 API 和南向 API（OpenFlow）。

**Q5: SNMP 和 NETCONF/YANG 的核心区别？**
A5: SNMP 侧重**监控**——通过 MIB 读设备状态、收 Trap 告警，简单但配置能力弱；NETCONF/YANG 侧重**配置管理**——基于 XML-RPC，支持多设备原子提交和回滚，YANG 是其数据建模语言。

---

## 考点标注

- ⭐⭐⭐ **BGP 基本概念与四种能力**：eBGP/iBGP 的区别、BGP 四种消息类型（OPEN/UPDATE/KEEPALIVE/NOTIFICATION）、路径向量协议的本质
- ⭐⭐⭐ **AS-PATH 与 NEXT-HOP 两个关键属性**：AS-PATH 防环路机制 + 选路作用，NEXT-HOP 与 OSPF 协作填转发表的过程
- ⭐⭐⭐ **BGP 路由选择四层优先级**：Local Preference > AS-PATH 长度 > Hot Potato > 其他；必须能解释每层含义和顺序原因
- ⭐⭐⭐ **策略路由（Policy-based Routing）**：ISP 商业关系如何决定路径选择——只路由客户流量、不承担中转流量；能分析课件原图场景（B 不向 C 通告 BAw 的原因）
- ⭐⭐ **热土豆路由**：选 AS 内部代价最小出口，不关心外部路径长度
- ⭐⭐⭐ **SDN 三层架构**：Network Control Apps → Northbound API → SDN Controller → Southbound API (OpenFlow) → Switches；每层职责和交互方式
- ⭐⭐ **OpenFlow 协议三类消息**：Controller→Switch（features/configure/modify-state/packet-out）、Switch→Controller（packet-in/flow-removed/port-status）、双向（Hello/Echo）
- ⭐⭐ **传统 vs SDN 控制平面**：Per-router control vs logically centralized control；SDN 四特征；为什么集中编程比分布式协议更容易
- ⭐⭐ **ICMP 两大功能与关键消息类型**：错误报告 + 诊断；ping (type 8/0)、traceroute 中间跳 (type 11 code 0)、traceroute 终止 (type 3 code 3)
- ⭐⭐ **traceroute 完整机制**：TTL 递增原理、每跳 ICMP TTL Expired、目标 ICMP Port Unreachable 作终止信号、为什么用 UDP 而不是 ICMP Echo
- ⭐ **SNMP vs NETCONF/YANG**：监控 vs 配置管理；请求/响应 + Trap vs RPC + 原子提交；MIB + SMI vs YANG
- ⭐ **SDN 控制器是分布式系统**：逻辑集中 ≠ 物理单点；性能/可扩展/容错/健壮四个目标

---

## 期末可能题型

### 一、简答题

**简答1：eBGP 和 iBGP 的区别是什么？网关路由器的特殊角色是什么？**
答：eBGP 在不同 AS 的网关路由器之间交换路由可达性信息；iBGP 在同一 AS 内部将 eBGP 学到的外部路由传播给所有路由器。网关路由器同时运行 eBGP 和 iBGP——通过 eBGP 从邻居 AS 学习路径，再通过 iBGP 在内部扩散。

**简答2：BGP 的 AS-PATH 属性有哪两个作用？**
答：(1) **防环路**——路由器收到包含自己 AS 号的路径通告就丢弃；(2) **选路依据**——优先选择 AS-PATH 较短的路径。

**简答3：解释 BGP 路由选择的四层优先级，为什么 Local Preference 排第一？**
答：Local Preference（策略）> AS-PATH 长度 > NEXT-HOP 最近（热土豆）> 其他。Local Preference 排第一因为互联网由不同商业实体组成，ISP 只愿意路由有经济利益的流量——生意逻辑优先于技术性能。

**简答4：什么是策略路由？为什么 ISP 不愿意承运中转流量？**
答：ISP 只路由去往/来自其客户网络的流量，不愿意为其他 ISP 之间的流量提供中转——因为不赚钱。这导致 IP 包走的路不一定是技术上最短的，而是商业上允许的路径中最好的。

**简答5：SDN 三层架构及各层职责？**
答：上层（Network Control Apps）——"大脑"，实现路由/负载均衡/防火墙等控制逻辑；中层（SDN Controller/Network OS）——"操作系统"，维护全网状态信息，对上提供北向 API，对下通过南向 API 管交换机，实现为分布式系统；下层（Data-plane Switches）——"硬件"，快速简单商用交换机，按控制器下发的流表转发。

**简答6：OpenFlow 协议三类消息及代表消息？**
答：Controller→Switch：features/configure/modify-state/packet-out；Switch→Controller（异步）：packet-in/flow-removed/port-status；双向（对称）：Hello/Echo。网络管理员通常不直接发 OpenFlow 消息，而是通过控制器高层抽象编程。

**简答7：traceroute 如何知道到达了目标主机？**
答：traceroute 向目标主机的无效端口发 UDP 段。当数据报最终到达目标，目标发现端口无人监听，返回 ICMP "Port Unreachable" (type 3, code 3)。源端收到 type 3 code 3 → 确认到达 → 停止发送。中间路由器丢弃包时返回的是 type 11（TTL Expired），二者完全可区分。

**简答8：SNMP 和 NETCONF 的核心区别？**
答：SNMP 侧重**监控**（读 MIB、收 Trap），请求/响应模式，走 UDP，以读取为主；NETCONF 侧重**多设备配置管理**，RPC 模式 + XML 编码 + TLS，支持原子提交和回滚，YANG 负责数据建模。

**简答9：SDN 控制器为什么不会成为单点故障？**
答：SDN 控制器是**逻辑集中、物理分布**的分布式系统，内置状态复制、故障转移和一致性机制。类比 Google 搜索——看起来是一个网站，物理上是几十万台服务器。实际部署（如 Google ORION、ONOS）验证了大规模分布式控制器的可行性。

### 二、分析/推理题

**推理1：BGP 路径通告全过程**
给定拓扑：AS1 含路由器 1a/1b/1c/1d，AS2 含 2a/2b/2c/2d，AS3 含 3a/3b/3c/3d，目的地 X 在 AS3 内。写出 AS3 向 AS2 及 AS2 向 AS1 通告路径 X 的完整过程，说明 eBGP 和 iBGP 分别在哪些步骤起作用。

答：
(1) AS3 网关 3a 通过 **eBGP** 向 AS2 网关 2c 通告路径 `AS3, X`
(2) AS2 的 2c 根据进口策略决定接受，通过 **iBGP** 向 AS2 内所有路由器（2a/2b/2d）扩散路径 `AS2, AS3, X`
(3) AS2 根据出口策略，由网关 2a 通过 **eBGP** 向 AS1 网关 1c 通告路径 `AS2, AS3, X`
(4) AS1 的 1c 通过 **iBGP** 向 AS1 内所有路由器扩散
(5) AS1 内路由器（如 1d）将"到 X 走 1c"写入转发表，通过 OSPF 找到去 1c 的具体接口

**推理2：策略路由场景分析**
拓扑：A、B、C 是三个提供商网络。w 是 A 的客户，x 是 A 的客户（同时接入 B 和 C，即 dual-homed），y 是 C 的客户。
(1) A 向 B 和 C 通告了路径 Aw。B 为什么不向 C 通告 BAw？
(2) x 是 dual-homed（同时接入 B 和 C）。为什么 x 不向 B 通告到 C 的路由？

答：
(1) B 不向 C 通告 BAw 因为 C、A、w 都不是 B 的客户——B 如果承运 C→A→w 的流量，赚不到钱。ISP 只路由去往/来自客户的流量，不承担中转流量。
(2) x 的策略是不想成为 B 和 C 之间的中转节点——如果 x 向 B 通告了到 C 的路由，B 的流量就可能经 x 到 C，x 要为此承担带宽成本而不获利。

**推理3：Hot Potato 路由计算**
AS2 内路由器 2d 通过 iBGP 学到两条到 X 的路径：经网关 2a（OSPF 内部代价=201）和经网关 2c（OSPF 内部代价=263）。经 2a 的 AS-PATH 长度为 3（AS2,AS1,AS3），经 2c 的 AS-PATH 长度为 2（AS2,AS3）。BGP 选择哪条路径？为什么？

答：BGP 选路优先级：Local Preference > AS-PATH 长度 > Hot Potato > 其他。
- 首先比较 AS-PATH：经 2c 路径更短（2 < 3），优于经 2a。**选经 2c。**
- Hot Potato 是第三优先级，只在 AS-PATH 长度相同时才起作用。本题中 AS-PATH 不同，Hot Potato 不会被触发。

**推理4：多路径 BGP 通告场景**
AS1 的网关路由器 1c 同时从 2a 学到 `AS2,AS3,X` 和从 3a 学到 `AS3,X`。两条路径的 Local Preference 相同，AS-PATH 长度不同。AS1 会选择哪条？iBGP 会通告哪条？

答：选择 `AS3,X`（AS-PATH 长度 1 < 2）。iBGP 只通告选中的那条（`AS3,X`）在 AS1 内扩散——AS1 内所有路由器只知道走 1c 到 X，不知道还有备选路径。

### 三、综合设计题

**设计题：SDN 链路故障处理流程**
SDN 网络中交换机 S1 发现一条链路故障。描述从故障发生到流表更新的完整过程，标明每一步涉及 SDN 架构中的哪一层、使用了什么协议/API。

答：
(1) S1（数据平面）通过 OpenFlow `port-status` 消息通知 SDN 控制器（南向接口）
(2) 控制器（通信层）接收 OpenFlow 消息，更新链路状态数据库（网络状态管理层）
(3) 控制器通过北向 API 通知已注册的路由应用——"链路状态变化了"
(4) 路由应用（控制应用层）从控制器获取最新网络图和链路状态，用 Dijkstra 重新计算路由
(5) 路由应用与控制器中的流表计算组件协作，算出需要更新的流表项
(6) 控制器通过 OpenFlow `modify-state` 消息向受影响交换机安装新流表（南向接口）
→ 全自动，无需人工逐台修改配置。
A6: 源端发送 TTL 递增的 UDP 段序列。第 N 跳路由器因 TTL=0 返回 ICMP "TTL Expired" (type 11, code 0)；到达目标后，目标返回 ICMP "Port Unreachable" (type 3, code 3) 作为终止信号。源端记录每跳 IP 和 RTT。
