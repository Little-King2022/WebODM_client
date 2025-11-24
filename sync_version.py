#!/usr/bin/env python3
"""
sync_version.py
自动将 pyproject.toml 中的 project.version 同步到 README.md 与 README zh_CN.md

用法:
    python sync_version.py

要求:
    Python 3.7+  安装 tomli (python<3.11)
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

def get_version() -> str:
    """读取 pyproject.toml 中的 project.version
    
    Returns:
        str: 版本号，如 "1.3.5"
    Raises:
        RuntimeError: 无法解析版本号时抛出
    """
    toml_path = os.path.join(ROOT, "pyproject.toml")
    if not os.path.exists(toml_path):
        raise RuntimeError("找不到 pyproject.toml")
    try:
        # Python 3.11+ 自带 tomllib
        try:
            import tomllib
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)
        except ImportError:
            import tomli
            with open(toml_path, "rb") as f:
                data = tomli.load(f)
        ver = str(data.get("project", {}).get("version", ""))
        if not ver:
            raise RuntimeError("project.version 为空")
        return ver
    except Exception as e:
        raise RuntimeError(f"解析版本号失败: {e}") from e

def sync_readme(path: str, version: str) -> bool:
    """替换指定 README 中的版本占位符
    
    Args:
        path: README 文件路径
        version: 新版本号
    Returns:
        bool: 文件有改动返回 True，否则 False
    """
    if not os.path.exists(path):
        print(f"⚠️  文件不存在，跳过: {path}")
        return False
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 支持 <!--VERSION-->v1.2.3<!--/VERSION--> 或 <!--VERSION-->1.2.3<!--/VERSION-->
    new_content = re.sub(
        r"(<!--VERSION-->)[^<]+(<!--/VERSION-->)",
        rf"\g<1>v{version}\g<2>",
        content,
        flags=re.I,
    )
    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False

def main() -> None:
    """入口函数"""
    try:
        ver = get_version()
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    updated = []
    for readme in ("README.md", "README zh_CN.md"):
        readme_path = os.path.join(ROOT, readme)
        if sync_readme(readme_path, ver):
            updated.append(readme)

    if updated:
        print(f"✅ 已同步版本号 v{ver} 到: {', '.join(updated)}")
    else:
        print(f"ℹ️  所有 README 版本号已是最新 v{ver}")

if __name__ == "__main__":
    main()