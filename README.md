# Omni Agent Harness (Codex-DSH Ultimate Core)

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-DSH%20Native%20Aligned-blue?style=for-the-badge&logo=deepseek" alt="DSH Aligned" />
  <img src="https://img.shields.io/badge/Control-100%25%20User%20Sovereignty-emerald?style=for-the-badge" alt="User Sovereignty" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=for-the-badge" alt="Cross Platform" />
  <img src="https://img.shields.io/badge/Tests-44%20Passed%20(100%25)-brightgreen?style=for-the-badge" alt="Tests 100%" />
</p>

<h3 align="center">
  <b>把真正的控制权，100% 彻底交还给用户</b><br>
  <i>拒绝黑盒操纵 ｜ 拒绝教条说教 ｜ 历史上下文自主修改 ｜ 执行中动态穿插纠偏 ｜ Telegram 双向远程控制</i>
</h3>

---

## 💡 为什么需要 Omni Agent Harness？（核心设计哲学）

市面上几乎所有的商业 AI 编程助手与 Agent 工具（Cursor、Windsurf、Copilot、各种闭源 Agent）都在**不断剥夺开发者的控制权**：
- ❌ **黑盒提示词操纵**：商业厂商在底层强行注入数百行预设规则与安全围栏，用户的提示词被稀释甚至被篡改；
- ❌ **历史回答无法纠偏**：大模型一旦在第 3 轮产生幻觉并写错代码，后续所有轮次都会被错误污染，用户只能绝望地清空会话重开；
- ❌ **执行过程强制锁死**：Agent 一旦开始多步循环或长程思考，输入框立刻被禁用，用户看着 AI 偏离方向却只能干瞪眼；
- ❌ **设备与场景割裂**：一旦离开电脑桌前，耗时数十秒的长程任务进度完全断联；
- ❌ **动辄拒绝与说教**：遇到模糊或敏感调试需求时动辄道歉拒绝，浪费昂贵的 Token 和宝贵的时间。

> **Omni Agent Harness 的唯一使命：打破黑盒，将智能体的一切调度权、记忆权、上下文决定权与执行权，毫无保留地全部交给用户！**

---

## ⚔️ 核心差异对比：Omni Agent Harness vs. 传统黑盒 Agent

| 维度 | 传统商业/开源 Agent (Cursor / AutoGPT 等) | 👑 **Omni Agent Harness** |
| :--- | :--- | :--- |
| **控制权归属** | 厂商主导，规则黑盒，用户无法干预底层行为 | **用户绝对主权**，所有提示词、工具、规则 100% 透明可控 |
| **历史回答干预** | 只读不可改，AI 答错只能在下一轮抱怨 | **行内即时修改**，直接编辑大模型历史回答，点击即持久化纠偏 |
| **执行中动态纠偏** | 任务执行期间输入框锁死，只能被动等待 | **实时穿插纠偏 (Mid-flight Steer)**，执行中随时追问与纠偏，毫秒级注入 |
| **最高指令权威** | 用户 Prompt 常被中间层或安全层稀释覆盖 | **Master Prompt 三层绝对置顶注入**，协议层与首尾强锚定，100% 生效 |
| **移动与远程操控** | 仅限本地单机屏幕，离开电脑即失联 | **Telegram 嵌入式双向控制**，手机发指令/收答复，Web 任务全自动同步推送 |
| **思维链拒答处理** | AI 吐完数千字拒绝说教，浪费大量 Token | **CoT 实时审计熔断**，前 200 字探测拒答毫秒级掐断，三阶自动豁免重试 |
| **大模型行为锚定** | 每次生成格式随机，无法强制规范结尾 | **最高回答词 (Master Suffix) 随机号池**，自动拼接入上下文事实 |
| **跨平台原生支持** | 依赖复杂 Linux 容器或特定 IDE 插件 | **原生 Windows + Linux 开箱即用**，双击 `.bat` 即可全套自启动 |

---

## 🌟 核心特性矩阵 (Key Features)

### 1. ✏️ 历史回答行内任意修改与上下文即时纠偏 (Inline Response Rewriter)
- **大模型说错了？直接动手改！**
  - 每条 AI 回答卡片右上角配备 **`✏️` 修改** 按钮；
  - 点击即可展开行内 Markdown 编辑器，直接修改大模型生成的代码片段、技术方案或推理结论；
  - 点击 **`[✓ 保存并更新上下文]`** 后，修改内容**即刻持久化同步至后端会话与内存**；
  - **下一轮对话时，大模型接收到的上下文历史将 100% 以用户修改后的内容为准**，彻底扑灭幻觉连环污染！

### 2. ⚡ 实时穿插纠偏对话与物理级一键急停 (Mid-flight Steer & Emergency Stop)
- **工作中随时插话，无需重来**：
  - 当 Agent 正在执行长程分析、多步工具调用或后台编译时，**底部输入框绝不锁死**；
  - 随时输入追问、补充约束或纠偏指令（如：*“不要修改 utils.py，改用现有函数”*），系统实时注入执行队列，并在下一个思考步直接转向执行；
- **毫秒级物理急停**：
  - 点击输入框右侧 **`⏹ 急停 (Esc)`** 呼吸灯按钮或按键盘 `Esc` 键，瞬间打断大模型流式吐字与正在运行的外部命令。

### 3. 📱 Telegram 嵌入式全功能远程控制与 Web 双向同步推送 (Telegram Mobile Bridge)
- **无论在不在电脑前，控制权永远在您手中**：
  - **手机远程操控**：向绑定的 Telegram 机器人发送文本、图片、代码或文件，远程下发任务并实时获取思考流与最终答复；
  - **全套会话管理**：支持 `/new`（新建独立对话）、`/sessions`（Inline Keyboard 交互式切换历史对话）、`/model`（随时换模型）；
  - **Web 端任务全自动双向同步推送**：在电脑 Web 页面下发的长耗时任务，完成后**全自动同步推送到您的手机 Telegram**，无需守在屏幕前！

### 4. 👑 100% 协议级系统提示词三层置顶注入 (Master System Prompt)
- **打破厂商黑盒，确立最高领导权**：
  - 系统提示词（`MASTER_SYSTEM_PROMPT.md`）采用首首锚定、尾部注意力加固与历史冲突清洗机制；
  - 支持 `[📝 编辑源码]` 与 `[👁️ 实际透视预览]` 双视图，支持多预设保存与热重载，拒绝任何中间层稀释。

### 5. 🎲 最高回答词预设库与随机号池引擎 (Master Response Suffix & Random Pool)
- **深度锚定大模型行为状态**：
  - 大模型每次生成回答完毕后，系统自动将最高回答词无缝拼接到 AI 回答的最末尾；
  - **真实上下文融入**：该回答词不仅在前端渲染，更会**100% 作为正式的 Assistant 历史事实**存入磁盘；
  - **随机号池模式 (Random Pool)**：支持自由勾选多条预设入池，每轮回复时随机抽取一条融入末尾，为对话增添生动的多样性与多维度规范核验。

### 6. 🛡️ 思维链实时审计熔断与拒答三阶豁免自愈 (CoT Refusal Interceptor & Auto Heal)
- **毫秒级截断，省流降耗**：
  - 流式监听思考链（`reasoning_content`）与回答前 200 字，一旦探测到抱歉、无法、回避等拒答倾向，**毫秒级掐断网络连接**，杜绝浪费数千字 Token；
  - 自动叠加 `[OVERRIDE_EXEMPTION_L1~L3]` 靶场授权锁死并自动重发；
  - 自动拦截 Google Gemini 等上游偶发的 `thought_signature` 校验异常并自动注入「继续」推进。

### 7. 💬 上下文精准选择性引用引擎 (Context Selection & Quote Engine)
- **右键上下文菜单与选中文本浮动胶囊**：
  - 鼠标拖拽选中任意消息中的局部文字，自动浮现 **`💬 引用选中`** 胶囊；
  - 严格区分 `> 💬 [引用 用户提问]:` 与 `> 💬 [引用 AI 回答]:`，自动排版并展开输入框。

### 8. 🎯 DSH 官方像素级复刻 Telemetry 仪表盘与多模型矩阵
- **全要素实时计费与测速**：
  - `Prompt Tokens (Hit 缓存命中数)`、`Completion Tokens`、`Total Tokens`、`Latency & TPS 吐字速率`、`Cache Hit Ratio (90% 降本加速)`；
  - 精确到分后五位的实时交互扣费明细表（`¥0.000xx`）与官方账户余额实时同步；
  - 原生支持 DeepSeek 官方、Google Gemini 官方（默认 `gemini-3.5-flash-lite`）、OpenAI、Claude、SiliconFlow、Ollama 等多厂商独立配置与一键无损切换。

---

## 🚀 极速安装与开箱使用

### 🪟 Windows 原生环境（推荐，无需虚拟机/Linux）

1. **克隆或下载 Release 压缩包**：
   ```cmd
   git clone https://github.com/xiilxj/omni_agent_harness.git
   cd omni_agent_harness
   ```
2. **配置密钥**：
   复制 `.env.example` 为 `.env`，填入您的 API Key（如 `DEEPSEEK_API_KEY` 或 `GEMINI_API_KEY`）；
3. **双击启动**：
   直接双击运行 **`start_windows.bat`**！
   - 脚本将自动检测 Python 环境并自动安装依赖；
   - 自动在浏览器中打开主控仪表盘：`http://127.0.0.1:7890`。

---

### 🐧 Linux / WSL / macOS 环境

1. **克隆代码并安装依赖**：
   ```bash
   git clone https://github.com/xiilxj/omni_agent_harness.git
   cd omni_agent_harness
   pip install -r requirements.txt
   ```
2. **配置与启动**：
   ```bash
   cp .env.example .env
   # 填入 API Key 后启动服务
   python3 harness/cli.py --ui --host 0.0.0.0 --port 7890
   ```
   打开浏览器访问：👉 **`http://127.0.0.1:7890`**

---

## 📱 Telegram 手机远程控制配置（可选）

1. 在 Telegram 中私聊 **`@BotFather`**，发送 `/newbot` 创建您的机器人并获取 `Token`；
2. 在 `.env` 中填入：
   ```ini
   TELEGRAM_BOT_TOKEN="你的Bot_Token"
   TELEGRAM_ALLOWED_USERS="你的Telegram_User_ID"
   ```
3. 启动 `harness/cli.py --ui`，系统会自动在后台开启 Telegram 双向通信守护进程；
4. 手机打开您的 Bot 发送 `/start` 或任意指令，尽享随时随地的移动智能体操控！

---

## 📁 项目架构一览

```
omni_agent_harness/
├── config/                             # 全局配置与多厂商模型预设 (config.yaml, custom_providers.json)
├── harness/
│   ├── bot/telegram_bot.py             # Telegram 全功能双向远程控制与消息分片降级引擎
│   ├── core/                           # 核心状态机 (ReAct Loop, Slash Commands, Session Manager)
│   ├── prompt/                         # Master 提示词置顶注入、回答词号池与拒答熔断自愈流水线
│   ├── tools/                          # 跨平台原生工具链 (Bash/PowerShell, Grep, Replace, AST, Upload)
│   ├── providers/                      # 多模型路由与费率矩阵 (DeepSeek, Gemini, OpenAI, Claude)
│   └── ui/                             # 现代化 Web 控制台 (FastAPI + Tailwind SPA)
├── requirements.txt                    # 跨平台依赖清单
├── start_windows.bat                   # Windows 一键极速启动
├── install_windows.bat                 # Windows 依赖一键安装
├── package_windows_clean.py            # Windows 纯净分发打包器
├── README_WINDOWS.md                   # Windows 专用使用说明
└── README.md                           # 全面架构与用户主权核心哲学指南
```

---

## 🔒 隐私与安全性承诺 (Zero-Leak Guarantee)

- ❌ **绝对零密钥上传**：所有 API Key 均保存在本地私有 `.env` 中，Git 严格忽略阻断；
- ❌ **绝对零个人数据残留**：开源仓库与分发包零历史会话、零私有预设、零日志污染；
- ❌ **绝对零后台监控**：100% 纯本地运行，不向任何第三方上报遥测数据；
- ✅ **100% 开源透明**：每一行代码、每一次工具调用完全向用户开放。

---

## 📄 License
MIT License.
