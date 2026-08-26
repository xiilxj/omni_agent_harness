# Omni Agent Harness (Codex-DSH Ultimate Core)

<p align="center">
  <b>基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度融合改造的工业级智能体底座</b><br>
  <i>100% 协议级系统提示词注入 ｜ 上下文精准引用与历史回答行内修改 ｜ 5 档深度推理强度 ｜ 实时穿插纠偏与一键急停 ｜ 跨平台 Linux & Windows 原生支持</i>
</p>

---

## 🌟 核心特性与亮点矩阵

### 1. 💬 上下文精准引用与选择性引用引擎 (Context Quote & Selection Engine)
- **严格区分消息来源与角色**：
  - 引用用户提问自动生成：`> 💬 [引用 用户提问]:` / `> 💬 [引用 用户提问 (片段)]:`;
  - 引用 AI 回答自动生成：`> 💬 [引用 AI 回答]:` / `> 💬 [引用 AI 回答 (片段)]:`;
- **多种便捷引用途径**：
  - **右键上下文菜单**：在任意消息卡片上右键，弹出快捷菜单支持「💬 引用整条消息」、「💬 引用选中局部内容」、「📋 复制」、「✏️ 编辑修改」；
  - **选中文本浮动胶囊**：鼠标在消息内拖拽选中任意局部文字时，自动浮现 **`💬 引用选中`** 胶囊，点击即引用；
  - **顶部操作栏小图标**：每条消息卡片顶部操作栏配备 **`💬 引用`** 图标；
- **智能排版与输入聚焦**：
  - 引用内容自动转换为标准 Markdown Blockquote（`>`）插入至输入框，并自动聚焦展开输入框高度。

### 2. ✏️ 模型历史回答自主修改与上下文即时替换 (Assistant Inline Response Editor)
- **行内交互编辑**：
  - 模型回答（Assistant Response）卡片右上角配备 **`✏️` 修改** 与 **`📋` 复制** 小图标；
  - 点击小图标展开内联深色编辑器，支持用户直接修正大模型生成的技术方案或回答；
- **持久化与下轮上下文无缝生效**：
  - 点击 **`[✓ 保存并更新上下文]`** 后，后端即时同步磁盘会话与活跃 Agent 内存；
  - **下一轮对话时，大模型接收到的上下文历史将 100% 以用户修改后的内容为准**，彻底解决大模型自我偏离与幻觉。

### 3. 🛑 一键急停与实时穿插纠偏对话机制 (Emergency Stop & Mid-flight Steer)
- **毫秒级急停打断 (Emergency Stop / Abort)**：
  - 输入框右侧配备 **`⏹ 急停 (Esc)`** 呼吸灯按钮与 Header 顶部状态急停按钮；
  - 点击或按下键盘 `Esc` 瞬间打断大模型吐字与正在执行的工具调用；
- **工作中实时穿插追问与动态纠偏 (Mid-flight Steer)**：
  - Agent 执行长程任务或多步工具循环期间，输入框**绝不锁死**；
  - 用户随时输入追问、补充约束与纠偏指令，指令实时注入运行队列，在下一个推理步中动态调整执行方向，无需中止重开。

### 4. ⚡ 全套斜杠快捷指令系统 (Slash Commands Engine)
- **智能联想浮层与键盘快速补全**：
  - 输入 `/` 自动弹出支持键盘 `↑` `↓` 切换与 `Enter` / `Tab` 补全的指令面板；
  - `/goal <目标>`: 开启长程自主攻坚模式，不达目的誓不罢休；
  - `/grill-me [议题]`: 资深架构师交互式多轮盘问，厘清设计决策与边界细节；
  - `/schedule <时间> <任务>`: 调度后台定时或周期性 Cron 自动化任务；
  - `/browser <URL>`: 调用 Chrome DevTools MCP 进行网页审计、DOM 提取与抓包；
  - `/teamwork-preview <项目>`: 多智能体集群协同攻关演练；
  - `/learn <经验>`: 将技术要点与避坑经验直接持久化写入长期记忆库；
  - `/clear`: 清空控制台与重置会话。

### 5. 🛡️ 100% 协议级系统提示词注入与纯净预设中心 (Master System Prompt)
- **首尾双锚定锁死**：首条 `system` 消息置顶锁死，末尾注意力加固，拒绝任何中间层稀释与冲突；
- **纯净自主预设管理**：初始纯净留白，支持多预设保存、覆盖管理与 `Ctrl+S` 快捷热保存；
- **双视图透明度**：支持 `[📝 编辑源码]` 与 `[👁️ 实际透视预览]` 双视图，彻底消除黑盒。

### 6. 👑 最高回答词预设库与随机号池引擎 (Master Response Suffix & Random Pool)
- **末尾无缝拼接**：大模型每次生成回答完毕后，系统自动将最高回答词**无缝附加在 AI 回答的最末尾**；
- **深度融入历史上下文**：该回答词不仅展示在前端，更会**100% 作为正式的 Assistant 消息事实**持久化保存到会话历史中；
- **下轮对话完美继承**：下一次用户提问或 AI 读取上下文时，大模型会完全将该最高回答词视作自己先前的正式回答，实现确定性的状态签结、格式约束与行为锚定；
- **多预设管理与覆盖保存**：支持自主创建多个回答词预设（如：状态签结、规范核验戳、极客风格总结等），支持快捷切换与覆盖保存；
- **🎲 随机号池模式 (Random Pool Mode)**：支持开启号池随机轮换，自由勾选多个预设入池，每轮 AI 回复时从池中**随机抽取**一条无缝融入末尾，为对话增添生动的丰富度与多维度核验能力；
- **📌 固定预设模式 (Fixed Preset Mode)**：选定指定预设持续生效，精准稳定。

### 7. 🌐 网络弹性防护与大模型长链思考超时加固 (3x Retry & 180s Timeout)
- **3 次指数退避自动重试**：遇到上游 API 网络抖动、闪断或代理连接重置时，自动执行 3 次平滑重试（间隔 1s / 2s / 3s）；
- **180 秒深度思考宽限**：针对 DeepSeek-R1、多步 Subagent 与复杂工具调用链，配置 180s 读取宽限，彻底杜绝 `Error: network error`。

### 7. 📏 输入框双向动态自适应与瞬间收缩 (Bidirectional Auto-Resize)
- **智能展开与平滑收缩**：多行输入/粘贴/插入引用时自动向下展开；删减文本、按 Enter 发送或点击清空小图标时，**100% 瞬间自动收缩回初始单行紧凑状态**。

### 8. 🎯 DSH 1:1 官方像素级复刻仪表盘与实时计费系统
- **实时 Telemetry 仪表盘**：`Prompt Tokens (Hit 缓存命中数)`、`Completion Tokens`、`Total Tokens`、`Latency & TPS 吐字速率`、`Cache Hit Ratio 缓存命中率 (90% 折扣加速)`、`本次计费 (精确至分后五位)`、`会话累计支出`、`账户实时余额`。

---

## 🚀 极速下载与安装使用指南

### 🐧 一、Linux / WSL 环境安装与运行

#### 1. 克隆代码仓库
```bash
git clone https://github.com/xiilxj/omni_agent_harness.git
cd omni_agent_harness
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 配置 API 密钥（安全隔离）
```bash
cp .env.example .env
# 编辑 .env 填入您的 DeepSeek API Key (或在 Web 界面设置抽屉中直接填写)
```

#### 4. 启动 Web 控制台
```bash
python3 harness/cli.py --ui --host 0.0.0.0 --port 7890
```
打开浏览器访问：👉 **`http://127.0.0.1:7890`**

---

### 🪟 二、Windows 原生环境安装与运行（无需虚拟机/Linux）

#### 方法 1：直接下载 Release ZIP 包（推荐）
1. 在 GitHub 页面点击 **Code -> Download ZIP**（或直接下载 Release 附件 `Omni_Agent_Harness_Windows_Clean.zip`）；
2. 解压到本地任意目录（例如 `D:\Omni_Agent_Harness`）；
3. **直接双击运行 `start_windows.bat`**：
   - 脚本会自动检测 Python 环境并安装所需依赖；
   - 自动在默认浏览器中弹出控制台页面：`http://127.0.0.1:7890`。

#### 方法 2：Git 命令行克隆
```cmd
git clone https://github.com/xiilxj/omni_agent_harness.git
cd omni_agent_harness
start_windows.bat
```

---

## 🔒 隐私与安全性保障 (Zero-Leak Guarantee)

- ❌ **绝对零密钥上传**：所有的 API Key 均保存在本地私有的 `.env` 中，`.gitignore` 严格阻断上传；
- ❌ **绝对零个人数据残留**：公共仓库中不包含任何私有预设、对话历史或日志，开箱即是纯净底座；
- ✅ **完全开源透明**：所有核心代码与工具调用逻辑 100% 开源可见。

---

## 📁 项目目录结构

```
omni_agent_harness/
├── config/
│   └── config.yaml                     # 全局 Provider、模型与端口配置
├── harness/
│   ├── cli.py                          # 统一 CLI 与 Web UI 启动入口
│   ├── core/                           # 核心状态机 (ReAct Loop, Slash Commands, Subagent)
│   ├── prompt/                         # 100% Master 提示词注入与预设管理器
│   ├── tools/                          # 跨平台工具箱 (Bash, PowerShell, Grep, Replace, Ast)
│   ├── providers/                      # 多模型适配层 (DeepSeek, OpenAI, Anthropic)
│   └── ui/                             # 现代化 Web 控制台 (FastAPI + Tailwind SPA)
├── requirements.txt                    # 跨平台标准依赖清单
├── start_windows.bat                   # Windows 一键启动批处理
├── install_windows.bat                 # Windows 依赖安装批处理
├── package_windows_clean.py            # Windows 纯净分发打包脚本
├── README_WINDOWS.md                   # Windows 专用说明文档
└── README.md                           # 全面架构与使用指南
```

---

## 📄 License
MIT License.
