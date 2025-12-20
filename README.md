# Context Graph

## Overview

The Context Graph codebase is designed to analyze a software repository and provide a high-level understanding of its technologies, dependencies, and framework usage.

At a high level, the system first detects which programming languages are used in the codebase and which package managers are associated with those languages. Based on this detection, the system generates structured output that describes the overall technology stack of the repository.

Once the languages and package managers are identified, the system determines which frameworks and libraries are used across the codebase. To ensure accuracy and completeness, the system generates a **Software Bill of Materials (SBOM)** for the entire repository using the **cdxgen** tool. This SBOM captures all dependencies, including both direct and transitive dependencies, across all supported ecosystems.

After the SBOM is generated, the code processes the SBOM data to extract the frameworks and major libraries used in the project. The detected frameworks are consolidated and written to a dedicated output file, which serves as a structured input for subsequent analysis steps.

Next, a code-search component consumes the framework output file and scans the repository to identify where each framework is used within the source code. For each detected usage, the system records the file path and line number, enabling precise traceability between frameworks and their implementation locations in the codebase.

Finally, the system performs a re-verification step to generate dependency trees for the entire project. In this stage, the code re-detects the package managers present in the repository and, based on each package manager, generates the corresponding dependency tree. This ensures that dependency information is accurate, validated, and aligned with the detected technology stack.

Overall, the Context Graph provides an end-to-end automated analysis pipeline that transforms a raw code repository into a structured and traceable representation of its languages, package managers, frameworks, and dependencies. This README serves as a foundation for deeper analysis, which is explained in detail in the following sections.

---

## Workflow

### 1. Repository Cloning

* The system starts by cloning the repository specified by the user.
* The repository is stored in a user-defined folder for analysis.

**Output Example:**

```
➡ Repo cloned at: /path/to/repo
```

---

### 2. OS Detection

* The analysis adapts based on the operating system (Windows or Linux).
* OS detection ensures that commands and scripts run correctly in each environment.

**Output Example:**

```
🖥 Detected OS: linux
```

---

### 3. Language and Package Manager Detection

* The system detects **programming languages** by analyzing file extensions.
* It also identifies **package managers** (e.g., npm, Maven, Gradle, pip, Go modules).
* Special configuration files (e.g., `package.json`, `pom.xml`, `requirements.txt`, `go.mod`) are detected to aid dependency analysis.

**Output Example:**

```
📂 File counts by language:
   - Python: 45 files
   - JavaScript: 20 files
📌 Detected language (most common): Python
📌 Dependency manager: pip
```

---

### 4. SBOM Generation

* A **Software Bill of Materials (SBOM)** is generated using `cdxgen` if it doesn’t already exist.
* The SBOM captures **all dependencies**, including direct and transitive dependencies.

**Output Example:**

```
📦 sbom.json not found — generating SBOM...
🔎 SBOM generated at: /repo/sbom.json
```

---

### 5. Framework Extraction

* Frameworks and major libraries are extracted from the SBOM.
* The output is saved to `output.txt` for further analysis.

**Output Example:**

```
--- output.txt ---
Flask
Django
React
```

---

### 6. Framework Usage Search

* Using `frame.txt`, the system identifies **where each framework is used** in the repository.
* Records include **file paths and line numbers** for precise traceability.

**Output Example:**

```
--- frame.txt ---
app/main.py:12: import Flask
frontend/src/App.js:5: import React
```

---

### 7. Dependency Tree Generation

* Dependency trees are generated for all detected package managers:

  * **Python** → pip/requirements
  * **Node.js** → npm/pnpm
  * **Java** → Maven/Gradle
  * **Go** → Go modules

* Each tree is saved as a JSON file for structured reference.

**Output Example:**

```
--- python_dependencies_combined.json ---
{
    "Flask": "2.2.2",
    "requests": "2.31.0"
}
--- node_dependency_tree_1.json ---
{
    "react": "18.2.0",
    "axios": "1.5.0"
}
```

---

### 8. Report Generation

* All outputs are **consolidated in `report.txt`**.
* This includes:

  * OS detection
  * Language & package manager info
  * SBOM details
  * Framework extraction results
  * Framework usage locations
  * Dependency trees

**Purpose:** A single file to quickly inspect repository analysis.

---

## Directory Structure

```
<analysis-folder>/
├─ report.txt                # Full analysis output
├─ output.txt                # Extracted frameworks
├─ frame.txt                 # Framework usage locations
├─ repo_path/sbom.json       # Generated SBOM
├─ python_dependencies_combined.json
├─ node_dependency_tree_1.json
├─ maven_dependency_tree_1.json
└─ go_deps_1.json
```

---

## Notes

* Supports both **Windows and Linux** workflows.
* Handles multiple languages and multiple package managers per repository.
* Provides a **traceable link** from SBOM → frameworks → usage locations → re-verficaion /dependency tree.

---
