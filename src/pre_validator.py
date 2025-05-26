# src/pre_validator.py
"""
New Pre-Validation Module based on PRD v2.3 (prdv2.md)
"""
import yaml
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter

# Constants derived from prdv2.md or commonly used
COLLECTION_SIZE = 420

# Glyph Tiers and Law Ranges from prdv2.md power_system.glyph_tiers
GLYPH_TIER_DEFINITIONS = {
    "Sovereign": {"laws": (1, 7), "count_per_glyph": 1, "total_tier_count": 7},
    "Capo": {"laws": (8, 14), "count_per_glyph": 5, "total_tier_count": 35},
    "Soldier": {"laws": (15, 28), "count_per_glyph": 6, "total_tier_count": 84},
    "Street": {"laws": (29, 48), "total_tier_count": 210}, 
    "Blank": {"count_per_glyph": 84, "total_tier_count": 84} 
}

STREET_TIER_LAW_MIN = 29
STREET_TIER_LAW_MAX = 48
STREET_TIER_GLYPHS_AT_COUNT_10 = 10
STREET_TIER_GLYPHS_AT_COUNT_11 = 10


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None: 
                return {}
            return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file {file_path}: {e}")


class PreValidator:
    """
    Validates numerology and rules configurations based on prdv2.md.
    """
    def __init__(self, numerology_config: Dict[str, Any], rules_config: Dict[str, Any]):
        self.numerology_config = numerology_config
        self.rules_config = rules_config
        self.errors: List[str] = []
        
        self._all_defined_traits: Dict[Tuple[str, str], Dict[str, Any]] = {} 
        self._parsed_glyph_details: Dict[str, Dict[str, Any]] = {}


    def _log_error(self, message: str):
        self.errors.append(message)

    def _parse_glyph_name(self, glyph_name: str) -> Optional[int]:
        """Extracts law number from glyph_name, returns None if not parsable or 'blank'."""
        if glyph_name.lower() == "blank":
            return None 
        if glyph_name.startswith("glyph_") and len(glyph_name) > 6 and glyph_name[6:].isdigit():
            return int(glyph_name[6:])
        return None 

    def _get_glyph_tier_by_law(self, law_number: Optional[int]) -> Optional[str]:
        """Determines glyph tier based on law number."""
        if law_number is None:
            return "Blank" 
        if GLYPH_TIER_DEFINITIONS["Sovereign"]["laws"][0] <= law_number <= GLYPH_TIER_DEFINITIONS["Sovereign"]["laws"][1]:
            return "Sovereign"
        if GLYPH_TIER_DEFINITIONS["Capo"]["laws"][0] <= law_number <= GLYPH_TIER_DEFINITIONS["Capo"]["laws"][1]:
            return "Capo"
        if GLYPH_TIER_DEFINITIONS["Soldier"]["laws"][0] <= law_number <= GLYPH_TIER_DEFINITIONS["Soldier"]["laws"][1]:
            return "Soldier"
        if STREET_TIER_LAW_MIN <= law_number <= STREET_TIER_LAW_MAX:
            return "Street"
        return None

    def _validate_numerology_structure_and_basic_values(self):
        if not isinstance(self.numerology_config, dict):
            self._log_error("Numerology: numerology.yaml content is not a valid dictionary.")
            return

        if self.numerology_config.get('target_count') != COLLECTION_SIZE:
            self._log_error(
                f"Numerology: Root 'target_count' must be {COLLECTION_SIZE}, "
                f"found {self.numerology_config.get('target_count')}.")

        categories = self.numerology_config.get('categories')
        if not isinstance(categories, dict):
            self._log_error("Numerology: 'categories' field is missing or not a dictionary.")
            return

        for cat_name, cat_data in categories.items():
            if not isinstance(cat_data, dict):
                self._log_error(f"Numerology: Category '{cat_name}' data is not a dictionary.")
                continue
            
            traits = cat_data.get('traits')
            if not isinstance(traits, dict):
                self._log_error(f"Numerology: Category '{cat_name}' is missing 'traits' dictionary or it's not a dictionary.")
                continue

            for trait_name, trait_data in traits.items():
                if not isinstance(trait_data, dict):
                    self._log_error(f"Numerology: Trait '{trait_name}' in Category '{cat_name}' is not a dictionary.")
                    continue

                if 'tolerance' not in trait_data:
                    self._log_error(f"Numerology (tolerance_field_missing_or_non_int): Trait '{trait_name}' in Category '{cat_name}' is missing 'tolerance' field.")
                elif not isinstance(trait_data['tolerance'], int):
                    self._log_error(f"Numerology (tolerance_field_missing_or_non_int): Trait '{trait_name}' in Category '{cat_name}' has 'tolerance' that is not an integer.")

                if 'target_count' not in trait_data:
                     self._log_error(f"Numerology: Trait '{trait_name}' in Category '{cat_name}' is missing 'target_count' field.")
                elif not isinstance(trait_data['target_count'], int):
                     self._log_error(f"Numerology: Trait '{trait_name}' in Category '{cat_name}' has 'target_count' that is not an integer.")
                
                self._all_defined_traits[(cat_name, trait_name)] = trait_data

                if cat_name == "Glyph":
                    law_num = self._parse_glyph_name(trait_name)
                    tier = self._get_glyph_tier_by_law(law_num)
                    
                    if tier is None : # Covers malformed glyph names not caught by _parse_glyph_name explicitly (e.g. glyph_non_numeric)
                         self._log_error(f"Numerology: Glyph trait '{trait_name}' has a malformed name or unmappable law number; cannot determine tier.")
                    
                    self._parsed_glyph_details[trait_name] = {
                        'target_count': trait_data.get('target_count'),
                        'law_num': law_num,
                        'tier': tier,
                        'trait_data': trait_data
                    }

    def _check_numerology_invariant_category_sums(self):
        categories = self.numerology_config.get('categories', {})
        for cat_name, cat_data in categories.items():
            if not isinstance(cat_data, dict) or not isinstance(cat_data.get('traits'), dict):
                continue 
            
            current_category_sum = 0
            valid_category = True
            for trait_name, trait_data in cat_data['traits'].items():
                if isinstance(trait_data, dict) and isinstance(trait_data.get('target_count'), int):
                    current_category_sum += trait_data['target_count']
                else:
                    # Error already logged by _validate_numerology_structure_and_basic_values
                    valid_category = False
                    break 
            
            if not valid_category:
                self._log_error(f"Numerology Invariant (category_sum_mismatch): Cannot calculate sum for category '{cat_name}' due to invalid/missing trait target_counts.")
                continue

            if current_category_sum != COLLECTION_SIZE:
                self._log_error(
                    f"Numerology Invariant (category_sum_mismatch): Category '{cat_name}' sum of trait target_counts is {current_category_sum}, "
                    f"but must be {COLLECTION_SIZE}.")

    def _check_glyph_distribution(self):
        if "Glyph" not in self.numerology_config.get('categories', {}):
            self._log_error("Numerology Invariant (glyph_distribution): 'Glyph' category not found.")
            return

        actual_tier_counts = Counter()
        for glyph_name, details in self._parsed_glyph_details.items():
            tier = details.get('tier')
            target_count = details.get('target_count')

            if tier is None: # Should have been caught by structure validation if name was malformed
                self._log_error(f"Numerology Invariant (glyph_distribution): Could not determine tier for glyph '{glyph_name}'.")
                continue
            if not isinstance(target_count, int) or target_count < 0:
                self._log_error(f"Numerology Invariant (glyph_distribution): Invalid target_count for glyph '{glyph_name}'.")
                continue
            actual_tier_counts[tier] += target_count
        
        expected_distribution = {
            "Sovereign": GLYPH_TIER_DEFINITIONS["Sovereign"]["total_tier_count"],
            "Capo": GLYPH_TIER_DEFINITIONS["Capo"]["total_tier_count"],
            "Soldier": GLYPH_TIER_DEFINITIONS["Soldier"]["total_tier_count"],
            "Street": GLYPH_TIER_DEFINITIONS["Street"]["total_tier_count"],
            "Blank": GLYPH_TIER_DEFINITIONS["Blank"]["total_tier_count"]
        }

        for tier_name, expected_total_count in expected_distribution.items():
            if actual_tier_counts.get(tier_name, 0) != expected_total_count:
                self._log_error(
                    f"Numerology Invariant (glyph_distribution): Tier '{tier_name}' sum of target_counts is "
                    f"{actual_tier_counts.get(tier_name, 0)}, expected {expected_total_count}.")

        for glyph_name, details in self._parsed_glyph_details.items():
            tier = details.get('tier')
            target_count = details.get('target_count')
            if not isinstance(target_count, int): continue # Already caught

            if tier in ["Sovereign", "Capo", "Soldier"]:
                expected_glyph_tc = GLYPH_TIER_DEFINITIONS[tier]["count_per_glyph"]
                if target_count != expected_glyph_tc:
                    self._log_error(
                        f"Numerology Invariant (glyph_distribution): Glyph '{glyph_name}' (Tier: {tier}) "
                        f"has target_count {target_count}, expected {expected_glyph_tc}.")
            elif tier == "Blank" and glyph_name == "blank":
                 if target_count != GLYPH_TIER_DEFINITIONS["Blank"]["count_per_glyph"]:
                     self._log_error(
                        f"Numerology Invariant (glyph_distribution): Glyph 'blank' "
                        f"has target_count {target_count}, expected {GLYPH_TIER_DEFINITIONS['Blank']['count_per_glyph']}.")


    def _check_street_tier_split(self):
        if "Glyph" not in self.numerology_config.get('categories', {}):
            return

        street_glyphs_tc10 = 0
        street_glyphs_tc11 = 0
        other_street_counts = []

        num_street_glyphs_defined = 0
        for glyph_name, details in self._parsed_glyph_details.items():
            if details.get('tier') == "Street":
                num_street_glyphs_defined +=1
                target_count = details.get('target_count')
                if not isinstance(target_count, int):
                    self._log_error(f"Numerology Invariant (street_tier_split_incorrect): Invalid target_count for Street glyph '{glyph_name}'.")
                    return 
                if target_count == 10:
                    street_glyphs_tc10 += 1
                elif target_count == 11:
                    street_glyphs_tc11 += 1
                else:
                    other_street_counts.append(f"'{glyph_name}' (count: {target_count})")
        
        expected_total_street_glyphs = STREET_TIER_LAW_MAX - STREET_TIER_LAW_MIN + 1
        if num_street_glyphs_defined != expected_total_street_glyphs:
             self._log_error(
                f"Numerology Invariant (street_tier_split_incorrect): Defined {num_street_glyphs_defined} Street tier glyphs, "
                f"but expected {expected_total_street_glyphs} (Laws {STREET_TIER_LAW_MIN}-{STREET_TIER_LAW_MAX}).")


        if street_glyphs_tc10 != STREET_TIER_GLYPHS_AT_COUNT_10:
            self._log_error(
                f"Numerology Invariant (street_tier_split_incorrect): Found {street_glyphs_tc10} Street glyphs "
                f"with target_count 10, expected {STREET_TIER_GLYPHS_AT_COUNT_10}.")
        if street_glyphs_tc11 != STREET_TIER_GLYPHS_AT_COUNT_11:
            self._log_error(
                f"Numerology Invariant (street_tier_split_incorrect): Found {street_glyphs_tc11} Street glyphs "
                f"with target_count 11, expected {STREET_TIER_GLYPHS_AT_COUNT_11}.")
        if other_street_counts:
            self._log_error(
                f"Numerology Invariant (street_tier_split_incorrect): Street glyphs found with counts other than 10 or 11: {', '.join(other_street_counts)}.")

    def _validate_rules_structure_and_references(self):
        if not isinstance(self.rules_config, dict):
            self._log_error("Rules: rules.yaml content is not a valid dictionary.")
            return

        incompatibilities = self.rules_config.get('incompatibilities')
        if incompatibilities is None: return 
        if not isinstance(incompatibilities, list):
            self._log_error("Rules: 'incompatibilities' field must be a list.")
            return

        for i, rule in enumerate(incompatibilities):
            rule_id = f"rule #{i+1}"
            if not isinstance(rule, dict):
                self._log_error(f"Rules: Incompatibility {rule_id} is not a dictionary.")
                continue

            for key in ['trait_a', 'trait_b']:
                if key not in rule:
                    self._log_error(f"Rules: Incompatibility {rule_id} is missing '{key}'.")
                    continue
                ref = rule[key]
                if not (isinstance(ref, list) and len(ref) == 2 and isinstance(ref[0], str) and isinstance(ref[1], str)):
                    self._log_error(f"Rules: {rule_id}, '{key}' malformed. Expected [Cat, Val]. Got: {ref}")
                    continue
                if (ref[0], ref[1]) not in self._all_defined_traits:
                    self._log_error(f"Rules: {rule_id}, '{key}' references trait ['{ref[0]}', '{ref[1]}'] not in numerology.")
            
            ta, tb = rule.get('trait_a'), rule.get('trait_b')
            if isinstance(ta, list) and isinstance(tb, list) and ta == tb:
                 self._log_error(f"Rules: {rule_id} makes trait incompatible with itself: {ta}.")

            if 'breakable_by' in rule:
                bb_ref = rule['breakable_by']
                if not (isinstance(bb_ref, list) and len(bb_ref) == 2 and bb_ref[0] == "Glyph" and isinstance(bb_ref[1], str)):
                    self._log_error(f"Rules: {rule_id}, 'breakable_by' malformed. Expected ['Glyph', id]. Got: {bb_ref}")
                else:
                    glyph_id = bb_ref[1]
                    if glyph_id not in self._parsed_glyph_details:
                        self._log_error(f"Rules (glyph_reference_in_rules_not_found): {rule_id}, 'breakable_by' glyph '{glyph_id}' not in numerology.")
                    elif self._parsed_glyph_details[glyph_id].get('tier') != "Sovereign":
                        self._log_error(f"Rules (glyph_reference_in_rules_not_found): {rule_id}, 'breakable_by' glyph '{glyph_id}' is not Sovereign tier.")
            
            if 'description' in rule and not isinstance(rule['description'], str):
                self._log_error(f"Rules: {rule_id}, 'description' must be a string.")

    def _check_gender_specific_trait_overflow(self):
        if "Gender" not in self.numerology_config.get('categories', {}):
            self._log_error("Gender Overflow: 'Gender' category not found.")
            return
        
        gcats = self.numerology_config['categories']["Gender"].get("traits", {})
        if not gcats:
            self._log_error("Gender Overflow: 'Gender' category has no traits.")
            return

        gender_supply_min = {}
        for g_name, g_data in gcats.items():
            if not (isinstance(g_data, dict) and isinstance(g_data.get('target_count'), int) and isinstance(g_data.get('tolerance'), int)):
                self._log_error(f"Gender Overflow: Invalid config for Gender trait '{g_name}'.")
                continue
            gender_supply_min[g_name] = max(0, g_data['target_count'] - g_data['tolerance'])

        for cat_name, cat_data in self.numerology_config.get('categories', {}).items():
            if cat_name == "Gender" or not isinstance(cat_data, dict): continue

            cat_gender_demand = Counter()
            cat_gender_specific_to = cat_data.get('gender_specific_to')

            # --- TEMPORARY ADJUSTMENT for Gender Overflow ---
            # Check if the category is "fully unisex" (no category-level gender spec, and no trait-level gender specs within it)
            is_fully_unisex_category = not cat_gender_specific_to
            if is_fully_unisex_category:
                for _, trait_data_check in cat_data.get('traits', {}).items():
                    if isinstance(trait_data_check, dict) and 'gender' in trait_data_check:
                        is_fully_unisex_category = False # Found a trait with specific gender, so not "fully unisex"
                        break
            
            if is_fully_unisex_category:
                # print(f"Skipping gender overflow check for fully unisex category: {cat_name}") # Optional debug
                continue # Skip gender overflow check for this category
            # --- END TEMPORARY ADJUSTMENT ---

            for trait_name, trait_data in cat_data.get('traits', {}).items():
                if not (isinstance(trait_data, dict) and isinstance(trait_data.get('target_count'), int) and isinstance(trait_data.get('tolerance'), int)):
                    continue
                
                min_demand = max(0, trait_data['target_count'] - trait_data['tolerance'])
                applies_to_genders = set()
                trait_level_gender = trait_data.get('gender')

                if cat_gender_specific_to == "Gender": # Category's traits are linked to the main Gender category
                    if trait_level_gender:
                        if trait_level_gender in gender_supply_min: applies_to_genders.add(trait_level_gender)
                        elif trait_level_gender == "Unisex": applies_to_genders.update(gender_supply_min.keys())
                    else: # Trait itself is unisex within a Gender-linked category
                        applies_to_genders.update(gender_supply_min.keys())
                elif cat_gender_specific_to and cat_gender_specific_to != "Gender": # Category is specific to "Male", "Female", etc.
                    if trait_level_gender: # Trait further refines gender
                         if trait_level_gender == cat_gender_specific_to or trait_level_gender == "Unisex":
                            if cat_gender_specific_to in gender_supply_min: applies_to_genders.add(cat_gender_specific_to)
                    elif cat_gender_specific_to in gender_supply_min: # Trait applies to the category's specified gender
                        applies_to_genders.add(cat_gender_specific_to)
                
                elif not cat_gender_specific_to: # Category is generally unisex (but might have gendered traits, handled by is_fully_unisex_category check above)
                    if trait_level_gender:
                        if trait_level_gender in gender_supply_min: applies_to_genders.add(trait_level_gender)
                        elif trait_level_gender == "Unisex": applies_to_genders.update(gender_supply_min.keys())
                    else: # Trait is also unisex within a generally unisex category
                        applies_to_genders.update(gender_supply_min.keys())
                
                for g in applies_to_genders: cat_gender_demand[g] += min_demand
            
            for gender, demand in cat_gender_demand.items():
                supply = gender_supply_min.get(gender)
                if supply is None: continue 
                if demand > supply:
                    self._log_error(
                        f"Gender Overflow (gender_specific_trait_overflow): Category '{cat_name}', "
                        f"min demand for gender '{gender}' is {demand}, "
                        f"exceeds supply {supply}.")

    def validate(self) -> List[str]:
        self.errors = [] 
        self._all_defined_traits = {}
        self._parsed_glyph_details = {}

        self._validate_numerology_structure_and_basic_values()
        
        # Only proceed with deeper checks if basic structure and parsing were okay
        if not self.errors: # Or a threshold of errors
            self._check_numerology_invariant_category_sums()
            if "Glyph" in self.numerology_config.get('categories', {}): # Only if Glyph category exists
                self._check_glyph_distribution() 
                self._check_street_tier_split()

            self._validate_rules_structure_and_references()
            self._check_gender_specific_trait_overflow()

        if not self.errors:
            return ["Configuration Valid"]
        return self.errors

if __name__ == '__main__':
    print("Running New PreValidator (PRD v2.3) example...")
    # This example usage should load the actual project files when run.
    # For now, it uses simplified mock data to test the validator's own logic.

    # For actual file loading:
    # numerology_file = "path/to/your/numerology.yaml"
    # rules_file = "path/to/your/rules.yaml"
    # try:
    #     numerology_conf = load_yaml_config(numerology_file)
    #     rules_conf = load_yaml_config(rules_file)
    #     validator = PreValidator(numerology_conf, rules_conf)
    #     results = validator.validate()
    #     print("\\nValidation Results for project files:")
    #     if results == ["Configuration Valid"]:
    #         print("  Configuration Valid")
    #     else:
    #         for item in results:
    #             print(f"  - {item}")
    # except Exception as e:
    #     print(f"Error during validation: {e}")

    # --- Mock Tests ---
    mock_numerology_pass = {
        "target_count": 420,
        "categories": {
            "Gender": {"traits": {
                "Male": {"target_count": 180, "tolerance": 1},
                "Female": {"target_count": 180, "tolerance": 1},
                "Unisex": {"target_count": 60, "tolerance": 1}
            }}, # Sum = 420
            "Glyph": {"traits": {
                "glyph_01": {"target_count": 1, "tolerance": 0}, # Sovereign
                "glyph_08": {"target_count": 5, "tolerance": 1}, # Capo
                "glyph_15": {"target_count": 6, "tolerance": 1}, # Soldier
                "glyph_29": {"target_count": 10, "tolerance": 1}, # Street (1 of 10)
                "glyph_39": {"target_count": 11, "tolerance": 1}, # Street (1 of 10)
                "blank":    {"target_count": 84, "tolerance": 1}
                # ... (This mock is incomplete for full glyph distribution checks)
            }}
        }
    }
    # Fill out glyphs for a more complete mock test of distribution
    for i in range(1, 8): mock_numerology_pass["categories"]["Glyph"]["traits"][f"glyph_{i:02d}"] = {"target_count": 1, "tolerance": 0} # Sovereign
    for i in range(8, 15): mock_numerology_pass["categories"]["Glyph"]["traits"][f"glyph_{i:02d}"] = {"target_count": 5, "tolerance": 1} # Capo
    for i in range(15, 29): mock_numerology_pass["categories"]["Glyph"]["traits"][f"glyph_{i:02d}"] = {"target_count": 6, "tolerance": 1} # Soldier
    for i in range(29, 39): mock_numerology_pass["categories"]["Glyph"]["traits"][f"glyph_{i:02d}"] = {"target_count": 10, "tolerance": 1} # Street (10 of these)
    for i in range(39, 49): mock_numerology_pass["categories"]["Glyph"]["traits"][f"glyph_{i:02d}"] = {"target_count": 11, "tolerance": 1} # Street (10 of these)
    mock_numerology_pass["categories"]["Glyph"]["traits"]["blank"] = {"target_count": 84, "tolerance": 1}


    mock_rules_pass = {
        "incompatibilities": [
            {
                "trait_a": ["Gender", "Male"], 
                "trait_b": ["Glyph", "glyph_01"], 
                "breakable_by": ["Glyph", "glyph_01"], # Valid Sovereign
                "description": "Test rule"
            }
        ]
    }

    print("\\n--- Validating Mock Passing Config (PRD v2.3 rules) ---")
    validator_pass = PreValidator(mock_numerology_pass, mock_rules_pass)
    results_pass = validator_pass.validate()
    for item in results_pass:
        print(f"  - {item}")

    mock_numerology_fail_sum = { "target_count": 420, "categories": { "TestCat": {"traits": {"T1": {"target_count": 100, "tolerance":1}}}}} # Sum != 420
    print("\\n--- Validating Mock Fail Category Sum ---")
    validator_fail_sum = PreValidator(mock_numerology_fail_sum, mock_rules_pass)
    results_fail_sum = validator_fail_sum.validate()
    for item in results_fail_sum: print(f"  - {item}")

    mock_numerology_fail_street_split = {
        "target_count": 420,
        "categories": {
            "Glyph": {"traits": {
                 # Fill other tiers correctly
                "glyph_01": {"target_count": 1, "tolerance": 0}, "glyph_02": {"target_count": 1, "tolerance": 0}, "glyph_03": {"target_count": 1, "tolerance": 0}, "glyph_04": {"target_count": 1, "tolerance": 0}, "glyph_05": {"target_count": 1, "tolerance": 0}, "glyph_06": {"target_count": 1, "tolerance": 0}, "glyph_07": {"target_count": 1, "tolerance": 0},
                "glyph_08": {"target_count": 5, "tolerance": 1}, "glyph_09": {"target_count": 5, "tolerance": 1}, "glyph_10": {"target_count": 5, "tolerance": 1}, "glyph_11": {"target_count": 5, "tolerance": 1}, "glyph_12": {"target_count": 5, "tolerance": 1}, "glyph_13": {"target_count": 5, "tolerance": 1}, "glyph_14": {"target_count": 5, "tolerance": 1},
                "glyph_15": {"target_count": 6, "tolerance": 1}, "glyph_16": {"target_count": 6, "tolerance": 1}, "glyph_17": {"target_count": 6, "tolerance": 1}, "glyph_18": {"target_count": 6, "tolerance": 1}, "glyph_19": {"target_count": 6, "tolerance": 1}, "glyph_20": {"target_count": 6, "tolerance": 1}, "glyph_21": {"target_count": 6, "tolerance": 1}, "glyph_22": {"target_count": 6, "tolerance": 1}, "glyph_23": {"target_count": 6, "tolerance": 1}, "glyph_24": {"target_count": 6, "tolerance": 1}, "glyph_25": {"target_count": 6, "tolerance": 1}, "glyph_26": {"target_count": 6, "tolerance": 1}, "glyph_27": {"target_count": 6, "tolerance": 1}, "glyph_28": {"target_count": 6, "tolerance": 1},
                "glyph_29": {"target_count": 10, "tolerance": 1}, # Only 1 at count 10 (expects 10)
                "glyph_30": {"target_count": 11, "tolerance": 1}, # Only 1 at count 11 (expects 10)
                 # Fill remaining 18 street glyphs with count 10 to make sum work for category, but split is wrong
                **{f"glyph_{i:02d}": {"target_count": (210-1-1-10-11)//18, "tolerance":1} for i in range(31,49)}, # This calculation is too simple for real test
                "blank": {"target_count": 84, "tolerance": 1}
            }}
        }
    }
     # Correct the street sum for the faulty split mock for testing that check specifically
    street_sum_for_faulty_mock = 0
    street_tc_10_faulty_count = 0
    street_tc_11_faulty_count = 0
    
    temp_street_glyphs = {}
    # Create 9 glyphs at count 10
    for i in range(STREET_TIER_LAW_MIN, STREET_TIER_LAW_MIN + STREET_TIER_GLYPHS_AT_COUNT_10 -1):
        temp_street_glyphs[f"glyph_{i:02d}"] = {"target_count": 10, "tolerance": 1}
        street_sum_for_faulty_mock += 10
        street_tc_10_faulty_count +=1
    # Create 11 glyphs at count 11 (this is the error for the split)
    for i in range(STREET_TIER_LAW_MIN + STREET_TIER_GLYPHS_AT_COUNT_10 -1, STREET_TIER_LAW_MAX + 1):
        temp_street_glyphs[f"glyph_{i:02d}"] = {"target_count": 11, "tolerance": 1}
        street_sum_for_faulty_mock += 11
        street_tc_11_faulty_count +=1

    mock_numerology_fail_street_split["categories"]["Glyph"]["traits"].update(temp_street_glyphs)
    
    print("\\n--- Validating Mock Fail Street Tier Split ---")
    validator_fail_street = PreValidator(mock_numerology_fail_street_split, mock_rules_pass)
    results_fail_street = validator_fail_street.validate()
    for item in results_fail_street: print(f"  - {item}")

    mock_rules_fail_glyph_ref = {
        "incompatibilities": [{
            "trait_a": ["Gender", "Male"], "trait_b": ["Glyph", "glyph_01"], 
            "breakable_by": ["Glyph", "glyph_08"] # Capo, not Sovereign
        }]
    }
    print("\\n--- Validating Mock Fail Rule Breakable_by Tier ---")
    validator_fail_rule_glyph = PreValidator(mock_numerology_pass, mock_rules_fail_glyph_ref) # Use passing numerology
    results_fail_rule_glyph = validator_fail_rule_glyph.validate()
    for item in results_fail_rule_glyph: print(f"  - {item}")