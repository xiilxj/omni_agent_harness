# Omni Agent Harness (Codex-DSH Core)

<p align="center">
  <b>基于 OpenAI Codex 与 DeepSeek Harness (DSH) 核心架构深度改造的工业级智能体底座</b><br>
  <i>100% 协议级系统提示词注入 ｜ 5 档真实推理强度 ｜ 纯净用户自主预设中心 ｜ 跨平台 Linux & Windows 原生支持</i>
</p>

---

## 🌟 核心特性与亮点

- 🛡️ **100% 协议级系统提示词注入 (Master System Prompt)**：首条 `system` 消息置顶锁死，拒绝任何中间层稀释与冲突。
- 🎨 **纯净用户自主提示词中心 (Transparent Visual Preset Center)**：
  - 初始 100% 纯白留白，零内置黑盒预设，完全由用户自主编写与管理。
  - 支持多预设保存、实时动态状态指示器（`已激活` vs `已修改/未存`）、二级菜单一键覆盖更新。
  - `[📝 源码编辑]` 与 `[👁️ 实际透视预览]` 双视图，彻底消除黑盒。
- 🧠 **5 档真实推理强度 (5-Tier Reasoning Intensity)**：
  - `Off (0 Token)` $\rightarrow$ `Low (2k)` $\rightarrow$ `Med (8k - 默认)` $\rightarrow$ `High (16k)` $\rightarrow$ `Max (32k 极限推演)`。
- 🛠️ **DSH 4 大模型档位 & 3 大权限控制**：
  - 模型档位：`⚡ Flash` / `🛠️ Pro` / `🧠 Reasoner` / `👁️ Vision`。
  - 权限模式：`🔓 Unrestricted (无限制自主)` / `🛡️ Controlled (受控审批)` / `🔒 Read-Only (只读审查)`。
- 🗂️ **会话管理、自主重命名与归档**：
  - 自动智能取名 + ✏️ 手动重命名，支持「Active / Archived」双分类子视图与一键恢复。
- ⚡ **DSH 规范级 Prompt Cache 优化**：工具字典序稳定排布，前缀 100% 字节级冻结，实测命中率 **93.1%+**，推理速度高达 **106~116 t/s**。
- 💰 **真实账户余额实时同步**：直连 DeepSeek 官方余额接口，任务完成自动刷新剩余额度。

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
# 编辑 .env 填入您的 DeepSeek API Key (或在 Web 界面中直接填写)
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
│   ├── core/                           # 核心状态机 (Agent ReAct Loop, Config, Session)
│   ├── prompt/                         # 100% Master 提示词注入与预设管理器
│   ├── tools/                          # 跨平台工具箱 (Bash, PowerShell, Grep, Replace)
│   ├── providers/                      # 多模型适配层 (DeepSeek, OpenAI, Anthropic)
│   └── ui/                             # 现代化 Web 控制台 (FastAPI + Tailwind SPA)
├── requirements.txt                    # 跨平台标准依赖清单
├── start_windows.bat                   # Windows 一键启动批处理
├── install_windows.bat                 # Windows 依赖安装批处理
├── README_WINDOWS.md                   # Windows 专用说明文档
├── README.md                           # 全局主说明文档
└── .env.example                        # 环境变量模板
```

---

## 📄 License
MIT License.
