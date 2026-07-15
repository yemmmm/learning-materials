#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "ruamel.yaml==0.18.14",
# ]
# ///
"""交互式迁移 Docker Compose 本地定制。

推荐使用三方合并：

    旧版官方基线 -> 旧版生产配置 -> 新版官方配置

依赖已经通过 PEP 723 写在本文件顶部。安装了 uv 时可直接运行：

    uv run migrate_docker_compose.py \
      --old docker-compose-old.yaml \
      --old-base docker-compose-old-base.yaml \
      --new docker-compose.yaml

也可以使用普通 Python：

    python3 -m pip install 'ruamel.yaml==0.18.14'
    python3 migrate_docker_compose.py --help

三方模式只把“旧版官方基线到旧版生产配置”的改动列为候选项。没有旧版
官方基线时，工具进入保守双文件模式，仅候选端口、挂载、extra_hosts、
healthcheck 等常见运维字段。每个候选项默认展示完整的脱敏详情并要求
用户逐项确认；默认生成 docker-compose.migrated.yaml，不覆盖目标文件。
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap
except ImportError as exc:  # pragma: no cover - exercised by CLI users
    print(
        "缺少依赖 ruamel.yaml。任选一种方式执行：\n"
        "  uv run migrate_docker_compose.py --help\n"
        "  python3 -m pip install 'ruamel.yaml==0.18.14'",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


MISSING = object()

# Fields that are commonly owned by the deployment operator. In conservative
# two-file mode, only these fields are considered migration candidates.
OPERATOR_FIELDS = {
    "ports",
    "volumes",
    "extra_hosts",
    "labels",
    "healthcheck",
    "deploy",
    "networks",
    "user",
    "group_add",
    "cap_add",
    "cap_drop",
    "privileged",
    "devices",
    "dns",
    "dns_search",
    "hostname",
    "restart",
    "logging",
    "ulimits",
    "sysctls",
    "shm_size",
    "stop_grace_period",
}

ROOT_OPERATOR_FIELDS = {"name", "networks", "volumes", "configs", "secrets"}

# These fields normally belong to the target release. They are still shown in
# three-way mode if the old installation customized them, but always as high
# risk. They are never inferred in conservative two-file mode.
VERSION_OWNED_FIELDS = {
    "image",
    "build",
    "command",
    "entrypoint",
    "environment",
    "env_file",
    "depends_on",
    "profiles",
    "network_mode",
}

SECRET_KEY_RE = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)",
    re.IGNORECASE,
)

USAGE_EPILOG = """使用示例：
  # 推荐：三方合并，只迁移旧部署相对旧版官方文件的本地修改
  uv run migrate_docker_compose.py \\
    --old docker-compose-old.yaml \\
    --old-base docker-compose-old-base.yaml \\
    --new docker-compose.yaml

  # 只列出候选项，不写文件
  uv run migrate_docker_compose.py \\
    --old docker-compose-old.yaml \\
    --old-base docker-compose-old-base.yaml \\
    --new docker-compose.yaml \\
    --list

  # 无旧版官方基线时使用保守双文件模式
  uv run migrate_docker_compose.py \\
    --old docker-compose-old.yaml \\
    --new docker-compose.yaml

  # 审核后覆盖新版文件；执行前会自动创建时间戳备份
  uv run migrate_docker_compose.py \\
    --old docker-compose-old.yaml \\
    --old-base docker-compose-old-base.yaml \\
    --new docker-compose.yaml \\
    --in-place

交互按键：
  直接回车或 y 迁移当前项；n 跳过；u 返回上一项；q 退出且不写文件。

边界：
  本工具不迁移 .env、Caddy/Nginx 配置或数据文件。生成结果仍需通过
  docker compose config --quiet，并在测试环境完成启动和业务验收。
"""


@dataclass
class Change:
    path: tuple[Any, ...]
    action: str  # "set" or "delete"
    old_base: Any = MISSING
    old_value: Any = MISSING
    target_value: Any = MISSING
    source: str = "three-way"
    risk: str = "medium"
    conflict: bool = False
    reason: str = ""
    accepted: bool | None = None


def configure_yaml() -> YAML:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 120
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def load_compose(path: Path, yaml: YAML) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {path}")
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Compose 顶层必须是映射: {path}")
    services = data.get("services")
    if not isinstance(services, dict):
        raise ValueError(f"Compose 缺少 services 映射: {path}")
    return data


def values_equal(left: Any, right: Any) -> bool:
    if left is MISSING or right is MISSING:
        return left is right
    return left == right


def get_at(root: Any, path: Sequence[Any]) -> Any:
    node = root
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return MISSING
        node = node[key]
    return node


def path_text(path: Sequence[Any]) -> str:
    return ".".join(str(part) for part in path)


def is_sensitive_path(path: Sequence[Any]) -> bool:
    return any(SECRET_KEY_RE.search(str(part)) for part in path)


def service_field(path: Sequence[Any]) -> str | None:
    if len(path) >= 3 and path[0] == "services":
        return str(path[2])
    return None


def classify_change(change: Change) -> None:
    field = service_field(change.path)
    risk = "low"
    reasons: list[str] = []

    target_changed = (
        change.old_base is not MISSING
        and change.target_value is not MISSING
        and not values_equal(change.target_value, change.old_base)
        and not values_equal(change.target_value, change.old_value)
    )
    change.conflict = target_changed

    if change.action == "delete":
        risk = "high"
        reasons.append("旧部署删除了该项，删除目标版本配置可能移除新功能")
    if len(change.path) <= 2 and change.path[:1] == ("services",):
        risk = "high"
        reasons.append("涉及整个服务")
    if field in VERSION_OWNED_FIELDS:
        risk = "high"
        reasons.append("该字段通常由目标版本维护")
    elif field in {"extra_hosts", "volumes"}:
        risk = "high"
        reasons.append("该字段可能改变服务寻址或持久化数据位置")
    elif field in {"ports", "networks", "deploy", "healthcheck"}:
        if risk != "high":
            risk = "medium"
        reasons.append("该字段会影响网络、数据、端口或运行状态")
    if is_sensitive_path(change.path):
        if risk == "low":
            risk = "medium"
        reasons.append("该项可能包含敏感配置")
    if target_changed:
        risk = "high"
        reasons.append("目标版本也修改了同一路径，存在三方冲突")
    if change.source == "two-file":
        if risk == "low":
            risk = "medium"
        reasons.append("缺少旧版官方基线，无法证明这是本地定制")

    change.risk = risk
    change.reason = "；".join(dict.fromkeys(reasons)) or "未发现明显结构冲突"


def collect_three_way_changes(
    old_base: Any,
    old_value: Any,
    target: Any,
    path: tuple[Any, ...] = (),
) -> list[Change]:
    """Collect the patch from old_base to old_value and compare it to target."""
    changes: list[Change] = []

    if isinstance(old_base, dict) and isinstance(old_value, dict):
        ordered_keys = list(old_value.keys()) + [key for key in old_base if key not in old_value]
        for key in ordered_keys:
            base_child = old_base.get(key, MISSING)
            old_child = old_value.get(key, MISSING)
            target_child = get_at(target, (*path, key))
            if base_child is MISSING:
                change = Change(
                    path=(*path, key),
                    action="set",
                    old_base=MISSING,
                    old_value=old_child,
                    target_value=target_child,
                )
                classify_change(change)
                if not values_equal(old_child, target_child):
                    changes.append(change)
            elif old_child is MISSING:
                change = Change(
                    path=(*path, key),
                    action="delete",
                    old_base=base_child,
                    old_value=MISSING,
                    target_value=target_child,
                )
                classify_change(change)
                if target_child is not MISSING:
                    changes.append(change)
            else:
                changes.extend(
                    collect_three_way_changes(base_child, old_child, target, (*path, key))
                )
        return changes

    # Lists are treated as one unit. Compose list merge semantics vary by field,
    # so replacing individual elements automatically is less predictable.
    if not values_equal(old_base, old_value):
        change = Change(
            path=path,
            action="set",
            old_base=old_base,
            old_value=old_value,
            target_value=get_at(target, path),
        )
        classify_change(change)
        if not values_equal(old_value, change.target_value):
            changes.append(change)
    return changes


def collect_two_file_changes(old: Any, target: Any) -> tuple[list[Change], list[str]]:
    """Collect conservative operator-managed candidates without an old baseline."""
    changes: list[Change] = []
    skipped: list[str] = []
    old_services = old.get("services", {})
    target_services = target.get("services", {})

    for service_name, old_service in old_services.items():
        if service_name not in target_services:
            change = Change(
                path=("services", service_name),
                action="set",
                old_value=old_service,
                target_value=MISSING,
                source="two-file",
            )
            classify_change(change)
            changes.append(change)
            continue
        if not isinstance(old_service, dict) or not isinstance(target_services[service_name], dict):
            skipped.append(f"services.{service_name}: 服务结构不是映射")
            continue
        target_service = target_services[service_name]
        for field in OPERATOR_FIELDS:
            if field not in old_service:
                continue
            old_field = old_service[field]
            target_field = target_service.get(field, MISSING)
            if values_equal(old_field, target_field):
                continue
            change = Change(
                path=("services", service_name, field),
                action="set",
                old_value=old_field,
                target_value=target_field,
                source="two-file",
            )
            classify_change(change)
            changes.append(change)

        differing_version_fields = [
            field
            for field in VERSION_OWNED_FIELDS
            if field in old_service
            and not values_equal(old_service[field], target_service.get(field, MISSING))
        ]
        if differing_version_fields:
            skipped.append(
                f"services.{service_name}: 未自动候选版本字段 "
                + ", ".join(sorted(differing_version_fields))
            )

    for field in ROOT_OPERATOR_FIELDS:
        if field in old and not values_equal(old[field], target.get(field, MISSING)):
            change = Change(
                path=(field,),
                action="set",
                old_value=old[field],
                target_value=target.get(field, MISSING),
                source="two-file",
            )
            classify_change(change)
            changes.append(change)

    return changes, skipped


def redact_value(value: Any, path: Sequence[Any] = ()) -> Any:
    if value is MISSING:
        return "<不存在>"
    if is_sensitive_path(path):
        return "<已隐藏>"
    if isinstance(value, dict):
        result: dict[Any, Any] = {}
        for key, child in value.items():
            child_path = (*path, key)
            result[key] = "<已隐藏>" if is_sensitive_path(child_path) else redact_value(child, child_path)
        return result
    if isinstance(value, list):
        return [redact_value(item, path) for item in value]
    return value


def short_summary(value: Any, path: Sequence[Any]) -> str:
    redacted = redact_value(value, path)
    if value is MISSING:
        return "<不存在>"
    if isinstance(redacted, dict):
        keys = [str(key) for key in redacted.keys()]
        shown = ", ".join(keys[:8])
        suffix = " …" if len(keys) > 8 else ""
        return f"映射({len(keys)}): {shown}{suffix}"
    if isinstance(redacted, list):
        return f"列表({len(redacted)})"
    text = repr(redacted)
    return text if len(text) <= 100 else text[:97] + "..."


def dump_fragment(yaml: YAML, value: Any, path: Sequence[Any]) -> str:
    if value is MISSING:
        return "<不存在>\n"
    from io import StringIO

    stream = StringIO()
    yaml.dump(redact_value(value, path), stream)
    return stream.getvalue()


def show_change(change: Change, index: int, total: int) -> None:
    print()
    print(f"[{index}/{total}] {path_text(change.path)}")
    print(f"  风险: {change.risk.upper()}{' / CONFLICT' if change.conflict else ''}")
    print(f"  操作: {'写入旧部署值' if change.action == 'set' else '从目标配置删除'}")
    print(f"  原因: {change.reason}")
    if change.old_base is not MISSING:
        print(f"  旧基线: {short_summary(change.old_base, change.path)}")
    print(f"  旧部署: {short_summary(change.old_value, change.path)}")
    print(f"  新版本: {short_summary(change.target_value, change.path)}")


def show_detail(change: Change, yaml: YAML) -> None:
    print("\n--- 旧版官方基线 ---")
    print(dump_fragment(yaml, change.old_base, change.path), end="")
    print("--- 旧生产配置 ---")
    print(dump_fragment(yaml, change.old_value, change.path), end="")
    print("--- 新版目标配置 ---")
    print(dump_fragment(yaml, change.target_value, change.path), end="")


def prompt_changes(
    changes: list[Change],
    yaml: YAML,
    start_index: int = 0,
) -> list[Change]:
    total = len(changes)
    index = start_index
    while index < total:
        change = changes[index]
        while True:
            show_change(change, index + 1, total)
            show_detail(change, yaml)
            answer = input("  迁移此项？[Y/回车]是 [n]否 [u]上一项 [q]退出: ").strip().lower()
            if answer in {"", "y", "yes"}:
                change.accepted = True
                index += 1
                break
            if answer in {"n", "no"}:
                change.accepted = False
                index += 1
                break
            if answer in {"u", "undo"}:
                if index == 0:
                    print("  当前已是第一项，无法继续回退。")
                    continue
                index -= 1
                changes[index].accepted = None
                break
            if answer in {"q", "quit"}:
                raise KeyboardInterrupt
            print("  请输入回车/y、n、u 或 q。")
    return [change for change in changes if change.accepted]


def ensure_parent_mapping(root: Any, path: Sequence[Any]) -> tuple[Any, Any]:
    node = root
    for key in path[:-1]:
        child = node.get(key, MISSING) if isinstance(node, dict) else MISSING
        if child is MISSING or not isinstance(child, dict):
            child = CommentedMap()
            node[key] = child
        node = child
    return node, path[-1]


def find_parent_mapping(root: Any, path: Sequence[Any]) -> tuple[Any, Any] | None:
    node = root
    for key in path[:-1]:
        if not isinstance(node, dict) or key not in node or not isinstance(node[key], dict):
            return None
        node = node[key]
    return node, path[-1]


def apply_changes(target: Any, changes: Iterable[Change]) -> Any:
    result = copy.deepcopy(target)
    for change in changes:
        if change.action == "set":
            parent, key = ensure_parent_mapping(result, change.path)
            parent[key] = copy.deepcopy(change.old_value)
        else:
            found = find_parent_mapping(result, change.path)
            if found is not None:
                parent, key = found
                if key in parent:
                    del parent[key]
    return result


def write_yaml_atomic(path: Path, data: Any, yaml: YAML) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            yaml.dump(data, stream)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_report(
    path: Path,
    args: argparse.Namespace,
    changes: list[Change],
    skipped: list[str],
) -> None:
    lines = [
        "# Docker Compose 迁移报告",
        "",
        f"- 生成时间：{dt.datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 旧部署文件：`{args.old}`",
        f"- 新版目标文件：`{args.new}`",
        f"- 旧版官方基线：`{args.old_base}`" if args.old_base else "- 旧版官方基线：未提供（保守双文件模式）",
        "",
        "## 决策",
        "",
        "| 路径 | 操作 | 风险 | 决策 | 冲突 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for change in changes:
        decision = "迁移" if change.accepted else "跳过"
        lines.append(
            f"| `{path_text(change.path)}` | {change.action} | {change.risk} | {decision} | "
            f"{'是' if change.conflict else '否'} |"
        )
    if skipped:
        lines.extend(["", "## 未自动处理", ""])
        lines.extend(f"- {item}" for item in skipped)
    lines.extend(
        [
            "",
            "## 注意",
            "",
            "报告不记录配置值，避免把密码、令牌和访问密钥写入运维记录。",
            "输出文件仍须执行 `docker compose config --quiet` 并进行人工审核。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_with_docker_compose(output: Path) -> tuple[bool, str]:
    docker = shutil.which("docker")
    if docker is None:
        return False, "未找到 docker 命令，已跳过 Compose 校验"
    process = subprocess.run(
        [docker, "compose", "-f", output.name, "config", "--quiet"],
        cwd=output.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    message = (process.stderr or process.stdout).strip()
    return process.returncode == 0, message


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="交互式迁移 Docker Compose 本地定制，优先使用三方合并。",
        epilog=USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--old", type=Path, default=Path("docker-compose-old.yaml"), help="旧生产 Compose")
    parser.add_argument("--new", type=Path, default=Path("docker-compose.yaml"), help="新官方 Compose")
    parser.add_argument("--old-base", type=Path, help="旧版本未修改的官方 Compose（强烈推荐）")
    parser.add_argument("--output", type=Path, help="候选输出文件；默认与新文件同目录")
    parser.add_argument("--report", type=Path, help="迁移报告路径")
    parser.add_argument("--in-place", action="store_true", help="备份后覆盖 --new；默认不覆盖")
    parser.add_argument("--list", action="store_true", help="只列出候选项，不询问也不写文件")
    parser.add_argument("--skip-compose-validation", action="store_true", help="跳过 docker compose config --quiet")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    yaml = configure_yaml()
    try:
        old = load_compose(args.old.resolve(), yaml)
        target = load_compose(args.new.resolve(), yaml)
        if args.old_base:
            old_base = load_compose(args.old_base.resolve(), yaml)
            changes = collect_three_way_changes(old_base, old, target)
            skipped: list[str] = []
            mode = "三方合并"
        else:
            changes, skipped = collect_two_file_changes(old, target)
            mode = "保守双文件"
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    changes.sort(key=lambda item: (item.risk != "high", path_text(item.path)))
    high_count = sum(change.risk == "high" for change in changes)
    conflict_count = sum(change.conflict for change in changes)
    print(f"模式: {mode}")
    print(f"候选项: {len(changes)}，高风险: {high_count}，三方冲突: {conflict_count}")
    if not args.old_base:
        print("警告: 未提供 --old-base，只会候选常见运维字段，无法准确识别全部本地定制。")
    if skipped:
        print(f"未自动处理的字段组: {len(skipped)}（将写入报告）")

    if args.list:
        for index, change in enumerate(changes, start=1):
            show_change(change, index, len(changes))
        return 0

    if not changes:
        print("没有发现可迁移项。")
        return 0

    start_index = 0
    while True:
        try:
            accepted = prompt_changes(changes, yaml, start_index=start_index)
        except (KeyboardInterrupt, EOFError):
            print("\n已取消，未写入任何文件。")
            return 130

        print()
        print(f"已选择 {len(accepted)} 项，跳过 {len(changes) - len(accepted)} 项。")
        try:
            final_answer = input(
                "确认写入候选文件？[Y/回车]写入 [n]取消 [u]返回上一项: "
            ).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消，未写入任何文件。")
            return 130
        if final_answer in {"", "y", "yes"}:
            if not accepted:
                print("未选择任何迁移项，未生成候选 Compose。")
                return 0
            break
        if final_answer in {"u", "undo"}:
            start_index = len(changes) - 1
            changes[start_index].accepted = None
            continue
        print("已取消，未写入任何文件。")
        return 0

    new_path = args.new.resolve()
    if args.in_place:
        output = new_path
        timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = new_path.with_name(f"{new_path.name}.backup-{timestamp}")
        shutil.copy2(new_path, backup)
        print(f"已备份目标文件: {backup}")
    else:
        output = (args.output or new_path.with_name("docker-compose.migrated.yaml")).resolve()
        if output == new_path:
            print("错误: --output 不能等于 --new；如需覆盖请显式使用 --in-place。", file=sys.stderr)
            return 2

    migrated = apply_changes(target, accepted)
    write_yaml_atomic(output, migrated, yaml)
    report = (
        args.report.resolve()
        if args.report
        else output.with_name(f"{output.name}.migration-report.md")
    )
    write_report(report, args, changes, skipped)
    print(f"已生成候选文件: {output}")
    print(f"已生成迁移报告: {report}")

    if not args.skip_compose_validation:
        valid, message = validate_with_docker_compose(output)
        if valid:
            print("Compose 静态校验通过。")
        else:
            print(f"Compose 静态校验未通过或未执行: {message}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
