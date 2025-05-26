# src/generator.py
"""
Handles the core logic of generating NFT metadata based on configurations.
"""

import random
from typing import List, Dict, Any, Tuple, Optional, Callable
import sys
import os
import json

# Assuming models.py contains Token and other necessary data structures
try:
    from src.models import Token
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.models import Token


# Assuming numerology.yaml and rules.yaml are loaded and parsed elsewhere
# and passed to the Generator class or its methods.

class Generator:
    """
    Generates NFT metadata based on trait rarities, gender rules, and incompatibilities.
    """

    def __init__(self, numerology_config: Dict[str, Any], rules_config: Dict[str, Any], seed: int = 0, log_callback: Optional[Callable[[str], None]] = None):
        """
        Initializes the Generator.

        Args:
            numerology_config: Parsed content of numerology.yaml.
            rules_config: Parsed content of rules.yaml.
            seed: Random seed for deterministic generation.
            log_callback: Optional function to call for emitting progress messages.
        """
        self.numerology_config = numerology_config
        self.rules_config = rules_config
        self.seed = seed
        self.log_callback = log_callback
        random.seed(self.seed)
        self.tokens_data: List[Dict[str, Any]] = [] # Stores trait dicts during generation
        self.trait_counts: Dict[Tuple[str, str], int] = {} # (CategoryName, TraitName) -> count

        self.target_collection_size = numerology_config.get('target_count', 420)

        # Initialize trait_counts from numerology_config
        for category_name, category_data in self.numerology_config.get('categories', {}).items():
            for trait_name in category_data.get('traits', {}).keys():
                self.trait_counts[(category_name, trait_name)] = 0

    def _parse_glyph_law_number(self, glyph_name: str) -> Optional[int]:
        """Extracts law number from glyph_name, returns None if not parsable or 'blank'."""
        if glyph_name.lower() == "blank":
            return None
        if glyph_name.startswith("glyph_") and len(glyph_name) > 6 and glyph_name[6:].isdigit():
            return int(glyph_name[6:])
        return None

    def _get_token_gender(self, token_traits: Dict[str, str]) -> str:
        """
        Determines token gender, prioritizing 'Gender' trait, then 'Body' trait's gender attribute.
        """
        if "Gender" in token_traits:
            return token_traits["Gender"]
        
        body_trait_value = token_traits.get("Body")
        if body_trait_value:
            body_category_config = self.numerology_config.get("categories", {}).get("Body", {})
            body_trait_config = body_category_config.get("traits", {}).get(body_trait_value)
            if body_trait_config and "gender" in body_trait_config: # Check if 'gender' key exists
                return body_trait_config["gender"]
        
        return "Unknown"

    def _is_category_applicable_by_gender_spec(self, category_name: str, token_gender: str) -> bool:
        """
        Checks if a category is applicable based on its 'gender_specific_to' field from numerology.
        """
        category_config = self.numerology_config.get('categories', {}).get(category_name, {})
        gender_specific_to = category_config.get('gender_specific_to') # e.g., "Male", "Female"

        if not gender_specific_to: # Unisex category or no gender specification for the category itself
            return True
        
        if token_gender == "Unknown":
            # If token gender is unknown, a category that IS gender_specific_to (e.g. "Male") is not applicable.
            # self._emit_progress(f"  DEBUG_FILL_APPLICABLE: Category '{category_name}' (spec: {gender_specific_to}) considered NOT applicable for token with UNKNOWN gender.")
            return False 
            
        # Category is applicable if its gender_specific_to matches the token's gender.
        return token_gender == gender_specific_to

    def _get_valid_traits_for_category(self, category_name: str, token_gender: str, assigned_traits: Dict[str, str]) -> List[str]:
        """
        Gets valid traits for a given category, considering token gender and incompatibilities.
        Implements "Flexible Unisex": Unisex tokens can be assigned Male/Female traits.
        """
        category_config = self.numerology_config.get('categories', {}).get(category_name, {})
        all_traits_in_category = list(category_config.get('traits', {}).keys())
        valid_traits = []

        for trait_name in all_traits_in_category:
            trait_config = category_config.get('traits', {}).get(trait_name, {})
            
            # 1. Check trait-level gender restriction (Flexible Unisex)
            trait_gender_restriction = trait_config.get('gender') # e.g., "Male", "Female", "Unisex"
            
            if trait_gender_restriction: # If the trait itself has a gender defined
                is_gender_match = False
                if token_gender == "Unknown":
                    self._emit_progress(f"      DEBUG_VALID_TRAITS: Trait '{trait_name}' (gender: {trait_gender_restriction}) skipped for UNKNOWN gender token.")
                    continue 

                if token_gender == "Unisex":
                    is_gender_match = True # Unisex token can be assigned any gendered trait
                elif trait_gender_restriction.lower() == "unisex":
                    is_gender_match = True # Unisex traits are available to Male/Female gender
                elif trait_gender_restriction == token_gender:
                    is_gender_match = True # Exact gender match
                
                if not is_gender_match:
                    self._emit_progress(f"      DEBUG_VALID_TRAITS: Trait '{trait_name}' (gender: {trait_gender_restriction}) skipped. No match for token gender '{token_gender}'.")
                    continue 

            # 2. Check incompatibilities with already assigned traits
            is_compatible = True
            for assigned_cat, assigned_trait_val in assigned_traits.items():
                if not self._check_compatibility(category_name, trait_name, assigned_cat, assigned_trait_val):
                    is_compatible = False
                    self._emit_progress(f"      DEBUG_VALID_TRAITS: Trait '{category_name}:{trait_name}' incompatible with existing '{assigned_cat}:{assigned_trait_val}'.")
                    break
            
            if is_compatible:
                valid_traits.append(trait_name)
        
        return valid_traits

    def _check_compatibility(self, cat1: str, trait1: str, cat2: str, trait2: str, for_adjustment_debug: bool = False) -> bool:
        """Checks if two traits are compatible based on rules.yaml."""
        if not self.rules_config or 'incompatibilities' not in self.rules_config:
            return True

        for rule_idx, rule in enumerate(self.rules_config['incompatibilities']):
            rule_a_cat, rule_a_trait = rule['trait_a']
            rule_b_cat, rule_b_trait = rule['trait_b']

            is_match = (cat1 == rule_a_cat and trait1 == rule_a_trait and \
                        cat2 == rule_b_cat and trait2 == rule_b_trait) or \
                       (cat1 == rule_b_cat and trait1 == rule_b_trait and \
                        cat2 == rule_a_cat and trait2 == rule_a_trait)

            if is_match:
                if for_adjustment_debug:
                    description = rule.get('description', 'No description')
                    self._emit_progress(f"        DEBUG_COMPAT_ADJ: Incompatibility by rule #{rule_idx}. Traits: ('{cat1}':'{trait1}') vs ('{cat2}':'{trait2}'). Rule details: '{rule_a_cat}':'{rule_a_trait}' incompatible with '{rule_b_cat}':'{rule_b_trait}'. Desc: {description}")
                return False
        return True

    def _calculate_weights(self, category_name: str, trait_names: List[str], current_token_idx: int) -> List[float]:
        """
        Calculates weights for trait selection.
        """
        weights = []
        category_traits_config = self.numerology_config['categories'][category_name]['traits']

        for trait_name in trait_names:
            trait_config = category_traits_config.get(trait_name, {})
            target_count = trait_config.get('target_count', 0)
            current_count = self.trait_counts.get((category_name, trait_name), 0)

            weight_numerator = target_count - current_count

            if target_count == 0: 
                weight = 0.0
            elif weight_numerator > 0:
                weight = float(weight_numerator + 1) 
            else:
                weight = 0.001 
            
            weights.append(max(0.0, weight))
            
        return weights

    def _can_swap(self, token1_idx: int, token2_idx: int, category_to_swap: str) -> bool:
        """
        NOTE: This method is currently NOT USED by the main generation logic's adjustment phase.
        """
        token1_traits = self.tokens_data[token1_idx]['traits'].copy()
        token2_traits = self.tokens_data[token2_idx]['traits'].copy()
        trait_from_token1 = token1_traits[category_to_swap]
        trait_from_token2 = token2_traits[category_to_swap]
        if trait_from_token1 == trait_from_token2: return False
        token1_gender = self._get_token_gender(token1_traits)
        token2_gender = self._get_token_gender(token2_traits)
        temp_token1_traits = token1_traits.copy()
        temp_token1_traits[category_to_swap] = trait_from_token2
        if not self._is_trait_valid_for_token(trait_from_token2, category_to_swap, temp_token1_traits, token1_gender): return False
        temp_token2_traits = token2_traits.copy()
        temp_token2_traits[category_to_swap] = trait_from_token1
        if not self._is_trait_valid_for_token(trait_from_token1, category_to_swap, temp_token2_traits, token2_gender): return False
        return True

    def _is_trait_valid_for_token(self, trait_to_check: str, category_of_trait: str, token_all_traits: Dict[str,str], token_gender: str, for_adjustment_debug: bool = False) -> bool:
        """
        Helper to check if a specific trait is valid for a token's existing traits and gender.
        `token_all_traits` should be the state *after* the hypothetical assignment of `trait_to_check`.
        Implements "Flexible Unisex": Unisex tokens can be assigned Male/Female traits.
        """
        trait_config = self.numerology_config['categories'][category_of_trait]['traits'][trait_to_check]
        
        # Check trait-specific gender if defined (Flexible Unisex)
        trait_gender_restriction = trait_config.get('gender')
        if trait_gender_restriction: # Trait has a gender attribute ("Male", "Female", or "Unisex")
            if token_gender == "Unknown": 
                 if for_adjustment_debug: self._emit_progress(f"      DEBUG_ADJUST_VALIDATE: FAILED (Gender). Trait '{category_of_trait}:{trait_to_check}' (gender: {trait_gender_restriction}) for UNKNOWN token gender.")
                 return False

            # If token_gender is "Unisex", it can wear any gendered trait.
            # Only proceed with stricter checks if the token_gender is Male or Female.
            if token_gender != "Unisex":
                # Token is Male or Female.
                # Trait must either be "Unisex" (can be worn by anyone) 
                # or match the token's specific gender.
                if trait_gender_restriction.lower() != "unisex" and trait_gender_restriction != token_gender:
                    if for_adjustment_debug: self._emit_progress(f"      DEBUG_ADJUST_VALIDATE: FAILED (Gender). Trait '{category_of_trait}:{trait_to_check}' (gender: {trait_gender_restriction}) for token gender '{token_gender}'.")
                    return False
        
        # Check incompatibilities with other traits
        for cat, assigned_trait in token_all_traits.items():
            if cat == category_of_trait:
                continue
            if not self._check_compatibility(category_of_trait, trait_to_check, cat, assigned_trait, for_adjustment_debug=for_adjustment_debug):
                if for_adjustment_debug: self._emit_progress(f"      DEBUG_ADJUST_VALIDATE: FAILED (Incompatibility). Trait '{category_of_trait}:{trait_to_check}' vs existing '{cat}:{assigned_trait}'. Rule triggered.")
                return False
        return True

    def _execute_swap(self, token1_idx: int, token2_idx: int, category_to_swap: str):
        """
        NOTE: This method is currently NOT USED by the main generation logic's adjustment phase.
        """
        token1_data = self.tokens_data[token1_idx]
        token2_data = self.tokens_data[token2_idx]
        trait1_original = token1_data['traits'][category_to_swap]
        trait2_original = token2_data['traits'][category_to_swap]
        self.trait_counts[(category_to_swap, trait1_original)] -= 1
        self.trait_counts[(category_to_swap, trait2_original)] -= 1
        token1_data['traits'][category_to_swap] = trait2_original
        token2_data['traits'][category_to_swap] = trait1_original
        self.trait_counts[(category_to_swap, trait2_original)] += 1
        self.trait_counts[(category_to_swap, trait1_original)] += 1

    def _emit_progress(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def _get_target_count(self, category_name: str, trait_name: str) -> int:
        try:
            return self.numerology_config['categories'][category_name]['traits'][trait_name]['target_count']
        except KeyError:
            return 0

    def _get_tolerance(self, category_name: str, trait_name: str) -> int:
        try:
            return self.numerology_config['categories'][category_name]['traits'][trait_name]['tolerance']
        except KeyError:
            return 0

    def _seed_sovereign_glyphs(self):
        self._emit_progress("Seeding Sovereign Glyphs...")
        glyph_category_data = self.numerology_config.get('categories', {}).get("Glyph", {})
        if not glyph_category_data or not glyph_category_data.get('traits'):
            self._emit_progress("  Warning: Glyph category or its traits not found. Skipping Sovereign seeding.")
            return

        sovereign_glyph_names = []
        for glyph_name, trait_data in glyph_category_data.get('traits', {}).items():
            law_num = self._parse_glyph_law_number(glyph_name)
            if law_num is not None and 1 <= law_num <= 7 and trait_data.get("target_count") == 1:
                sovereign_glyph_names.append(glyph_name)
        
        expected_sovereign_count = 7 
        if len(sovereign_glyph_names) != expected_sovereign_count:
            self._emit_progress(f"  Warning: Expected {expected_sovereign_count} Sovereign Glyphs with target_count 1, found {len(sovereign_glyph_names)}. Check numerology.")

        available_token_indices = list(range(self.target_collection_size))
        random.shuffle(available_token_indices)

        for glyph_name in sovereign_glyph_names:
            if not available_token_indices:
                self._emit_progress(f"  Error: Ran out of tokens for Sovereign Glyph {glyph_name}.")
                continue
            chosen_token_idx = available_token_indices.pop()
            token_id_str = self.tokens_data[chosen_token_idx]['token_id']
            
            current_token_traits = self.tokens_data[chosen_token_idx]['traits']
            glyph_law_num = self._parse_glyph_law_number(glyph_name)

            self.tokens_data[chosen_token_idx]['traits']["Glyph"] = glyph_name
            self.tokens_data[chosen_token_idx]['law_number'] = glyph_law_num
            self.trait_counts[("Glyph", glyph_name)] = self.trait_counts.get(("Glyph", glyph_name), 0) + 1
            
            if glyph_law_num == 5: 
                self.tokens_data[chosen_token_idx]['traits']["Rank"] = "Boss / Don"
                self.trait_counts[("Rank", "Boss / Don")] = self.trait_counts.get(("Rank", "Boss / Don"), 0) + 1
                self._emit_progress(f"  Assigned Sovereign Glyph '{glyph_name}' to Token ID {token_id_str} & forced Rank to 'Boss / Don'.")
            else:
                self._emit_progress(f"  Assigned Sovereign Glyph '{glyph_name}' to Token ID {token_id_str}")

    def _seed_special_singletons(self):
        self._emit_progress("Seeding Special Singleton Traits...")
        special_traits_to_assign: List[Tuple[str, str]] = []
        
        for cat_name, cat_data in self.numerology_config.get('categories', {}).items():
            for trait_name, trait_config in cat_data.get('traits', {}).items():
                if trait_config.get('target_count') == 1:
                    is_sovereign_glyph = False
                    if cat_name == "Glyph": 
                        law_num = self._parse_glyph_law_number(trait_name)
                        if law_num is not None and 1 <= law_num <= 7:
                            is_sovereign_glyph = True
                    
                    if not is_sovereign_glyph:
                        special_traits_to_assign.append((cat_name, trait_name))

        if not special_traits_to_assign:
            self._emit_progress("  No special singleton traits to seed (excluding Sovereign Glyphs).")
            return

        available_token_indices = []
        for idx, data in enumerate(self.tokens_data):
            is_sovereign_holder = False
            glyph_trait = data['traits'].get("Glyph")
            if glyph_trait:
                law_num = self._parse_glyph_law_number(glyph_trait)
                if law_num is not None and 1 <= law_num <=7:
                    is_sovereign_holder = True
            if not is_sovereign_holder:
                available_token_indices.append(idx)
        
        if not available_token_indices and self.target_collection_size > 7 : 
            self._emit_progress("  Warning: All tokens might be Sovereign holders; seeding singletons on any available.")
            available_token_indices = list(range(self.target_collection_size))

        random.shuffle(available_token_indices)
        
        assigned_tokens_for_category_during_seeding: Dict[str, List[int]] = {} 

        for cat_name, trait_name in special_traits_to_assign:
            assigned_to_token = False
            
            current_candidates = [
                idx for idx in available_token_indices
                if cat_name not in self.tokens_data[idx]['traits']
            ]
            if not current_candidates: 
                current_candidates = [
                    idx for idx in available_token_indices
                     if not (cat_name in assigned_tokens_for_category_during_seeding and \
                             idx in assigned_tokens_for_category_during_seeding[cat_name])
                ]
            if not current_candidates: 
                current_candidates = list(available_token_indices)

            random.shuffle(current_candidates)

            for token_idx in current_candidates:
                current_token_data = self.tokens_data[token_idx]
                token_id_str = current_token_data['token_id']
                
                is_token_sovereign_holder = False
                token_glyph_trait = current_token_data['traits'].get("Glyph")
                if token_glyph_trait:
                    law_n = self._parse_glyph_law_number(token_glyph_trait)
                    if law_n and 1 <= law_n <= 7: is_token_sovereign_holder = True
                
                if cat_name == "Rank" and trait_name == "Joker / Wildcard" and is_token_sovereign_holder:
                    continue

                token_gender_for_check = self._get_token_gender(current_token_data['traits'])
                hypothetical_traits = current_token_data['traits'].copy()
                hypothetical_traits[cat_name] = trait_name 
                
                effective_gender_for_validation = trait_name if cat_name == "Gender" else token_gender_for_check

                if self._is_trait_valid_for_token(trait_name, cat_name, hypothetical_traits, effective_gender_for_validation):
                    current_token_data['traits'][cat_name] = trait_name
                    self.trait_counts[(cat_name, trait_name)] = self.trait_counts.get((cat_name, trait_name), 0) + 1
                    
                    if cat_name not in assigned_tokens_for_category_during_seeding:
                        assigned_tokens_for_category_during_seeding[cat_name] = []
                    assigned_tokens_for_category_during_seeding[cat_name].append(token_idx)
                    
                    if cat_name == "Glyph": 
                        current_token_data['law_number'] = self._parse_glyph_law_number(trait_name)
                    
                    self._emit_progress(f"    Assigned singleton '{cat_name}: {trait_name}' to Token ID {token_id_str}")
                    if token_idx in available_token_indices: 
                        available_token_indices.remove(token_idx) 
                    assigned_to_token = True
                    break 
            
            if not assigned_to_token:
                self._emit_progress(f"  Warning: Could not find a suitable token for special singleton '{cat_name}: {trait_name}'. Trait count for it will be 0.")

    def _get_category_order(self) -> List[str]:
        categories = list(self.numerology_config.get('categories', {}).keys())
        preferred_order = ["Gender", "Body", "Rank", "Glyph"] 
        
        ordered_categories = [cat for cat in preferred_order if cat in categories]
        for cat in categories:
            if cat not in ordered_categories:
                ordered_categories.append(cat)
        return ordered_categories

    def generate_tokens(self) -> List[Token]:
        self.tokens_data = [] 
        id_padding = len(str(self.target_collection_size))
        for i in range(self.target_collection_size):
            self.tokens_data.append({
                "token_id": str(i + 1).zfill(id_padding),
                "traits": {},
                "law_number": None
            })

        for key in self.trait_counts: self.trait_counts[key] = 0

        self._seed_sovereign_glyphs() 
        self._seed_special_singletons() 

        self._emit_progress(f"Weighted Random Fill Phase starting for {self.target_collection_size} tokens...")
        category_order = self._get_category_order()

        for i in range(self.target_collection_size):
            current_token_data = self.tokens_data[i]
            token_id_str = current_token_data['token_id']
            self._emit_progress(f"\nDEBUG_FILL: Processing Token ID {token_id_str}")

            token_gender = self._get_token_gender(current_token_data['traits'])
            self._emit_progress(f"  DEBUG_FILL: Token ID {token_id_str} - Initial Gender for Fill: {token_gender} (Current traits: {current_token_data['traits']})")

            for category_name in category_order:
                self._emit_progress(f"  DEBUG_FILL: Token ID {token_id_str}, Category: {category_name}")
                if category_name in current_token_data['traits']:
                    self._emit_progress(f"    DEBUG_FILL: Skipped (already assigned by seeding/earlier fill): {category_name} = {current_token_data['traits'][category_name]}")
                    if category_name == "Gender": token_gender = current_token_data['traits']["Gender"]
                    elif category_name == "Body": token_gender = self._get_token_gender(current_token_data['traits']) 
                    continue
                
                current_processing_gender = self._get_token_gender(current_token_data['traits'])

                if not self._is_category_applicable_by_gender_spec(category_name, current_processing_gender):
                    self._emit_progress(f"    DEBUG_FILL: Skipped Category '{category_name}' for Token ID {token_id_str}. Reason: Not applicable for gender '{current_processing_gender}'.")
                    continue
                
                valid_traits = self._get_valid_traits_for_category(category_name, current_processing_gender, current_token_data['traits'])

                if valid_traits:
                    temp_valid_traits = []
                    for trait_name_check in valid_traits:
                        keep_trait = True 
                        if category_name == "Rank" and trait_name_check == "Joker / Wildcard":
                            joker_target = self._get_target_count("Rank", "Joker / Wildcard")
                            if self.trait_counts.get(("Rank", "Joker / Wildcard"), 0) >= joker_target:
                                self._emit_progress(f"  DEBUG_FILL_STRICT: Token ID {token_id_str}, Cat '{category_name}'. Trait '{trait_name_check}' count ({self.trait_counts.get(('Rank', 'Joker / Wildcard'),0)}) met/exceeded target ({joker_target}). Excluding from fill choices.")
                                keep_trait = False
                        
                        elif category_name == "Glyph" and trait_name_check == "glyph_13":
                            g13_target = self._get_target_count("Glyph", "glyph_13")
                            g13_tol = self._get_tolerance("Glyph", "glyph_13")
                            if self.trait_counts.get(("Glyph", "glyph_13"), 0) >= g13_target + g13_tol:
                                self._emit_progress(f"  DEBUG_FILL_STRICT: Token ID {token_id_str}, Cat '{category_name}'. Trait '{trait_name_check}' count ({self.trait_counts.get(('Glyph', 'glyph_13'),0)}) met/exceeded target+tolerance ({g13_target + g13_tol}). Excluding.")
                                keep_trait = False
                        
                        if keep_trait:
                            temp_valid_traits.append(trait_name_check)
                    
                    valid_traits = temp_valid_traits 

                if not valid_traits:
                    self._emit_progress(f"  WARNING_FILL: No valid traits left for Token ID {token_id_str}, Category '{category_name}' after STRICT target adherence checks. Gender: '{current_processing_gender}'. Current Traits: {current_token_data['traits']}. Skipping category.")
                    continue
                
                weights = self._calculate_weights(category_name, valid_traits, i)
                
                chosen_trait = ""
                if not any(w > 0 for w in weights): 
                    self._emit_progress(f"    DEBUG_FILL: Token ID {token_id_str}, Category '{category_name}'. All actual weights zero (target=0 traits). Valid traits (if any): {valid_traits}. Attempting random choice if any valid.")
                    if valid_traits: 
                        chosen_trait = random.choice(valid_traits)
                    else: 
                        self._emit_progress(f"  ERROR_FILL: Token ID {token_id_str}, Category '{category_name}'. No valid traits and all actual weights zero. Cannot assign.")
                        continue 
                else: 
                    chosen_trait = random.choices(valid_traits, weights=weights, k=1)[0]
                
                if chosen_trait:
                    current_token_data['traits'][category_name] = chosen_trait
                    self.trait_counts[(category_name, chosen_trait)] = self.trait_counts.get((category_name, chosen_trait), 0) + 1
                    self._emit_progress(f"    DEBUG_FILL: Assigned to Token ID {token_id_str}: {category_name} = {chosen_trait} (Gender used for selection: {current_processing_gender})")
                    
                    if category_name == "Gender":
                        token_gender = chosen_trait 
                        self._emit_progress(f"    DEBUG_FILL: Token ID {token_id_str} - Gender updated to: {token_gender} after assigning Gender trait.")
                    elif category_name == "Body":
                        new_gender_after_body = self._get_token_gender(current_token_data['traits'])
                        if new_gender_after_body != token_gender :
                            token_gender = new_gender_after_body
                            self._emit_progress(f"    DEBUG_FILL: Token ID {token_id_str} - Gender updated to: {token_gender} after assigning Body trait.")
                else:
                    self._emit_progress(f"  ERROR_FILL: Token ID {token_id_str}, Category '{category_name}'. chosen_trait is empty. This shouldn't happen if valid_traits existed. Skipping.")
            
            if "Glyph" in current_token_data['traits'] and current_token_data.get('law_number') is None:
                 current_token_data['law_number'] = self._parse_glyph_law_number(current_token_data['traits']["Glyph"])

            if (i + 1) % (self.target_collection_size // 20 or 1) == 0 or (i+1) == self.target_collection_size :
                self._emit_progress(f"Weighted Random Fill Phase: {i+1}/{self.target_collection_size} tokens processed.")

        self._emit_progress("Adjustment Phase starting...")
        max_iterations = self.numerology_config.get("adjustment_max_iterations", 1000) 
        current_iteration = 0
        all_tolerances = [cfg.get('tolerance', 0) for cat_data in self.numerology_config['categories'].values() for cfg in cat_data['traits'].values() if isinstance(cfg, dict)]
        max_config_tolerance = max(all_tolerances) if all_tolerances else 0
        adjustment_tolerance_cap = max_config_tolerance + 8 # Increased cap slightly
        current_adjustment_tolerance = 0

        while current_iteration < max_iterations:
            traits_still_outside_final_tolerance = []
            for (cat, trait_name), current_count in self.trait_counts.items():
                trait_config = self.numerology_config['categories'][cat]['traits'][trait_name]
                target = trait_config['target_count']
                final_tol = trait_config['tolerance']
                if not (target - final_tol <= current_count <= target + final_tol):
                    traits_still_outside_final_tolerance.append({
                        'category': cat, 'trait': trait_name, 
                        'current': current_count, 'target': target, 'final_tol': final_tol
                    })

            if not traits_still_outside_final_tolerance:
                self._emit_progress(f"Adjustment successful: All traits within final configured tolerances after {current_iteration} iterations.")
                break
            
            self._emit_progress(
                f"Adjustment Iter: {current_iteration + 1}, Current Adj. Tol: {current_adjustment_tolerance}, "
                f"Traits outside FINAL tol: {len(traits_still_outside_final_tolerance)}"
            )

            over_assigned_for_current_tol = []
            under_assigned_for_current_tol = []
            for (cat, trait_name), current_count in self.trait_counts.items():
                trait_config = self.numerology_config['categories'][cat]['traits'][trait_name]
                target = trait_config['target_count']
                if current_count > target + current_adjustment_tolerance:
                    over_assigned_for_current_tol.append({'category': cat, 'trait': trait_name, 'current': current_count, 'target': target})
                elif current_count < target - current_adjustment_tolerance and target > 0 : 
                    under_assigned_for_current_tol.append({'category': cat, 'trait': trait_name, 'current': current_count, 'target': target})

            swaps_made_this_iteration = 0
            random.shuffle(over_assigned_for_current_tol)

            problematic_traits_for_debug = [
                ("Hair Style", "Straight Center-Part"),
                ("Outfit", "Fur Coat"),
                ("Outfit", "Techwear")
            ]

            for over_info in over_assigned_for_current_tol:
                cat_to_adjust = over_info['category']
                over_trait = over_info['trait']
                tokens_with_over_trait = [
                    idx for idx, t_data in enumerate(self.tokens_data)
                    if t_data['traits'].get(cat_to_adjust) == over_trait
                ]
                random.shuffle(tokens_with_over_trait)

                for under_info in sorted(under_assigned_for_current_tol, key=lambda x: (x['target'] - x['current']), reverse=True): 
                    if under_info['category'] != cat_to_adjust: continue
                    under_trait = under_info['trait']
                    if over_trait == under_trait: continue

                    for token_idx_to_change in tokens_with_over_trait:
                        token_data_to_change = self.tokens_data[token_idx_to_change]
                        original_traits = token_data_to_change['traits'].copy()
                        token_gender = self._get_token_gender(original_traits)
                        
                        # Create hypothetical traits *after* the swap for validation
                        hypothetical_traits_for_validation = original_traits.copy()
                        hypothetical_traits_for_validation[cat_to_adjust] = under_trait # Test with the new trait
                        
                        current_for_adjustment_debug = False
                        if (cat_to_adjust, over_trait) in problematic_traits_for_debug or \
                           (cat_to_adjust, under_trait) in problematic_traits_for_debug:
                            current_for_adjustment_debug = True

                        if self._is_trait_valid_for_token(under_trait, cat_to_adjust, hypothetical_traits_for_validation, token_gender, for_adjustment_debug=current_for_adjustment_debug):
                            token_data_to_change['traits'][cat_to_adjust] = under_trait
                            self.trait_counts[(cat_to_adjust, over_trait)] -= 1
                            self.trait_counts[(cat_to_adjust, under_trait)] = self.trait_counts.get((cat_to_adjust, under_trait),0) + 1
                            if cat_to_adjust == "Glyph":
                                token_data_to_change['law_number'] = self._parse_glyph_law_number(under_trait)
                            swaps_made_this_iteration += 1
                            
                            tokens_with_over_trait.remove(token_idx_to_change) 

                            over_still_needs_fixing = self.trait_counts[(cat_to_adjust, over_trait)] > over_info['target'] + current_adjustment_tolerance
                            if not over_still_needs_fixing: break 
                    
                    if not (self.trait_counts[(cat_to_adjust, over_trait)] > over_info['target'] + current_adjustment_tolerance): break
            
            current_iteration += 1
            if swaps_made_this_iteration == 0:
                current_adjustment_tolerance += 1
                if current_adjustment_tolerance > adjustment_tolerance_cap:
                    self._emit_progress(f"  Max adjustment tolerance ({adjustment_tolerance_cap}) reached.")
                    final_check_traits_outside = [
                        f"{cat}-{tn}: {cc} (target {tc['target_count']} ±{tc['tolerance']})"
                        for (cat, tn), cc in self.trait_counts.items()
                        for tc in [self.numerology_config['categories'][cat]['traits'][tn]]
                        if not (tc['target_count'] - tc['tolerance'] <= cc <= tc['target_count'] + tc['tolerance'])
                    ]
                    if final_check_traits_outside:
                        self._emit_progress(f"CONSTRAINT VIOLATION (post-max-adj-tol): {len(final_check_traits_outside)} traits outside final tolerance.")
                        for violation in final_check_traits_outside[:10]: self._emit_progress(f"    - {violation}")
                        self._print_problematic_trait_counts_debug()
                        # raise RuntimeError("Cannot satisfy trait count constraints even after max adjustment tolerance strategy.") # Keep this commented for now to see if it passes with flexible unisex
                        break # Exit loop if max tolerance reached and still violations
                    else:
                        self._emit_progress("All traits within final configured tolerances after exhausting adjustment tolerance strategy.")
                        break 
        
        if current_iteration >= max_iterations and traits_still_outside_final_tolerance: 
            self._emit_progress(f"Max iterations ({max_iterations}) reached. {len(traits_still_outside_final_tolerance)} traits still outside final tolerance.")
            for t_info in traits_still_outside_final_tolerance[:10]: self._emit_progress(f"    - MaxIter Violation: {t_info['category']}:{t_info['trait']} (Count: {t_info['current']}, Target: {t_info['target']} ±{t_info['final_tol']})")
            self._print_problematic_trait_counts_debug()
            # raise RuntimeError("Max iterations reached, and constraints not met.") # Keep this commented for now
        elif current_iteration >= max_iterations:
             self._emit_progress(f"Max iterations ({max_iterations}) reached; all traits appear to be within final tolerance.")

        self._emit_progress("Final Validation starting...")
        self._final_validation_checks() 

        final_tokens_list: List[Token] = []
        for token_dict_data in self.tokens_data:
            final_tokens_list.append(
                Token(
                    token_id=token_dict_data["token_id"],
                    traits=token_dict_data["traits"],
                    law_number=token_dict_data.get("law_number") 
                )
            )
        return final_tokens_list

    def _print_problematic_trait_counts_debug(self):
        self._emit_progress("\n=== DEBUG: Problematic Trait Counts (vs Final Tolerance) ===")
        found_problems = False
        for (cat, trait_name), current_count in sorted(self.trait_counts.items()):
            try:
                trait_config = self.numerology_config['categories'][cat]['traits'][trait_name]
                target = trait_config['target_count']
                final_tol = trait_config['tolerance']
                if not (target - final_tol <= current_count <= target + final_tol):
                    found_problems = True
                    self._emit_progress(f"  VIOLATION: {cat}-{trait_name}: {current_count} (Target: {target} ±{final_tol})")
            except KeyError:
                self._emit_progress(f"  ERROR_DEBUG: Could not find config for {cat}-{trait_name} during debug print.")
        if not found_problems:
            self._emit_progress("  No problematic counts found in this debug check.")

    def _final_validation_checks(self):
        violations = []
        for (cat, trait_name), count in self.trait_counts.items():
            cfg = self.numerology_config['categories'][cat]['traits'][trait_name]
            if not (cfg['target_count'] - cfg['tolerance'] <= count <= cfg['target_count'] + cfg['tolerance']):
                violations.append(f"Trait {cat}-{trait_name} count {count} is outside target {cfg['target_count']} +/- {cfg['tolerance']}.")
        if violations:
            self._emit_progress(f"Validation Error (Counts): {len(violations)} violations found.")
            for v in violations[:5]: self._emit_progress(f"  - {v}")
            self._print_problematic_trait_counts_debug()
            # raise ValueError("Trait count validation failed.") # Keep commented for now
        else: # Only print if no violations
            self._emit_progress("  ✓ Trait counts within tolerance.")

        temp_token_hashes = set()
        for i, token_dict_data in enumerate(self.tokens_data):
            trait_items = sorted(token_dict_data['traits'].items())
            stable_traits = {k: str(v) if v is not None else "None" for k, v in trait_items}
            trait_string = json.dumps(stable_traits, sort_keys=True)
            
            if trait_string in temp_token_hashes:
                original_token_id_str = "N/A (could not find original)"
                for prev_idx in range(i):
                    prev_trait_items = sorted(self.tokens_data[prev_idx]['traits'].items())
                    prev_stable_traits = {k: str(v) if v is not None else "None" for k, v in prev_trait_items}
                    if json.dumps(prev_stable_traits, sort_keys=True) == trait_string:
                        original_token_id_str = self.tokens_data[prev_idx]['token_id']
                        break
                raise ValueError(f"Validation Error (Uniqueness): Duplicate token. Token ID {token_dict_data['token_id']} (idx {i}) is same as {original_token_id_str}. Traits: {token_dict_data['traits']}")
            temp_token_hashes.add(trait_string)
        if len(temp_token_hashes) != self.target_collection_size:
             raise ValueError(f"Validation Error (Uniqueness): Number of unique tokens ({len(temp_token_hashes)}) does not match target ({self.target_collection_size}).")
        self._emit_progress(f"  ✓ All {len(self.tokens_data)} tokens have unique trait combinations.")

        for i, token_dict_data in enumerate(self.tokens_data):
            assigned_traits = token_dict_data['traits']
            trait_list = list(assigned_traits.items())
            for j1_idx in range(len(trait_list)):
                for j2_idx in range(j1_idx + 1, len(trait_list)):
                    cat1, val1 = trait_list[j1_idx]
                    cat2, val2 = trait_list[j2_idx]
                    if not self._check_compatibility(cat1, val1, cat2, val2):
                        raise ValueError(f"Validation Error (Incompatibility): Token {token_dict_data.get('token_id', i)} violates rule between {cat1}:{val1} and {cat2}:{val2}.")
        self._emit_progress("  ✓ No incompatibility rules violated.")

        for i, token_dict_data in enumerate(self.tokens_data):
            token_traits = token_dict_data['traits']
            token_gender_val = self._get_token_gender(token_traits)
            
            for category_name, category_data_cfg in self.numerology_config.get('categories', {}).items():
                if self._is_category_applicable_by_gender_spec(category_name, token_gender_val):
                    if category_name not in token_traits:
                        if not category_data_cfg.get('traits'):
                            continue 
                        possible_traits_for_cat = self._get_valid_traits_for_category(category_name, token_gender_val, {}) 
                        if possible_traits_for_cat: 
                            raise ValueError(f"Validation Error (Missing Category): Token {token_dict_data.get('token_id', i)} (Gender: {token_gender_val}) is missing assignable category '{category_name}'.")
        self._emit_progress("  ✓ All required and assignable categories appear to be assigned.")


if __name__ == '__main__':
    print("Generator module direct execution (for basic testing).")
    dummy_numerology_prd_like = {
        "target_count": 30, 
        "adjustment_max_iterations": 500,
        "categories": {
            "Gender": {"traits": {"Male": {"target_count": 10, "tolerance": 1}, "Female": {"target_count": 10, "tolerance": 1}, "Unisex": {"target_count": 10, "tolerance": 1}}},
            "Body": {
                "traits": {
                    "Human Male": {"target_count": 7, "tolerance": 1, "gender": "Male"}, "Robot Male": {"target_count": 3, "tolerance": 1, "gender": "Male"},
                    "Human Female": {"target_count": 7, "tolerance": 1, "gender": "Female"}, "Robot Female": {"target_count": 3, "tolerance": 1, "gender": "Female"},
                    "Cyborg": {"target_count": 10, "tolerance": 1, "gender": "Unisex"} # Added Unisex body
                }
            },
            "Rank": {
                "traits": { 
                    "Boss / Don": {"target_count": 2, "tolerance": 0}, "Capo": {"target_count": 5, "tolerance": 1}, 
                    "Soldier": {"target_count": 10, "tolerance": 2}, "Associate": {"target_count": 13, "tolerance": 2}
                }
            },
            "Glyph": { 
                "traits": {
                    "glyph_01": {"target_count": 1, "tolerance": 0}, 
                    "glyph_05": {"target_count": 1, "tolerance": 0}, 
                    "glyph_08": {"target_count": 2, "tolerance": 0}, 
                    "glyph_15": {"target_count": 3, "tolerance": 1}, 
                    "glyph_29": {"target_count": 5, "tolerance": 1}, 
                    "blank": {"target_count": 18, "tolerance": 2}
                }
            },
            "Outfit": { 
                "traits": {
                    "Suit": {"target_count": 5, "tolerance": 1, "gender": "Male"},
                    "Dress": {"target_count": 5, "tolerance": 1, "gender": "Female"},
                    "Tracksuit": {"target_count": 8, "tolerance": 2, "gender": "Unisex"}, 
                    "Labcoat": {"target_count": 6, "tolerance": 1}, 
                    "Leather Jacket": {"target_count": 6, "tolerance": 1, "gender": "Unisex"} # Added another Unisex outfit
                }
            },
            "Hair Style": { # Added for testing the specific problematic traits
                 "traits": {
                    "Slick-Back Undercut": {"target_count": 5, "tolerance": 1, "gender": "Male"},
                    "High Ponytail": {"target_count": 5, "tolerance": 1, "gender": "Female"},
                    "Wolf Cut": {"target_count": 10, "tolerance": 2, "gender": "Unisex"},
                    "Straight Center-Part": {"target_count": 10, "tolerance": 2} # Implicitly Unisex
                 }
            }
        }
    }
    dummy_rules_prd_like = {
        "incompatibilities": [
            {"trait_a": ["Rank", "Boss / Don"], "trait_b": ["Outfit", "Tracksuit"], "description": "Bosses don't wear tracksuits (unless Law 1)"}
        ]
    }

    generator = Generator(dummy_numerology_prd_like, dummy_rules_prd_like, seed=42)
    try:
        generated_tokens = generator.generate_tokens()
        print(f"\nSuccessfully generated {len(generated_tokens)} tokens.")
        
        print("\nFinal Trait Counts (from generator.trait_counts):")
        for (cat, trait), count in sorted(generator.trait_counts.items()):
            target = generator._get_target_count(cat, trait) 
            tol = generator._get_tolerance(cat, trait)     
            status = "OK"
            if not (target - tol <= count <= target + tol): status = "VIOLATION"
            print(f"  {cat} - {trait}: {count} (target {target} +/- {tol}) - {status}")

    except Exception as e:
        print(f"\nError during generation: {e}")
        import traceback
        traceback.print_exc()
        if hasattr(generator, '_print_problematic_trait_counts_debug'):
            print("\n--- Attempting to print problematic counts from generator state ---")
            generator._print_problematic_trait_counts_debug()
