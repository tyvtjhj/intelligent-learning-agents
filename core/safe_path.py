from pathlib import Path


def safe_path(path_text: str, workspace: Path, write: bool = False) -> Path:
    if not path_text or not path_text.strip():
        raise ValueError("path_text 不能为空")

    resolved = (workspace / path_text).resolve()

    try:
        resolved.relative_to(workspace.resolve())
    except ValueError:
        raise PermissionError(f"路径不在工作区范围内: {path_text} → {resolved}")

    if write:
        resolved.parent.mkdir(parents=True, exist_ok=True)

    return resolved
