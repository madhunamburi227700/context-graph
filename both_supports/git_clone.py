import subprocess
from pathlib import Path


def clone_and_checkout(repo_with_branch: str, base_dir: str | Path) -> str:
    """
    Clone a git repo into base_dir and checkout branch provided via @branch.

    Examples:
        https://github.com/user/repo.git
        https://github.com/user/repo.git@develop
        https://github.com/user/repo.git@release/1.0
    """

    if not repo_with_branch or not isinstance(repo_with_branch, str):
        raise ValueError("❌ Repo URL is required")

    base_dir = Path(base_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    # ✅ Parse repo URL and branch correctly
    if "@@" in repo_with_branch:
        raise ValueError("❌ Invalid repo format")

    if "@" in repo_with_branch:
        repo_url, branch = repo_with_branch.rsplit("@", 1)
    else:
        repo_url, branch = repo_with_branch, None

    repo_name = Path(repo_url).stem
    repo_path = base_dir / repo_name

    # Clone repo if not exists
    if not repo_path.exists():
        print(f"📥 Cloning {repo_url} into {repo_path}")
        subprocess.run(
            ["git", "clone", repo_url, str(repo_path)],
            check=True
        )
    else:
        print(f"✔ Repository '{repo_name}' already exists")

    # ✅ Checkout branch if provided
    if branch:
        print(f"🔄 Checking out branch: {branch}")
        subprocess.run(
            ["git", "fetch", "--all"],
            cwd=repo_path,
            check=True
        )
        subprocess.run(
            ["git", "checkout", branch],
            cwd=repo_path,
            check=True
        )
    else:
        print("✔ Using default branch")

    return str(repo_path)
