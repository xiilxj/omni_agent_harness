# Omni Agent Harness (Codex-DSH Ultimate Edition) 实时开发与架构文档

## 1. 项目定位与核心愿景
本项目是基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度重构融合的工业级终极智能体底座（Agent Harness），具备以下核心系统：

### 🎯 DSH 1:1 官方像素级复刻仪表盘与实时计费系统
- **实时 Telemetry 仪表盘 (Bottom Telemetry Meter)**：
  * `Prompt Tokens`：提示词总量与 `(Hit: xxx)` 绿色缓存命中数；
  * `Completion Tokens`：生成输出 Token 数量；
  * `Total Tokens`：本轮总消耗 Token；
  * `Latency & Live TPS`：毫秒级秒表走秒与生成速率动态测速；
  * `Cache Hit Ratio`：提示词缓存命中率徽章（>50% 高亮绿色，节省 90% 成本）；
  * `Turn Cost (本次计费)`：基于官方标准费率精准核算至分后五位（`¥0.000xx`）；
  * `Session Cost (会话累计)`：多轮交互累计消耗总金额（`¥0.0xxxx`）；
  * `Account Balance`：官方账户实时可用余额（`¥XX.XX`）；
  * `128K Context Bar`：上下文窗口已占用比例与进度条。
- **实时计费与 Token 成本明细表弹窗 (`#modal-billing-breakdown`)**：
  * 点击仪表盘中的 **`📊 计费明细`** 按钮或点击余额，即弹出计费清单；
  * 展示当前模型费率标准（输入未命中、缓存命中、输出单价）；
  * 逐项拆解本次交互各计费项（Prompt 未命中、缓存命中、Completion 输出）的 Token 数量、计费单价与实扣费用；
  * 会话累计总支出与账户余额实时同步。

### 👁️ 右侧产物透视与实时预览系统 (Right-Side Overview & Live Preview Panel)
- **三大透视模式**：
  1. `🌐 实时 Web / UI 渲染`: 内嵌 `<iframe id="preview-live-iframe">`，支持下拉选择工作区内的任何 HTML 页面实时交互渲染、重新载入与在新浏览器窗口全屏打开；
  2. `📄 交付文档 (Artifacts)`: Markdown 渲染器，实时展示系统生成的开发文档、规划与报告；
  3. `🔍 代码与 Diff 透视`: 高亮查看代码文件与修改补丁。

### 🧩 技能插件中心 (Skills Engine & Manager)
- **多源自动感知与扫描**：
  * 自动扫描 `~/.gemini/antigravity/skills/`、宿主机软链接与本地 `./skills/` 目录；
  * 提取 `SKILL.md` 的功能描述、调用触发词与提示词模版，卡片化展示就绪状态；
  * 支持一键将指定 Skill 注入当前提示词中生效，并支持在线新建自定义 Skill 插件。

### 🔌 MCP 服务管理中心 (Model Context Protocol Manager)
- **STDIO 协议服务可视化监控与热重载**：
  * 直观展示当前已连接的 MCP 服务实例（如 Chrome DevTools、Filesystem 等）及其包含的工具数量；
  * 内嵌 `mcp_config.json` 专用编辑器，支持在线配置、语法校验并一键「💾 保存配置并热重载 MCP 服务」。

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

### 🛑 一键急停与实时穿插纠偏对话机制 (Emergency Stop & Mid-flight Steer)
- **多端一键急停 (Emergency Stop / Abort)**：
  * 输入框右侧醒目呼吸灯按钮 **`⏹ 急停 (Esc)`** 与 Header 顶部状态急停按钮；
  * 按下或键盘 `Esc` 立即发送 `/api/agent/abort` 并中断前端 SSE，瞬间打断大模型吐字与正在执行的工具调用。
- **工作中实时穿插追问与纠偏对话 (Mid-flight Steer)**：
  * 在 Agent 执行任务或多步工具循环期间，输入框**不锁死**；
  * 随时输入追问、补充约束与纠偏指令，点击 `⚡ 实时穿插纠偏 (Enter)`；
  * 指令直接注入 Agent 运行队列，在下一个推理步中动态调整执行方向，无需中止重开。

### ⚡ 全套斜杠快捷指令系统 (Slash Commands Engine)
- **智能联想浮层 (`#slash-commands-popover`)**：
  * 输入 `/` 自动弹出支持键盘 `↑` `↓` 切换与 `Enter` / `Tab` 补全的指令列表；
  * `/goal <目标>`: 开启深度长程自主攻坚模式，不达目的誓不罢休；
  * `/grill-me [议题]`: 资深架构师交互式多轮追问盘问，厘清设计决策与边界细节；
  * `/schedule <时间> <任务>`: 调度后台定时或周期性 Cron 自动化任务；
  * `/browser <URL>`: 调用 Chrome DevTools MCP 进行页面审计、DOM 提取与抓包；
  * `/teamwork-preview <项目>`: 多智能体集群协同攻关演练；
  * `/learn <经验>`: 将技术要点与避坑经验直接持久化写入 `persistent_memory.txt`；
  * `/rollback [步数]`: 历史会话时空回退；
  * `/clear`: 清空控制台与重置会话；
  * `/help`: 查看完整斜杠指令清单。

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
- **审核轮数**: 第 31 轮（一键急停 + 工作中实时穿插纠偏追问 + 全套斜杠快捷指令系统全量验收）
- **测试状态**:
  - `pytest tests/`: **18/18 全部通过 (100% Passed)**。
- **纯净 Windows 分发包导出路径**: 
  - `/mnt/d/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/c/Users/Lenovo/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/d/Omni_Agent_Harness_Windows_Clean.zip`
- **GitHub 远程同步**: `https://github.com/xiilxj/omni_agent_harness`（最新 Commit 已推送）。
