# Web-Based UI Development Plan for NFT Generator

This document outlines the plan for developing a web-based user interface for the NFT metadata generator, primarily using Streamlit.

## 1. Overall Objective

To create an intuitive, web-based UI that allows users to:
*   Manage configuration files ([`numerology.yaml`](numerology.yaml), [`rules.yaml`](rules.yaml)).
*   Set generation parameters (seed, target count).
*   Trigger the NFT generation process.
*   Monitor generation progress and view logs.
*   View generated token data in a structured format.
*   Download generated metadata (JSON, CSV).
*   Validate the generated output against configuration rules and targets.

## 2. Proposed Technology

*   **Frontend/Application Framework:** Streamlit (due to its rapid development capabilities for data-centric Python applications).
*   **Backend Logic:** Existing Python scripts ([`src/generator.py`](src/generator.py), [`src/models.py`](src/models.py), [`src/exporter.py`](src/exporter.py)).

## 3. Phased Development Approach

### Phase 1: Core Application Setup & Generation Control

**Objective:** Establish the basic Streamlit application, allow users to set core generation parameters, and trigger the generation process with basic progress feedback.

**Key Features & Steps:**
1.  **Environment Setup:** Add `streamlit` to `requirements.txt`.
2.  **Initial `src/gui.py` Structure:**
    *   Import `streamlit as st`, `yaml`, project-specific modules.
    *   Set basic app title: `st.title("NFT Metadata Generator UI")`.
3.  **Layout & Parameter Inputs (Sidebar):**
    *   `st.sidebar.header("Generation Parameters")`.
    *   Inputs for Seed, Target Collection Size.
    *   Text inputs for paths to `numerology.yaml` and `rules.yaml` (to be enhanced in Phase 2).
4.  **"Generate NFTs" Button:**
    *   `st.sidebar.button("Generate NFTs")` to trigger the process.
5.  **Backend Integration:**
    *   Load `numerology_config` and `rules_config` from specified paths.
    *   Update `numerology_config['target_count']` with UI input.
    *   Instantiate `Generator` from `src/generator.py`.
6.  **Progress Bar & Status Updates:**
    *   `st.progress(0)` and `st.empty()` for status text.
    *   **Initial approach:** Simulate progress or use basic text updates.
    *   **Future enhancement:** Modify `Generator._emit_progress` for a callback mechanism to provide real-time progress updates to the Streamlit UI.
7.  **Trigger Generation & Display Outcome:**
    *   Call `generator_instance.generate_tokens()`.
    *   Display success (`st.success`) or error (`st.error`) messages.
    *   Store generated tokens and counts in `st.session_state` for use in other phases.

### Phase 2: Configuration Management

**Objective:** Allow users to view and manage the `numerology.yaml` and `rules.yaml` configuration files from within the UI.

**Key Features & Steps:**
1.  **Display Current Configurations:**
    *   Sections to show the content of loaded `numerology.yaml` and `rules.yaml` using `st.text_area` or `st.json`.
2.  **Configuration Input Method (Choose one or implement progressively):**
    *   **Option A (File Upload - Recommended Start):**
        *   `st.file_uploader` for `numerology.yaml` and `rules.yaml`.
        *   Uploaded files are parsed and used for generation.
    *   **Option B (Direct Text Edit - Advanced):**
        *   Allow editing YAML content in `st.text_area`.
        *   Include "Save/Apply" button with YAML validation.

### Phase 3: Output Viewing & Download

**Objective:** Enable users to view the generated token data in a structured table and download it in common formats.

**Key Features & Steps:**
1.  **Display Generated Tokens Table:**
    *   Use `st.dataframe` or `st.table` to display Token ID, traits, law number, etc., from `st.session_state.generated_tokens`.
    *   Ensure the table is sortable/searchable if using `st.dataframe`.
2.  **Download Options:**
    *   **JSON Download:**
        *   `st.download_button` to download full metadata as a JSON file.
        *   Requires a backend function to serialize token data to JSON.
    *   **CSV Download:**
        *   `st.download_button` to download a CSV representation (e.g., one token per row).
        *   Requires a backend function to format token data as CSV.

### Phase 4: Metadata Validation Display

**Objective:** Provide a UI section to validate the generated outputs against the defined numerology and rules, giving clear pass/fail feedback.

**Key Features & Steps:**
1.  **"Validate Output" Trigger:** A button or dedicated section to run validation.
2.  **Backend Validation Logic:**
    *   Adapt/reuse logic from `generator._final_validation_checks()` and/or `src/pre_validator.py`.
    *   Checks to include:
        *   Trait counts vs. target/tolerance.
        *   Incompatibility rule adherence.
        *   Token uniqueness.
        *   Category completeness.
3.  **Display Validation Results:**
    *   Overall summary (Pass/Fail).
    *   Detailed table/list for trait validation: `Trait Name`, `Category`, `Actual Count`, `Target`, `Tolerance`, `Status (✓/X)`. Use icons/colors.
    *   List any tokens violating incompatibility rules or found to be duplicates.

### Phase 5: Generation Log Viewing

**Objective:** Allow users to see the detailed logs produced during the generation process.

**Key Features & Steps:**
1.  **Log Display Area:**
    *   Use an `st.expander` or a separate tab.
    *   Display logs captured from `Generator._emit_progress` (either via callback or stdout redirection to `io.StringIO`).
    *   Make the log area scrollable.

## 4. UI Flow Diagram

```mermaid
graph TD
    A[Start: Open UI] --> B(Configuration);
    B --> B1[Load/Upload numerology.yaml];
    B --> B2[Load/Upload rules.yaml];
    B --> C(Generation Setup);
    C --> C1[Set Seed];
    C --> C2[Set Target Count];
    C --> D{Generate Tokens?};
    D -- Yes --> E[Show Progress Bar & Logs];
    E --> F{Generation Complete};
    F -- Success --> G(View Outputs);
    G --> G1[Display Token Table];
    G --> G2[Download JSON];
    G --> G3[Download CSV];
    G --> H(Validate Outputs);
    H --> H1[Display Validation Results (Pass/Fail per Trait/Rule)];
    F -- Failure --> I[Show Error Message & Logs];
    
    subgraph "Main Sections"
        direction LR
        B
        C
        G
        H
        I
    end

    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style G fill:#ccf,stroke:#333,stroke-width:2px
    style H fill:#ccf,stroke:#333,stroke-width:2px
    style I fill:#fcc,stroke:#333,stroke-width:2px
```

## 5. Key Implementation Considerations

*   **State Management:** Utilize `st.session_state` extensively to preserve data (configurations, generated tokens, validation results) across Streamlit's script reruns.
*   **Modularity:** Structure `src/gui.py` with functions for different UI sections/components to maintain clarity and reusability.
*   **Error Handling:** Implement comprehensive error handling (e.g., for file parsing, generation failures) and provide clear feedback to the user.
*   **User Experience:** Keep the UI clean, intuitive, and responsive.
*   **Backend Modifications:** Be prepared to make minor adjustments to `src/generator.py` (e.g., for progress callbacks) or `src/exporter.py` to support UI functionalities.

This plan provides a structured approach to developing the UI. Implementation will proceed phase by phase, starting with Phase 1.