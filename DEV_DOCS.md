# Omni Agent Harness (Codex-DSH Ultimate Edition) 实时开发与架构文档

## 1. 项目定位与核心愿景
本项目是基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度重构融合的工业级终极智能体底座（Agent Harness），具备以下核心系统：

### 🎯 全厂商模型矩阵与自适应档位映射 (Universal Multi-Provider Matrix)
- **7 大主流厂商一键快速模版 (Provider Quick Profiles)**：
  1. `DeepSeek 官方` (`https://api.deepseek.com/v1`)
  2. `OpenAI 官方` (`https://api.openai.com/v1`)
  3. `硅基流动 SiliconFlow` (`https://api.siliconflow.cn/v1`)
  4. `OpenRouter 聚合/Claude` (`https://openrouter.ai/api/v1`)
  5. `Ollama 本地私有化` (`http://localhost:11434/v1`)
  6. `阿里百炼 通义千问` (`https://dashscope.aliyuncs.com/compatible-mode/v1`)
  7. `月之暗面 Kimi` (`https://api.moonshot.cn/v1`)
- **4 档智能体能力自定义绑定 (Custom Tier Mapping)**：
  - 用户可自由修改并持久化 4 大档位所绑定的具体模型名（如 Flash 绑定 `gpt-4o-mini`，Pro 绑定 `claude-3-5-sonnet`，Reasoner 绑定 `o3-mini`，Vision 绑定 `gpt-4o`）；
  - 顶部导航栏药丸、底部胶囊与下拉选单实现 100% 毫秒级双向全双工同步。

### ⚡ DSH 与 Codex 全部高阶系统 100% 终极装配清单
1. **`ask_user` (交互式提问卡片)**：遇到设计分支或需用户确认时，弹出交互选择卡片，异步挂起并等待提交。
2. **`update_todo_list` (动态里程碑进度条)**：多步骤任务自主拆解，前端实时渲染进度百分比与 `待执行`、`执行中 (呼吸动效)`、`已完成 (划线打勾)`。
3. **`diff_viewer` (红绿代码差异查看器)**：精准记录并高亮展示文件修改 Unified Diff 补丁。
4. **`checkpoint_rollback` (会话时间旅行回退)**：鼠标悬浮历史用户提问即可 `⏪ 回退到此步`，安全裁剪并重新分叉。
5. **`context_pruner` (长会话上下文剪枝与 Token 优化器)**：
   - 自动检测并压缩历史早期超大工具输出（保留特征标识），保护最新轮次与 Master Prompt 100% 完好；
   - 彻底解决长任务多轮对话爆 Token 问题，极大降低 API 费用。
6. **`subagent_swarm` / `invoke_subagent` (多智能体集群协同派发)**：
   - 主智能体可按需派发专精子智能体（如 `researcher` 只读探索专家、`code_auditor` 安全审计专家、`exploit_analyst` 协议分析专家）；
   - 子智能体拥有独立上下文与内存沙箱，完成后向上级主 Agent 提交结构化研判报告。
7. **`manage_task` / `task_manager` (后台常驻进程与守护任务管理器)**：
   - 支持启动后台常驻支持进程（如 Dev Server、持续编译监听器、后台抓取），支持查看状态/日志、终止与列表列出。
8. **`find_symbol_definition` (Codex AST 符号定位器)**：
   - 跨语言精准检索类声明 (`class`)、函数 (`def`/`fn`/`function`)、结构体与接口，无需加载超大文件。
9. **`run_code_tests` (Codex 自愈测试驱动验证执行器)**：
   - 自动运行测试套件（`pytest`, `npm test` 等），解析报错与堆栈，驱动 ReAct 循环自主修复缺陷直至全绿。
10. **`mcp_client` (Model Context Protocol 客户端)**：
    - 支持 Anthropic STDIO MCP 协议，无缝连接第三方 MCP 服务。

---

## 2. 核心模块与工具集 (共 14 项完整工具)

| 工具名称 | 分类 | 用途说明 |
| :--- | :--- | :--- |
| `run_command` | Shell 执行 | 跨平台执行 Bash / PowerShell 命令。 |
| `view_file` | 文件系统 | 切片读取文件内容。 |
| `write_file` | 文件系统 | 创建或完全覆盖写入文件。 |
| `replace_file_content` | 文件系统 | 精准行级文本替换并生成 Unified Diff。 |
| `list_dir` | 搜索浏览 | 递归列出目录层级结构。 |
| `grep_search` | 搜索浏览 | 文本与正则模式搜索。 |
| `find_by_name` | 搜索浏览 | 文件名通配符快速查找。 |
| `read_url_content` | 网络提取 | HTTP 抓取并转换为纯净 Markdown。 |
| `ask_user` | 交互控制 | 决策分支向用户弹出选项卡片。 |
| `update_todo_list` | 任务追踪 | 动态维护里程碑 Checklist 与进度百分比。 |
| `find_symbol_definition` | Codex 引擎 | AST 符号与函数定义精准定位。 |
| `run_code_tests` | Codex 引擎 | 运行测试套件并结构化解析报错。 |
| `manage_task` | DSH 后台 | 启动、监控与终止后台守护进程。 |
| `invoke_subagent` | DSH 集群 | 异步派发专精子智能体执行独立子任务。 |

---

## 3. 审核与验证记录
- **审核轮数**: 第 28 轮（全厂商模型矩阵 + DSH & Codex 核心系统全量装配验收）
- **测试状态**:
  - `pytest tests/`: **14/14 全部通过**。
- **纯净 Windows 分发包导出路径**: 
  - `/mnt/d/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/c/Users/Lenovo/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/d/Omni_Agent_Harness_Windows_Clean.zip`
- **GitHub 远程同步**: `https://github.com/xiilxj/omni_agent_harness`（Commit: `4374a51`）。
