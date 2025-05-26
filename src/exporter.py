# src/exporter.py
"""
Handles the export of generated NFT metadata to JSON and CSV formats.
"""
import json
import csv
import os
from typing import List, Dict, Any
import sys # Added for path adjustment
import os # Added for path adjustment

# Import the authoritative Token class from models.py
try:
    from src.models import Token
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.models import Token


class Exporter:
    """
    Exports token metadata to specified formats.
    """

    def __init__(self, output_dir_base: str = "output"):
        self.output_dir_base = output_dir_base
        self.versioned_output_dir = self._get_next_versioned_dir(self.output_dir_base)

    def _get_next_versioned_dir(self, base_dir_name: str) -> str:
        """
        Determines the next available versioned output directory.
        e.g., output_1, output_2, etc.
        The base_dir_name itself is used for the first attempt, then _1, _2 etc.
        According to PRD "Create versioned output directories: output_1/, output_2/, etc."
        So it starts with _1.
        """
        i = 1
        while True:
            # PRD specifies output_1, output_2, not output_base_1
            # This implies the base_dir_name itself might be the prefix if it's just "output"
            # Let's assume the provided output_dir_base is the root for versioned dirs
            # e.g. if output_dir_base is "my_outputs", it will create "my_outputs/run_1", "my_outputs/run_2"
            # Or, if output_dir_base is "output" (default), it creates "output_1", "output_2"
            # The PRD example is "output_1/", so if output_dir is "output", it should become "output_1"
            
            # If output_dir is "output", then "output_1", "output_2"
            # If output_dir is "custom_output", then "custom_output_1", "custom_output_2"
            
            dir_name_to_check = f"{base_dir_name}_{i}"

            # Check relative to the project root, not current working directory if this script is run directly
            # However, for library use, paths should be relative to where they are used or absolute
            # For now, let's assume it's relative to the execution context.
            if not os.path.exists(dir_name_to_check):
                return dir_name_to_check
            i += 1
    
    def _ensure_dir_exists(self, path: str):
        """Ensures that a directory exists, creating it if necessary."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True) # exist_ok=True is helpful

    def export_tokens(self, tokens: List[Token], numerology_categories: List[str]):
        """
        Generates all token data in memory and then writes all files in batch.
        `numerology_categories` should be a list of category names in desired order for CSV.
        """
        if not tokens:
            print("No tokens to export.")
            return

        # Create the versioned output directory
        self._ensure_dir_exists(self.versioned_output_dir)

        # Export to JSON
        json_output_dir = os.path.join(self.versioned_output_dir, "json")
        self._ensure_dir_exists(json_output_dir)
        self._export_to_json(tokens, json_output_dir)

        # Export to CSV
        csv_output_path = os.path.join(self.versioned_output_dir, "metadata.csv")
        self._export_to_csv(tokens, csv_output_path, numerology_categories)

        print(f"Successfully exported {len(tokens)} tokens to {self.versioned_output_dir}")

    def _export_to_json(self, tokens: List[Token], json_output_dir: str):
        """
        Exports each token to an individual JSON file.
        Format (as per PRD v2.3):
        {
            "token_id": "001",
            "hash_id": "abc123...",
            "traits": {
                "Background": "Alleyway",
                "Body": "Human Male",
                ...
            },
            "metadata": {
                "power_tier": "Common",
                "power_score": 10,
                "law_number": null,
                "trait_count": 3,
                "special_abilities": [],
                "set_bonuses": []
            }
        }
        """
        for token in tokens:
            file_path = os.path.join(json_output_dir, f"{token.token_id}.json")
            
            # Prepare metadata block with defaults for now
            # These would ideally come from the Token object if populated by the generator
            metadata_block = {
                "power_tier": getattr(token, 'power_tier', "Common"),
                "power_score": getattr(token, 'power_score', 0),
                "law_number": getattr(token, 'law_number', None), # Assuming None is acceptable for null
                "trait_count": len(token.traits), # This can be calculated directly
                "special_abilities": getattr(token, 'special_abilities', []),
                "set_bonuses": getattr(token, 'set_bonuses', [])
            }
            
            token_data = {
                "token_id": token.token_id,
                "hash_id": token.hash_id,
                "traits": token.traits,
                "metadata": metadata_block
            }
            with open(file_path, 'w') as f:
                json.dump(token_data, f, indent=4)
        # print(f"Exported {len(tokens)} tokens to JSON files in {json_output_dir}") # Covered by main export message

    def _export_to_csv(self, tokens: List[Token], csv_output_path: str, numerology_categories: List[str]):
        """
        Exports all tokens to a single CSV file.
        Headers: token_id,hash_id,Background,Body,Eyes,... (order from numerology_categories)
        """
        if not tokens:
            return

        # Headers based on PRD and numerology_categories for order
        fieldnames = ["token_id", "hash_id"] + numerology_categories
        
        with open(csv_output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore') # ignore extra keys in row_data
            writer.writeheader()
            for token in tokens:
                row_data = {
                    "token_id": token.token_id,
                    "hash_id": token.hash_id,
                }
                # Add trait values to the row, using .get for safety if a category is missing for a token
                for category in numerology_categories:
                    row_data[category] = token.traits.get(category, "") 
                writer.writerow(row_data)
        # print(f"Exported {len(tokens)} tokens to CSV file: {csv_output_path}") # Covered by main export message

if __name__ == '__main__':
    # Example Usage:
    # This block allows testing the exporter independently.
    # It requires the Token class (defined above as a placeholder).
    # In the actual project, Token would be imported from .models.

    print("Running Exporter example...")

    # Define sample numerology categories for CSV header order
    # This order should ideally come from the loaded numerology.yaml config
    sample_numerology_categories = ["Background", "Body", "Eyes", "Hat", "Masks"]


    # Sample tokens
    sample_tokens_data = [
        Token(token_id="001", traits={"Background": "Alleyway", "Body": "Human Male", "Eyes": "Blue"}),
        Token(token_id="002", traits={"Background": "Snow Forest", "Body": "Human Female", "Eyes": "Green", "Hat": "Crown"}),
        Token(token_id="003", traits={"Background": "Alleyway", "Body": "Zombie", "Eyes": "Red Glare", "Masks": "Ski Mask"}),
        Token(token_id="004", traits={"Background": "Alleyway", "Body": "Augmented", "Eyes": "Cyborg", "Hat": "Top Hat"}), # Body "Augmented"
    ]

    # The CLI will determine the actual output directory, e.g., "output"
    # The exporter then creates versioned subdirectories like "output_1", "output_2"
    # For this test, let's simulate the CLI providing "output" as the base.
    # The exporter will then create "output_1" (or output_N if others exist)
    
    # Create a temporary base output directory for the test if it doesn't exist
    if not os.path.exists("Projects/nft_metadata_generator/output"):
        os.makedirs("Projects/nft_metadata_generator/output")
        
    exporter = Exporter(output_dir_base="Projects/nft_metadata_generator/output") # Base directory for versioned runs
    
    # Important: The _get_next_versioned_dir logic creates names like "output_1", "output_2".
    # If output_dir_base is "Projects/nft_metadata_generator/output",
    # it will create "Projects/nft_metadata_generator/output_1", "Projects/nft_metadata_generator/output_2", etc.
    # This matches the PRD "output_1/", "output_2/" assuming the script is run from project root.
    # If a different base is needed, adjust Exporter initialization.
    # For example, if we want "Projects/nft_metadata_generator/output/run_1",
    # then init with Exporter(output_dir_base="Projects/nft_metadata_generator/output/run")

    exporter.export_tokens(sample_tokens_data, sample_numerology_categories)

    print(f"\nData exported to: {exporter.versioned_output_dir}")
    
    print(f"\nExample CSV content ({os.path.join(exporter.versioned_output_dir, 'metadata.csv')}):")
    try:
        with open(os.path.join(exporter.versioned_output_dir, "metadata.csv"), 'r') as f:
            print(f.read())
    except FileNotFoundError:
        print("CSV file not found. Check exporter logic and paths.")

    print(f"\nExample JSON content ({os.path.join(exporter.versioned_output_dir, 'json', '001.json')}):")
    try:
        with open(os.path.join(exporter.versioned_output_dir, "json", "001.json"), 'r') as f:
            print(f.read())
    except FileNotFoundError:
        print("JSON file for 001.json not found. Check exporter logic and paths.")

    print("\nVerifying genders from Body trait (example):")
    for t in sample_tokens_data:
        print(f"Token {t.token_id}, Body: '{t.traits.get('Body', '')}', Deduced Gender: {t.gender}")