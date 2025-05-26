```python
# tests/test_determinism.py
"""
Tests for ensuring the deterministic nature of the NFT generation process
based on a given seed.
"""

import pytest
import os
import yaml

# Assuming the generator and supporting classes will be in src
# Adjust these imports as the project structure solidifies
# from src.generator import Generator
# from src.models import Token # If needed for comparison
# from src.pre_validator import PreValidator # If pre-validation affects determinism indirectly

# For now, since the actual Generator class is complex and might not be fully stubbed,
# these tests will be more conceptual or will require a simplified mock/stub.
# We'll assume a function `run_generation_process(seed, numerology_path, rules_path)`
# that encapsulates the full generation and returns the list of token data (e.g., list of dicts).

# Mock/placeholder for the generation function
# This would eventually call the actual Generator().generate_tokens()
def mock_run_generation_process(seed: int, numerology_config: dict, rules_config: dict) -> list:
    """
    A simplified mock of the generation process for testing determinism.
    It should use the seed to produce a predictable output.
    """
    # In a real test, this would initialize and run the actual Generator
    # from src.generator import Generator
    # generator = Generator(numerology_config=numerology_config, rules_config=rules_config, seed=seed)
    # tokens_data = generator.generate_tokens() # Assuming this returns list of dicts or Token objects
    # return tokens_data

    # Simplified deterministic output based on seed for placeholder:
    # This is NOT how the real generator works but serves to test the determinism test itself.
    output = []
    # Ensure the number of tokens matches target_count for consistency
    num_tokens = numerology_config.get("target_count", 3) # Default to 3 for simple test configs

    for i in range(num_tokens):
        # Create pseudo-random (but deterministic from seed) traits
        # The actual generator would have complex logic here.
        # This simplified version just ensures output changes with seed predictably.
        trait_value_base = (seed + i) % 100
        output.append({
            "token_id": str(i + 1).zfill(3),
            "traits": {
                "CategoryA": f"TraitA_val{trait_value_base}",
                "CategoryB": f"TraitB_val{trait_value_base + 1}",
                # If 'Gender' and 'Body' are critical for the PRD's example generator:
                "Gender": "Male" if (seed + i) % 2 == 0 else "Female",
                "Body": f"BodyType{(seed + i) % 3}"
            }
            # In real scenario, include hash_id if Token objects are returned
        })
    return output

# Sample minimal numerology and rules for testing
# These should be loaded from files in a real test setup if required by the generator
SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM = {
    "target_count": 3,
    "categories": {
        "Gender": {
            "traits": {
                "Male": {"target_count": 2, "tolerance": 1},
                "Female": {"target_count": 1, "tolerance": 1}
            }
        },
        "Body": {
             "traits": {
                "BodyType0": {"target_count": 1, "tolerance": 1, "gender": "Male"},
                "BodyType1": {"target_count": 1, "tolerance": 1, "gender": "Female"},
                "BodyType2": {"target_count": 1, "tolerance": 1, "gender": "Male"}
            }
        },
        "CategoryA": {
            "traits": {
                f"TraitA_val{i}": {"target_count": 1, "tolerance": 1} for i in range(100)
            }
        },
        "CategoryB": {
            "traits": {
                f"TraitB_val{i}": {"target_count": 1, "tolerance": 1} for i in range(101)
            }
        }
    }
}

SAMPLE_RULES_CONFIG_DETERMINISM = {
    "incompatibilities": []
}


def get_token_representation(token_data: dict) -> tuple:
    """
    Creates a stable, sortable representation of a token's traits for comparison.
    Input is a dictionary representing a token (e.g. from generator).
    """
    # Sort traits by category name to ensure consistent order for comparison
    # Example: {"token_id": "001", "traits": {"CatA": "Val1", "CatB": "Val2"}}
    # Sorting traits: [("CatA", "Val1"), ("CatB", "Val2")]
    if not isinstance(token_data, dict) or "traits" not in token_data or not isinstance(token_data["traits"], dict):
        raise TypeError("Token data must be a dict with a 'traits' dictionary.")
    
    sorted_traits = tuple(sorted(token_data["traits"].items()))
    # Include token_id if it's part of the deterministic output being checked
    # return (token_data.get("token_id"), sorted_traits)
    # For pure trait generation determinism, sorted_traits might be enough if token_ids are sequential.
    # However, if token_id assignment or hash_id is also part of seeded generation, include them.
    # For now, focusing on traits.
    return sorted_traits


class TestDeterminism:
    """
    Test suite for generation determinism.
    """

    def test_same_seed_produces_same_output(self):
        """
        Tests that running the generation process multiple times with the same seed
        produces the exact same set of tokens and traits.
        """
        seed = 12345
        
        # Run generation process first time
        # In a real test, load configs from files or use shared fixtures
        output1_raw = mock_run_generation_process(seed, SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM, SAMPLE_RULES_CONFIG_DETERMINISM)
        
        # Run generation process second time with the same seed
        output2_raw = mock_run_generation_process(seed, SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM, SAMPLE_RULES_CONFIG_DETERMINISM)

        assert len(output1_raw) == len(output2_raw), "Number of generated tokens differs for the same seed."

        # Convert to a comparable format (e.g., set of tuples of sorted trait items)
        # This ensures order of tokens doesn't matter, but content of each token does.
        # If order of tokens *must* also be deterministic, compare lists directly.
        # The PRD implies a collection, so set comparison is usually fine for content.
        # However, token_ids are sequential ("001" to "420"), so list order might be intended.

        # Let's assume token order should be deterministic as well.
        output1_repr = [get_token_representation(t) for t in output1_raw]
        output2_repr = [get_token_representation(t) for t in output2_raw]
        
        assert output1_repr == output2_repr, \
            "Generated token data differs for the same seed.\n" \
            f"Output 1: {output1_repr}\nOutput 2: {output2_repr}"

    def test_different_seeds_produce_different_output(self):
        """
        Tests that running the generation process with different seeds
        produces different sets of tokens and traits.
        This test is probabilistic: it's theoretically possible (though extremely unlikely
        for a good PRNG and complex generation) that two different seeds produce identical
        outputs for a small N. If this test flickers, the generation might be too simple
        or the seeds chosen too close / PRNG quality is low.
        """
        seed1 = 12345
        seed2 = 54321

        assert seed1 != seed2, "Seeds for this test must be different."

        output1_raw = mock_run_generation_process(seed1, SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM, SAMPLE_RULES_CONFIG_DETERMINISM)
        output2_raw = mock_run_generation_process(seed2, SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM, SAMPLE_RULES_CONFIG_DETERMINISM)

        # It's possible the number of tokens is the same (target_count)
        # So we must compare the content.
        if len(output1_raw) == SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM["target_count"] and \
           len(output2_raw) == SAMPLE_NUMEROLOGY_CONFIG_DETERMINISM["target_count"]:
            
            output1_repr = [get_token_representation(t) for t in output1_raw]
            output2_repr = [get_token_representation(t) for t in output2_raw]

            # For this test to be robust, a significant difference is expected.
            # If only one trait on one token differs, it's still different.
            assert output1_repr != output2_repr, \
                "Generated token data is unexpectedly the same for different seeds.\n" \
                f"Seed 1 Output: {output1_repr}\nSeed 2 Output: {output2_repr}"
        else:
            # If lengths differ, that's also a difference.
            # (Though for a fixed target_count, lengths should be same unless generation fails)
            pass # Assertion will be implicitly true if lengths differ and one is non-empty.
                 # If target_count is fixed, this path is less likely.

    # More tests could be added:
    # - Test with more complex configurations.
    # - If the generator uses external libraries that might have their own global random state,
    #   ensure the Generator class properly isolates its random number generation.
    # - Test that if numerology/rules change but seed is same, output is different.
    #   (This isn't strictly determinism of the *seed*, but determinism of the *input state*)

# To run these tests (pytest needs to be installed):
# Ensure you are in the root of the project (e.g., nft_metadata_generator)
# Command: pytest tests/test_determinism.py
# Or simply: pytest (if __init__.py files are correctly set up in tests/ and src/)

if __name__ == '__main__':
    # Example of how to run a test function directly (for debugging)
    # This is not standard for pytest, but can be useful.
    # Note: pytest fixtures and some advanced features might not work this way.
    
    # For direct execution, ensure paths for config loading (if any) are correct.
    # The mock_run_generation_process currently takes configs directly.

    print("Running determinism tests manually...")
    
    test_suite = TestDeterminism()
    
    print("\nTesting same_seed_produces_same_output...")
    try:
        test_suite.test_same_seed_produces_same_output()
        print("PASSED: test_same_seed_produces_same_output")
    except AssertionError as e:
        print(f"FAILED: test_same_seed_produces_same_output\n{e}")

    print("\nTesting different_seeds_produce_different_output...")
    try:
        test_suite.test_different_seeds_produce_different_output()
        print("PASSED: test_different_seeds_produce_different_output")
    except AssertionError as e:
        print(f"FAILED: test_different_seeds_produce_different_output\n{e}")

```