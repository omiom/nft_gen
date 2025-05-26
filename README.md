# NFT Metadata Generator v2.1 (Streamlit Edition)

This project implements an NFT Metadata Generator, now featuring a Streamlit-based Graphical User Interface (GUI). It generates unique NFT metadata based on defined trait rarities, gender-specific rules, and trait incompatibilities, as specified in the original Product Requirements Document v2.0 and subsequent UI development plans.

## Overview

The system allows users to configure and generate NFT metadata collections. Key features include:
*   Generation of a user-defined number of unique NFT metadata entries.
*   Trait distribution based on target counts and tolerances defined in a `numerology.yaml` file.
*   Enforcement of gender-specific traits and trait incompatibility rules (defined in `rules.yaml`).
*   Deterministic output based on a user-provided or randomized seed.
*   Configuration management via:
    *   Uploading custom `numerology.yaml` and `rules.yaml` files.
    *   Directly editing active YAML configurations within the UI.
    *   Using default `numerology.yaml` and `rules.yaml` files present in the project root.
*   Pre-validation of configuration files.
*   Comprehensive validation of generated outputs.
*   Export of metadata in JSON (per token) and CSV (summary) formats.
*   Both a Streamlit GUI and a Command-Line Interface (CLI) are available.

## Project Structure

```
nft_metadata_generator/
├── numerology.yaml         # Default configuration for traits, rarities, genders
├── rules.yaml              # Default configuration for trait incompatibilities
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── pre_validator.py    # Module for pre-validating configurations
│   ├── generator.py        # Core metadata generation logic
│   ├── models.py           # Data models (e.g., Token)
│   ├── exporter.py         # Module for exporting metadata to JSON and CSV (used by CLI)
│   ├── cli.py              # Command-line interface
│   └── gui.py              # Streamlit-based Graphical User Interface
├── tests/
│   ├── __init__.py
│   ├── test_pre_validator.py
│   ├── test_generator.py
│   ├── test_incompatibilities.py
│   └── test_determinism.py
├── output/                 # Default base directory for generated metadata from CLI
│                           # (GUI typically outputs to output_1, output_2 etc. in project root)
└── docs/
    ├── active-config-display-plan.md
    ├── category-completeness-validation-plan.md
    ├── direct-yaml-editing-plan.md
    ├── token-uniqueness-validation-plan.md
    └── ui_development_plan.md
```

## Setup and Installation

1.  **Clone the repository (if applicable)**
    ```bash
    # git clone <repository_url>
    # cd nft_metadata_generator
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    Ensure your `requirements.txt` file includes `streamlit` and other necessary libraries.
    ```bash
    pip install -r requirements.txt
    ```

## Configuration Files

The generator relies on two main YAML configuration files. Default versions (`numerology.yaml` and `rules.yaml`) are provided in the project root. The GUI allows for uploading custom versions of these files or editing them directly within the UI for the current session.

*   **`numerology.yaml`**:
    *   Defines trait categories (e.g., "Body", "Outfit", "Glyph").
    *   Lists individual traits within each category.
    *   Specifies `target_count` for each trait (how many times it should ideally appear in the collection).
    *   Sets `tolerance` for deviation from the `target_count`.
    *   Can define `gender` specificity for traits (e.g., "Male", "Female", "Unisex").
    *   Can define `gender_specific_to` for entire categories, making them applicable only to tokens of a certain gender.
    *   Contains the overall `target_count` for the collection size (this is overridden by the UI's "Target Collection Size" input when using the GUI).

*   **`rules.yaml`**:
    *   Defines incompatibility rules between pairs of traits.
    *   Each rule specifies `trait_a` (as `[category_name, trait_name]`) and `trait_b` that cannot appear together on the same token.
    *   An optional `description` can be added to each rule for clarity.

Refer to the example `numerology.yaml` and `rules.yaml` files in the project root for detailed structure and examples. The original "Product Requirements Document v2.0" may also contain further details on these specifications.

## Usage

### Graphical User Interface (GUI) - Streamlit

The primary way to use the generator is through its Streamlit-based GUI.

1.  **Start the GUI:**
    Navigate to the project's root directory in your terminal (where `src/` is a subdirectory) and run:
    ```bash
    streamlit run src/gui.py
    ```
2.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

**GUI Features:**

*   **Main Informational Message:** A persistent message at the top guides users on basic operation.
*   **Sidebar (`⚙️ Generation Parameters`):**
    *   **Seed:** Input field for the random seed (integer). A "Randomize Seed" button provides a random value.
    *   **Target Collection Size:** Input field for the desired number of NFTs to generate.
    *   **Configuration File Uploads (Optional):**
        *   `Custom Numerology YAML`: Upload your `numerology.yaml`. Overrides the default `numerology.yaml` in the project root.
        *   `Custom Rules YAML`: Upload your `rules.yaml`. Overrides the default `rules.yaml` in the project root.
    *   **Actions:**
        *   `Validate Configuration Files`: Pre-validates the currently active configuration (uploaded, edited, or default) and displays results in the main area.
        *   `Generate NFTs`: Starts the metadata generation process using the active configurations and parameters.

*   **Main Area:**
    *   **`📑 Active Configuration Files` (Expanders):**
        *   `🔎 View/Edit Active Numerology Config`: Displays the content of the numerology configuration that will be used. An "✏️ Edit" button allows for direct YAML editing within a text area for the current session. Applied edits take precedence over uploaded or default files until a new file is uploaded or the edit is canceled.
        *   `🔎 View/Edit Active Rules Config`: Similar functionality for the rules configuration.
    *   **`Configuration Pre-Validation Results`:** Appears after clicking "Validate Configuration Files," showing success or error details, and indicating the source of the validated files.
    *   **Generation Progress:** A progress bar and status text appear when "Generate NFTs" is clicked.
    *   **Output Tabs (appear after successful generation):**
        *   **`📊 Generated Tokens & Downloads`:**
            *   Displays a table of the generated tokens and their assigned traits.
            *   Provides "Download All as JSON" and "Download All as CSV" buttons.
            *   Expander to view the `generator.py` source code.
        *   **`✔️ Output Validation`:**
            *   `Trait Count Adherence`: Table showing actual vs. target counts for traits.
            *   `Incompatibility Rule Adherence`: Lists any tokens violating incompatibility rules.
            *   `Token Uniqueness`: Confirms if all generated tokens are unique.
            *   `Category Completeness`: Confirms if tokens have traits from all applicable defined categories.
            *   `Gender-Trait Mismatch Validation`: Lists any tokens with gender-trait mismatches.
            *   `Tokens with 1/1 Traits`: Expander to show tokens possessing traits that appear only once in the collection.
        *   **`📜 Generation Log`:** Displays detailed log messages from the generation process.

### Command-Line Interface (CLI)

The CLI remains available for script-based generation.

```bash
python -m src.cli --seed <random_seed> --numerology <path_to_numerology.yaml> --rules <path_to_rules.yaml> --output-dir <output_directory>
```

**CLI Arguments:**

*   `--seed`: Random seed for deterministic generation (default: 0).
*   `--numerology`: Path to the numerology configuration file (default: `numerology.yaml`).
*   `--rules`: Path to the rules configuration file (default: `rules.yaml`).
*   `--output-dir`: Base directory for output files (default: `output`). Each run creates a versioned subdirectory (e.g., `output/run_1`, `output/run_2`).
*   `--max-attempts`: Maximum generation attempts if constraints are hard to meet (default: 5, as per `generator.py` logic).
*   `--relaxed-tolerance`: (Flag) If present, may influence internal adjustment strategies (consult `generator.py` for specifics).

## Output Files

When metadata is generated (either via GUI or CLI):

*   **JSON Files:**
    *   Individual JSON files are created for each token (e.g., `001.json`, `002.json`, etc.).
    *   These are typically placed in a `json/` subdirectory within the run's output folder (e.g., `output_1/json/`, `output_2/json/` for GUI runs, or `output/run_X/json/` for CLI runs).
    *   **JSON Structure:**
        ```json
        {
          "token_id": "001",
          "hash_id": "abcdef123456...",
          "traits": {
            "Category1": "TraitNameA",
            "Category2": "TraitNameB",
            // ... other assigned traits
          },
          "metadata": {
            "trait_count": 7 
          }
        }
        ```
*   **CSV File (`metadata.csv`):**
    *   A single CSV file summarizing all generated tokens.
    *   Located in the root of the run's output folder (e.g., `output_1/metadata.csv`).
    *   **CSV Columns:** `Token ID`, `Hash ID`, one column for each trait category (e.g., `Body`, `Outfit`), `Trait Count`.

## Development and Testing

*   **Primary Language:** Python
*   **GUI Framework:** Streamlit
*   **Testing Framework:** `pytest`
*   **To run tests:**
    Navigate to the project root directory and execute:
    ```bash
    pytest
    ```
    Ensure all test files are located within the `tests/` directory and follow the `test_*.py` naming convention.

## Core Modules (in `src/`)

*   **`gui.py`**: Implements the Streamlit-based Graphical User Interface, providing controls for configuration, generation, validation, and viewing results.
*   **`generator.py`**: Contains the core logic for NFT metadata generation, including weighted random trait assignment, adherence to target counts and tolerances, gender rule application, and incompatibility checks.
*   **`pre_validator.py`**: Validates `numerology.yaml` and `rules.yaml` files for logical consistency, correct schema, and feasibility before attempting generation.
*   **`models.py`**: Defines data structures, primarily the `Token` class, used throughout the application.
*   **`cli.py`**: Provides the command-line interface for the generator.
*   **`exporter.py`**: (Primarily used by the CLI) Handles writing the generated metadata to versioned output directories in JSON (per token) and CSV (summary) formats. The GUI has its own internal export logic for downloads.

## Key Features

This generator implements a robust set of features to create diverse and rule-compliant NFT collections:

*   **Flexible Collection Size:** Generates a user-defined number of unique tokens (default was 420 in PRD, now configurable in UI).
*   **Trait Distribution Control:** Assigns traits based on target counts and tolerance levels defined in `numerology.yaml`.
*   **Gender Mechanics:** Supports gender-specific categories and traits, allowing for distinct male, female, or unisex characteristics.
*   **Incompatibility Rules:** Enforces rules defined in `rules.yaml` to prevent conflicting traits from appearing on the same token.
*   **Deterministic Generation:** Produces identical collections for a given seed and configuration, ensuring reproducibility.
*   **Configuration Pre-Validation:** Checks YAML configuration files for errors and logical issues before starting the main generation process.
*   **Iterative Adjustment Phase:** The core generator attempts to meet trait count targets and tolerances through an adjustment phase.
*   **Comprehensive UI:**
    *   Easy-to-use Streamlit interface.
    *   File upload for custom configurations.
    *   Direct in-UI editing of active configurations (session-based).
    *   Detailed validation reporting in the UI.
    *   Progress tracking and logging.
*   **Multiple Output Formats:** Exports metadata as individual JSON files per token and a summary CSV file.
*   **CLI Availability:** Retains a command-line interface for automated or scripted generation.

For the original detailed requirements, refer to the "Product Requirements Document – NFT Metadata Generator v2.0" and subsequent planning documents in the `docs/` directory.
