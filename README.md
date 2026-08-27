# Omni Agent Harness

<p align="center">
  <img src="https://img.shields.io/badge/Author-15%20y/o%20High%20Schooler-blueviolet?style=flat-square" alt="Author" />
  <img src="https://img.shields.io/badge/Architecture-DSH%20Aligned-blue?style=flat-square&logo=deepseek" alt="DSH Aligned" />
  <img src="https://img.shields.io/badge/Focus-User%20Control%20First-emerald?style=flat-square" alt="User Control First" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=flat-square" alt="Cross Platform" />
  <img src="https://img.shields.io/badge/Tests-44%20Passed-brightgreen?style=flat-square" alt="Tests" />
</p>

<p align="center">
  <b>一个把「提示词主权、历史记忆修改权、执行纠偏权」完全还给用户的轻量级开源 AI Agent 执行底座</b><br>
  <i>支持修改大模型历史回答 ｜ 执行中动态插话纠偏 ｜ Telegram 双向远程控制 ｜ 跨平台一键开箱</i>
</p>

---

## 👦 关于作者与立项初衷

大家好！我是一名 **15 岁的准高一学生**。平时非常热爱编程、Linux 与大模型技术，在课余时间里喜欢探索各种开源智能体（Agent）和工具链。

### 为什么要做这个项目？

在日常使用各种 AI 编程助手和商业 Agent（如 Cursor、Copilot、各种闭源助手）的过程中，我遇到了一些很让我头疼的实际痛点：

1. **大模型说错了不能直接改**：大模型如果在前几轮输出了有误的代码或理解偏差，后续对话往往会被旧错误一直误导。商业工具往往只能在下一轮反复发提示词解释，不仅浪费 Token 还容易越抹越黑，最后只能无奈清空重来；
2. **长任务执行期间完全无法插话**：当 Agent 在跑多步分析或耗时任务时，输入框往往被彻底锁死。如果看到大模型执行方向偏了，只能干瞪眼等它跑完或者强制中止全部重来；
3. **底层提示词不透明**：很多商业产品底层会偷偷注入成百上千行的安全规则或行为框架，用户自己写的 Prompt 常常被稀释；
4. **离开电脑就无法继续跟进**：下发耗时几分钟的复杂任务后离开桌前，没办法在手机上及时看到最终结果，也没办法用手机临时给电脑派活。

为了解决这些痛点，我参考了开源的 **DSH (DeepSeek Harness)** 架构与 OpenAI Codex 的设计思路，用 Python (FastAPI) + 原生 Web 前端写了这个 **Omni Agent Harness**。

这个项目的核心想法很简单：**不做黑盒，把关于大模型的一切控制权（提示词、历史上下文、中途插话纠偏、远程消息收发）完完全全交还给使用者自己。**

---

## 🛠️ 目前已经实现的核心功能

### 1. ✏️ 大模型历史回答行内任意修改 (Inline Response Rewriter)
- 每条 AI 回答卡片右上角都有一个 `✏️` 修改图标；
- 如果大模型生成的代码有小 Bug 或表述不准确，**你可以直接在网页上编辑修改它的回答**；
- 点击「保存并更新上下文」后，修改内容会直接持久化写入后端会话。**下一轮对话时，大模型接收到的历史上下文将完全以你修改后的版本为准**，避免幻觉连环污染。

### 2. ⚡ 任务执行中随时插话纠偏 (Mid-flight Steer) 与急停 (Esc)
- 当 Agent 正在执行长程分析、多步工具调用或终端命令时，**底部输入框不会被锁死**；
- 你可以随时输入新的补充要求或纠偏指令（如：*“刚才那个文件别改了，换一种思路”*），系统会在下一个思考步动态注入，直接调整后续执行方向；
- 配备物理级急停按钮（按键盘 `Esc` 即可瞬间打断当前流式生成与工具执行）。

### 3. 📱 Telegram 手机端双向远程控制与 Web 完成通知
- **手机下发任务**：在手机 Telegram 给你的专属 Bot 发送文字、图片或文件，远程下发任务并接收实时思考流与最终答复；
- **Web 端任务自动同步到手机**：在电脑 Web 页面提交了长耗时任务后即使离开电脑，任务完成后系统会**全自动把最终答复推送到你的手机 Telegram**；
- 支持 `/new`（新建对话）、`/sessions`（交互式切换历史对话）、`/model`（切换模型）。

### 4. 👑 Master 置顶系统提示词与最高回答词 (Master Suffix)
- **纯净自主提示词**：支持在 Web 界面随时编写置顶系统提示词（`MASTER_SYSTEM_PROMPT.md`），保证用户指令处于最高优先级；
- **回答词号池**：支持配置最高回答词（支持固定模式与随机号池模式），自动在每轮 AI 回复末尾附加并写入真实会话历史。

### 5. 🛡️ 思考链拒答拦截与 Gemini 异常自愈
- 在流式接收思考链的前 200 字内做轻量级的拒答倾向检测，一旦检测到道歉回避，快速掐断流以节省 Token，并自动尝试追加沙箱执行授权重试；
- 针对 Google Gemini 等上游偶发的 `thought_signature` 校验异常，自动注入指令自愈推进。

### 6. 📊 实时 Telemetry 测速与计费展示
- 实时统计 Prompt Tokens（含缓存命中数，命中节省 90% 成本）、Completion Tokens、吐字速度（TPS）以及按官方费率估算的本次扣费与累计消耗；
- 支持主流多厂商自由切换：DeepSeek 官方、Google Gemini（默认推荐 `gemini-3.5-flash-lite`）、OpenAI、Claude、SiliconFlow、本地 Ollama 等。

### 7. 💻 Windows / Linux / macOS 跨平台原生支持
- 原生兼容 Windows PowerShell 与 Linux Bash 工具链；
- Windows 用户无需配置 WSL 或虚拟机，直接双击 `start_windows.bat` 即可开箱自启动。

---

## ⚠️ 诚实说明：目前的已知局限性

1. **个人课余作品**：本项目主要由我利用业余时间开发，架构与代码风格可能不如大厂成熟工程完备，如果遇到 Bug 欢迎随时提 Issue，我会尽快修复；
2. **前端架构追求轻量**：前端采用单文件 HTML + Tailwind CSS + 原生 JavaScript 实现，未引入大型前端构建流程（如 React/Vue），更注重单机轻量与免编译开箱即用；
3. **网络与 API 依赖**：工具本身不自带模型权重，需连接外部大模型 API（如 DeepSeek、Gemini 或本地 Ollama 服务）。

---

## 🚀 极速安装与使用指南

### 🪟 Windows 原生使用（推荐，无需 Linux/WSL）

1. **下载或克隆项目**：
   ```cmd
   git clone https://github.com/xiilxj/omni_agent_harness.git
   cd omni_agent_harness
   ```
2. **配置 API 密钥**：
   将 `.env.example` 复制为 `.env`，填入你的 API Key（例如 `DEEPSEEK_API_KEY` 或 `GEMINI_API_KEY`）；
3. **一键运行**：
   **直接双击运行 `start_windows.bat`**。脚本会自动检查 Python 环境、安装依赖并在浏览器中打开控制台：
   👉 **`http://127.0.0.1:7890`**

---

### 🐧 Linux / macOS 使用

1. **克隆代码与安装依赖**：
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

## 📱 Telegram 手机控制配置步骤（可选）

1. 在 Telegram 私聊 **`@BotFather`**，输入 `/newbot` 创建一个机器人并获取 `Token`；
2. 在 `.env` 中填写：
   ```ini
   TELEGRAM_BOT_TOKEN="你的Bot_Token"
   TELEGRAM_ALLOWED_USERS="你的Telegram_数字User_ID"
   ```
3. 启动项目后，后台会自动拉起 Telegram 监听。在手机上向 Bot 发送 `/start` 即可开始使用。

---

## 🔒 隐私与开源声明

- **零密钥上传**：所有 API Key 和用户编写的本地私有提示词均保存在本地 `.env` 与本地文件中，已全部加入 `.gitignore`，绝不上传远程仓库；
- **纯本地运行**：100% 本地运行，不收集任何用户使用数据或遥测上报；
- **欢迎指点交流**：如果你觉得这个小工具有点意思，或者在代码里发现了可以写得更好的地方，非常欢迎提交 Issue 或 PR，感谢各位前辈的包容与支持！

---

## 📄 License
MIT License.

