# 项目工具

[返回总览](../README.md)。用户日常用自然语言即可，不要求运行命令。

| 工具 | 职责 |
|---|---|
| learning.py | 按稳定ID发现三类目标；新建或接管已有课程目录，登记材料、记录事件、保存笔记、恢复会话、共享计划及刷新导航 |
| extract_file.py | 唯一资料提取入口；必须明确输入单个文件或目录，不默认解析全项目 |
| extract_pdfs.py / extract_pptx.py / mineru_extract.py | 底层解析与历史兼容；不要绕开统一入口批量操作 |
| test_*.py | 隔离测试，不写真实学习状态 |
| demo_learning.py | 合成场景演练，不是用户学习证据 |
| one-off migration scripts | 只留在本机供恢复参考，不作为日常命令或新课程模板 |

维护时执行受影响检查及 `python -B -m unittest discover -s tools -p "test_*.py"`。结构测试不能替代材料语义或真实学习验收。
