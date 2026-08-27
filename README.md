# Omni Agent Harness

<p align="center">
  <img src="https://img.shields.io/badge/Author-15%20y/o%20Student-blueviolet?style=flat-square" alt="Author" />
  <img src="https://img.shields.io/badge/Architecture-DSH%20Native%20Aligned-blue?style=flat-square&logo=deepseek" alt="DSH Aligned" />
  <img src="https://img.shields.io/badge/Philosophy-User%20Sovereignty%20First-emerald?style=flat-square" alt="User Sovereignty First" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=flat-square" alt="Cross Platform" />
  <img src="https://img.shields.io/badge/Tests-44%20Passed%20(100%25)-brightgreen?style=flat-square" alt="Tests" />
</p>

<p align="center">
  <b>面向开发者的高自主权、轻量级本地 AI Agent 执行与交互工作台</b><br>
  <i>大模型历史回答行内修改 ｜ 任务执行中动态插话纠偏 ｜ Telegram 双向远程交互 ｜ 跨平台原生开箱即用</i>
</p>

---

## 📌 项目概述 (Overview)

**Omni Agent Harness** 是一款基于开源 **DSH (DeepSeek Harness)** 架构与 OpenAI Codex 理念深度重构的轻量级 AI Agent 执行底座。

该项目的核心目标是**打破商业 Agent 的黑盒限制，将对大模型的提示词主权、历史上下文修改权、任务执行干预权与多端消息调度权完全交还给使用者**。

---

## 💡 设计理念与痛点解决 (Design Philosophy)

在传统商业 AI 编程助手（如 Cursor、Copilot、各类闭源 Agent）的实际使用场景中，普遍存在以下交互痛点：

| 常见痛点 | 商业/传统 Agent 表现 | Omni Agent Harness 解决方案 |
| :--- | :--- | :--- |
| **大模型答错后的纠偏** | 只读不可改，用户只能在下一轮反复补充解释，易造成上下文二次污染 | **行内即时修改**：直接在网页卡片编辑大模型历史回答，点击即持久化同步至后端上下文 |
| **长任务执行中的干预** | 任务执行期间输入框强制锁死，方向偏离时只能等待结束或强制中止 | **实时穿插纠偏 (Mid-flight Steer)**：输入框全程可用，随时输入补充指令并在下一步动态注入 |
| **底层提示词透明度** | 底层强行注入大量预设规则与安全围栏，用户 Prompt 容易被稀释 | **Master Prompt 协议层置顶**：提供纯净留白模板，首尾双锚定，确保用户指令拥有最高权威 |
| **跨设备移动协同** | 离开电脑后长任务进度断联，无法及时获知结果 | **Telegram 嵌入式双向控制**：手机可远程下发任务，Web 端耗时任务完成后自动向手机推送答复 |
| **思维链拒答消耗** | 大模型产生拒绝回避倾向时仍吐出大量说教文本，浪费 Token | **CoT 实时审计截断**：前 200 字探测拒答倾向毫秒级掐断网络流，自动追加沙箱授权重发 |

---

## 🛠️ 核心功能矩阵 (Core Features)

### 1. ✏️ 历史回答行内自主修改 (Inline Response Rewriter)
- 每条 AI 回答卡片均配备行内编辑控件；
- 用户可直接修正大模型输出的代码片段、数据或技术方案；
- 保存后直接同步更新磁盘会话与内存，**后续轮次大模型将 100% 基于修改后的内容进行推理**，根除幻觉连环污染。

### 2. ⚡ 执行中动态插话纠偏 (Mid-flight Steer) 与物理急停 (Esc)
- Agent 执行多步工具调用或长程分析期间，底部输入框保持可用；
- 用户可随时输入追加约束或调整建议，系统在下一推理步自动合流；
- 支持键盘 `Esc` 键物理级瞬时打断流式生成与外部命令执行。

### 3. 📱 Telegram 全双工远程交互与 Web 完成通知 (Mobile Bridge)
- **远程任务下发**：通过绑定的 Telegram Bot 远程发送文本、图片或文件指令，实时查看推理流与终答；
- **Web 任务自动同步**：在电脑 Web 端执行的长耗时任务，完成后自动将结果推送至管理员手机 Telegram；
- 支持 `/new`（新建会话）、`/sessions`（交互式切换历史对话）、`/model`（在线切换模型）。

### 4. 👑 Master 系统提示词置顶注入与最高回答词 (Master Suffix)
- **置顶系统提示词**：支持在线编辑 `MASTER_SYSTEM_PROMPT.md`，首首锚定与尾部注意力加固；
- **最高回答词引擎**：支持在每轮 AI 回复末尾固定或随机（号池轮换）注入自定义签结词，并深度融入会话事实。

### 5. 🛡️ 思考链拒答审计与 Gemini 异常自愈
- 流式接收思考链时进行轻量级语义审计，探测到拒绝倾向毫秒级中断并三阶递进追加沙箱授权；
- 自动适配 Google Gemini 系列模型的 `thought_signature` 校验机制并实现自动推进。

### 6. 📊 实时 Telemetry 测速与计费清单
- 实时统计 Prompt Tokens（含缓存命中数，命中节省 90% 成本）、Completion Tokens、TPS 速率；
- 按官方费率精准核算单次交互费用与会话累计支出；
- 支持 DeepSeek 官方、Google Gemini（推荐 `gemini-3.5-flash-lite`）、OpenAI、Claude、SiliconFlow、本地 Ollama 等多厂商独立配置与一键切换。

### 7. 💻 Windows / Linux / macOS 跨平台原生支持
- 原生兼容 Windows PowerShell、CMD 与 Linux Bash 工具链；
- Windows 环境无需 WSL 或 Docker，双击即可拉起完整服务。

---

## 🚀 快速上手指南 (Quick Start)

### 🪟 Windows 原生运行

1. **获取代码**：
   ```cmd
   git clone https://github.com/xiilxj/omni_agent_harness.git
   cd omni_agent_harness
   ```
2. **配置密钥**：
   复制 `.env.example` 为 `.env`，填入您的 API Key（如 `DEEPSEEK_API_KEY` 或 `GEMINI_API_KEY`）；
3. **一键启动**：
   双击运行 **`start_windows.bat`**。脚本将自动检测环境、安装依赖并在浏览器中打开控制台：
   👉 **`http://127.0.0.1:7890`**

---

### 🐧 Linux / macOS 运行

1. **克隆仓库并安装依赖**：
   ```bash
   git clone https://github.com/xiilxj/omni_agent_harness.git
   cd omni_agent_harness
   pip install -r requirements.txt
   ```
2. **配置并启动**：
   ```bash
   cp .env.example .env
   # 在 .env 中填入 API Key
   python3 harness/cli.py --ui --host 0.0.0.0 --port 7890
   ```
   浏览器访问：👉 **`http://127.0.0.1:7890`**

---

## 📱 Telegram 远程控制配置（可选）

1. 在 Telegram 私聊 **`@BotFather`**，通过 `/newbot` 创建机器人并获取 `Token`；
2. 在 `.env` 中配置：
   ```ini
   TELEGRAM_BOT_TOKEN="你的Bot_Token"
   TELEGRAM_ALLOWED_USERS="你的Telegram_数字User_ID"
   ```
3. 启动项目后，后台自动拉起 Telegram 守护进程，手机端发送 `/start` 即可交互。

---

## ℹ️ 关于项目与作者 (About the Project)

- **项目起源**：本项目由一名 **15 岁的准高一学生** 在课余时间基于对大模型智能体架构的兴趣独立主导设计与开发；
- **开发初衷**：旨在探索一套轻量、纯净且能将全流程控制权归还给使用者的个人 Agent 工作台架构；
- **工程局限**：作为课余开源项目，工程实现与前端架构以轻量单机、零编译开箱即用为导向（原生 HTML + Tailwind + JS），未引入复杂重型框架；
- **社区交流**：项目保持开源开放，欢迎技术同行与开发者提出 Issue 交流与 PR 建议。

---

## 🔒 隐私与安全性规范 (Privacy & Security)

- **零密钥外发**：所有 API Key 及用户自定提示词均保存在本地私有文件内，并已加入 `.gitignore`，绝不向远程仓库提交；
- **纯本地运行**：程序完全运行于用户本地机器，不包含任何第三方数据采集或遥测上报；
- **完全开源透明**：所有工具调用逻辑与提示词处理机制完全开源可见。

---

## 📄 开源协议 (License)
本项目采用 [MIT License](LICENSE) 开源。

