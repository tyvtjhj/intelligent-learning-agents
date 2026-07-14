import ast
import operator
from datetime import datetime, timezone, timedelta


def calculator(expression: str) -> dict:
    ALLOWED_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }

    def _safe_eval_node(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](
                _safe_eval_node(node.left), _safe_eval_node(node.right)
            )
        if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPS:
            return ALLOWED_OPS[type(node.op)](_safe_eval_node(node.operand))
        raise ValueError(f"不支持的运算: {type(node).__name__}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval_node(tree.body)
        return {"ok": True, "result": result, "expression": expression}
    except Exception as e:
        return {"ok": False, "error": str(e), "expression": expression}


def get_current_time() -> dict:
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    return {
        "ok": True,
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "weekday": now.strftime("%A"),
    }


def save_text(filename: str, content: str) -> dict:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.safe_path import safe_path

    workspace = project_root / "workspace"
    try:
        target = safe_path(filename, workspace, write=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(target.relative_to(workspace)), "size": len(content)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def read_text(filename: str) -> dict:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from core.safe_path import safe_path

    workspace = project_root / "workspace"
    try:
        target = safe_path(filename, workspace, write=False)
        content = target.read_text(encoding="utf-8")
        return {"ok": True, "content": content, "path": str(target.relative_to(workspace)), "size": len(content)}
    except FileNotFoundError:
        return {"ok": False, "error": f"文件不存在: {filename}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
