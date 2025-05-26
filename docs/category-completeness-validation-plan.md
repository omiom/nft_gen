# Plan: Category Completeness Validation Display in UI

This document outlines the plan to add a "Category Completeness" validation status display to the Streamlit UI (`src/gui.py`) for the NFT Metadata Generator. This feature is part of completing Phase 4 of the original [`ui_development_plan.md`](ui_development_plan.md:83).

## 1. Background

The requirement is that **every token must have a trait from every *applicable* category defined in `numerology.yaml`**. The core `Generator` class in [`src/generator.py`](src/generator.py:1) already performs this validation internally during its `_final_validation_checks` method (specifically around [`src/generator.py:717-729`](src/generator.py:717)). If a token is found to be missing an applicable category, the generator raises a `ValueError` with a message like "Validation Error (Missing Category)...".

This plan focuses on reflecting the outcome of this existing internal generator check in the UI.

## 2. Objective

*   Provide clear feedback in the "Output Validation" tab of the UI regarding whether all generated tokens meet the category completeness criteria (for applicable categories).
*   Leverage the `Generator`'s internal validation to avoid redundant logic.
*   Display specific error information if a category completeness failure is the reason for a generation halt.

## 3. Implementation in `src/gui.py`

### 3.1. Session State for Error Messages

The implementation will use the already planned `st.session_state.generation_error_message` variable. This variable is set in the `try...except` block of the "Generate NFTs" button logic if any exception occurs during generation.

*   **Initialization (already planned for Token Uniqueness):**
    `st.session_state.generation_error_message = None` at the start of a generation attempt.
*   **Error Capturing (already planned for Token Uniqueness):**
    In the `except Exception as e:` block for generation, `st.session_state.generation_error_message = str(e)` will store the error.

### 3.2. UI Display in "Output Validation" Tab

A new section will be added to the "Output Validation" tab.

*   **Location:** Within the `with tab_validation:` block, logically placed among other validation results (e.g., after "Token Uniqueness").
*   **UI Elements and Logic:**

    ```python
    # Inside 'with tab_validation:' after other checks:
    st.markdown("---") # Separator
    st.markdown("#### Category Completeness")

    if 'generated_tokens' in st.session_state and st.session_state.generated_tokens:
        # If tokens were successfully generated, it implies the generator's internal 
        # category completeness check (for applicable categories) passed.
        st.success("✅ Category Completeness: All tokens possess traits from all applicable defined categories (as per generator's internal validation).")
    else:
        # Tokens were not generated, or generation failed.
        generation_error_msg = st.session_state.get('generation_error_message')
        if generation_error_msg and "Validation Error (Missing Category)" in generation_error_msg:
            st.error(f"❌ Category Completeness Check Failed: {generation_error_msg}")
        else:
            st.info("ℹ️ Category completeness status not determined. Generation may have failed, produced no tokens, or failed due to other validation issues. Check main error messages and logs.")
    ```

## 4. Mermaid Diagram (Interaction Flow)

This reuses the error message handling established for Token Uniqueness.

```mermaid
graph TD
    subgraph "Generation Process in src/gui.py"
        direction LR
        AA[Attempt generator.generate_tokens()] --> AB{Exception Occurred?};
        AB -- Yes --> AC[Store str(e) in st.session_state.generation_error_message, st.session_state.generated_tokens is None];
        AB -- No --> AD[Populate st.session_state.generated_tokens, st.session_state.generation_error_message is None/Empty];
    end

    subgraph "Validation Tab Display for Category Completeness"
        direction TB
        CA[User Navigates to Validation Tab] --> CB{`st.session_state.generated_tokens` Populated?};
        CB -- Yes --> CC[Display "✅ Category Completeness: All tokens possess traits from all applicable defined categories..."];
        CB -- No --> CD{`st.session_state.generation_error_message` contains "Validation Error (Missing Category)"?};
        CD -- Yes --> CE[Display "❌ Category Completeness Check Failed: [Error Message]"];
        CD -- No --> CF[Display "ℹ️ Category completeness status not determined..."];
    end
```

## 5. Next Steps

Once this plan is confirmed, the next step is to switch to "Code" mode to implement these changes in [`src/gui.py`](src/gui.py:1).