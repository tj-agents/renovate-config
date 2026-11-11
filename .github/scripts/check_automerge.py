import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ORGANIZATION = "tj-agents"
PRESET = f"github>{ORGANIZATION}/renovate-config"
CONFIG_FILES = (
    "renovate.json",
    "renovate.json5",
    ".renovaterc",
    ".renovaterc.json",
    ".renovaterc.json5",
    ".github/renovate.json",
    ".github/renovate.json5",
    ".gitlab/renovate.json",
    ".gitlab/renovate.json5",
)


def fetch(path: str, token: str) -> bytes | None:
    request = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={
            "Accept": "application/vnd.github.raw+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def get(path: str, token: str) -> Any:
    body = fetch(path, token)
    return None if body is None else json.loads(body)


def disables_automerge(value: Any) -> bool:
    if isinstance(value, dict):
        return value.get("automerge") is False or any(
            disables_automerge(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(disables_automerge(item) for item in value)
    return False


def problems(config: Any, source: str) -> list[str]:
    found = []
    if PRESET not in config.get("extends", []):
        found.append(f"{source} does not extend {PRESET}")
    if disables_automerge(config):
        found.append(f"{source} disables automerge")
    return found


def repository_problems(repository: dict[str, Any], token: str) -> list[str]:
    name = repository["full_name"]
    found = []
    for path in CONFIG_FILES:
        if path.endswith("json5") or path == ".renovaterc":
            if fetch(f"repos/{name}/contents/{path}", token) is not None:
                found.append(f"{name}/{path} must be JSON named renovate.json")
            continue
        config = get(f"repos/{name}/contents/{path}", token)
        if config is not None:
            found += problems(config, f"{name}/{path}")
    package = get(f"repos/{name}/contents/package.json", token)
    if package is not None and "renovate" in package:
        found += problems(package["renovate"], f"{name}/package.json")
    return found


def main() -> int:
    token = os.environ["GITHUB_TOKEN"]
    preset = json.loads(Path("default.json").read_text(encoding="utf-8"))
    found = []
    if preset.get("automerge") is not True or disables_automerge(preset):
        found.append("default.json must enable automerge for every update")
    repositories = [
        repository
        for repository in get(f"orgs/{ORGANIZATION}/repos?per_page=100", token)
        if not repository["archived"]
    ]
    for repository in repositories:
        found += repository_problems(repository, token)
    for problem in found:
        print(f"::error::{problem}")
    print(f"checked {len(repositories)} repositories, {len(found)} problems")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
