# Plan: Direct YAML Editing in UI

This document outlines the plan to implement a feature in the Streamlit UI (`src/gui.py`) that allows users to directly edit the content of `numerology.yaml` and `rules.yaml` configurations. This corresponds to the "Advanced" option of Phase 2 in the original [`ui_development_plan.md`](ui_development_plan.md:1).

## 1. Objective

To provide users with an advanced method to modify active configurations directly within the UI, offering an alternative or supplement to file uploads for quick adjustments or experimentation.

## 2. UI Implementation

*   **Location:** The editing functionality will be integrated into the existing "🔎 View Active Numerology Config" and "🔎 View Active Rules Config" `st.expander` elements in the main UI area.
*   **Workflow:**
    1.  Each expander will initially display the active configuration content using `st.code`.
    2.  An "✏️ Edit Configuration" button within each expander will toggle an "edit mode."
    3.  In edit mode, the `st.code` display is replaced by an `st.text_area` pre-filled with the content of the configuration being viewed.
    4.  Below the `st.text_area`, two buttons will appear:
        *   "✅ Apply Edited Content"
        *   "↩️ Revert to Uploaded/Default" (or "Cancel Edit")
    5.  The source of the active configuration (default, uploaded, or edited) will be clearly indicated.

## 3. State Management (`st.session_state`)

The following session state variables will be used:

*   `st.session_state.edit_numerology_mode` (bool): `True` if the numerology editor is active, `False` otherwise.
*   `st.session_state.edit_rules_mode` (bool): `True` if the rules editor is active, `False` otherwise.
*   `st.session_state.current_numerology_edit_str` (str): Holds the live string content from the numerology `st.text_area`.
*   `st.session_state.current_rules_edit_str` (str): Holds the live string content from the rules `st.text_area`.
*   `st.session_state.applied_edited_numerology_str` (Optional[str]): Stores the last successfully validated and "applied" YAML string from the numerology editor. `None` if no edits applied or reverted.
*   `st.session_state.applied_edited_rules_str` (Optional[str]): Stores the last successfully validated and "applied" YAML string from the rules editor. `None` if no edits applied or reverted.
*   `st.session_state.active_numerology_source_type` (str): Indicates the current source: "default", "uploaded", or "edited".
*   `st.session_state.active_rules_source_type` (str): Indicates the current source: "default", "uploaded", or "edited".

*(Existing session state variables like `st.session_state.uploaded_numerology_file_state` and `st.session_state.uploaded_rules_file_state` will continue to be used for file uploads.)*

## 4. Detailed Logic in `src/gui.py`

### 4.1. Initialization of New Session State Variables

```python
# At the top with other session state initializations
if 'edit_numerology_mode' not in st.session_state:
    st.session_state.edit_numerology_mode = False
if 'edit_rules_mode' not in st.session_state:
    st.session_state.edit_rules_mode = False
if 'current_numerology_edit_str' not in st.session_state:
    st.session_state.current_numerology_edit_str = ""
if 'current_rules_edit_str' not in st.session_state:
    st.session_state.current_rules_edit_str = ""
if 'applied_edited_numerology_str' not in st.session_state:
    st.session_state.applied_edited_numerology_str = None
if 'applied_edited_rules_str' not in st.session_state:
    st.session_state.applied_edited_rules_str = None
if 'active_numerology_source_type' not in st.session_state:
    st.session_state.active_numerology_source_type = "default" # Or determine based on initial file presence
if 'active_rules_source_type' not in st.session_state:
    st.session_state.active_rules_source_type = "default"
```

### 4.2. Modifying `get_active_config_content_and_source`

This function will need to be aware of the new "edited" state.

```python
# Pseudocode adjustment for get_active_config_content_and_source
def get_active_config_content_and_source(
    applied_edited_str: Optional[str], 
    uploaded_file_buffer: Optional[io.BytesIO], 
    default_file_path: str,
    config_type_name: str # e.g., "Numerology"
) -> Tuple[Optional[str], str]:

    if applied_edited_str is not None:
        st.session_state[f'active_{config_type_name.lower()}_source_type'] = "edited"
        return applied_edited_str, f"Currently Active: Edited in UI"
    elif uploaded_file_buffer is not None:
        # ... (logic to read from uploaded_file_buffer) ...
        st.session_state[f'active_{config_type_name.lower()}_source_type'] = "uploaded"
        return content, f"Uploaded File: '{file_name}' (Active)"
    else:
        # ... (logic to read from default_file_path) ...
        st.session_state[f'active_{config_type_name.lower()}_source_type'] = "default"
        return content, f"Default File: '{default_file_path}' (Active)"
    # Handle errors and "Not Found" as before
```
The actual source for generation/validation will also need to check `applied_edited_..._str` first.

### 4.3. Logic within Each Config Expander (Example for Numerology)

```python
# Inside the "View Active Numerology Config" expander
# (Content of numerology_content_to_display and numerology_source_desc 
#  will be determined by the modified get_active_config_content_and_source)

st.markdown(f"**Source:** `{numerology_source_desc}`") # This will now reflect "edited" if applicable

if st.session_state.edit_numerology_mode:
    # --- EDIT MODE ---
    st.session_state.current_numerology_edit_str = st.text_area(
        "Edit Numerology YAML:", 
        value=st.session_state.current_numerology_edit_str, # Persists edits within text_area
        height=300,
        key="numerology_editor_text_area"
    )
    
    col_apply, col_revert = st.columns(2)
    with col_apply:
        if st.button("✅ Apply Edited Numerology", key="apply_numerology_edit"):
            try:
                yaml.safe_load(st.session_state.current_numerology_edit_str) # Validate YAML
                st.session_state.applied_edited_numerology_str = st.session_state.current_numerology_edit_str
                st.session_state.active_numerology_source_type = "edited"
                st.session_state.edit_numerology_mode = False
                # Clear uploaded file state for this config type to ensure edit takes precedence until next upload
                st.session_state.uploaded_numerology_file_state = None 
                st.experimental_rerun()
            except yaml.YAMLError as ye:
                st.error(f"Invalid YAML syntax in Numerology Config: {ye}")
            except Exception as ex:
                st.error(f"Error applying Numerology Config: {ex}")

    with col_revert:
        if st.button("↩️ Revert to Uploaded/Default", key="revert_numerology_edit"):
            st.session_state.applied_edited_numerology_str = None # Clear applied edit
            st.session_state.edit_numerology_mode = False
            # The get_active_config will now pick up uploaded or default
            st.experimental_rerun()
else:
    # --- VIEW MODE ---
    if numerology_content_to_display is not None:
        st.code(numerology_content_to_display, language='yaml', line_numbers=True)
    
    if st.button("✏️ Edit Numerology Config", key="edit_numerology_button"):
        # Load current active content into current_numerology_edit_str before switching to edit mode
        content_to_edit, _ = get_active_config_content_and_source(
            st.session_state.applied_edited_numerology_str, # Prioritize applied edit if exists
            st.session_state.uploaded_numerology_file_state,
            default_numerology_path,
            "Numerology"
        )
        st.session_state.current_numerology_edit_str = content_to_edit if content_to_edit else ""
        st.session_state.edit_numerology_mode = True
        st.experimental_rerun()

# Similar structure for Rules configuration
```

### 4.4. Updating File Uploader Callbacks

When a new file is uploaded, it should take precedence over any applied edits.
```python
def on_numerology_upload_change():
    st.session_state.uploaded_numerology_file_state = st.session_state.get('uploader_numerology_key')
    st.session_state.applied_edited_numerology_str = None # Clear applied edit
    st.session_state.edit_numerology_mode = False # Exit edit mode if active
    st.session_state.active_numerology_source_type = "uploaded" if st.session_state.uploaded_numerology_file_state else "default"

# Similar for on_rules_upload_change()
```

### 4.5. Updating Validation and Generation Logic

The logic for "Validate Configuration Files" and "Generate NFTs" must be updated to prioritize configurations in the following order:
1.  Content from `st.session_state.applied_edited_numerology_str` (if not `None`).
2.  Content from `st.session_state.uploaded_numerology_file_state` (if not `None`).
3.  Content from `default_numerology_path`.
(And similarly for rules).

## 5. Precedence Logic Summary

1.  **Applied Edit:** If `applied_edited_..._str` exists, it's used. `active_..._source_type` is "edited".
2.  **Uploaded File:** If no applied edit, and `uploaded_..._file_state` exists, it's used. `active_..._source_type` is "uploaded". Uploading a new file clears any "applied edit" for that config type.
3.  **Default File:** If no applied edit and no uploaded file, the default on-disk file is used. `active_..._source_type` is "default".
4.  **"Revert/Cancel Edit" Button:** Clears `applied_edited_..._str`. The system then falls back to uploaded or default.

## 6. Mermaid Diagram (Simplified Flow for one config type)

```mermaid
graph TD
    A[Expander: View/Edit Config] --> B{Edit Mode?};
    B -- No --> C[Display Active Config (st.code)];
    C --> D[Button: "✏️ Edit"];
    D -- Click --> E[Load current active to text_area_str, Set Edit Mode = True];

    B -- Yes --> F[Display st.text_area(value=text_area_str)];
    F --> G[Button: "✅ Apply"];
    G -- Click --> H{Validate YAML};
    H -- Valid --> I[Update applied_edited_str, Set Edit Mode = False, Clear uploaded_file_state for this type];
    H -- Invalid --> J[Show Error];
    
    F --> K[Button: "↩️ Revert/Cancel"];
    K -- Click --> L[Clear applied_edited_str, Set Edit Mode = False];

    M[File Uploader on_change] -- New Upload --> N[Update uploaded_file_state, Clear applied_edited_str, Set Edit Mode = False];

    subgraph Generation/Validation
        O[Action Triggered] --> P{applied_edited_str exists?};
        P -- Yes --> Q[Use applied_edited_str];
        P -- No --> R{uploaded_file_state exists?};
        R -- Yes --> S[Use uploaded_file_state];
        R -- No --> T[Use default_file_path];
    end
```

## 7. Next Steps
Implement these changes in [`src/gui.py`](src/gui.py:1) after switching to "Code" mode.