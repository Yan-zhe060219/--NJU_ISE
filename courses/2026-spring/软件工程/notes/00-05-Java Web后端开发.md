---
title: "Java Web 后端开发"
course: "软件工程与计算 II"
tags: [Java, Spring Boot, MyBatis, Spring Security, JWT, REST API, 后端开发]
created: 2026-05-22
source: "00-05-Java Web后端开发.pdf"
source_lang: "zh"
status: draft
related: ["00-04-前端开发基础"]
chapter: "0-5"
---

## 一句话总结

Spring Boot（快速构建 API）+ MyBatis（安全操作数据库）+ Spring Security（认证授权）= 现代 Java Web 三层技术栈，对应三道防线：接口层 → 数据层 → 安全层。

## 阅读说明

> 本文标注体系：
> - 📝 **考点** — 期末笔试可能考察的概念、原理、对比辨析。复习时优先掌握。
> - 🔧 **实践** — 工程能力，笔试不直接考但项目/作业必备。学有余力时关注。

## 知识地图

```mermaid
flowchart TD
    JavaWeb[Java Web 后端开发] --> HTTP[HTTP 基础]
    JavaWeb --> Boot[Spring Boot]
    JavaWeb --> MyBatis[MyBatis]
    JavaWeb --> Security[Spring Security]

    HTTP --> H1[协议栈：应用层/传输层/网络层/接口层]
    HTTP --> H2[请求格式：方法+URL+Headers+Body]
    HTTP --> H3[响应格式：状态码+Headers+Body]
    HTTP --> H4[REST：以资源为中心，URL即文档]
    HTTP --> H5[JSON：轻量级数据交换格式]

    Boot --> B1[约定优于配置，自动配置]
    Boot --> B2[@RestController + 常用注解]
    Boot --> B3[内嵌 Tomcat，java -jar 即运行]

    MyBatis --> M1[#{param} 预编译防注入 vs ${} 危险]
    MyBatis --> M2[MVC 分层：Controller→Service→Mapper]
    MyBatis --> M3[注解写法 vs XML 写法]

    Security --> S1[认证 AuthN vs 授权 AuthZ]
    Security --> S2[过滤器链：安全与业务解耦]
    Security --> S3[JWT：Header.Payload.Signature]
    Security --> S4[BCrypt 密码存储黄金法则]
```

## 核心概念

### 1. HTTP 协议基础

HTTP 属于应用层协议，构建在 TCP 连接之上，采用客户端-服务器模型。**HTTP 是无状态的**——每次请求建立新连接，响应后关闭，服务器不保留连接信息（Keep-Alive 模式可复用连接）。

**HTTP 请求格式：** 请求行（方法 + URL + HTTP 版本）+ Headers + Body（GET 无 Body）。

常用方法：`GET`（获取）、`POST`（新增/修改）、`PUT`（替换更新）、`DELETE`（删除）。

**HTTP 响应状态码：** `2xx` 成功，`3xx` 重定向，`4xx` 客户端错误，`5xx` 服务器错误。

> 📝 **考点**：HTTP 无状态的含义；GET/POST/PUT/DELETE 的语义区分；状态码分类（2xx/3xx/4xx/5xx）——选择题、填空题高频。REST 部分会结合考。

### 2. URL 结构

```
http://blog.example.com:8080/users?gender=male&page=1
↑协议  ↑主机名（域名）      ↑端口 ↑路径 ↑查询参数（键值对）
```

HTTP 默认端口 80，HTTPS 默认 443，Spring Boot 开发常用 8080。

### 3. REST API 设计规范

REST 以资源为中心设计 URL，用 HTTP 方法表达操作：

| 操作 | HTTP 方法 | URL 示例 |
|------|----------|---------|
| 获取全部 | `GET` | `/api/products` |
| 获取单个 | `GET` | `/api/products/123` |
| 新建 | `POST` | `/api/products` |
| 更新 | `PUT` | `/api/products/123` |
| 删除 | `DELETE` | `/api/products/123` |

REST 不是强制标准，但遵守规范让 API 一目了然——**URL 即文档**。

> 📝 **考点**：REST 的核心原则——以资源为中心设计 URL，用 HTTP 方法表达操作（而非在 URL 中用动词）。简答题常考"RESTful API 的设计原则"，可直接引用上表。对比反例：`/getProducts`、`/createProduct` 不是 RESTful。

### 4. Spring Boot：约定优于配置

**核心价值：** 消灭传统 Spring 数百行 XML 配置。

| 特性 | 说明 |
|------|------|
| 约定优于配置 | 默认值覆盖 90% 场景，只需配置例外 |
| 自动配置 | 检测 classpath，自动装配 DataSource、MVC 等 |
| Starter 依赖 | 一行引入 Web 全套依赖（`spring-boot-starter-web`） |
| 内嵌服务器 | Fat JAR 自带 Tomcat，`java -jar` 直接运行 |

类比：传统 Spring 像散装零件自己组装，Spring Boot 像开箱即用的 MacBook。

> 📝 **考点**："约定优于配置"（Convention over Configuration）是 Spring Boot 的核心理念——名词解释高频。三个关键词：自动配置、Starter 依赖、内嵌服务器。🔧 具体 Starter 名称和配置细节属工程实践，笔试不要求。

### 5. Spring Boot 常用注解

| 注解 | 作用 |
|------|------|
| `@SpringBootApplication` | 启动入口，开启自动配置 |
| `@RestController` | 控制器，返回值自动序列化为 JSON（= `@Controller` + `@ResponseBody`） |
| `@GetMapping("/path")` | 处理 HTTP GET 请求 |
| `@PostMapping("/path")` | 处理 HTTP POST 请求 |
| `@RequestBody` | 从请求体读取 JSON 并反序列化为对象 |
| `@PathVariable` | 从 URL 路径提取变量（`/{id}` → 参数） |
| `@RequestParam` | 从 URL 查询字符串读取值（`?page=1` → 参数） |

> 📝 **考点**：注解与功能匹配——选择题/连线题常见。重点记 `@RestController`（= `@Controller` + `@ResponseBody`）、`@PathVariable` vs `@RequestParam` 的区别（一个从路径取，一个从查询串取）。🔧 具体编码细节属实践。

### 6. MyBatis：参数化 SQL 映射

**为什么需要 MyBatis？** 原始 JDBC 需要手动管理连接、手动映射字段、容易忘记关闭导致连接泄漏。MyBatis 自动处理连接管理、参数预编译绑定、结果集映射、异常转换。

**安全关键：`#{id}` vs `${id}`**
- `#{id}` — 预编译参数（PreparedStatement），防 SQL 注入，**始终使用**
- `${id}` — 字符串拼接，**危险！永远别用于用户输入**

> 📝 **必考**：`#{id}` 与 `${id}` 的安全区别。核心是预编译（PreparedStatement）vs 字符串拼接。能解释为什么 `#{}`  防注入——参数与 SQL 结构分离，用户输入永远不会被当作 SQL 关键字执行。这是整篇笔记最重要的考点之一。

**MVC 分层结构：**
```
HTTP 请求 → Controller (@RestController) → Service (@Service, 业务逻辑 + @Transactional)
→ Mapper (@Mapper, SQL 操作) → MySQL
```

> 📝 **考点**：MVC 三层各自的职责——Controller（接收请求、参数校验）、Service（业务逻辑、事务）、Mapper（数据访问、SQL）。简答题可能问"为什么要分层"——答案：关注点分离、可测试性、可维护性。🔧 具体 `@Transactional` 使用场景属实践。

### 7. Spring Security：认证与授权

| 概念 | 英文 | 回答的问题 |
|------|------|-----------|
| 认证 | Authentication (AuthN) | 你是谁？ |
| 授权 | Authorization (AuthZ) | 你能做什么？ |

**核心机制：过滤器链（Filter Chain）**——安全横切关注点，不侵入业务代码，全部在过滤器链中处理。HTTP 请求依次通过各过滤器，只有全部通过才能到达 Controller。

> 📝 **考点**：认证（AuthN）vs 授权（AuthZ）的概念辨析——名词解释/选择题高频。过滤器链的设计思想是"横切关注点"——为什么不在每个 Controller 里检查权限？能回答这个才算真正理解。

### 8. JWT 认证流程

**JWT 结构：** `Header.Payload.Signature`（三段 Base64 用 `.` 分隔）
- Header：签名算法（如 HS256）
- Payload：用户信息（Base64 编码，**非加密！任何人可解码**）
- Signature：密钥 HMAC 签名，防篡改

**⚠ JWT Payload 只是 Base64 编码，任何人都能解码——绝不要把密码存入 Payload！**

> 📝 **必考**：JWT 三段结构（Header.Payload.Signature）及各段作用。关键是理解 Payload 是 Base64 编码而非加密——所以不能放敏感信息。Signature 的作用是防篡改而非保密。认证流程（登录→发 Token→后续请求带 Token）可能出简答题。🔧 JWT 具体集成代码属实践。

**认证流程：**
1. 客户端 POST 用户名 + 密码 → 服务端验证 → 返回 JWT Token
2. 后续请求携带 `Authorization: Bearer <token>` → 服务端验证签名 + 过期时间 → 执行业务逻辑

**密码存储黄金法则：永远使用 `BCryptPasswordEncoder`，绝不存储明文密码。**

### 9. 三层技术栈 = 三道防线

| 防线 | 技术 | 职责 |
|------|------|------|
| 第一道：守门员 | Spring Security 过滤器链 | JWT 验证、认证鉴权、拦截未授权请求 |
| 第二道：业务处理 | Spring Boot Controller + Service | RESTful API、业务逻辑、参数校验 |
| 第三道：数据守护 | MyBatis Mapper + MySQL | 参数化查询、防 SQL 注入、最小权限账号 |

回到 Equifax 案例：若当年使用 Spring Security（及时升级框架）+ MyBatis 参数化查询 + 最小权限数据库账号，1.47 亿条数据不会如此轻易被窃。

> 📝 **考点**：三道防线模型是综合论述题的天然素材——每道防线对应什么技术、解决什么安全问题。可以与 Equifax 数据泄露案例结合论述"如何构建安全的 Web 后端"。

## 难点突破

**难点 1：理解 Spring Security 过滤器链的设计思想**

初学者困惑："为什么不能在每个 Controller 方法里检查 Token？"

过滤器链的设计遵循**横切关注点（Cross-Cutting Concern）**原则——安全逻辑与业务逻辑分离。好处：
- Controller 只关心业务，不用每行写 `if (!authenticated) return 401;`
- 新增安全规则只需改配置类，不用改散落在各处的业务代码
- 不会有人"忘记"加认证检查——不经过过滤器链根本到不了 Controller

类比：过滤器链就像写字楼的安检闸机——前台验证身份、分配权限，进楼后各个办公室（Controller）只管自己的业务，不用人人守在门口查证件。

> 📝 **考点**：过滤器链 = 横切关注点（Cross-Cutting Concern）的实现。能用自己的话解释"为什么不在每个 Controller 方法里检查 Token"——三个理由：解耦、防遗漏、改规则只需改一处。简答/论述题高频。

**难点 2：MyBatis vs Hibernate/JPA 的选择**

MyBatis 完全手写 SQL，适合需要精细控制 SQL 的场景（国内大厂主流）；Hibernate 自动生成 SQL，学习曲线更陡，复杂查询容易出现 N+1 问题。这门课选 MyBatis 是因为它让你直接面对 SQL，不会隐藏数据库操作的本质。

> 📝 **考点**：MyBatis vs Hibernate/JPA 的定位区分——前者手写 SQL 精细控制，后者 ORM 自动生成。能解释 N+1 问题是什么、为什么 MyBatis 在国内大厂更主流（性能可控、DBA 友好）。属于理解层次，不太可能单独出大题，但可作为论述题素材。🔧 实际选型经验属实践。

## 与前章关联

- 前置依赖：00-04（前端 Vue 通过 axios 调用本讲构建的 REST API）
- 本讲构建的 Spring Boot + MyBatis + Spring Security 是 00-06（VibeCoding）的技术基础
- HTTP 协议知识贯穿整个前后端交互
- MVC 分层思想后续在体系结构模块（03-xx）中会进一步深化

## 考试速查

> 复习优先级从高到低排列。标 ⭐ 为极大概率考题。

| 优先级 | 考点 | 题型 | 所在节 |
|--------|------|------|--------|
| ⭐⭐⭐ | `#{id}` vs `${id}` 安全区别（预编译 vs 拼接） | 简答/填空 | MyBatis |
| ⭐⭐⭐ | JWT 三段结构 & Payload 非加密 | 简答/选择 | Spring Security |
| ⭐⭐⭐ | 认证 vs 授权概念辨析 | 名词解释/选择 | Spring Security |
| ⭐⭐ | RESTful API 设计原则 | 简答 | HTTP |
| ⭐⭐ | 过滤器链 = 横切关注点，为什么不用 Controller 内检查 | 简答/论述 | 难点突破 |
| ⭐⭐ | 三道防线模型 & 对应技术栈 | 论述 | 核心概念 §9 |
| ⭐ | Spring Boot "约定优于配置" | 名词解释 | Spring Boot |
| ⭐ | HTTP 方法语义 + 状态码分类 | 选择/填空 | HTTP |
| ⭐ | MVC 三层分层及职责 | 简答 | MyBatis |
| ⭐ | MyBatis vs Hibernate 定位区分 | 选择/简答 | 难点突破 |
| — | 注解功能匹配（`@RestController` 等） | 连线/选择 | Spring Boot |
| — | URL 组成结构 | 填空 | HTTP |

**论述题押题**：结合 Equifax 案例，阐述"三道防线"如何构建安全 Web 后端——这道题能同时覆盖 Spring Security、MyBatis `#{}` 防注入、密码 BCrypt 存储、最小权限原则，性价比极高。

## 记忆卡片

**Q: Spring Boot 的核心优势是什么？**
A: 自动配置 + Starter 依赖 + 内嵌 Tomcat，开箱即用。传统 Spring 要写数百行 XML，Spring Boot 只需一个 `@SpringBootApplication`。

**Q: MyBatis 中 `#{id}` 和 `${id}` 的区别？**
A: `#{id}` 是预编译参数（PreparedStatement），防 SQL 注入，始终使用。`${id}` 是字符串拼接，危险，永远别用于用户输入。

**Q: JWT 的三个组成部分是什么？为什么不能把密码放在 Payload？**
A: Header（算法）+ Payload（数据）+ Signature（签名）。Payload 只是 Base64 编码而非加密，任何人都能解码——绝不要把密码等敏感信息存入 Payload。

**Q: 认证（Authentication）和授权（Authorization）的区别？**
A: 认证回答"你是谁？"（用户名+密码登录）；授权回答"你能做什么？"（管理员才能删除用户）。

**Q: Spring Security 为什么用过滤器链而不是在每个 Controller 里检查权限？**
A: 过滤器链实现安全逻辑与业务逻辑解耦（横切关注点），Controller 只关注业务，不怕忘记加认证检查。类比写字楼安检闸机——前台验证后各办公室只管业务。

---

## 期末简答题备考

> 以下为笔试可能出现的简答题及标准答案要点。按出题概率排序。

**Q1: 简述 Spring Boot "约定优于配置"的含义，并列出三个核心特性。**

A: 含义：框架预设默认配置覆盖 90% 场景，开发者只需配置例外，无需手写大量 XML。三个核心特性：① 自动配置——检测 classpath 自动装配组件；② Starter 依赖——一行引入全套依赖（如 `spring-boot-starter-web`）；③ 内嵌服务器——Fat JAR 自带 Tomcat，`java -jar` 直接运行。

---

**Q2: MyBatis 中 `#{id}` 和 `${id}` 的区别是什么？为什么 `${id}` 是危险的？**

A: `#{id}` 使用预编译参数（PreparedStatement），参数与 SQL 结构分离，用户输入不会被当作 SQL 关键字执行，可防 SQL 注入。`${id}` 是字符串直接拼接进 SQL，攻击者输入 `1 OR 1=1` 会改变 SQL 语义，导致数据泄露。**始终使用 `#{}` ，永远不对用户输入使用 `${}` 。**

---

**Q3: 什么是 JWT？简述其三段结构及各部分作用。**

A: JWT（JSON Web Token）是一种无状态身份认证令牌。三段结构（用 `.` 分隔）：① Header——声明签名算法（如 HS256）；② Payload——存放用户信息（Base64 编码，非加密，任何人可解码）；③ Signature——用密钥对 Header+Payload 做 HMAC 签名，防篡改。

---

**Q4: 为什么 JWT 的 Payload 不能存放密码等敏感信息？**

A: Payload 只是 Base64 编码，不是加密。任何人拿到 Token 后可直接解码 Payload 读取内容。敏感信息（如密码）应存储在服务端数据库中，绝不出现在 JWT 中。Signature 的作用是防篡改而非保密。

---

**Q5: 解释认证（Authentication）和授权（Authorization）的区别。**

A: 认证（AuthN）回答"你是谁？"——验证用户身份（如用户名+密码登录）。授权（AuthZ）回答"你能做什么？"——控制用户权限（如管理员才能删除用户）。认证在前，授权在后；先确认身份，再分配权限。

---

**Q6: Spring Security 为什么采用过滤器链机制，而不是在每个 Controller 方法中检查权限？**

A: 过滤器链实现**横切关注点**（Cross-Cutting Concern）——将安全逻辑与业务逻辑解耦。好处：① Controller 只关注业务，代码简洁；② 修改安全规则只需改配置类，不需改动分散在各处的业务代码；③ 不会有人"忘记"加认证检查——不经过过滤器链根本到不了 Controller。

---

**Q7: 简述 Java Web 后端的"三道防线"模型及各防线对应的技术。**

A: ① 第一道——守门员：Spring Security 过滤器链，负责 JWT 验证、认证鉴权、拦截未授权请求。② 第二道——业务处理：Spring Boot Controller + Service，负责 RESTful API、业务逻辑、参数校验。③ 第三道——数据守护：MyBatis Mapper + MySQL，负责参数化查询、防 SQL 注入、最小权限账号。三道防线层层递进，任一环节失守都可能导致数据泄露（如 Equifax 案例）。

---

**Q8: 简述 MVC 三层架构各层的职责，以及为什么要分层。**

A: Controller 层——接收 HTTP 请求、参数校验、调用 Service；Service 层——业务逻辑、事务管理；Mapper 层——数据访问、执行 SQL。分层原因：关注点分离（每层只做一件事）、可测试性（可单独 mock 某一层测试）、可维护性（修改某层不影响其他层）。
