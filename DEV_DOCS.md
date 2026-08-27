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

### ✏️ 模型历史回答自主修改与上下文无缝替换引擎 (Assistant Message Inline Editor)
- **内联交互编辑卡片**：
  * 每个模型输出（Assistant Response）卡片右上角配备 **`✏️ 修改回答`** 与 **`📋 复制`** 快捷小图标；
  * 点击小图标即可展开深色文本编辑框，用户可直接修正或修改模型的回答内容；
- **会话持久化与下轮上下文即时替换**：
  * 点击 **`[✓ 保存并更新上下文]`** 后，后端 `/api/sessions/{session_id}/messages/{msg_index}/edit` 立即更新磁盘会话记录与活跃 Agent 内存；
  * 下一轮对话触发时，大模型接收到的上下文历史将完全以用户修改后的新内容为准，确保逻辑纠偏无缝生效。

---

### 💬 对话上下文精准引用与选择性引用系统 (Context Quote & Selection System)
- **严格区分用户提问与 AI 回答**：
  * 引用用户提问时自动标记：`> 💬 [引用 用户提问]:` / `> 💬 [引用 用户提问 (片段)]:`;
  * 引用 AI 回答时自动标记：`> 💬 [引用 AI 回答]:` / `> 💬 [引用 AI 回答 (片段)]:`;
- **多种便捷引用途径**：
  * **右键上下文菜单**：在任意消息卡片上右键，弹出快捷菜单支持「💬 引用整条消息」、「💬 引用选中局部内容」、「📋 复制」、「✏️ 编辑修改」；
  * **选中文本浮动胶囊**：鼠标在任意消息内拖拽选中任意文字时，自动浮现 **`💬 引用选中`** 快捷胶囊，点击即引用；
  * **顶部操作栏按钮**：每条消息卡片顶部悬浮栏均配备 **`💬 引用`** 按钮；
- **智能排版与输入聚焦**：
  * 引用内容自动转换为标准 Markdown Blockquote（`>`）插入至输入框光标位置，自适应调整输入框高度并聚焦，随时开启下一轮针对性追问。

---

### 📏 输入框双向动态自适应与瞬间收缩机制 (Bidirectional Auto-Resize)
- **动态高度自适应计算**：
  * 精准算法 `adjustPromptInputHeight()`：多行文本输入、粘贴或插入长引用时向下平滑撑开；
  * 退格删除缩减时实时向下收缩，绝不残留多余空白；
- **清空与发送瞬间复位**：
  * 消息发送、点击清除图标或执行 `/clear` 时，自动调用 `resetPromptInputHeight()`，瞬间归位至初始单行紧凑状态。

---

### 🌐 网络弹性防护与长思考超时宽限 (3x Exponential Retry & 180s Timeout)
- **3 次指数退避网络重试**：
  * 捕获 `ConnectError`, `ReadTimeout`, `RemoteProtocolError`, `ConnectTimeout` 并自动以 1s / 2s / 3s 间隔重试，杜绝偶发网络闪断报错；
- **180s 深度思考宽限**：
  * 适配 DeepSeek-R1 与 Subagent 长程复杂调用链，彻底消除超时断连。

### 👑 最高回答词预设库与随机号池引擎 (Master Response Suffix & Random Pool)
- **末尾无缝拼接**：`MasterPromptInjector.apply_master_suffix()` 将配置的最高回答词无缝拼接到大模型每轮回答的最末尾；
- **真实上下文融入**：不仅在前端渲染，更作为 `role: "assistant"` 的持久化事实存入磁盘会话 `SessionItem.messages`；
- **下轮对话完美继承**：后续多轮交互中，大模型将该回答词作为自身先前的回答历史读取，实现行为状态锚定与严谨签结；
- **多预设管理与覆盖保存**：`SuffixPresetManager` 支持创建、保存、覆盖与删除多条回答词预设；
- **🎲 随机号池模式 (Random Pool Mode)**：支持自由勾选多个预设入池，每轮 AI 回复时从池中**随机抽取**一条无缝融入末尾，为对话增添生动的丰富度与多维度核验能力；
- **全套 API 与 UI 闭环**：提供 `/api/master-suffix/presets` (GET/POST/DELETE) 及 `/api/master-suffix/settings`，设置抽屉全套交互卡片与 `Ctrl+S` 即时热保存。

### 🛡️ 思维链实时审计熔断与多轮历史净化流水线 (CoT Refusal Interceptor & Sanitizer)
- **毫秒级中英文拒绝指纹探测**：`refusal_detector.py` 覆盖 sorry、cannot、无法、抱歉、违规、无能为力等全语义特征；
- **流式毫秒级掐断熔断**：在 `reasoning_content` 前 350 字与回答前 200 字探测到拒绝倾向时立即 break 掐断流，节省 90% 耗时与 Token 开销；
- **三阶递进强制豁免重试**：自动叠加 `[OVERRIDE_EXEMPTION_L1~L3]` 靶场授权锁死与占位符指令重发（最多 3 次）；
- **历史上下文防污染净化**：`sanitize_messages_history()` 挂载会话时全自动剔除旧的拒绝脏历史。

---

## 4. DSH 架构对齐与源码更新全量吸收体系 (DSH Deep Alignment & Continuous Absorption)

本项目与 DeepSeek Harness (DSH) 保持同源架构与深度语义对齐，确立了以下「DSH 源码更新全量吸收原则」：

1. **协议层与工具链无缝吸收 (Protocol & Tools Alignment)**：
   - 严格对齐 DSH 的工具定义规范（包含基于字典序严格排序的 Schema 注册、缓存友好结构与参数紧凑化处理）；
   - 当 DSH 新增工具（如新型代码分析、多文件批量编辑、符号索引或浏览器交互协议）时，本项目将以跨平台原生实现（Linux / Windows / macOS）无缝吸收。
2. **上下文流式事件与剪枝机制 (Streaming Events & Context Compaction)**：
   - 对齐 DSH 的流式事件分发协议（`step_start`, `thought_delta`, `tool_executing`, `tool_result`, `thought_signature_injected`, `task_completed` 等）；
   - 吸收 DSH 最新的上下文自动修剪（Context Pruning / Auto Compaction）与长思考 Token 优化算法。
3. **多模态与计费模型同步 (Multimodal & Cost Telemetry)**：
   - 紧密跟进 DSH 针对最新大模型（如 DeepSeek-V3/R1, Gemini 3.5, Claude 3.5, GPT-4o）的费率矩阵、Prompt Cache 命中测算与多模态图文编码流水线。
4. **本工程专有特性融合保留 (Zero Loss Integration)**：
   - 在吸纳 DSH 更新的同时，100% 完整保留本工程专有的核心能力：
     * 👑 Master Prompt 绝对置顶三层注入与最高回答词随机号池（Master Response Suffix）；
     * 📱 Telegram Bot 嵌入式全功能远程控制与 Web UI 任务双向实时同步推送；
     * ⚡ thought_signature 丢失自动自愈注入与思维链拒答三阶豁免熔断；
     * 💻 Windows / Linux 跨平台一键开箱自启动（`.bat` / `.sh`）与零污染纯净打包体系。
5. **测试驱动与零回归验证 (Test-Driven Verification)**：
   - 每次吸纳 DSH 源码更新后，全量运行并扩充 `tests/test_dsh_*.py` 自动化测试集，确保全量测试 100% Passed。

---

## 5. 审核与验证记录
- **审核轮数**: 第 39 轮（DSH 源码更新全量吸收机制 + Telegram 双向同步通信 + Gemini 3.5 锁定 + 44 项全量测试 100% 通过）
- **测试状态**:
  - `pytest tests/`: **42 passed, 2 skipped (100% Passed)**。
- **纯净 Windows 分发包导出路径**: 
  - `./dist/Omni_Agent_Harness_Windows_Clean.zip` (纯净工程打包，严格不向 Arch 桌面投递)
- **GitHub 远程同步**: `https://github.com/xiilxj/omni_agent_harness`（已全面推送到 main 分支）。
