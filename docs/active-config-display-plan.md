# Plan: Display Active Configuration in UI

This document outlines the plan to implement a feature in the Streamlit UI (`src/gui.py`) that allows users to view the content of the currently active `numerology.yaml` and `rules.yaml` files. This is a key part of completing Phase 2 of the [`ui_development_plan.md`](ui_development_plan.md:1).

## 1. Objective

To provide users with a clear and immediate way to inspect the exact configuration (either from an uploaded file or the default on-disk file) that will be used for NFT generation and pre-validation, before these actions are initiated.

## 2. UI Implementation

*   **Location:** Two new tabs will be added to the main area of the Streamlit application:
    *   "🔎 Active Numerology Config"
    *   "🔎 Active Rules Config"
*   These tabs will be placed near the top of the main content area, ideally visible before any generation results are displayed.

## 3. Logic and Implementation Details in `src/gui.py`

### 3.1. Session State for Uploaded Files

To ensure the active configuration tabs can access the most recently uploaded files (since Streamlit re-runs the script on interactions), the `UploadedFile` objects from the `st.file_uploader` widgets will be stored in `st.session_state`.

*   **Initialization:**
    ```python
    if 'uploaded_numerology_file_state' not in st.session_state:
        st.session_state.uploaded_numerology_file_state = None
    if 'uploaded_rules_file_state' not in st.session_state:
        st.session_state.uploaded_rules_file_state = None
    ```
*   **Callbacks for `st.file_uploader`:**
    ```python
    # In the sidebar section where file uploaders are defined:
    def store_numerology_upload():
        # 'uploaded_numerology_file_widget' is the key of the st.file_uploader
        if 'uploaded_numerology_file_widget' in st.session_state:
             st.session_state.uploaded_numerology_file_state = st.session_state.uploaded_numerology_file_widget

    def store_rules_upload():
        # 'uploaded_rules_file_widget' is the key of the st.file_uploader
        if 'uploaded_rules_file_widget' in st.session_state:
             st.session_state.uploaded_rules_file_state = st.session_state.uploaded_rules_file_widget

    # ... inside the sidebar ...
    uploaded_numerology_file_widget = st.sidebar.file_uploader(
        "Custom Numerology YAML", 
        type=['yaml', 'yml'], 
        help="Upload your custom numerology.yaml. If not provided, 'numerology.yaml' will be used.",
        key='uploaded_numerology_file_widget', # Unique key for the widget
        on_change=store_numerology_upload
    )
    # The actual variable `uploaded_numerology_file_widget` will be used by the generation/validation logic directly
    # if it needs the most up-to-date instance from the current script run.
    # The session state version is primarily for the independent display tabs.

    uploaded_rules_file_widget = st.sidebar.file_uploader(
        "Custom Rules YAML", 
        type=['yaml', 'yml'], 
        help="Upload your custom rules.yaml. If not provided, 'rules.yaml' will be used.",
        key='uploaded_rules_file_widget', # Unique key for the widget
        on_change=store_rules_upload
    )
    ```
    *Note: The generation and validation logic will also need to be updated to primarily use `st.session_state.uploaded_numerology_file_state` and `st.session_state.uploaded_rules_file_state` when determining which file to parse, falling back to default paths if these session state variables are `None`.*

### 3.2. Helper Function: `get_active_config_content_and_source`

This function will read the content and determine its source.

```python
import os # Ensure os is imported at the top of src/gui.py
from typing import Tuple, Optional # Ensure typing is imported

def get_active_config_content_and_source(uploaded_file_buffer: Optional[io.BytesIO], default_file_path: str) -> Tuple[Optional[str], str]:
    """
    Reads content from an uploaded file (BytesIO buffer) if available, 
    otherwise from a default path.
    Returns a tuple of (content_string_or_None, source_description_string).
    """
    if uploaded_file_buffer is not None:
        try:
            uploaded_file_buffer.seek(0) # Reset buffer pointer for reading
            content = uploaded_file_buffer.getvalue().decode('utf-8')
            # Use .name if available, otherwise a generic placeholder
            file_name = getattr(uploaded_file_buffer, 'name', 'uploaded_file') 
            return content, f"Uploaded File: '{file_name}'"
        except Exception as e:
            file_name = getattr(uploaded_file_buffer, 'name', 'uploaded_file')
            return f"# Error reading uploaded file '{file_name}': {e}", f"Uploaded File: '{file_name}' (Error)"
    else:
        if os.path.exists(default_file_path):
            try:
                with open(default_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, f"Default File: '{default_file_path}'"
            except Exception as e:
                return f"# Error reading default file '{default_file_path}': {e}", f"Default File: '{default_file_path}' (Error)"
        else:
            return None, f"Default File: '{default_file_path}' (Not Found)"
```

### 3.3. Tab Creation and Content Display

This code will be placed in the main area of the Streamlit app.

```python
# (Assumes default_numerology_path and default_rules_path are defined globally)

# --- Display Active Configurations ---
st.subheader("📑 Active Configuration Files")
st.caption("The content shown here will be used for validation and generation if the respective buttons are clicked.")

# Retrieve from session state for display purposes
active_numerology_buffer = st.session_state.get('uploaded_numerology_file_state')
active_rules_buffer = st.session_state.get('uploaded_rules_file_state')

numerology_content_to_display, numerology_source_desc = get_active_config_content_and_source(
    active_numerology_buffer,
    default_numerology_path 
)
rules_content_to_display, rules_source_desc = get_active_config_content_and_source(
    active_rules_buffer,
    default_rules_path
)

tab_active_num, tab_active_rules = st.tabs(["🔎 Active Numerology Config", "🔎 Active Rules Config"])

with tab_active_num:
    st.markdown(f"**Source:** `{numerology_source_desc}`")
    if numerology_content_to_display is not None:
        st.code(numerology_content_to_display, language='yaml', line_numbers=True)
    # If content is None, it means the default file was not found, and the source_desc already indicates this.
    # An additional warning might be redundant if source_desc is clear.

with tab_active_rules:
    st.markdown(f"**Source:** `{rules_source_desc}`")
    if rules_content_to_display is not None:
        st.code(rules_content_to_display, language='yaml', line_numbers=True)

st.markdown("---") # Separator before other main content (like generation results)
```

## 4. Mermaid Diagram (Flow)

```mermaid
graph TD
    subgraph Sidebar_Input
        direction TB
        S_INIT[Initialize st.session_state.uploaded_numerology_file_state = None]
        S_INIT2[Initialize st.session_state.uploaded_rules_file_state = None]
        
        S1[st.file_uploader for Numerology (key='num_widget', on_change=store_num_upload)] --> S2[Callback store_num_upload()]
        S2 --> S_UPDATE_NUM[Update st.session_state.uploaded_numerology_file_state = st.session_state.num_widget]
        
        S3[st.file_uploader for Rules (key='rules_widget', on_change=store_rules_upload)] --> S4[Callback store_rules_upload()]
        S4 --> S_UPDATE_RULES[Update st.session_state.uploaded_rules_file_state = st.session_state.rules_widget]
    end

    subgraph MainArea_ActiveConfigDisplayTabs
        direction TB
        M_TABS[Define Tabs: ActiveNum, ActiveRules]
        
        M_TABS --> M_GET_NUM_STATE[Read st.session_state.uploaded_numerology_file_state]
        M_GET_NUM_STATE --> M_CALL_HELPER_NUM[get_active_config_content_and_source(state, default_num_path)]
        M_CALL_HELPER_NUM --> M_CONTENT_NUM{Numerology Content & Source}
        M_CONTENT_NUM --> M_DISPLAY_NUM_SOURCE[Display Numerology Source in ActiveNum Tab]
        M_CONTENT_NUM --> M_DISPLAY_NUM_CONTENT[Display Numerology Content (st.code) in ActiveNum Tab]
        
        M_TABS --> M_GET_RULES_STATE[Read st.session_state.uploaded_rules_file_state]
        M_GET_RULES_STATE --> M_CALL_HELPER_RULES[get_active_config_content_and_source(state, default_rules_path)]
        M_CALL_HELPER_RULES --> M_CONTENT_RULES{Rules Content & Source}
        M_CONTENT_RULES --> M_DISPLAY_RULES_SOURCE[Display Rules Source in ActiveRules Tab]
        M_CONTENT_RULES --> M_DISPLAY_RULES_CONTENT[Display Rules Content (st.code) in ActiveRules Tab]
    end

    subgraph CoreLogic_Validation_Generation
        direction TB
        L_ACTION[User clicks Validate or Generate]
        L_ACTION --> L_READ_NUM_STATE[Read st.session_state.uploaded_numerology_file_state]
        L_READ_NUM_STATE --> L_PARSE_NUM{Parse Numerology: Uploaded or Default}
        
        L_ACTION --> L_READ_RULES_STATE[Read st.session_state.uploaded_rules_file_state]
        L_READ_RULES_STATE --> L_PARSE_RULES{Parse Rules: Uploaded or Default}
        
        L_PARSE_NUM --> L_PROCEED[Proceed with Action]
        L_PARSE_RULES --> L_PROCEED
    end
    
    Sidebar_Input -.-> CoreLogic_Validation_Generation;
    Sidebar_Input -.-> MainArea_ActiveConfigDisplayTabs;
```

## 5. Next Steps
After this plan is confirmed, the next step is to switch to "Code" mode to implement these changes in [`src/gui.py`](src/gui.py:1).