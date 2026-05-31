#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "registry"
NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
GITHUB_URL_RE = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)
INDEX_HEADER = "name\turl\towner"
ALLOWED_REGISTRY_FILES = {"README.md", "index.tsv"}
WRITE_PERMISSIONS = {"admin", "maintain", "write"}
ZERO_ENTRYPOINTS = ("src/mod.0", "src/lib.0", "src/main.0")


@dataclass(frozen=True)
class Entry:
    name: str
    url: str
    owner: str
    repo: str
    path: Path


def fail(errors):
    write_summary("Registry validation failed:\n\n" + "\n".join(f"- {error}" for error in errors))
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    sys.exit(1)


def write_summary(text):
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text.rstrip() + "\n")
    print(text)


def api(path, token):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = res.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def normalize_url(url):
    url = url.strip()
    match = GITHUB_URL_RE.match(url)
    if not match:
        return "", "", ""
    owner = match.group(1)
    repo = match.group(2)
    return f"https://github.com/{owner}/{repo}", owner, repo


def read_registry_entries():
    errors = []
    entries = {}
    if not REGISTRY.exists():
        return entries, ["registry directory is missing"]

    for path in sorted(REGISTRY.rglob("*")):
        rel = path.relative_to(REGISTRY)
        rel_text = rel.as_posix()
        if path.is_dir():
            errors.append(f"registry must not contain subdirectories: registry/{rel_text}")
            continue
        if len(rel.parts) != 1:
            errors.append(f"registry entries must be direct files: registry/{rel_text}")
            continue
        if rel.name in ALLOWED_REGISTRY_FILES:
            continue
        if rel.name.startswith("."):
            errors.append(f"hidden registry files are not allowed: registry/{rel_text}")
            continue
        name = rel.name
        if not NAMESPACE_RE.match(name):
            errors.append(f"invalid registry package name filename: registry/{name}")
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) != 1 or not lines[0].strip():
            errors.append(f"registry/{name} must contain exactly one URL line")
            continue
        url, owner, repo = normalize_url(lines[0])
        if not url:
            errors.append(f"registry/{name} must point to https://github.com/<owner>/<repo>")
            continue
        if lines[0].strip() != url:
            errors.append(f"registry/{name} must use normalized endpoint URL {url}")
            continue
        entries[name] = Entry(name, url, owner, repo, path)
    return entries, errors


def read_index():
    index = REGISTRY / "index.tsv"
    if not index.exists():
        return {}, ["registry/index.tsv is missing"]

    lines = index.read_text(encoding="utf-8").splitlines()
    if not lines:
        return {}, ["registry/index.tsv is empty"]
    errors = []
    if lines[0] != INDEX_HEADER:
        errors.append(f"registry/index.tsv header must be `{INDEX_HEADER}`")

    rows = {}
    previous = ""
    for line_no, line in enumerate(lines[1:], start=2):
        parts = line.split("\t")
        if len(parts) != 3:
            errors.append(f"registry/index.tsv:{line_no} must have name, url, and owner columns")
            continue
        name, url, owner = parts
        if name in rows:
            errors.append(f"duplicate registry/index.tsv row for {name}")
        if previous and name <= previous:
            errors.append("registry/index.tsv rows must be sorted by package name")
        previous = name
        rows[name] = (url, owner)
    return rows, errors


def validate_index(entries, rows):
    errors = []
    entry_names = set(entries)
    row_names = set(rows)
    for name in sorted(entry_names - row_names):
        errors.append(f"registry/index.tsv is missing row for {name}")
    for name in sorted(row_names - entry_names):
        errors.append(f"registry/index.tsv has row without registry/{name}")
    for name in sorted(entry_names & row_names):
        entry = entries[name]
        row_url, row_owner = rows[name]
        if row_url != entry.url:
            errors.append(f"registry/index.tsv URL for {name} must be {entry.url}")
        if row_owner != entry.owner:
            errors.append(f"registry/index.tsv owner for {name} must be {entry.owner}")
    return errors


def git_diff_paths(pathspec=None):
    base = os.environ.get("BASE_SHA")
    if not base:
        return []
    command = ["git", "diff", "--name-status", f"{base}...HEAD"]
    if pathspec:
        command.extend(["--", pathspec])
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    changes = []
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if not fields:
            continue
        status = fields[0]
        path = fields[-1]
        changes.append((status, path))
    return changes


def changed_entry_names():
    changes = git_diff_paths("registry")
    if not changes:
        return set(), []
    errors = []
    names = set()
    for status, path in changes:
        if not path.startswith("registry/"):
            continue
        rel = Path(path).relative_to("registry")
        if len(rel.parts) != 1:
            errors.append(f"registry changes must stay at top level: {path}")
            continue
        if rel.name in ALLOWED_REGISTRY_FILES:
            continue
        if not status.startswith("A"):
            errors.append(f"existing registry entries cannot be changed by registration PRs: {path}")
            continue
        names.add(rel.name)
    return names, errors


def validate_change_scope():
    changes = git_diff_paths()
    if not changes:
        return []
    changed_paths = [path for _, path in changes]
    registry_changed = any(path.startswith("registry/") for path in changed_paths)
    if not registry_changed:
        return []
    errors = []
    for path in changed_paths:
        if not path.startswith("registry/"):
            errors.append(f"registry registration PRs must not change non-registry files: {path}")
    return errors


def validate_rate_limit(repo, actor, token):
    errors = []
    rate = api("/rate_limit", token)
    core = rate.get("resources", {}).get("core", {})
    if int(core.get("remaining", 0)) < 50:
        errors.append("GitHub API core rate limit is too low for registry validation")

    since = (datetime.now(timezone.utc) - timedelta(hours=24)).date().isoformat()
    query = f"repo:{repo} is:pr author:{actor} created:>{since}"
    path = "/search/issues?" + urllib.parse.urlencode({"q": query})
    data = api(path, token)
    if int(data.get("total_count", 0)) > 10:
        errors.append("registry pull request rate limit exceeded for this GitHub actor")
    return errors


def validate_ownership(entry, actor, token):
    if actor.lower() == entry.owner.lower():
        return []
    try:
        data = api(f"/repos/{entry.owner}/{entry.repo}/collaborators/{actor}/permission", token)
    except Exception as exc:
        return [f"could not verify @{actor} permission on {entry.owner}/{entry.repo}: {exc}"]
    permission = data.get("permission", "")
    if permission in WRITE_PERMISSIONS:
        return []
    return [
        f"@{actor} must own {entry.owner}/{entry.repo} or have write, maintain, or admin permission"
    ]


def find_zero_check_input(package_dir):
    manifest = package_dir / "zero.json"
    if not manifest.exists():
        return ""
    for rel in ZERO_ENTRYPOINTS:
        if (package_dir / rel).exists():
            return "."
    return ""


def read_zero_package_name(package_dir):
    manifest = package_dir / "zero.json"
    if not manifest.exists():
        return "", ["endpoint must contain zero.json"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception as exc:
        return "", [f"endpoint zero.json could not be parsed: {exc}"]
    package = data.get("package", {})
    if not isinstance(package, dict):
        return "", ["endpoint zero.json must contain a package object"]
    name = package.get("name", "")
    if not isinstance(name, str) or not name:
        return "", ["endpoint zero.json must contain package.name"]
    if not NAMESPACE_RE.match(name):
        return "", ["endpoint zero.json package.name must be a lowercase Zero identifier"]
    return name, []


def validate_zero_package(entry):
    with tempfile.TemporaryDirectory(prefix="zkg-registry-") as tmp:
        checkout = Path(tmp) / entry.name
        clone = subprocess.run(
            ["git", "clone", "--depth", "1", entry.url, str(checkout)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if clone.returncode != 0:
            return [f"could not clone endpoint for {entry.name}: {clone.stderr.strip()}"]

        package_name, errors = read_zero_package_name(checkout)
        if errors:
            return errors
        if package_name != entry.name:
            return [
                f"registry/{entry.name} must match endpoint zero.json package.name `{package_name}`"
            ]

        check_input = find_zero_check_input(checkout)
        if not check_input:
            expected = ", ".join(ZERO_ENTRYPOINTS)
            return [f"{entry.name} endpoint must contain a zkg entrypoint: {expected}"]

        checked = subprocess.run(
            ["zero", "check", check_input],
            cwd=checkout,
            text=True,
            capture_output=True,
        )
        if checked.returncode == 0:
            return []
        details = (checked.stdout + checked.stderr).strip()
        if len(details) > 4000:
            details = details[:4000] + "\n..."
        return [f"zero check failed for {entry.name} ({check_input}):\n{details}"]


def main():
    local_only = os.environ.get("LOCAL_REGISTRY_VALIDATE") == "1"
    token = os.environ.get("GITHUB_TOKEN", "")
    actor = os.environ.get("GITHUB_ACTOR", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    entries, entry_errors = read_registry_entries()
    rows, index_errors = read_index()
    changed_names, change_errors = changed_entry_names()
    errors = (
        entry_errors
        + index_errors
        + validate_index(entries, rows)
        + change_errors
        + validate_change_scope()
    )

    if not local_only:
        if not token:
            errors.append("GITHUB_TOKEN is required for ownership and rate-limit validation")
        if not actor:
            errors.append("GITHUB_ACTOR is required for ownership validation")
        if not repo:
            errors.append("GITHUB_REPOSITORY is required for rate-limit validation")

    if not errors and not local_only:
        errors.extend(validate_rate_limit(repo, actor, token))
        for package_name in sorted(changed_names):
            entry = entries.get(package_name)
            if entry is None:
                errors.append(f"changed registry entry is missing after validation: {package_name}")
                continue
            errors.extend(validate_ownership(entry, actor, token))
            if not errors:
                errors.extend(validate_zero_package(entry))

    if errors:
        fail(errors)

    changed = ", ".join(sorted(changed_names)) if changed_names else "none"
    write_summary(f"Registry validation passed. Changed registry entries: {changed}")


if __name__ == "__main__":
    main()
