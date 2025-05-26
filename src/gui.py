import streamlit as st
import random # For randomizing seed
import yaml
import os # For joining paths
import sys
import itertools # For checking incompatibility pairs
import json
import csv
import io
import hashlib
from typing import Tuple, Optional # Added for type hinting

# Ensure src directory is in path for imports if running streamlit from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.generator import Generator
    from src.models import Token # Assuming Token might be useful later
    from src.pre_validator import PreValidator
except ImportError as e:
    st.error(f"Failed to import necessary modules. Ensure you are in the project root and src is in PYTHONPATH: {e}")
    st.stop()


# --- Page Config (must be the first Streamlit command) ---
st.set_page_config(initial_sidebar_state="expanded", page_title="NFT MetaGen UI")

# --- App Title ---
st.title("NFT Metadata Generator UI")
# Static informational message, always visible
st.info("Adjust parameters in the sidebar and click 'Validate Configuration Files' or 'Generate NFTs'. View active configurations below before generating.")

# --- Sidebar for Inputs ---
st.sidebar.header("⚙️ Generation Parameters")

# Initialize seed in session state if not present
if 'ui_seed' not in st.session_state:
    st.session_state.ui_seed = 69
if 'uploaded_numerology_file_state' not in st.session_state: # Added
    st.session_state.uploaded_numerology_file_state = None  # Added
if 'uploaded_rules_file_state' not in st.session_state:     # Added
    st.session_state.uploaded_rules_file_state = None        # Added
if 'validation_numerology_source_msg' not in st.session_state: # Added
    st.session_state.validation_numerology_source_msg = ""     # Added
if 'validation_rules_source_msg' not in st.session_state:       # Added
    st.session_state.validation_rules_source_msg = ""          # Added

# For Direct YAML Editing
if 'edit_numerology_mode' not in st.session_state:
    st.session_state.edit_numerology_mode = False
if 'edit_rules_mode' not in st.session_state:
    st.session_state.edit_rules_mode = False
if 'current_numerology_edit_str' not in st.session_state: # Stores text_area content live
    st.session_state.current_numerology_edit_str = ""
if 'current_rules_edit_str' not in st.session_state: # Stores text_area content live
    st.session_state.current_rules_edit_str = ""
if 'applied_edited_numerology_str' not in st.session_state: # Stores successfully applied edit
    st.session_state.applied_edited_numerology_str = None
if 'applied_edited_rules_str' not in st.session_state: # Stores successfully applied edit
    st.session_state.applied_edited_rules_str = None
# active_source_type will be determined by get_active_config_content_and_source
# and used to inform the user. We don't need separate session state for it if the function handles it.

def update_seed_randomly():
    st.session_state.ui_seed = random.randint(1, 1000000)

st.sidebar.number_input("Enter Seed", key="ui_seed", step=1)
st.sidebar.button("Randomize Seed", on_click=update_seed_randomly)

seed = st.session_state.ui_seed 
target_size = st.sidebar.number_input("Target Collection Size", value=420, min_value=1, step=1)

default_numerology_path = "numerology.yaml"
default_rules_path = "rules.yaml"

# Callbacks for file uploaders
def on_numerology_upload_change():
    st.session_state.uploaded_numerology_file_state = st.session_state.get('uploader_numerology_key')
    st.session_state.applied_edited_numerology_str = None # New upload overrides applied edit
    st.session_state.edit_numerology_mode = False      # Exit edit mode
    st.session_state.current_numerology_edit_str = ""  # Clear temp edit string
    # No need to rerun here, will rerun on next interaction or if main area depends on it.

def on_rules_upload_change():
    st.session_state.uploaded_rules_file_state = st.session_state.get('uploader_rules_key')
    st.session_state.applied_edited_rules_str = None   # New upload overrides applied edit
    st.session_state.edit_rules_mode = False        # Exit edit mode
    st.session_state.current_rules_edit_str = ""    # Clear temp edit string

# File Uploaders
st.sidebar.markdown("Upload custom configuration files (optional):")
st.sidebar.file_uploader(
    "Custom Numerology YAML",
    type=['yaml', 'yml'],
    help=f"Upload your custom numerology.yaml. If not provided, '{default_numerology_path}' will be used.",
    key='uploader_numerology_key', # Added key
    on_change=on_numerology_upload_change # Added on_change
)
st.sidebar.file_uploader(
    "Custom Rules YAML",
    type=['yaml', 'yml'],
    help=f"Upload your custom rules.yaml. If not provided, '{default_rules_path}' will be used.",
    key='uploader_rules_key', # Added key
    on_change=on_rules_upload_change # Added on_change
)

st.sidebar.markdown("---")

if st.sidebar.button("Validate Configuration Files"):
    st.session_state.pre_validation_results = None
    pv_numerology_config = None
    pv_rules_config = None
    validation_numerology_source = ""
    validation_rules_source = ""

    try:
        # Load Numerology Config for Validation (edited > uploaded > default)
        if st.session_state.applied_edited_numerology_str is not None:
            pv_numerology_config = yaml.safe_load(st.session_state.applied_edited_numerology_str)
            validation_numerology_source = "edited in UI"
        elif st.session_state.get('uploaded_numerology_file_state') is not None:
            uploaded_file = st.session_state.uploaded_numerology_file_state
            uploaded_file.seek(0)
            pv_numerology_config = yaml.safe_load(uploaded_file)
            uploaded_file.seek(0)
            validation_numerology_source = f"uploaded file ('{uploaded_file.name}')"
        else:
            if not os.path.exists(default_numerology_path):
                st.error(f"Default numerology file for validation not found at: {default_numerology_path}"); st.stop()
            with open(default_numerology_path, 'r') as f:
                pv_numerology_config = yaml.safe_load(f)
            validation_numerology_source = f"default file ('{default_numerology_path}')"
        
        if pv_numerology_config is None: pv_numerology_config = {}

        # Load Rules Config for Validation (edited > uploaded > default)
        if st.session_state.applied_edited_rules_str is not None:
            pv_rules_config = yaml.safe_load(st.session_state.applied_edited_rules_str)
            validation_rules_source = "edited in UI"
        elif st.session_state.get('uploaded_rules_file_state') is not None:
            uploaded_file = st.session_state.uploaded_rules_file_state
            uploaded_file.seek(0)
            pv_rules_config = yaml.safe_load(uploaded_file)
            uploaded_file.seek(0)
            validation_rules_source = f"uploaded file ('{uploaded_file.name}')"
        else:
            if not os.path.exists(default_rules_path):
                st.error(f"Default rules file for validation not found at: {default_rules_path}"); st.stop()
            with open(default_rules_path, 'r') as f:
                pv_rules_config = yaml.safe_load(f)
            validation_rules_source = f"default file ('{default_rules_path}')"

        if pv_rules_config is None: pv_rules_config = {}
        
        st.session_state.validation_numerology_source_msg = validation_numerology_source # Store in session state
        st.session_state.validation_rules_source_msg = validation_rules_source     # Store in session state
        # Removed st.caption from here
        pre_validator = PreValidator(pv_numerology_config, pv_rules_config)
        st.session_state.pre_validation_results = pre_validator.validate()

    except FileNotFoundError as e_pv: st.session_state.pre_validation_results = [f"ERROR: Default config file not found during validation: {e_pv}"]
    except yaml.YAMLError as e_pv_yaml: st.session_state.pre_validation_results = [f"ERROR: YAML parsing error during validation: {e_pv_yaml}"]
    except Exception as e_pv_exc: st.session_state.pre_validation_results = [f"ERROR: Unexpected pre-validation error: {e_pv_exc}"]

st.sidebar.markdown("---")

# --- Helper functions ---
def prepare_json_data(tokens_list):
    # ... (content remains the same)
    output_data = []
    for token in tokens_list:
        sorted_traits_str = json.dumps(sorted(token.traits.items()), sort_keys=True)
        hash_id = hashlib.md5(sorted_traits_str.encode('utf-8')).hexdigest()
        output_data.append({
            "token_id": token.token_id, "hash_id": hash_id, "traits": token.traits,
            "metadata": {"trait_count": len(token.traits)}
        })
    return output_data

def prepare_csv_data(tokens_list, numerology_config):
    # ... (content remains the same)
    if not tokens_list: return ""
    headers = ["Token ID", "Hash ID"]
    category_names = []
    if numerology_config and 'categories' in numerology_config:
        category_names = sorted(list(numerology_config['categories'].keys()))
    elif tokens_list: 
        all_cats = set(); [all_cats.update(token.traits.keys()) for token in tokens_list]; category_names = sorted(list(all_cats))
    headers.extend(category_names)
    headers.append("Trait Count") # Keep Trait Count
    output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=headers); writer.writeheader()
    for token in tokens_list:
        sorted_traits_str = json.dumps(sorted(token.traits.items()), sort_keys=True)
        hash_id = hashlib.md5(sorted_traits_str.encode('utf-8')).hexdigest()
        row = {"Token ID": token.token_id, "Hash ID": hash_id, "Trait Count": len(token.traits)}
        for cat_name in category_names: row[cat_name] = token.traits.get(cat_name, "")
        writer.writerow(row)
    return output.getvalue()

def get_active_config_content_and_source(
    applied_edited_str: Optional[str],
    uploaded_file_buffer: Optional[io.BytesIO],
    default_file_path: str,
    config_type_for_source_msg: str # "Numerology" or "Rules"
) -> Tuple[Optional[str], str]:
    """
    Determines active config content and its source description.
    Precedence: Applied Edit > Uploaded File > Default File.
    """
    source_desc_prefix = f"Active {config_type_for_source_msg} from: "
    if applied_edited_str is not None:
        return applied_edited_str, source_desc_prefix + "Edited in UI"
    
    if uploaded_file_buffer is not None:
        try:
            uploaded_file_buffer.seek(0)
            content = uploaded_file_buffer.getvalue().decode('utf-8')
            file_name = getattr(uploaded_file_buffer, 'name', 'uploaded_file')
            return content, source_desc_prefix + f"Uploaded File ('{file_name}')"
        except Exception as e:
            file_name = getattr(uploaded_file_buffer, 'name', 'uploaded_file')
            return f"# Error reading uploaded file '{file_name}': {e}", source_desc_prefix + f"Uploaded File ('{file_name}') - Error"
    
    # Fallback to default file
    if os.path.exists(default_file_path):
        try:
            with open(default_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, source_desc_prefix + f"Default File ('{default_file_path}')"
        except Exception as e:
            return f"# Error reading default file '{default_file_path}': {e}", source_desc_prefix + f"Default File ('{default_file_path}') - Error"
    else:
        return None, source_desc_prefix + f"Default File ('{default_file_path}') - Not Found"

# --- Main Area ---

# Display Active Configurations
st.subheader("📑 Active Configuration Files")
st.caption("The content shown here will be used for validation and generation if the respective buttons are clicked.")

active_numerology_buffer_for_display = st.session_state.get('uploaded_numerology_file_state')
active_rules_buffer_for_display = st.session_state.get('uploaded_rules_file_state')

# Get content for display based on precedence
numerology_content_to_display, numerology_source_desc = get_active_config_content_and_source(
    st.session_state.applied_edited_numerology_str,
    st.session_state.uploaded_numerology_file_state,
    default_numerology_path,
    "Numerology"
)
rules_content_to_display, rules_source_desc = get_active_config_content_and_source(
    st.session_state.applied_edited_rules_str,
    st.session_state.uploaded_rules_file_state,
    default_rules_path,
    "Rules"
)

with st.expander("🔎 View/Edit Active Numerology Config", expanded=False):
    st.markdown(f"**Source:** `{numerology_source_desc}`")
    if st.session_state.edit_numerology_mode:
        st.session_state.current_numerology_edit_str = st.text_area(
            "Edit Numerology YAML:",
            value=st.session_state.current_numerology_edit_str,
            height=300,
            key="numerology_editor_text_area_key" # Unique key
        )
        col_apply_num, col_revert_num = st.columns(2)
        with col_apply_num:
            if st.button("✅ Apply Edited Numerology", key="apply_numerology_edit_btn", help="Validates and applies the edited YAML as the active configuration for this session. An uploaded file will override this edit."):
                try:
                    yaml.safe_load(st.session_state.current_numerology_edit_str) # Validate
                    st.session_state.applied_edited_numerology_str = st.session_state.current_numerology_edit_str
                    st.session_state.edit_numerology_mode = False
                    # To ensure edit takes precedence, we could clear uploaded, but this might be too aggressive.
                    # The get_active_config function's precedence handles this.
                    # A new upload via on_change callback will clear applied_edited_numerology_str.
                    st.rerun()
                except yaml.YAMLError as ye:
                    st.error(f"Invalid YAML in Numerology: {ye}")
        with col_revert_num:
            if st.button("↩️ Cancel Numerology Edit", key="revert_numerology_edit_btn"):
                st.session_state.edit_numerology_mode = False
                # Content will revert to applied_edit (if any), then uploaded, then default on next display
                st.rerun()
    else:
        # VIEW MODE
        if st.button("✏️ Edit Numerology Config", key="edit_numerology_btn"): # Moved button up
            # Load current active content for editing
            content_to_edit, _ = get_active_config_content_and_source(
                st.session_state.applied_edited_numerology_str,
                st.session_state.uploaded_numerology_file_state,
                default_numerology_path,
                "Numerology" # Not strictly needed here, but consistent
            )
            st.session_state.current_numerology_edit_str = content_to_edit if content_to_edit is not None else ""
            st.session_state.edit_numerology_mode = True
            st.rerun()
        if numerology_content_to_display is not None: # Moved code display after button
            st.code(numerology_content_to_display, language='yaml', line_numbers=True)

with st.expander("🔎 View/Edit Active Rules Config", expanded=False):
    st.markdown(f"**Source:** `{rules_source_desc}`")
    if st.session_state.edit_rules_mode:
        st.session_state.current_rules_edit_str = st.text_area(
            "Edit Rules YAML:",
            value=st.session_state.current_rules_edit_str,
            height=300,
            key="rules_editor_text_area_key" # Unique key
        )
        col_apply_rules, col_revert_rules = st.columns(2)
        with col_apply_rules:
            if st.button("✅ Apply Edited Rules", key="apply_rules_edit_btn", help="Validates and applies the edited YAML as the active configuration for this session. An uploaded file will override this edit."):
                try:
                    yaml.safe_load(st.session_state.current_rules_edit_str) # Validate
                    st.session_state.applied_edited_rules_str = st.session_state.current_rules_edit_str
                    st.session_state.edit_rules_mode = False
                    st.rerun()
                except yaml.YAMLError as ye:
                    st.error(f"Invalid YAML in Rules: {ye}")
        with col_revert_rules:
            if st.button("↩️ Cancel Rules Edit", key="revert_rules_edit_btn"):
                st.session_state.edit_rules_mode = False
                st.rerun()
    else:
        # VIEW MODE
        if st.button("✏️ Edit Rules Config", key="edit_rules_btn"): # Moved button up
            content_to_edit, _ = get_active_config_content_and_source(
                st.session_state.applied_edited_rules_str,
                st.session_state.uploaded_rules_file_state,
                default_rules_path,
                "Rules"
            )
            st.session_state.current_rules_edit_str = content_to_edit if content_to_edit is not None else ""
            st.session_state.edit_rules_mode = True
            st.rerun()
        if rules_content_to_display is not None: # Moved code display after button
            st.code(rules_content_to_display, language='yaml', line_numbers=True)

st.markdown("---")

if 'pre_validation_results' in st.session_state and st.session_state.pre_validation_results:
    st.subheader("Configuration Pre-Validation Results")
    # Display the source caption here
    if st.session_state.validation_numerology_source_msg and st.session_state.validation_rules_source_msg:
        st.caption(f"Validated with numerology from {st.session_state.validation_numerology_source_msg} and rules from {st.session_state.validation_rules_source_msg}.")
    
    results = st.session_state.pre_validation_results
    if results == ["Configuration Valid"]: st.success("✅ Configuration is valid.")
    else: st.error(f"❌ Configuration has {len(results)} error(s).")
    with st.expander("View Pre-Validator Source Code", expanded=False):
        try:
            with open("src/pre_validator.py", "r") as f: pv_code = f.read(); st.code(pv_code, language="python")
        except Exception as e: st.error(f"Could not read pre_validator.py: {e}")
    st.markdown("---")

if st.sidebar.button("Generate NFTs"):
    # ... (generation logic remains the same) ...
    st.session_state.generated_tokens = None 
    st.session_state.raw_token_data_for_export = None
    st.session_state.trait_counts = None
    st.session_state.generation_log = [] 
    st.session_state.generator_instance = None 
    st.session_state.numerology_config_loaded = None
    st.session_state.generation_error_message = None # Initialize/clear previous error
    progress_bar = st.progress(0); status_text = st.empty()
    def log_message_to_ui(message: str): st.session_state.generation_log.append(message)
    try:
        log_message_to_ui("Loading configuration files..."); status_text.info("Loading configuration files...")
        numerology_config = None
        rules_config = None
        numerology_source_msg = ""
        rules_source_msg = ""

        # Load Numerology Config for Generation (edited > uploaded > default)
        if st.session_state.applied_edited_numerology_str is not None:
            numerology_config = yaml.safe_load(st.session_state.applied_edited_numerology_str)
            numerology_source_msg = "Numerology config loaded from: Edited in UI"
        elif st.session_state.get('uploaded_numerology_file_state') is not None:
            uploaded_file = st.session_state.uploaded_numerology_file_state
            uploaded_file.seek(0)
            numerology_config = yaml.safe_load(uploaded_file)
            uploaded_file.seek(0)
            numerology_source_msg = f"Numerology config loaded from: Uploaded File ('{uploaded_file.name}')"
        else:
            if not os.path.exists(default_numerology_path):
                err_msg = f"Default numerology file not found: {default_numerology_path}"; log_message_to_ui(f"ERROR: {err_msg}"); st.error(err_msg); st.stop()
            with open(default_numerology_path, 'r') as f: numerology_config = yaml.safe_load(f)
            numerology_source_msg = f"Numerology config loaded from: Default File ('{default_numerology_path}')"
        log_message_to_ui(numerology_source_msg)
        if numerology_config is None: err_msg = "Numerology config is empty/failed to load."; log_message_to_ui(f"ERROR: {err_msg}"); st.error(err_msg); st.stop()

        # Load Rules Config for Generation (edited > uploaded > default)
        if st.session_state.applied_edited_rules_str is not None:
            rules_config = yaml.safe_load(st.session_state.applied_edited_rules_str)
            rules_source_msg = "Rules config loaded from: Edited in UI"
        elif st.session_state.get('uploaded_rules_file_state') is not None:
            uploaded_file = st.session_state.uploaded_rules_file_state
            uploaded_file.seek(0)
            rules_config = yaml.safe_load(uploaded_file)
            uploaded_file.seek(0)
            rules_source_msg = f"Rules config loaded from: Uploaded File ('{uploaded_file.name}')"
        else:
            if not os.path.exists(default_rules_path):
                err_msg = f"Default rules file not found: {default_rules_path}"; log_message_to_ui(f"ERROR: {err_msg}"); st.error(err_msg); st.stop()
            with open(default_rules_path, 'r') as f: rules_config = yaml.safe_load(f)
            rules_source_msg = f"Rules config loaded from: Default File ('{default_rules_path}')"
        log_message_to_ui(rules_source_msg)
        if rules_config is None: err_msg = "Rules config is empty/failed to load."; log_message_to_ui(f"ERROR: {err_msg}"); st.error(err_msg); st.stop()

        st.session_state.numerology_config_loaded = numerology_config # Store the actually used config
        status_text.info(f"Using: {numerology_source_msg} & {rules_source_msg}")
        progress_bar.progress(10)
        
        numerology_config['target_count'] = target_size # Apply UI target size

        log_message_to_ui("Instantiating generator..."); status_text.info("Instantiating generator...")
        generator_instance = Generator(numerology_config, rules_config, seed=st.session_state.ui_seed, log_callback=log_message_to_ui)
        st.session_state.generator_instance = generator_instance; progress_bar.progress(20)
        
        log_message_to_ui("Starting generation..."); status_text.info("Starting generation...")
        generated_tokens_list = generator_instance.generate_tokens()
        progress_bar.progress(100); log_message_to_ui("Generation Complete!")
        status_text.success("Generation Complete!"); st.success(f"Successfully generated {len(generated_tokens_list)} tokens.")
        st.session_state.generated_tokens = generated_tokens_list
        st.session_state.raw_token_data_for_export = generator_instance.tokens_data
        st.session_state.trait_counts = generator_instance.trait_counts
    except FileNotFoundError as e:
        err_msg_fnf = f"A required default configuration file was not found: {e}"
        log_message_to_ui(f"ERROR: {err_msg_fnf}"); status_text.error(err_msg_fnf)
    except yaml.YAMLError as e:
        err_msg_yaml = f"YAML parsing error in configuration file(s): {e}"
        log_message_to_ui(f"ERROR: {err_msg_yaml}"); status_text.error(err_msg_yaml)
    except Exception as e:
        st.session_state.generation_error_message = str(e) # Store the error message
        err_msg_exc = f"Generation error: {e}"
        log_message_to_ui(f"ERROR: {err_msg_exc}"); status_text.error(err_msg_exc)
# Removed the conditional st.info message from here, as it's now static at the top.


if 'generated_tokens' in st.session_state and st.session_state.generated_tokens:
    tab_tokens, tab_validation, tab_log = st.tabs(["📊 Generated Tokens & Downloads", "✔️ Output Validation", "📜 Generation Log"])

    with tab_tokens:
        st.subheader("Generated Tokens")
        # ... (Generated Tokens Table logic remains the same) ...
        table_data_display = []
        current_numerology_config_display = st.session_state.numerology_config_loaded 
        if current_numerology_config_display and 'categories' in current_numerology_config_display:
            category_names_display_table = sorted(list(current_numerology_config_display['categories'].keys()))
        else: 
            category_names_display_table = sorted(list(st.session_state.generated_tokens[0].traits.keys())) if st.session_state.generated_tokens else []
        for token_obj_display in st.session_state.generated_tokens:
            row_data_display = {"Token ID": token_obj_display.token_id}
            for category_display in category_names_display_table:
                row_data_display[category_display] = token_obj_display.traits.get(category_display, "")
            # row_data_display["Law Number"] = token_obj_display.law_number # Removed Law Number
            table_data_display.append(row_data_display)
        if table_data_display:
            column_order_display = ["Token ID"] + category_names_display_table # Removed Law Number
            # Trait Count is not part of category_names_display_table, so it won't be added here unless explicitly handled.
            # The CSV and JSON will have it. For UI table, it's often derived or less critical than direct traits.
            valid_column_order_display = [col for col in column_order_display if col in table_data_display[0]]
            st.dataframe(table_data_display, column_order=valid_column_order_display)
        else: st.write("No token data to display.")

        st.markdown("---")
        st.subheader("Download Generated Metadata")
        # ... (Download logic remains the same) ...
        tokens_for_json_dl = prepare_json_data(st.session_state.generated_tokens)
        json_string_dl = json.dumps(tokens_for_json_dl, indent=2)
        csv_string_dl = prepare_csv_data(st.session_state.generated_tokens, st.session_state.get('numerology_config_loaded'))
        col1_dl, col2_dl = st.columns(2)
        with col1_dl: st.download_button(label="Download All as JSON", data=json_string_dl, file_name="nft_metadata_all.json", mime="application/json")
        with col2_dl: st.download_button(label="Download All as CSV", data=csv_string_dl, file_name="nft_metadata_all.csv", mime="text/csv")
        
        st.markdown("---") 
        with st.expander("View Generator Source Code", expanded=False):
            try:
                with open("src/generator.py", "r") as f: gen_code = f.read(); st.code(gen_code, language="python")
            except Exception as e: st.error(f"Could not read generator.py: {e}")

    with tab_validation:
        st.subheader("Output Validation")
        st.markdown("#### Trait Count Adherence")
        # ... (Trait Count Adherence table logic remains the same) ...
        if 'trait_counts' in st.session_state and 'numerology_config_loaded' in st.session_state:
            trait_counts_validation_data = []
            numerology_conf_val = st.session_state.numerology_config_loaded
            overall_trait_count_status = "✅ All trait counts within tolerance."
            for (category, trait_name), actual_count in sorted(list(st.session_state.trait_counts.items())):
                try:
                    trait_config = numerology_conf_val['categories'][category]['traits'][trait_name]
                    target = trait_config.get('target_count', 0); tolerance = trait_config.get('tolerance', 0)
                    deviation = actual_count - target; status = "✅ OK"
                    min_val = target - tolerance; max_val = target + tolerance
                    if actual_count < min_val: status = f"❌ Under (Min: {min_val})"; overall_trait_count_status = "⚠️ Some trait counts are outside tolerance."
                    elif actual_count > max_val: status = f"❌ Over (Max: {max_val})"; overall_trait_count_status = "⚠️ Some trait counts are outside tolerance."
                    trait_counts_validation_data.append({"Category": category, "Trait": trait_name, "Actual": actual_count, "Target": target, "Tol(±)": tolerance, "Deviation": deviation, "Status": status})
                except KeyError:
                    trait_counts_validation_data.append({"Category": category, "Trait": trait_name, "Actual": actual_count, "Target": "N/A", "Tol(±)": "N/A", "Deviation": "N/A", "Status": "⚠️ Config Missing"})
                    overall_trait_count_status = "⚠️ Config missing for some traits."
            if trait_counts_validation_data:
                st.dataframe(trait_counts_validation_data)
                if "⚠️" in overall_trait_count_status: st.warning(overall_trait_count_status)
                else: st.success(overall_trait_count_status)
            else: st.write("No trait count data available to validate.")
        else: st.info("Generate tokens to see trait count validation.")

        # Incompatibility Rule Adherence (No sub-header)
        if 'generator_instance' in st.session_state and st.session_state.generator_instance and \
           'generated_tokens' in st.session_state and st.session_state.generated_tokens:
            gen_instance_val = st.session_state.generator_instance; incompatibility_violations = []
            for token_obj_val in st.session_state.generated_tokens:
                assigned_traits_list_val = list(token_obj_val.traits.items())
                for trait_pair in itertools.combinations(assigned_traits_list_val, 2):
                    (cat1, trait1_val) = trait_pair[0]; (cat2, trait2_val) = trait_pair[1]
                    if not gen_instance_val._check_compatibility(cat1, trait1_val, cat2, trait2_val):
                        incompatibility_violations.append({"Token ID": token_obj_val.token_id, "Conflicting Trait 1": f"{cat1}: {trait1_val}", "Conflicting Trait 2": f"{cat2}: {trait2_val}"})
            if incompatibility_violations: st.warning(f"Found {len(incompatibility_violations)} incompatibility violation(s):"); st.dataframe(incompatibility_violations)
            else: st.success("✅ No incompatibility rule violations found.")
        else: st.info("Generate tokens to see incompatibility rule validation.")

        st.markdown("---")
        st.markdown("#### Token Uniqueness")
        if 'generated_tokens' in st.session_state and st.session_state.generated_tokens:
            st.success("✅ All generated tokens have unique trait combinations.")
        else:
            generation_error_msg = st.session_state.get('generation_error_message')
            if generation_error_msg and "Validation Error (Uniqueness)" in generation_error_msg:
                st.error(f"❌ Token Uniqueness Check Failed: {generation_error_msg}")
            else:
                st.info("ℹ️ Token uniqueness status not determined. Generation may have failed or produced no tokens. Check main error messages and logs.")
        
        st.markdown("---")
        st.markdown("#### Category Completeness")
        if 'generated_tokens' in st.session_state and st.session_state.generated_tokens:
            st.success("✅ Category Completeness: All tokens possess traits from all applicable defined categories (as per generator's internal validation).")
        else:
            generation_error_msg = st.session_state.get('generation_error_message')
            if generation_error_msg and "Validation Error (Missing Category)" in generation_error_msg:
                st.error(f"❌ Category Completeness Check Failed: {generation_error_msg}")
            else:
                st.info("ℹ️ Category completeness status not determined. Generation may have failed, produced no tokens, or failed due to other validation issues. Check main error messages and logs.")
 
        # Gender-Trait Mismatch Validation (No sub-header)
        if 'generator_instance' in st.session_state and st.session_state.generator_instance and \
           'generated_tokens' in st.session_state and st.session_state.generated_tokens and \
           'numerology_config_loaded' in st.session_state:
            gen_instance_gender_val = st.session_state.generator_instance; numerology_conf_gender_val = st.session_state.numerology_config_loaded; gender_mismatches = []
            for token_obj_gender_val in st.session_state.generated_tokens:
                token_id = token_obj_gender_val.token_id; token_traits = token_obj_gender_val.traits
                determined_token_gender = gen_instance_gender_val._get_token_gender(token_traits)
                if determined_token_gender in ["Male", "Female"]:
                    for trait_category, trait_name in token_traits.items():
                        try:
                            trait_config_gender = numerology_conf_gender_val['categories'][trait_category]['traits'][trait_name]
                            trait_gender_restriction = trait_config_gender.get('gender'); is_mismatch = False
                            if determined_token_gender == "Male" and trait_gender_restriction == "Female": is_mismatch = True
                            elif determined_token_gender == "Female" and trait_gender_restriction == "Male": is_mismatch = True
                            if is_mismatch: gender_mismatches.append({"Token ID": token_id, "Token Gender": determined_token_gender, "Mismatched Category": trait_category, "Mismatched Trait": trait_name, "Trait's Gender Spec": trait_gender_restriction})
                        except KeyError: pass 
            if gender_mismatches: st.warning(f"Found {len(gender_mismatches)} gender-trait mismatch(es):"); st.dataframe(gender_mismatches)
            else: st.success("✅ No gender-trait mismatches found.")
        else: st.info("Generate tokens to see gender-trait mismatch validation.")

        # Config file viewers for default on-disk files were here.
        # Removed as per user feedback since active configs are now shown in main area expanders.

        st.markdown("---")
        st.markdown("#### Tokens with 1/1 Traits")
        # ... (Tokens with 1/1 Traits logic remains the same) ...
        with st.expander("Show Tokens with 1/1 Traits", expanded=False):
            if 'trait_counts' in st.session_state and 'generated_tokens' in st.session_state:
                one_of_one_traits = []
                for (category, trait_name), actual_count in st.session_state.trait_counts.items():
                    if actual_count == 1: one_of_one_traits.append((category, trait_name))
                if not one_of_one_traits: st.success("✅ No traits with a count of exactly 1 found.")
                else:
                    st.write(f"Identified {len(one_of_one_traits)} trait(s) that appear only once.")
                    tokens_with_1_of_1s_data = []
                    for token_obj_unique in st.session_state.generated_tokens:
                        token_1_of_1_details_list = []
                        for cat_u, trait_u_name in token_obj_unique.traits.items():
                            if (cat_u, trait_u_name) in one_of_one_traits: token_1_of_1_details_list.append(f"{cat_u}: {trait_u_name}")
                        if token_1_of_1_details_list: tokens_with_1_of_1s_data.append({"Token ID": token_obj_unique.token_id, "1/1 Trait(s)": ", ".join(token_1_of_1_details_list)})
                    if tokens_with_1_of_1s_data: st.dataframe(tokens_with_1_of_1s_data)
                    else: st.info("No tokens found possessing any 1/1 traits.")
            else: st.info("Generate tokens to see collection uniqueness.")

    with tab_log:
        st.subheader("Generation Log")
        # ... (Log display logic remains the same) ...
        if 'generation_log' in st.session_state and st.session_state.generation_log:
            log_content = "\n".join(st.session_state.generation_log)
            st.text_area("Log Output:", value=log_content, height=400, disabled=True)
        else: st.info("No log messages recorded.")