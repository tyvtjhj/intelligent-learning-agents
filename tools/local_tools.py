import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.tool_spec import ToolSpec
from core.tool_registry import ToolRegistry
from tools.utility_tools import calculator, get_current_time, save_text, read_text
from tools.db_tools import (
    db_list_subjects, db_list_knowledge_points, db_get_question,
    db_search_questions, db_get_mastery_score, db_get_mistake_count,
    db_get_recent_sessions,
)


def register_all_local_tools(registry: ToolRegistry) -> None:
    tools = [
        ToolSpec(
            name="calculator",
            description=(
                "安全计算数学表达式。支持 +-*/%** 运算符和括号。\n"
                "适用场景：练习数值计算。\n"
                "不适用场景：非数学计算。"
            ),
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式, 如 '1+2*3'"}},
                "required": ["expression"],
            },
            function=calculator,
        ),
        ToolSpec(
            name="get_current_time",
            description="获取当前日期和时间（含时区）。\n适用场景：需要知道现在几点、今天几号。",
            parameters={"type": "object", "properties": {}, "required": []},
            function=get_current_time,
        ),
        ToolSpec(
            name="save_text",
            description=(
                "将文本保存到 workspace 目录。\n"
                "适用场景：保存笔记、报告。\n"
                "不适用场景：保存二进制文件。"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "文件名, 如 'notes.txt'"},
                    "content": {"type": "string", "description": "要保存的文本"},
                },
                "required": ["filename", "content"],
            },
            function=save_text,
        ),
        ToolSpec(
            name="read_text",
            description="从 workspace 目录读取文本文件。\n适用场景：读取之前保存的笔记、报告。",
            parameters={
                "type": "object",
                "properties": {"filename": {"type": "string", "description": "要读取的文件名"}},
                "required": ["filename"],
            },
            function=read_text,
        ),
        ToolSpec(
            name="db_list_subjects",
            description="列出所有学科。\n适用场景：开始学习前了解有哪些可用学科。",
            parameters={"type": "object", "properties": {}, "required": []},
            function=db_list_subjects, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_list_knowledge_points",
            description=(
                "列出指定学科的所有知识点（含层级结构）。\n"
                "适用场景：了解某学科的知识体系。"
            ),
            parameters={
                "type": "object",
                "properties": {"subject_id": {"type": "integer", "description": "学科 ID"}},
                "required": ["subject_id"],
            },
            function=db_list_knowledge_points, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_get_question",
            description="查询单个题目的完整信息。\n适用场景：学生要做某道题时。",
            parameters={
                "type": "object",
                "properties": {"question_id": {"type": "integer", "description": "题目 ID"}},
                "required": ["question_id"],
            },
            function=db_get_question, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_search_questions",
            description="按关键词模糊搜索题目。\n适用场景：找某个知识点相关的题目。",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词"},
                    "limit": {"type": "integer", "description": "返回数量上限(默认20)", "default": 20},
                },
                "required": ["keyword"],
            },
            function=db_search_questions, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_get_mastery_score",
            description="查询某知识点的掌握度评分(0.0-1.0)。\n适用场景：了解学生对某个知识点的掌握程度。",
            parameters={
                "type": "object",
                "properties": {"kp_id": {"type": "integer", "description": "知识点 ID"}},
                "required": ["kp_id"],
            },
            function=db_get_mastery_score, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_get_mistake_count",
            description="查询某知识点的错题数量。\n适用场景：了解学生在某知识点的薄弱程度。",
            parameters={
                "type": "object",
                "properties": {"kp_id": {"type": "integer", "description": "知识点 ID"}},
                "required": ["kp_id"],
            },
            function=db_get_mistake_count, source_type="function", source_name="db",
        ),
        ToolSpec(
            name="db_get_recent_sessions",
            description="查询最近的学习会话记录。\n适用场景：了解最近的学习情况。",
            parameters={
                "type": "object",
                "properties": {"limit": {"type": "integer", "description": "返回条数(默认5)", "default": 5}},
                "required": [],
            },
            function=db_get_recent_sessions, source_type="function", source_name="db",
        ),
    ]

    for tool in tools:
        registry.register(tool)
