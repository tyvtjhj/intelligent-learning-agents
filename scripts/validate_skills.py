import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.adapters.skill_adapter import DANGEROUS_PATTERNS


class AuditResult(NamedTuple):
    passed: bool
    issues: list[str]
    skill_name: str


class SkillAuditor:
    def __init__(self, target_dir: Path):
        self.target_dir = target_dir

    def audit_skill(self, skill_dir: Path) -> AuditResult:
        skill_name = skill_dir.name
        issues: list[str] = []

        skill_md = skill_dir / "SKILL.md"
        catalog_json = skill_dir / "catalog.json"

        if not skill_md.exists():
            sub_skills = list(skill_dir.rglob("SKILL.md"))
            if catalog_json.exists() and len(sub_skills) > 0:
                pass
            elif sub_skills:
                pass
            else:
                issues.append("缺少 SKILL.md 文件")

        content = ""
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")

        for pattern, label in DANGEROUS_PATTERNS:
            if re.search(pattern, content):
                issues.append(f"SKILL.md 中检测到危险模式 [{label}]: {pattern}")

        for py_file in sorted(skill_dir.rglob("*.py")):
            try:
                py_content = py_file.read_text(encoding="utf-8")
                for pattern, label in DANGEROUS_PATTERNS:
                    if re.search(pattern, py_content):
                        issues.append(
                            f"{py_file.name} 中检测到危险模式 [{label}]: {pattern}"
                        )
            except Exception as e:
                issues.append(f"无法读取 {py_file}: {e}")

        for sh_file in sorted(skill_dir.rglob("*.sh")):
            try:
                sh_content = sh_file.read_text(encoding="utf-8")
                if re.search(r"\brm\s+-rf\b", sh_content):
                    issues.append(f"{sh_file.name} 中检测到危险模式 [rm -rf]")
            except Exception as e:
                issues.append(f"无法读取 {sh_file}: {e}")

        return AuditResult(
            passed=len(issues) == 0,
            issues=issues,
            skill_name=skill_name,
        )

    def audit_all(self) -> list[AuditResult]:
        results: list[AuditResult] = []
        if not self.target_dir.exists():
            return results

        for skill_dir in sorted(self.target_dir.iterdir()):
            if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                result = self.audit_skill(skill_dir)
                results.append(result)

        return results


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else project_root / "installed_external_skills"
    auditor = SkillAuditor(target)

    print(f"审查目录: {target}")
    print(f"{'='*60}")

    results = auditor.audit_all()
    passed_count = 0
    failed_count = 0

    for r in results:
        status = "✅ 通过" if r.passed else "❌ 未通过"
        if r.passed:
            passed_count += 1
        else:
            failed_count += 1

        print(f"\n[{status}] {r.skill_name}")
        if r.issues:
            for issue in r.issues:
                print(f"  - {issue}")

    print(f"\n{'='*60}")
    print(f"审查完成: {passed_count} 通过 / {failed_count} 未通过 / {len(results)} 总计")

    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
