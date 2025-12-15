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

## Workflow Steps

### Step 1: Repository Scanning

The system begins by scanning the entire codebase to understand the repository structure. During this phase, it identifies relevant source files and configuration artifacts required for language, package manager, and dependency detection.

### Step 2: Programming Language Detection and Package Manager Detection

* The code analyzes file extensions and well-known project configuration files to detect which programming languages are used in the repository.
* The detected languages are recorded as structured output for use in later stages.
* After identifying the package manager, the system also detects the corresponding configuration file (for example, `package.json`, `pom.xml`, `requirements.txt`, `go.mod`, etc.).

### Step 3: SBOM Generation

After identifying the package managers, the system generates a Software Bill of Materials (SBOM) for the entire repository using the **cdxgen** tool.

* The SBOM provides a complete and standardized inventory of all dependencies.
* Both direct and transitive dependencies are captured.

### Step 4: Framework Extraction from SBOM

* The generated SBOM is parsed to identify frameworks and major libraries used in the codebase.
* The extracted framework information is consolidated and written to an output file.
* This output file serves as an input for subsequent analysis steps.

### Step 5: Framework Usage Code Search

* The code-search component takes the framework output file as input.
* It scans the repository to locate where each framework is used in the source code.
* For every match, the system captures the file path and line number.

### Step 6: Dependency Tree Re-verification

* As a validation step, the system re-detects the package managers in the repository.
* Dependency trees are generated for each detected package manager.
* This step ensures that dependency information is accurate and consistent with the SBOM data.
* It also allows verification of whether transitive dependencies appear correctly in the dependency trees.

### Step 7: Output Generation

Finally, all results are collected and written to structured output files, including:

* Detected programming languages
* Detected package managers
* Generated SBOM
* Framework list
* Framework usage locations
* Dependency trees

These outputs together provide a complete and traceable view of the repository.

---

## Architecture Diagram

*(Add the architecture diagram here showing repository input, language and package manager detection, SBOM generation, framework extraction, code search, and dependency tree generation.)*

---

## Output Formats

### Repository Cloning and Initial Analysis

* The process begins by cloning the target repository.
* The system detects the programming languages used and identifies the main package manager.
* This analysis is performed using a Python script on Windows or other operating systems, or using equivalent Linux commands on Linux machines.
* The results are saved in a file named `repo_analysis.json`.

### SBOM Generation and Retrieval

* The tool searches for an existing `sbom.json` file in the repository.
* If it is not available, **cdxgen** is used to generate the SBOM automatically.
* The SBOM contains detailed information about frameworks, libraries, and applications used in the source code.

### Frameworks and Libraries Extraction

* A Python script parses `sbom.json` to extract all frameworks, libraries, and applications used in the repository.
* The extracted data is saved in a file named `output.txt`.

### Code Search Tool

* The extracted frameworks from `output.txt` are searched in the source code using the Code Search Tool.
* For each occurrence, the file path and line number are recorded in `frame.txt`.

### Dependency Tree Generation

* To verify and understand dependencies, dependency trees are generated for supported package managers, such as:

  * Python
  * Java (Maven / Gradle)
  * Golang
* If a repository uses multiple package managers, separate dependency trees are generated for each.
* If multiple configuration files exist for the same package manager, output files are indexed for easy reference.

This approach allows efficient identification of both direct and transitive dependencies and ensures consistency between SBOM data and dependency trees.
