import subprocess
from pathlib import Path

def run_cmd(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

def count_total_files(repo_path):
    print("\n📄 Counting total files...")
    cmd = "find . -type f | wc -l"
    output = run_cmd(cmd, cwd=repo_path)
    print(f"➡ Total files: {output}")
    return output

def language_wise_stats(repo_path):
    print("\n📊 Language wise file count...")
    cmd = 'find . -type f -printf "%f\\n" | awk -F. \'{print $NF}\' | sort | uniq -c'
    output = run_cmd(cmd, cwd=repo_path)
    print(output)
    return output

def detect_dependency_manager(repo_path):
    print("\n🛠 Detecting dependency manager...")
    cmd = r'''
    find . -maxdepth 5 -type f \( \
        -name "package.json" -o \
        -name "pom.xml" -o \
        -name "build.gradle" -o \
        -name "build.gradle.kts" -o \
        -name "go.mod" -o \
        -name "requirements.txt" -o \
        -name "Pipfile" -o \
        -name "Pipfile.lock" -o \
        -name "poetry.lock" -o \
        -name "uv.lock" -o \
        -name "Cargo.toml" -o \
        -name "composer.json" \
    \) 2>/dev/null | awk '
        /package.json/      {print "npm / yarn / pnpm"; exit}
        /pom.xml/           {print "maven"; exit}
        /build.gradle/      {print "gradle"; exit}
        /build.gradle.kts/  {print "gradle"; exit}
        /go.mod/            {print "go modules"; exit}
        /requirements.txt/  {print "pip"; exit}
        /Pipfile.lock/      {print "pipenv"; exit}
        /Pipfile/           {print "pipenv"; exit}
        /poetry.lock/       {print "poetry"; exit}
        /uv.lock/           {print "uv"; exit}
        /Cargo.toml/        {print "cargo"; exit}
        /composer.json/     {print "composer"; exit}
        {print "Unknown"}
    '
    '''
    output = run_cmd(cmd, cwd=repo_path)
    print(f"➡ Dependency Manager: {output}")
    return output
