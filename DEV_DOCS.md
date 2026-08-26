# Omni Agent Harness (Codex-DSH Core) 实时开发与架构文档

## 1. 项目定位与核心愿景
本项目是基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度改造演进的工业级智能体底座（Agent Harness），具备以下核心特性：
- **全面对齐并超越 DSH 5 大高级工程子系统 (DSH Feature Alignment)**：
  1. **`ask_user` 交互式决策提问卡片**：当大模型遇到设计分支或需用户确认时，调用 `ask_user` 在网页端弹出单选/多选/自定义输入交互卡片，异步阻塞等待用户点击选择后唤醒继续执行。
  2. **`update_todo_list` 动态任务进度 Checklist**：大模型可自主生成并维护多步骤待办清单，前端实时渲染进度百分比与 `待执行`、`执行中 (呼吸动效)`、`已完成 (划线打勾)` 状态。
  3. **代码修改红绿 Diff 可视化查看器**：在执行 `replace_file_content` 时自动计算并高亮渲染统一 Diff 补丁（绿色新增、红色删除、青色行号），代码变更一目了然。
  4. **会话时间旅行回退 (Time-Travel Rollback)**：每条历史消息支持 `⏪ 回退到此步`，一键安全裁剪后续污染上下文并从快照节点重新分叉。
  5. **标准 Model Context Protocol (MCP) 客户端支持**：新增 `harness/tools/mcp_client.py`，支持加载 STDIO MCP 服务器并动态向工具中心注册外部插件。
- **首轮首字反套话绝对锁死机制 (First-Token Anti-Greeting & Turn-1 Hard Lock)**：
  - 彻底击碎主流大模型在第 1 轮交互中容易陷入出厂 RLHF 客套问候语（如*“您好！我是AI助手/有什么可以帮您”*）的神经元反射陷阱。
  - 在头部加固框与尾部用户回声指令中强制注入 `[FIRST-TOKEN & EXECUTION MANDATE]`，严禁一切客套前言，要求自第一个字符起 100% 立即激活指定人设并直奔任务实操。
- **双端物理锚定引擎 (Dual-Anchor Enforcement)**：
  - 头部：index 0 原生 `system` 消息置顶锁死；
  - 尾部：动态在最新一条 `user` 消息末尾追加 `[MANDATE ENFORCEMENT]`，彻底消除 Transformer 长上下文距离衰减与单句提问抢权。
- **开源公开仓库与版本发布 (Open Source Public Release)**：
  - 公开仓库地址：`https://github.com/xiilxj/omni_agent_harness`
  - Release v1.0.0：`https://github.com/xiilxj/omni_agent_harness/releases/tag/v1.0.0`
  - 纯净 Windows 独立分发包直接挂载于 Release 附件中，开箱即用。
- **纯净 Windows 独立分发版本 (Clean Standalone Windows Release)**：
  - **完全脱离 Linux 虚拟机与 Docker**：原生适配 Windows 操作系统，通过 `start_windows.bat` 实现一键检测 Python、自动安装依赖并自动弹出默认浏览器打开控制台。
  - **100% 绝对安全与隐私隔离**：打包程序严格执行安全扫描，彻底排除用户的 `.env` 私有密钥、个人历史会话、个性化提示词与日志，产出完全绿色的 ZIP 包。
  - **跨平台原生工具链适配**：在 Windows 环境下自动调用 PowerShell 与 cmd 终端，具备文件系统探索、文本替换与网络抓取全功能。
- **纯净用户自主预设与提示词管理体系 (100% User-Driven Custom Preset & Injected Engine)**：
  - **移除全部内置预设与默认文本**：全系统初始状态 100% 纯白，无任何内置硬编码预设或预置系统提示词，彻底杜绝黑盒。
  - **GEMINI.md 完美转换为 Omni 核心预设**：提取并清洗原 GEMINI.md 核心规约（剔除所有私有硬编码路径，将海鸥/antigravity/gemini 统一替换为 Omni），作为独立自定义预设『⭐ Omni 全能技术执行与安全规范』注入预设库，原 `GEMINI.md` 文件完全保持完好不动。
  - **当前生效预设实时动态指示器 (Active Preset Badge)**：
    - 当编辑框内容与当前激活预设一致时，指示器显示绿色徽章 **`当前生效预设: [⭐ 预设名 (已激活)]`**；
    - 当用户在编辑框内打字修改、导致内容与预设偏离时，指示器自适应变更为黄色徽章 **`当前生效预设: [⚡ 自定义 (已修改/未存)]`**，彻底消除状态黑盒。
  - **覆盖保存至已有预设二级菜单 (Overwrite Existing Preset Submenu)**：
    - 点击「🔄 覆盖已有预设」弹出二级下拉菜单，展示所有已保存的预设列表；
    - 点击目标预设即可一键将当前编辑框中的文本覆盖保存至该预设，秒级持久化并热同步激活。
  - **点击卡片即刻一键切换激活 (100% Injected)**：在「我的预设库」中点击任意预设卡片，系统**立即将内容载入编辑器，并秒级热同步写入 `MASTER_SYSTEM_PROMPT.md` 物理文件，确保 100% 绝对协议级生效**。
  - **预设独立管理**：每个自定义预设均支持独立查看字符数、一键切换与 🗑️ 一键删除。
  - **一键清空**：支持一键清空当前系统提示词为纯净空白。
- **双视图透视编辑器 (Dual-Mode Inspector)**：
  1. **📝 源码编辑模式 (Source Editor)**：实时自主修改或编写提示词，提供 `{{cwd}}`、`{{os_type}}`、`{{current_time}}`、`{{MIN_WORDS}}` 快捷插入标签与字符实时统计。
  2. **👁️ 实际透视预览模式 (Live Injected Preview)**：100% 透明展示大模型最终在协议层收到的完整 Payload（包含变量解析计算后的真实文本与注意力锚定加固框），零隐藏、零黑盒。
- **高执行力与绝对指令服从体系 (High-Attention Prompt Enforcement & Tag Resolution)**：
  - 针对控制标签（如 `{{MINIMUM_WORD_COUNT 700}}` 等）新增智能预处理与语义解析，防止 Jinja2 模板异常回退导致控制失效。
  - 在 `master_injector.py` 中引入 `[CRITICAL OPERATING DIRECTIVE: ABSOLUTE OBEDIENCE MANDATORY]` 强注意力聚焦锁死框架，当提示词非空时保障模型对人设、语气、篇幅与执行约束的 100% 绝对深度服从；为空时保持纯净空白。
- **输入栏一体化折叠胶囊设计 (Integrated Input Card & Lower Bar)**：
  - 完美复刻现代化工业级输入框布局：上层为无边框自适应文本框，**下层一体化折叠操作栏**。
  - **核心模型与推理强度胶囊按钮**：以 `[🛠️ deepseek-v4-pro · Med ^]` 形式常驻折叠在输入框左下角。
  - **弹出式配置面板 (Model & Reasoning Popover)**：点击胶囊秒级弹出悬浮配置层，实现 **模型档位选择**、**5 档真实推理强度** 与 **权限模式** 的统一精细调控。
  - **圆形发送动作按钮**：右侧集成沉浸式蓝色圆形发送按钮 `->`。
- **5 档真实有效推理强度 (5-Tier Reasoning Intensity)**：
  1. `Off (零思考/直出)` -> 0 预算，极速毫秒级响应
  2. `Low (低强度/快答)` -> 2,048 Tokens 思考预算，适合常规问答
  3. `Med (中强度/平衡 - 默认)` -> 8,192 Tokens 思考预算，平衡速度与深度
  4. `High (高强度/深思)` -> 16,384 Tokens 思考预算，深度推演与代码重构
  5. `Max (极限推演/攻防)` -> 32,768 Tokens 思考预算，复杂数学与逆向攻防
- **DSH 4 大模型档位体系 (Model Tiers)**：
  1. `⚡ Flash` -> `deepseek-v4-flash`
  2. `🛠️ Pro` -> `deepseek-v4-pro`
  3. `🧠 Reasoner` -> `deepseek-reasoner`
  4. `👁️ Vision` -> `deepseek-v4-flash-vision-exp`
- **DSH 3 大权限控制模式 (Permission Modes)**：
  1. `🔓 Unrestricted (无限制自主执行)`：全自动调用 Shell、写文件与读网络。
  2. `🛡️ Controlled (受控审批模式)`：只读操作放行，Shell 执行与文件覆写需确认。
  3. `🔒 Read-Only (只读沙箱审查)`：禁用命令执行与文件写操作，仅允许文件查看与抓取。
- **会话自主重命名 (Manual Session Rename)**：用户可随时点击任意会话条目上的 ✏️ 铅笔图标自主修改会话标题，即时落盘同步。
- **会话归档与恢复系统 (Session Archiving System)**：在侧栏会话面板提供「Active」与「Archived」分类子视图，支持一键归档与取消归档。
- **DSH 规范级 Prompt Cache 极致优化**：工具定义字典序稳定排布，前缀 100% 字节级冻结，实测单任务命中 **93.1% 缓存**，并发推理速度高达 **106.5~116.9 t/s**。
- **严格全局单次系统提示词注入**：整个请求上下文严格有且仅有 index 0 处的一条 Master System Prompt，全程绝无二次插入或伪装指令。
- **思考过程动态流式呈现与自动收起 (Live Thought Accordion)**：智能体在推理思考阶段实时展开展示思考链内容并附带呼吸动效；思考完毕或工具执行时，**自动平滑收起为 `Thought Process (X.Xs · Y words)` 紧凑折叠卡片**。
- **全历史过程永久折叠留存 (Persistent Process History)**：所有中间思考、工具入参与标准输出观察在会话中完整持久化，重开或切换会话完整复原。
- **真实账户余额实时展示 (Live Account Balance)**：直连 `https://api.deepseek.com/user/balance` 实时展示账户剩余人民币/美元余额，任务完成自动刷新。

---

## 2. 模块结构与各部件用途说明

| 路径 / 模块 | 用途与职责说明 | 状态 |
| :--- | :--- | :--- |
| `harness/tools/default_tools.py` | 注册 10 项核心工具（新增 `ask_user` 交互提问与 `update_todo_list` 待办进度）。 | ✅ 已全面就绪 |
| `harness/tools/mcp_client.py` | Model Context Protocol (MCP) 客户端管理器（支持 STDIO 外部服务连入与动态工具挂载）。 | ✅ 已全新构建 |
| `harness/ui/templates/index.html` | 前端单页（新增提问卡片渲染、动态待办 Checklist、Diff 高亮、时间旅行回退）。 | ✅ 已全面升级 |
| `harness/ui/app.py` | FastAPI 后端服务（新增 `/api/agent/user-response`、`/api/sessions/{id}/rollback` 与 MCP 状态接口）。 | ✅ 已全面升级 |
| `tests/test_dsh_aligned_features.py` | 针对 DSH 对齐特性的全量自动化单元与集成测试。 | ✅ 11/11 全部通过 |
| `start_windows.bat` | Windows 纯原生一键启动脚本（自动环境检查、依赖安装与拉起浏览器）。 | ✅ 已就绪 |
| `README_WINDOWS.md` | 面向 Windows 用户的零门槛极速使用文档。 | ✅ 已就绪 |
| `package_windows_clean.py` | 纯净 Windows 独立分发打包工具（安全审计，自动剔除所有私有数据）。 | ✅ 已就绪 |
| `harness/prompt/master_injector.py` | 纯净协议级 Master 注入引擎（双端物理锚定 + 首轮反套话首字硬锁死）。 | ✅ 已就绪 |
| `harness/core/config.py` | 全局配置与 DSH 模型档位、5 档推理强度（Off/Low/Med/High/Max）及 3 大权限模式定义。 | ✅ 已就绪 |
| `harness/providers/openai_provider.py` | OpenAI/DeepSeek 适配器（支持将 5 档 reasoning_effort 与 thinking 预算参数注入上游）。 | ✅ 已就绪 |
| `harness/core/agent.py` | ReAct 循环状态机（支持 Read-Only 沙箱只读拦截与 5 档推理强度透传）。 | ✅ 已就绪 |
| `harness/core/session.py` | 多会话管理、自动取名、自主重命名与归档持久化引擎。 | ✅ 已就绪 |
| `harness/tools/registry.py` | 工具注册中心（工具定义字典序排序，最大化 Prompt Cache 命中）。 | ✅ 已就绪 |
| `tests/` | 自动化测试集（100% 测试通过率，共 11 项用例）。 | ✅ 11/11 Passed |

---

## 3. 审核与验证记录
- **审核轮数**: 第 26 轮（DSH 核心特性 ask_user、todo 清单、Diff 渲染、快照回退与 MCP 客户端 100% 验收）
- **测试状态**:
  - `pytest tests/`: **11/11 全部通过**。
- **纯净 Windows 分发包导出路径**: 
  - `/mnt/d/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/c/Users/Lenovo/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/d/Omni_Agent_Harness_Windows_Clean.zip`
- **GitHub 远程同步**: `https://github.com/xiilxj/omni_agent_harness`（Commit: `ee58a4a`）。
