import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
target_dir = project_root / "installed_external_skills"
target_dir.mkdir(exist_ok=True)

SKILLS = [
    {
        "name": "feynman_tutor",
        "repo": "https://github.com/wangsiyi7/feynman-tutor.git",
        "target": target_dir / "feynman_tutor",
    },
    {
        "name": "sigma",
        "repo": "https://github.com/sanyuan0704/sanyuan-skills.git",
        "target": target_dir / "sigma",
        "sparse_path": "skills/sigma",
    },
    {
        "name": "hermes_edu",
        "repo": "https://github.com/hezkvectory/hermes-edu-skills.git",
        "target": target_dir / "hermes_edu",
    },
]


def clone(skill: dict) -> bool:
    print(f"\n[INFO] 克隆 {skill['name']}: {skill['repo']}")

    if skill["target"].exists():
        print(f"  [SKIP] 目录已存在, 跳过克隆")
        return True

    if "sparse_path" in skill:
        return _sparse_clone(skill)

    try:
        subprocess.run(
            ["git", "clone", skill["repo"], str(skill["target"])],
            check=True, capture_output=True, text=True,
        )
        print(f"  [OK] 克隆成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] 克隆失败: {e.stderr}")
        return False


def _sparse_clone(skill: dict) -> bool:
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
             skill["repo"], str(skill["target"])],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "-C", str(skill["target"]), "sparse-checkout", "set", skill["sparse_path"]],
            check=True, capture_output=True, text=True,
        )
        src = skill["target"] / skill["sparse_path"]
        if src.exists():
            for item in src.iterdir():
                dest = skill["target"] / item.name
                if not dest.exists():
                    item.rename(dest)
            import shutil
            shutil.rmtree(src.parent, ignore_errors=True)
        print(f"  [OK] 稀疏克隆成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] 稀疏克隆失败: {e.stderr}")
        return False


def main():
    all_ok = True
    for skill in SKILLS:
        if not clone(skill):
            all_ok = False

    if all_ok:
        print(f"\n[OK] 所有外部 Skill 安装完成")
    else:
        print(f"\n[WARN] 部分 Skill 安装失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
