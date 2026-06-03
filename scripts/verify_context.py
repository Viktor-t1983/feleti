#!/usr/bin/env python3
"""verify_context.py — проверка целостности контекста проекта.

Запускать в начале и в конце каждой сессии.
Проверяет:
- Обязательные файлы на месте
- Git репозиторий инициализирован
- Docker compose валиден
- Backend парсится (AST)
- Alembic миграции не сломаны
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# Обязательные файлы контекста
# ============================================================
REQUIRED_FILES = [
    ".opencode/AGENTS.md",
    "docs/PROJECT_BOOT.md",
    "docs/ARCHITECTURE.md",
    "docs/CONTEXT_HANDOFF.md",
    "CHANGELOG.md",
    "TODO.md",
    "docs/SKILL_DEV.md",
    "docs/SKILL_SMOKING.md",
]

# ============================================================
# Обязательные директории
# ============================================================
REQUIRED_DIRS = [
    ".opencode/skills",
    "backend/app",
    "backend/app/models",
    "backend/app/api",
    "backend/app/services",
    "docs",
]

# ============================================================
# Цвета для терминала
# ============================================================
OK = "\033[92mOK\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"

errors = 0
warnings = 0


def check(msg: str, condition: bool) -> None:
    global errors
    if condition:
        print(f"  {OK} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        errors += 1


def warn(msg: str, condition: bool) -> None:
    global warnings
    if condition:
        print(f"  {OK} {msg}")
    else:
        print(f"  {WARN} {msg}")
        warnings += 1


def check_files() -> None:
    print("\n[1] Обязательные файлы контекста:")
    for rel in REQUIRED_FILES:
        path = PROJECT_ROOT / rel
        check(rel, path.exists())


def check_dirs() -> None:
    print("\n[2] Обязательные директории:")
    for rel in REQUIRED_DIRS:
        path = PROJECT_ROOT / rel
        check(rel, path.is_dir())


def check_git() -> None:
    print("\n[3] Git репозиторий:")
    git_dir = PROJECT_ROOT / ".git"
    check(".git/ инициализирован", git_dir.is_dir())

    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "log", "--oneline", "-1"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(f"  {OK} Последний коммит: {result.stdout.strip()}")
    else:
        check("Есть хотя бы 1 коммит", False)

    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "status", "--short"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        warn("Незакоммиченные изменения", False)
        for line in result.stdout.strip().split("\n")[:5]:
            print(f"      {line}")
        if result.stdout.count("\n") > 5:
            print(f"      ... и ещё {result.stdout.count(chr(10)) - 5} файлов")
    else:
        print(f"  {OK} Рабочая директория чиста")


def check_docker() -> None:
    print("\n[4] Docker Compose:")
    compose_file = PROJECT_ROOT / "docker-compose.yml"
    check("docker-compose.yml существует", compose_file.exists())

    result = subprocess.run(
        ["docker", "compose", "config"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    check("docker compose config валиден", result.returncode == 0)
    if result.returncode != 0:
        print(f"      {result.stderr.strip()}")


def check_backend_ast() -> None:
    print("\n[5] Backend Python AST:")
    py_files = list((PROJECT_ROOT / "backend" / "app").rglob("*.py"))
    bad = []
    for f in py_files:
        try:
            ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad.append((f.relative_to(PROJECT_ROOT), exc.lineno))

    check(f"Все {len(py_files)} .py файлы парсятся (AST)", len(bad) == 0)
    for path, line in bad:
        print(f"      {FAIL} {path}:{line}")


def check_alembic() -> None:
    print("\n[6] Alembic миграции:")
    versions_dir = PROJECT_ROOT / "backend" / "alembic" / "versions"
    if versions_dir.exists():
        migrations = list(versions_dir.glob("*.py"))
        check(f"Миграции найдены ({len(migrations)})", len(migrations) > 0)
    else:
        check("Директория alembic/versions/", False)


def check_skills() -> None:
    print("\n[7] SKILL.md файлы:")
    skills_dir = PROJECT_ROOT / ".opencode" / "skills"
    if skills_dir.exists():
        skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]
        check(f"Найдено {len(skills)} скиллов", len(skills) >= 10)
        # Проверим, что в каждом есть SKILL.md
        incomplete = [s for s in skills if not (skills_dir / s / "SKILL.md").exists()]
        check("Все скиллы имеют SKILL.md", len(incomplete) == 0)
        for s in incomplete:
            print(f"      {FAIL} {s}/SKILL.md отсутствует")
    else:
        check("Директория .opencode/skills/", False)


def check_history() -> None:
    print("\n[8] Session history:")
    history_dir = PROJECT_ROOT / ".opencode" / "session" / "history"
    if history_dir.exists():
        files = sorted(history_dir.glob("*.md"))
        check(f"История сессий ({len(files)} файлов)", len(files) > 0)
        if files:
            print(f"      Последний: {files[-1].name}")
    else:
        warn("Директория .opencode/session/history/ не найдена", False)


def main() -> int:
    print("=" * 60)
    print("  FELETI-SMOK — verify_context.py")
    print("  Проверка целостности контекста проекта")
    print("=" * 60)

    check_files()
    check_dirs()
    check_git()
    check_docker()
    check_backend_ast()
    check_alembic()
    check_skills()
    check_history()

    print("\n" + "=" * 60)
    if errors == 0 and warnings == 0:
        print(f"  {OK} ВСЁ ХОРОШО — контекст целостен")
        print("=" * 60)
        return 0
    elif errors == 0:
        print(f"  {WARN} ПРЕДУПРЕЖДЕНИЯ: {warnings} (не критично)")
        print("=" * 60)
        return 0
    else:
        print(f"  {FAIL} ОШИБКИ: {errors}, ПРЕДУПРЕЖДЕНИЯ: {warnings}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
