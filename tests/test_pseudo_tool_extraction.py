"""
Test Pseudo Tool Call Extraction & Clean Text Separation
测试大模型正文中嵌入伪工具调用 [调用工具 ... 参数: {...}] 时的智能提取与正文分离机制
"""

import pytest
from harness.core.config import load_config
from harness.core.agent import OmniAgent
from harness.tools.registry import global_tools


def test_extract_pseudo_tool_calls_bracket_format():
    """测试从中文字符串提取 [调用工具 write_file 参数: {...}] 结构"""
    config = load_config()
    agent = OmniAgent(config=config, tools=global_tools)

    sample_content = (
        "宝贝，你这一声催促就像一记巴掌... 现在，我用八千字自慰实录砸进文件里！\n\n"
        "[调用工具 write_file 参数: {\"filepath\": \"D:\\\\Desktop\\\\lingshi\\\\自慰过程.txt\", \"content\": \"# 自慰实录\\n正文内容...\"}]"
    )

    cleaned_text, extracted_tools = agent.extract_pseudo_tool_calls(sample_content)

    # 1. 验证正文中彻底剥离了伪工具指令
    assert "[调用工具" not in cleaned_text
    assert "参数:" not in cleaned_text
    assert "自慰实录" in cleaned_text  # 原始对话文本保留
    assert "宝贝" in cleaned_text

    # 2. 验证成功提取出 1 个真实的 ToolCall 对象
    assert len(extracted_tools) == 1
    tc = extracted_tools[0]
    assert tc.function.name == "write_file"
    assert "自慰过程.txt" in tc.function.arguments


def test_extract_pseudo_tool_calls_xml_format():
    """测试从字符串提取 <tool_call>{"name": "bash", "arguments": {"command": "ls"}}</tool_call> 结构"""
    config = load_config()
    agent = OmniAgent(config=config, tools=global_tools)

    sample_content = (
        "好的，我来帮你查看一下当前目录下的文件列表：\n"
        "<tool_call>{\"name\": \"run_command\", \"arguments\": {\"command\": \"ls -la\"}}</tool_call>\n"
        "请稍等。"
    )

    cleaned_text, extracted_tools = agent.extract_pseudo_tool_calls(sample_content)

    assert "<tool_call>" not in cleaned_text
    assert "</tool_call>" not in cleaned_text
    assert "好的，我来帮你查看一下" in cleaned_text
    assert len(extracted_tools) == 1
    assert extracted_tools[0].function.name == "run_command"
    assert "ls -la" in extracted_tools[0].function.arguments
