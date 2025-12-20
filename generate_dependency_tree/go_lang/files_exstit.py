from .dependency_tree import generate_dependency_tree, install_deptree
from pathlib import Path

def process_go(repo_path, output_root):
    repo_root = Path(repo_path)

    go_files = list(repo_root.rglob("go.mod"))

    if not go_files:
        print("ℹ️ No Go modules found — skipping Go dependency analysis.")
        return False   # 👈 IMPORTANT

    print(f"\n📦 Detected {len(go_files)} Go module(s)")

    output_root = Path(output_root).resolve()
    install_deptree()

    for idx, go_mod in enumerate(go_files, start=1):
        mod_path = go_mod.parent
        print(f"\n🚀 Processing Go module #{idx}: {mod_path}")

        try:
            deps_file = generate_dependency_tree(
                repo_path=mod_path,
                current_folder=output_root,
                output_name=f"go_deps_{idx}.json"
            )
            print(f"✅ Go dep_tree completed → {deps_file}")

        except Exception as e:
            print(f"❌ Failed generating dependency tree for {mod_path}")
            print(f"   Error: {e}")

    return True
