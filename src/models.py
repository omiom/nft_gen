# src/models.py
"""
Data models for the NFT Metadata Generator, including the Token dataclass.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any # Added List, Optional, Any
import hashlib
import json

@dataclass
class Token:
    """
    Represents a single NFT token with its ID, traits, and metadata.
    """
    token_id: str  # Example: "001" to "420"
    traits: Dict[str, str]  # Example: {"CategoryName": "TraitValue", ...}

    # Metadata fields from PRD json_schema.exporter
    # Defaults are set here. Generator will be responsible for populating them.
    power_tier: str = "Common"
    power_score: int = 0
    law_number: Optional[int] = None # Can be int or null
    # trait_count is a property now
    special_abilities: List[str] = field(default_factory=list)
    set_bonuses: List[str] = field(default_factory=list)
    # Internal/helper attributes, not directly part of PRD export schema but useful
    # gender_identity: Optional[str] = None # Could store the determined gender more explicitly

    @property
    def trait_count(self) -> int:
        """Calculates the number of traits assigned to this token."""
        return len(self.traits)

    @property
    def hash_id(self) -> str:
        """
        Generates a SHA-1 hash of the token's traits.
        The hash is based on a canonical string representation of the sorted traits.
        """
        if not self.traits:
            return hashlib.sha1("".encode('utf-8')).hexdigest()

        # Sort traits by category name (key) to ensure consistent order for hashing
        sorted_trait_items = sorted(self.traits.items())

        # Create a canonical string representation using JSON dump
        # Using dict(sorted_trait_items) ensures the dictionary itself is ordered before dumping,
        # and sort_keys=True in json.dumps provides an additional layer of canonical representation
        # for the structure if traits were more complex (e.g. nested).
        canonical_string = json.dumps(dict(sorted_trait_items), sort_keys=True)

        return hashlib.sha1(canonical_string.encode('utf-8')).hexdigest()

    @property
    def gender(self) -> str:
        """
        Extracts the gender of the token primarily from its 'Body' trait value.
        This interpretation assumes the Body trait's value string contains gender information
        (e.g., "Human Male", "Robot Female").
        If the 'Body' trait is not present or doesn't explicitly state gender,
        it may return "Unknown".
        """
        body_trait_value = self.traits.get("Body", "").lower()

        if "female" in body_trait_value: # Check for "female" first
            return "Female"
        elif "male" in body_trait_value: # Then check for "male"
            return "Male"
        # Add more sophisticated parsing or keywords if needed for other genders like "Other"
        # For example, based on the PRD's "Augmented" (gender: "Other") example,
        # if the Body trait value were "Augmented Type Other", this could be caught.
        # Currently, it defaults to "Unknown" if not "male" or "female".
        # PRD example: `Body: "Augmented"` with `gender: "Other"` in numerology.
        # This property alone cannot infer "Other" from just "Augmented".
        # If a "Gender" trait is present (e.g. self.traits["Gender"]), that would be a more reliable source.
        # However, PRD 4.5 specifies "Extract from Body trait".
        
        # Check for "Gender" trait as a potentially more direct source,
        # though PRD 4.5 specifically mentions "Body trait".
        # If "Gender" trait is canonical for gender, this could be:
        # if "Gender" in self.traits:
        #    return self.traits["Gender"]
        # For now, strictly adhering to "Extract from Body trait" via string parsing.

        return "Unknown"

if __name__ == '__main__':
    # Example Usage:
    token1_traits = {"Background": "Alleyway", "Body": "Human Male", "Eyes": "Blue"}
    token1 = Token(token_id="001", traits=token1_traits)
    print(f"Token ID: {token1.token_id}")
    print(f"Traits: {token1.traits}")
    print(f"Hash ID: {token1.hash_id}")
    print(f"Gender (from Body): {token1.gender}")
    # Expected Gender: Male

    token2_traits = {"Body": "Cyborg Female", "Headwear": "Helmet", "Background": "Cityscape"} # Note: traits order changed
    token2 = Token(token_id="002", traits=token2_traits)
    print(f"\nToken ID: {token2.token_id}")
    print(f"Traits: {token2.traits}")
    print(f"Hash ID: {token2.hash_id}") # Should be different from a simple concat due to sorting
    print(f"Gender (from Body): {token2.gender}")
    # Expected Gender: Female
    
    token3_traits = {"Body": "Zombie", "Eyes": "Red"} # No explicit gender in "Zombie"
    token3 = Token(token_id="003", traits=token3_traits)
    print(f"\nToken ID: {token3.token_id}")
    print(f"Traits: {token3.traits}")
    print(f"Hash ID: {token3.hash_id}")
    print(f"Gender (from Body): {token3.gender}")
    # Expected Gender: Unknown (unless "Zombie Male" or similar was the trait value)

    token4_traits = {"Body": "Human Male", "Background": "Alleyway", "Eyes": "Blue"} # Same as token1 but different order
    token4 = Token(token_id="004", traits=token4_traits)
    print(f"\nToken ID: {token4.token_id}")
    print(f"Traits: {token4.traits}")
    print(f"Hash ID (should match token1): {token4.hash_id}")
    print(f"Gender (from Body): {token4.gender}")
    assert token1.hash_id == token4.hash_id, "Hash ID should be consistent regardless of initial trait order."

    token5_traits = {} # Empty traits
    token5 = Token(token_id="005", traits=token5_traits)
    print(f"\nToken ID: {token5.token_id}")
    print(f"Traits: {token5.traits}")
    print(f"Hash ID (for empty traits): {token5.hash_id}")
    print(f"Gender (from Body): {token5.gender}")

    # Example for hash consistency
    traits_a = {"Body": "Robot", "Accessory": "Laser"}
    traits_b = {"Accessory": "Laser", "Body": "Robot"}
    hash_a = Token("007", traits_a).hash_id
    hash_b = Token("008", traits_b).hash_id
    assert hash_a == hash_b, "Hashes should be identical for the same traits regardless of dict order."
    print(f"\nHash A: {hash_a}")
    print(f"Hash B: {hash_b} (Should be same as A)")
