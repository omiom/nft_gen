```python
# tests/test_incompatibilities.py
"""
Tests for trait incompatibility rule enforcement.
Ensures that the generator does not produce tokens with incompatible traits
as defined in rules.yaml.
"""
import pytest
# Assuming the Generator and config loading utilities will be available
# from src.generator import Generator
# from src.utils import load_numerology_config, load_rules_config
# For now, using placeholders or simplified structures for testing concepts.

# Placeholder for a simplified way to check incompatibilities,
# similar to what might be in the Generator or a utility module.
def are_traits_incompatible(trait_a_category, trait_a_value, trait_b_category, trait_b_value, rules_config):
    """
    Checks if two specific traits are incompatible based on the rules.
    """
    if not rules_config or 'incompatibilities' not in rules_config:
        return False
    for rule in rules_config['incompatibilities']:
        ra_cat, ra_val = rule['trait_a']
        rb_cat, rb_val = rule['trait_b']
        if (trait_a_category == ra_cat and trait_a_value == ra_val and \
            trait_b_category == rb_cat and trait_b_value == rb_val) or \
           (trait_a_category == rb_cat and trait_a_value == rb_val and \
            trait_b_category == ra_cat and trait_b_value == ra_val):
            return True
    return False

# Sample configurations for testing
SAMPLE_NUMEROLOGY_CONFIG_INCOMPAT = {
    "target_count": 2, # Small for testing
    "categories": {
        "Hat": {
            "traits": {
                "Top Hat": {"target_count": 1, "tolerance": 1},
                "Baseball Cap": {"target_count": 1, "tolerance": 1}
            }
        },
        "Masks": {
            "traits": {
                "Ski Mask": {"target_count": 1, "tolerance": 1},
                "Opera Mask": {"target_count": 1, "tolerance": 1}
            }
        },
        "Eyes": { # Added for another rule
             "traits": {
                "Sunglasses": {"target_count": 1, "tolerance": 1},
                "Brown": {"target_count": 1, "tolerance": 1}
            }
        },
        "Body": { # Added for another rule
            "traits": {
                 "Zombie": {"target_count": 1, "tolerance": 1},
                 "Alien": {"target_count": 1, "tolerance": 1}
            }
        }
    }
}

SAMPLE_RULES_CONFIG_INCOMPAT = {
    "incompatibilities": [
        {"trait_a": ["Masks", "Ski Mask"], "trait_b": ["Hat", "Top Hat"]},
        {"trait_a": ["Body", "Zombie"], "trait_b": ["Eyes", "Sunglasses"]},
    ]
}

# This test suite will require a running Generator instance and its output.
# For now, these are conceptual tests of how one might verify incompatibility logic.

@pytest.mark.skip(reason="Requires full Generator implementation and config loading")
def test_generator_avoids_defined_incompatibilities(generator_instance_with_incompat_rules):
    """
    Test that the fully generated set of tokens does not violate any incompatibility rules.
    """
    # generator_instance_with_incompat_rules would be a fixture that sets up
    # the Generator with SAMPLE_NUMEROLOGY_CONFIG_INCOMPAT and SAMPLE_RULES_CONFIG_INCOMPAT
    tokens = generator_instance_with_incompat_rules.generate_tokens()
    rules = generator_instance_with_incompat_rules.rules_config

    for token in tokens:
        traits_list = list(token.traits.items())
        for i in range(len(traits_list)):
            for j in range(i + 1, len(traits_list)):
                cat1, val1 = traits_list[i]
                cat2, val2 = traits_list[j]
                assert not are_traits_incompatible(cat1, val1, cat2, val2, rules), \
                    f"Token {token.token_id} has incompatible traits: {cat1}:{val1} and {cat2}:{val2}"

def test_incompatibility_check_logic():
    """
    Directly test the `are_traits_incompatible` helper or similar logic
    that would be part of the Generator.
    """
    rules = SAMPLE_RULES_CONFIG_INCOMPAT
    # Test a defined incompatibility
    assert are_traits_incompatible("Masks", "Ski Mask", "Hat", "Top Hat", rules) == True
    # Test in reverse (rules should be bidirectional if helper implies it, or Generator handles it)
    assert are_traits_incompatible("Hat", "Top Hat", "Masks", "Ski Mask", rules) == True

    # Test another defined incompatibility
    assert are_traits_incompatible("Body", "Zombie", "Eyes", "Sunglasses", rules) == True

    # Test compatible traits
    assert are_traits_incompatible("Masks", "Opera Mask", "Hat", "Top Hat", rules) == False
    assert are_traits_incompatible("Body", "Alien", "Eyes", "Sunglasses", rules) == False
    assert are_traits_incompatible("Hat", "Baseball Cap", "Eyes", "Brown", rules) == False

    # Test with a trait not in rules
    assert are_traits_incompatible("Masks", "NonExistentMask", "Hat", "Top Hat", rules) == False
    
    # Test with empty rules
    empty_rules = {"incompatibilities": []}
    assert are_traits_incompatible("Masks", "Ski Mask", "Hat", "Top Hat", empty_rules) == False
    
    null_rules = {}
    assert are_traits_incompatible("Masks", "Ski Mask", "Hat", "Top Hat", null_rules) == False


@pytest.mark.skip(reason="Requires Generator's internal _check_compatibility or similar")
def test_generator_internal_compatibility_check(generator_instance):
    """
    Test the Generator's internal `_check_compatibility` method if accessible,
    or a similar utility function it uses.
    This assumes `generator_instance` is initialized with SAMPLE_RULES_CONFIG_INCOMPAT.
    """
    # gen = generator_instance (this would come from a fixture)
    # gen.rules_config = SAMPLE_RULES_CONFIG_INCOMPAT # Ensure rules are loaded

    # Placeholder for actual call:
    # assert gen._check_compatibility("Masks", "Ski Mask", "Hat", "Top Hat") == False # Incompatible
    # assert gen._check_compatibility("Hat", "Top Hat", "Masks", "Ski Mask") == False # Bidirectional
    # assert gen._check_compatibility("Masks", "Opera Mask", "Hat", "Top Hat") == True # Compatible
    pass

# More tests could include:
# - Complex chains of incompatibilities (if the system should detect/prevent them at a higher level, e.g. pre_validator.py)
# - Scenarios where an incompatibility might make a certain trait impossible to assign.

if __name__ == "__main__":
    # This allows running pytest on this file directly if needed
    # For example: python -m pytest tests/test_incompatibilities.py
    # You'll need to install pytest: pip install pytest
    
    # Manual run of a test for quick check without pytest runner:
    print("Running manual check for test_incompatibility_check_logic:")
    test_incompatibility_check_logic()
    print("Manual check for test_incompatibility_check_logic passed.")
```