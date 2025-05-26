# Plan for Token Uniqueness Validation Display in UI

This document outlines the plan to add a "Token Uniqueness" validation check display to the Streamlit UI (`src/gui.py`) for the NFT Metadata Generator. This corresponds to an enhancement of Phase 4 of the original [`ui_development_plan.md`](ui_development_plan.md:83).

## 1. Background

The core `Generator` class in [`src/generator.py`](src/generator.py:1) already performs a token uniqueness check using trait hashes during its `_final_validation_checks` method ([`src/generator.py:686-704`](src/generator.py:686)). If duplicates are found, it raises a `ValueError`. The UI needs to reflect the outcome of this internal check.

## 2. Objectives

*   Provide clear feedback to the user within the "Output Validation" tab of the UI regarding the uniqueness of the generated token set.
*   Leverage the existing uniqueness check in the `Generator` class rather than re-implementing detection logic in the UI.
*   Offer specific error information if a uniqueness validation failure is the cause of a generation halt.

## 3. Proposed Implementation in `src/gui.py`

### 3.1. Modifying Generation Logic for Error Capturing

*   **Location:** The `try...except` block associated with the "Generate NFTs" button (currently around [`src/gui.py:168-240`](src/gui.py:168)).
*   **Changes:**
    1.  Initialize a new session state variable `st.session_state.generation_error_message = None` at the beginning of the "Generate NFTs" button's logic (e.g., after clearing `st.session_state.generated_tokens`).
    2.  In the `except Exception as e:` block ([`src/gui.py:238`](src/gui.py:238)), store the string representation of the exception:
        ```python
        st.session_state.generation_error_message = str(e)
        # Existing error logging and display remains
        err_msg_exc = f"Generation error: {e}"
        log_message_to_ui(f"ERROR: {err_msg_exc}"); status_text.error(err_msg_exc)
        ```

### 3.2. Adding Uniqueness Display to "Output Validation" Tab

*   **Location:** Within the "Output Validation" tab, created by `with tab_validation:` (currently around [`src/gui.py:287`](src/gui.py:287)). This new section can be placed logically among other validation checks (e.g., after "Incompatibility Rule Adherence").
*   **UI Elements and Logic:**
    ```python
    # Inside 'with tab_validation:'
    st.markdown("---") # Separator
    st.markdown("#### Token Uniqueness")

    if 'generated_tokens' in st.session_state and st.session_state.generated_tokens:
        # If tokens were successfully generated, it implies the generator's internal uniqueness check passed.
        st.success("✅ All generated tokens have unique trait combinations.")
    else:
        # Tokens were not generated, or generation failed.
        generation_error_msg = st.session_state.get('generation_error_message')
        if generation_error_msg and "Validation Error (Uniqueness)" in generation_error_msg:
            st.error(f"❌ Token Uniqueness Check Failed: {generation_error_msg}")
        else:
            st.info("ℹ️ Token uniqueness status not determined. Generation may have failed or produced no tokens. Check main error messages and logs.")
    ```

## 4. UI Flow Diagram

```mermaid
graph TD
    subgraph "Generation Process in src/gui.py"
        direction LR
        AA[Attempt generator.generate_tokens()] --> AB{Exception Occurred?};
        AB -- Yes --> AC[Store str(e) in st.session_state.generation_error_message, st.session_state.generated_tokens is None];
        AB -- No --> AD[Populate st.session_state.generated_tokens, st.session_state.generation_error_message is None/Empty];
    end

    subgraph "Validation Tab Display for Uniqueness"
        direction TB
        BA[User Navigates to Validation Tab] --> BB{`st.session_state.generated_tokens` Populated?};
        BB -- Yes --> BC[Display "✅ Token Uniqueness: All tokens unique."];
        BB -- No --> BD{`st.session_state.generation_error_message` contains "Validation Error (Uniqueness)"?};
        BD -- Yes --> BE[Display "❌ Token Uniqueness Check Failed: [Error Message]"];
        BD -- No --> BF[Display "ℹ️ Token Uniqueness: Not determined (check logs/main error)."];
    end
```

## 5. Next Steps

Once this plan is approved, the next step is to switch to "Code" mode to implement these changes in [`src/gui.py`](src/gui.py:1).