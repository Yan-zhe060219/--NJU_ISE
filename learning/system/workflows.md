# 日常工作流与工具契约

先读 [共享规范](standards.md)，需要写笔记再读 [模板](templates.md)。这些步骤供 agent 执行，用户用自然语言即可。

## 1. 建目标和放资料

入口是 `learning/INDEX.md`，也可从根README按分类和学期进入。身份事实源位于 `courses/<学期>/<课程名>/goal.json`、`papers/<论文或专题名>/goal.json` 或 `self-study/<项目名>/goal.json`。catalog 返回稳定ID及相对path，索引仅导航，不扫描所有资料正文。create自动刷新总导航、分类和学期README；迁移或补登记后调用 refresh_navigation。课程目录已存在但尚无 goal.json 时，用 adopt_course 补入口；它保留现有文件，只补缺少的系统目录。

已明确名称和用途就新建目标；学校课程必须提供用户确认的 details.semester，不按当前日期猜。默认目录名为title，可用directory_name指定不含路径分隔符的可读名称；稳定goal_id独立于目录名。course归入courses，paper归入papers，self-study以及兼容类型exam归入self-study。相近名称或多个学期存在实质歧义时才询问。旧学期课程照常学习，原状态未重新核验。同一材料只放一份。

资料放所选课程/论文/自主学习目录下的 `materials/`，以create返回值或catalog的path定位；保留原名，子目录可选。新建或补充资料后同步对象README及必要的MATERIALS清单，生成笔记后把正文加入导航。雅思可选听力/口语/阅读/写作，参考答案注明对应题目；来源未知先登记unknown，不能猜为官方答案。归属不明放 `learning/待归属/`，仅提出候选；已知课程但内容尚未核实的旧暂存材料仍放pending，不混入已核实笔记。

先枚举文件和读取少量目录信息判断角色，`register` 按内容 SHA-256 登记文件，不调用解析、不生成笔记、不升级学习状态。重复内容只提示别名，保留原件不删除；同名不同内容保留版本记录。用户放了新文件后再次 register 即可。材料清单中的 paths 是历史路径，available_paths 是当前可用版本。

确认归属后需要从待归属区移动时：先记源/目标绝对路径、类别、哈希，检查目标不覆盖，移动后核对哈希和引用。外部文件先读无需导入；记录外部绝对路径、位置和当前指纹，说明移动后需重新定位。若用户要正式纳入且来源范围明确，按其选择迁入 materials；不自动扫描外部目录。

补充来源/材料角色或真实解析结果时使用annotate_material：goal_id、material、expected_revision、source、role，及parse_status（not_requested/parsed/unavailable）、quality（unverified/checked）、cache（目标内缓存相对路径）。parsed必须对应实际缓存；checked仍需agent实际核查原件，字段校验不是内容校验。混合来源不要整批声明为官方资料。

## 2. 解析与按需问答

原生文本/Markdown直接读；PDF/PPT先定位目录、页码，再提取需要的部分；单页图片和图表优先直接查看。需要缓存时调用：

```powershell
python tools/extract_file.py "courses/2026-spring/操作系统/materials/<文件>" --backend auto
```

新缓存位于源文件旁 `.cache/<完整文件名>/<内容SHA256>/content.txt` 或 `content.md`，旧 `.cache/<stem>.txt` 原样保留但不当作新版内容。不同后缀、不同版本不会复用同名缓存。成功解析不等于内容校验通过；缓存未带页码时回原件确认定位，不能伪造页码。无需为普通问答安装所有 requirements。工具缺失时报告缺哪个能力，继续可读部分；不自动下载 OCR 模型或新增网络服务。

`auto` 延续 MarkItDown→传统PDF/PPTX→MinerU回退。复杂 OCR/MinerU 可能依赖已安装环境或模型；调用前检查能力，若会触发下载或安装，停在该步骤请求必要授权。音频和旧 PPT 可以登记；当前提取器不承诺解析，优先宿主可用能力或用户提供的转写/转换版本。

阅读错题先定位题干、相关原文、用户答案与其理由、参考答案出处。缺答案时只能提出待核实分析，不能直接确定用户错因。说明原文证据如何排除选项，先回答当前题，是否做类似题由用户决定。

## 3. 保存与恢复

先 open_session。有价值事实用 record；每次记录后 checkpoint 保存材料ID、准确位置、短摘要、未解决问题、下一步。这样即使 checkpoint 写失败，records 的事实仍在。已核实笔记用 save_note；未核实内容保存 pending 并在问题记录中链接。

新对话“继续上次”：只列目标导航；已指定目标则 resume。存在多个目标/会话且无法从用户上下文排除时，展示2至3个简短候选并问续接哪一个。读取选中的检查点、近期事件和相关片段，复述一两句位置后继续。恢复到本对话的新session ID，不能继续修改另一个仍活跃对话的ID。历史旧会话没有时效覆盖机制，不因24小时过去而删除。

## 4. 计划调整

制定正式计划前需要确定目标、日期、总时间预算、材料，并说明能力依据。计划覆盖目标要求的任务类型；雅思需听说读写均有来源和产出，薄弱项需诊断/反馈证据。目标、日期、预算或材料缺失时保留待确认，不能创建看似完整的正式日程。若仅能力基线未知、用户已委托安排时间，可在明确不保证分数的前提下制定均衡的正式初版：weakness=0，首轮练习提供可选诊断，之后依据真实表现调整，不能把用户拒绝诊断作为拒绝制定计划的理由。

从所有活跃目标收集候选任务，估算分钟，给可检查产出；用 plan 生成日程。工具排序依据为截止日、优先级、弱项强度，不能替代教学判断。agent审阅任务顺序、先修依赖与听说读写覆盖，必要时拆成有明确材料范围的小任务再规划。

用户说“今天完成一半”时确认指的是哪些任务（上下文明确则不用问），记录累计完成0.5和实际产出。重新估算剩余内容，过期任务与预算不足必须列出。重排只替代未来建议，不改昨日计划和学习事实。不要多目标各跑一份互不知晓的时间表。

## 5. JSON 调用示例

agent将请求存入临时文件，再执行 `python tools/learning.py <请求.json>`。返回JSON；错误退出码1，不得声称已保存。隔离演练使用 `--root <临时项目>`。以下 ID/哈希用实际返回值替换，不能照抄占位符。

```json
{"action":"create","goal_id":"course-example","title":"课程名称","kind":"course","details":{"semester":"用户确认的学期"}}
```

```json
{"action":"adopt_course","goal_id":"course-existing","title":"已有课程","semester":"用户确认的学期","directory_name":"已有课程目录名"}
```

```json
{"action":"register","goal_id":"ielts-20d","source":"用户提供；出版信息待确认","role":"unclassified"}
```

```json
{"action":"open_session","goal_id":"ielts-20d","label":"阅读题讨论"}
```

```json
{"action":"record","goal_id":"ielts-20d","session":"返回的会话ID","kind":"skip_test","topic":"阅读限定词","summary":"用户今天先不自测，理解证据不足","evidence":{"basis":"用户明确选择"}}
```

record 的类型：studied / self_report / understanding / mastery / question / mistake / resolved / skip_test / checkpoint / task_progress / note。

- 共同字段：goal_id、session、kind、topic、summary；material和location可选但引用已登记材料时必须同时提供。
- understanding/mastery 的 evidence：method（independent_explanation / independent_application / self_test / external_result）、observation、basis、result；mastery 还需scope且result=pass。工具只检查字段，agent仍须核实真实证据。
- result只接受pass/partial/fail，失败或部分通过不计作正面的理解证据；studied必须有evidence.basis。
- mistake 的 evidence：user_answer、answer_source、reason。存在未知可写待核实，不能伪造标准答案。
- resolved 的 evidence：resolves=本目标问题/错题事件ID，附解决依据。
- task_progress：task=已入计划任务ID，evidence含completed_fraction（累计比例）、basis、output。第二次及之后更新还需previous_event=已读到的该任务最新完成事件ID，防止旧聊天覆盖新进度；冲突时重读并核对事实。
- event_id 可预先生成UUID用于安全重试；相同ID相同内容不会重复记，变内容会拒绝。

```json
{"action":"checkpoint","goal_id":"ielts-20d","session":"会话ID","expected_revision":0,"material":null,"location":"外部文件路径或尚未定位","summary":"讨论到哪里","open_questions":["仍待解决的问题"],"next_step":"下一步具体做什么"}
```

```json
{"action":"resume","goal_id":"ielts-20d"}
```

```json
{"action":"progress","goal_id":"ielts-20d"}
```

save_note 接受 goal_id、relative（notes/文件.md 或 MAP.md）、content、expected_sha256（新文件null，旧文件为读前哈希）、sources（material/location对象列表）、verified=true。外部未导入原件可用external_path（用户已明确指定的绝对路径）、sha256、location作为source；不搬原件。保存后追加note事件链接产出。冲突返回 saved=false 和候选路径，必须合并后再试；不要自动把expected_sha256换成新值而不重读内容。

笔记写入同时在notes/.history记录该版本的来源和目标内容指纹；只有正文指纹匹配才证明该版本落盘，历史元数据不作为第二份当前笔记。笔记本身仍应提供可读来源链接。

plan 接受 start（YYYY-MM-DD）、days、tasks、save（默认false）。每项task必填 id、goal、title、material、location、minutes、output；可填deadline、priority（1至3）、weakness（0至2）。minutes是任务原始总工作量，拆分/换产出需新任务ID。任务可以分配到多天；同一ID从进度中扣除已完成比例。save=true只新增计划版本。延期/移出计划需明确写入deferred映射（任务ID→原因），不能悄悄丢掉其他目标任务。

## 6. 提醒宿主协议

配置时发现并使用宿主 automation_update。先查已有对应提醒避免重复；把用户确认的时刻/星期/开始日/结束日转为宿主支持的日程，Asia/Shanghai（若工具不支持时区字段，以明确提示和回执核对宿主时区；不可猜）。若日程不支持结束日期，任务提示需在结束日后不再发学习通知并停用本提醒；若连停用能力也无，不能承诺自动停止。

保存正式回执中的ID和日程摘要，核对后才置configured。提醒提示读取绝对项目路径下的 AGENTS.md、learning/PLAN.md、availability.json、goal.json、最新计划和真实事件；输出今天预算内的具体建议，缺资料就指出一个可行动的准备步骤，不把缺失当完成。考试确认提醒只提示用户，绝不报名。不能仅因计划工具输出成功就标记提醒生效。
