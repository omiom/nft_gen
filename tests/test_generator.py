```python
# tests/test_generator.py
"""
Unit tests for the Generator module.
Focuses on algorithm phases and helper functions.
"""
import pytest
import random
from typing import Dict, Any

# Adjust the import path based on your project structure
# This assumes 'src' is a package and 'generator' is a module within it.
# If 'src' is directly in PYTHONPATH, 'from src.generator import Generator' might work.
# If running pytest from the project root, you might need to adjust sys.path or use relative imports.
# For now, let's assume a structure where this import works or will be made to work.
try:
    from src.generator import Generator
    from src.models import Token # Assuming Token will be defined here
except ImportError:
    # Fallback for environments where src is not immediately on path
    # This is a common pattern but might need adjustment based on test runner config
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
    from src.generator import Generator
    # from src.models import Token # Re-import after path adjustment

# --- Test Fixtures ---

@pytest.fixture
def basic_numerology_config() -> Dict[str, Any]:
    """A simple numerology configuration for testing."""
    return {
        "target_count": 3,
        "categories": {
            "Gender": {
                "traits": {
                    "Male": {"target_count": 2, "tolerance": 1},
                    "Female": {"target_count": 1, "tolerance": 1}
                }
            },
            "Hat": {
                "gender_specific_to": "Male",
                "traits": {
                    "Fedora": {"target_count": 1, "tolerance": 0}, # Male token 1
                    "Cap": {"target_count": 1, "tolerance": 0}     # Male token 2
                }
            },
            "Accessory": { # Unisex
                 "traits": {
                    "Watch": {"target_count": 2, "tolerance": 1},
                    "Ring": {"target_count": 1, "tolerance": 1}
                 }
            }
        }
    }

@pytest.fixture
def simple_rules_config() -> Dict[str, Any]:
    """A simple rules configuration, initially no incompatibilities."""
    return {"incompatibilities": []}

@pytest.fixture
def generator_instance(basic_numerology_config, simple_rules_config) -> Generator:
    """Returns a Generator instance initialized with basic configs and a fixed seed."""
    return Generator(numerology_config=basic_numerology_config, rules_config=simple_rules_config, seed=42)

# --- Test Helper Functions of Generator ---

def test_get_token_gender_from_gender_trait(generator_instance):
    # Test with "Gender" trait present
    token_traits_male = {"Gender": "Male", "Body": "Irrelevant"}
    assert generator_instance._get_token_gender(token_traits_male) == "Male"
    
    token_traits_female = {"Gender": "Female"}
    assert generator_instance._get_token_gender(token_traits_female) == "Female"

def test_get_token_gender_from_body_trait_fallback(generator_instance):
    # Requires numerology to have Body traits with 'gender' attribute
    # Let's add a temporary Body config to the instance for this test
    generator_instance.numerology_config["categories"]["Body"] = {
        "traits": {
            "RobotMale": {"gender": "Male", "target_count": 1, "tolerance": 1},
            "RobotFemale": {"gender": "Female", "target_count": 1, "tolerance": 1}
        }
    }
    token_traits_robot_male = {"Body": "RobotMale"}
    assert generator_instance._get_token_gender(token_traits_robot_male) == "Male"

    token_traits_robot_female = {"Body": "RobotFemale", "Accessory": "Watch"}
    assert generator_instance._get_token_gender(token_traits_robot_female) == "Female"
    
    token_traits_unknown = {"Body": "UnknownBodyType"}
    assert generator_instance._get_token_gender(token_traits_unknown) == "Unknown" # Or raises error

def test_is_category_applicable(generator_instance):
    # Unisex category
    assert generator_instance._is_category_applicable("Accessory", "Male") == True
    assert generator_instance._is_category_applicable("Accessory", "Female") == True
    
    # Gender-specific category
    assert generator_instance._is_category_applicable("Hat", "Male") == True  # Hat is for Male
    assert generator_instance._is_category_applicable("Hat", "Female") == False # Hat is not for Female

def test_get_valid_traits_for_category_gender_filtering(generator_instance):
    # Add a trait with specific gender to Accessory for testing
    generator_instance.numerology_config["categories"]["Accessory"]["traits"]["Necklace"] = {
        "gender": "Female", "target_count": 1, "tolerance": 1
    }
    
    # Male token, Accessory category
    # Should get Watch, Ring but not Necklace
    valid_for_male = generator_instance._get_valid_traits_for_category("Accessory", "Male", {})
    assert "Watch" in valid_for_male
    assert "Ring" in valid_for_male
    assert "Necklace" not in valid_for_male
    
    # Female token, Accessory category
    # Should get Watch, Ring, Necklace
    valid_for_female = generator_instance._get_valid_traits_for_category("Accessory", "Female", {})
    assert "Watch" in valid_for_female
    assert "Ring" in valid_for_female
    assert "Necklace" in valid_for_female

def test_get_valid_traits_incompatibility_filtering(generator_instance):
    # Add incompatibility: Accessory:Watch is incompatible with Hat:Fedora
    generator_instance.rules_config["incompatibilities"].append({
        "trait_a": ["Accessory", "Watch"], "trait_b": ["Hat", "Fedora"]
    })
    
    # Token is Male, has Hat:Fedora assigned. Looking for Accessory.
    assigned_traits = {"Hat": "Fedora", "Gender": "Male"}
    valid_accessories = generator_instance._get_valid_traits_for_category("Accessory", "Male", assigned_traits)
    
    # Watch should be filtered out due to incompatibility with Fedora
    assert "Watch" not in valid_accessories
    assert "Ring" in valid_accessories # Ring is still okay

def test_check_compatibility(generator_instance):
    generator_instance.rules_config["incompatibilities"].append({
        "trait_a": ["Masks", "Ski Mask"], "trait_b": ["Hat", "Top Hat"]
    })
    assert generator_instance._check_compatibility("Masks", "Ski Mask", "Hat", "Top Hat") == False
    assert generator_instance._check_compatibility("Hat", "Top Hat", "Masks", "Ski Mask") == False # Bidirectional
    assert generator_instance._check_compatibility("Masks", "Opera Mask", "Hat", "Top Hat") == True

def test_calculate_weights(generator_instance):
    # Test for Gender category, 2 tokens remaining in collection
    # Male: target 2, current 0
    # Female: target 1, current 0
    # Expected weights: Male (2-0)/2 = 1.0, Female (1-0)/2 = 0.5 (before normalization/min_value)
    # random.choices normalizes, so relative values matter.
    # generator_instance.trait_counts is initialized to 0 for all.
    
    category_name = "Gender"
    traits_in_gender = ["Male", "Female"]
    remaining_tokens = 2 # Total collection size is 3, 1 token being generated, 2 more to go
    
    weights = generator_instance._calculate_weights(category_name, traits_in_gender, remaining_tokens)
    
    # Check relative weighting: Male should be higher or equal if positive weights
    # The actual weight values depend on implementation details (e.g. min weight)
    # Male target=2, current=0 -> num = 2
    # Female target=1, current=0 -> num = 1
    # Assuming max(0.001, numerator / remaining_tokens)
    # Male weight: max(0.001, 2/2) = 1.0
    # Female weight: max(0.001, 1/2) = 0.5
    assert weights[traits_in_gender.index("Male")] > weights[traits_in_gender.index("Female")]
    assert weights[traits_in_gender.index("Male")] == 1.0 
    assert weights[traits_in_gender.index("Female")] == 0.5

    # Test when a trait is at target
    generator_instance.trait_counts[("Gender", "Female")] = 1 # Female is at target
    # Female target=1, current=1 -> num = 0. Weight should be min_positive (e.g. 0.001)
    weights_female_at_target = generator_instance._calculate_weights(category_name, traits_in_gender, remaining_tokens)
    assert weights_female_at_target[traits_in_gender.index("Male")] == 1.0
    assert weights_female_at_target[traits_in_gender.index("Female")] == 0.001 # or whatever small positive is chosen


# --- Test Main Generation Logic (Simplified) ---

def test_generate_tokens_basic_run(generator_instance):
    """
    Test a full generation run with a simple configuration.
    Checks for correct number of tokens, and basic structure.
    More detailed validation (uniqueness, counts) in integration tests.
    """
    tokens = generator_instance.generate_tokens()
    
    assert len(tokens) == generator_instance.numerology_config["target_count"] # Should be 3
    
    for i, token_data in enumerate(tokens):
        assert "token_id" in token_data
        assert token_data["token_id"] == str(i+1).zfill(3)
        assert "traits" in token_data
        assert isinstance(token_data["traits"], dict)
        
        # Check if Gender trait is assigned
        assert "Gender" in token_data["traits"]
        
        token_gender = token_data["traits"]["Gender"]
        
        # Check Hat: only for Males
        if token_gender == "Male":
            assert "Hat" in token_data["traits"]
        elif token_gender == "Female":
            assert "Hat" not in token_data["traits"] # Females should not have Hats per config
            
        # Check Accessory: for all
        assert "Accessory" in token_data["traits"]

def test_adjustment_phase_logic_conceptual(generator_instance):
    """
    Conceptual test for adjustment phase.
    This is hard to unit test fully without complex setup.
    Focus on whether it attempts to fix counts.
    """
    # Setup: Force a trait to be over-assigned after initial generation (mocking phase 1)
    # This requires more direct manipulation or a way to hook into the generator.
    # For a unit test, it might be better to test _can_swap and _execute_swap more directly,
    # or the sub-logic within the adjustment loop.
    
    # For now, this is a placeholder. True testing of adjustment needs specific scenarios.
    # E.g., create a state where one trait is over, one is under, and a swap is possible.
    
    # Example:
    # Token 0: {Gender: Male, Hat: Fedora, Accessory: Watch}
    # Token 1: {Gender: Male, Hat: Cap,    Accessory: Watch} # Watch is over-target if target was 1
    # Token 2: {Gender: Female,           Accessory: Ring}  # Ring is under-target if target was 2
    
    # If Watch target is 1, tolerance 0. Currently 2.
    # If Ring target is 2, tolerance 0. Currently 1.
    
    # A possible adjustment: Token 1 changes Accessory:Watch to Accessory:Ring
    # Requires _is_trait_valid_for_token(Ring, Accessory, {Gender:Male, Hat:Cap, Acc:Ring}, Male) to be true.
    
    # This kind of test is more of an integration or scenario test for the adjustment loop.
    pass


def test_is_trait_valid_for_token(generator_instance):
    # Token: Male, Has Hat:Fedora. Try to add Accessory:Watch.
    # Rule: Accessory:Watch incompatible with Hat:Fedora
    generator_instance.rules_config["incompatibilities"].append({
        "trait_a": ["Accessory", "Watch"], "trait_b": ["Hat", "Fedora"]
    })
    
    token_traits = {"Gender": "Male", "Hat": "Fedora"} # Trying to add Accessory:Watch
    token_gender = "Male"
    
    # Hypothetical state *after* adding Watch
    hypothetical_traits_with_watch = token_traits.copy()
    hypothetical_traits_with_watch["Accessory"] = "Watch"

    # Watch is incompatible with existing Fedora
    assert generator_instance._is_trait_valid_for_token(
        trait_to_check="Watch", 
        category_of_trait="Accessory", 
        token_all_traits=hypothetical_traits_with_watch, 
        token_gender=token_gender
    ) == False

    # Try adding Accessory:Ring (assuming Ring is compatible)
    hypothetical_traits_with_ring = token_traits.copy()
    hypothetical_traits_with_ring["Accessory"] = "Ring"
    assert generator_instance._is_trait_valid_for_token(
        trait_to_check="Ring", 
        category_of_trait="Accessory", 
        token_all_traits=hypothetical_traits_with_ring, 
        token_gender=token_gender
    ) == True

    # Test trait-level gender restriction
    # Accessory.Necklace is Female-only (from test_get_valid_traits_for_category_gender_filtering setup)
    generator_instance.numerology_config["categories"]["Accessory"]["traits"]["Necklace"] = {
        "gender": "Female", "target_count": 1, "tolerance": 1
    }
    hypothetical_traits_with_necklace = token_traits.copy() # token_traits is for a Male token
    hypothetical_traits_with_necklace["Accessory"] = "Necklace"
    assert generator_instance._is_trait_valid_for_token(
        trait_to_check="Necklace",
        category_of_trait="Accessory",
        token_all_traits=hypothetical_traits_with_necklace,
        token_gender="Male" # Male token trying to get Female trait
    ) == False


# --- More tests to consider ---
# - Test `_can_swap` and `_execute_swap` (these are complex due to state changes)
# - Test generation with more complex incompatibility rules.
# - Test generation where no valid traits can be found for a category (error handling).
# - Test the adjustment loop with specific scenarios leading to swaps or tolerance increase.
# - Test determinism (covered in test_determinism.py but could have a simple check here too).
# - Test edge cases for weight calculation (e.g., all traits at target).

# Note: Some functions in Generator.py (like _emit_progress) are side effects and harder to unit test
# directly without mocking or capturing output. For now, their direct testing is skipped.

```