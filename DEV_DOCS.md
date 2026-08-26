# Omni Agent Harness (Codex-DSH Ultimate Edition) 实时开发与架构文档

## 1. 项目定位与核心愿景
本项目是基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度重构融合的工业级终极智能体底座（Agent Harness），具备以下核心系统：

### 🎯 右侧产物透视与实时预览系统 (Right-Side Overview & Live Preview Panel)
- **可自由展开/收回的右侧专属工作区面板**：
  * 点击顶部导航栏 **`👁️ 产物预览 (Overview)`** 按钮、使用快捷键 **`Ctrl+P`** 或 **`Alt+O`**，即可无缝侧滑展开/收回；
  * Agent 执行任务创建或修改 HTML/MD 等产物时，自动联动刷新产物列表。
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

## 3. 审核与验证记录
- **审核轮数**: 第 29 轮（右侧产物实时透视面板 + Skills/MCP 深度配置管理中心全量交付验收）
- **测试状态**:
  - `pytest tests/`: **15/15 全部通过 (100% Passed)**。
- **纯净 Windows 分发包导出路径**: 
  - `/mnt/d/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/c/Users/Lenovo/Desktop/Omni_Agent_Harness_Windows_Clean.zip`
  - `/mnt/d/Omni_Agent_Harness_Windows_Clean.zip`
- **GitHub 远程同步**: `https://github.com/xiilxj/omni_agent_harness`（Commit: `4304bcd`）。
