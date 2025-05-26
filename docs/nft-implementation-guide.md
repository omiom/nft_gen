# Implementation Guide for Enhanced Rarity System

## Overview
This guide explains how to modify the existing generator to implement the enhanced rarity system with the 48 Laws of Power glyphs, rule-breaking mechanics, and set bonuses.

## Key Implementation Changes

### 1. Update Models (`models.py`)

Add new fields to the Token dataclass:
```python
@dataclass
class Token:
    token_id: str
    traits: Dict[str, str]
    
    # New fields
    power_score: int = 0
    power_tier: str = ""  # "Sovereign", "Capo", "Soldier", "Street", "Unmarked"
    law_number: Optional[int] = None  # 1-48 or None for blank
    special_abilities: List[str] = field(default_factory=list)
    set_bonuses: List[str] = field(default_factory=list)
    
    @property
    def trait_count(self) -> int:
        return len([v for v in self.traits.values() if v and v != "None"])
```

### 2. Modify Generator (`generator.py`)

#### A. Add Glyph-Based Logic

```python
def _get_glyph_power_tier(self, glyph_value: str) -> Tuple[str, Optional[int]]:
    """Determine power tier and law number from glyph"""
    if glyph_value == "blank":
        return "Unmarked", None
    
    glyph_num = int(glyph_value.split('_')[1])
    
    if 1 <= glyph_num <= 7:
        return "Sovereign", glyph_num
    elif 8 <= glyph_num <= 14:
        return "Capo", glyph_num
    elif 15 <= glyph_num <= 28:
        return "Soldier", glyph_num
    elif 29 <= glyph_num <= 48:
        return "Street", glyph_num
```

#### B. Implement Rule Breaking

```python
def _can_break_rule(self, token: Token, rule: IncompatibilityRule) -> bool:
    """Check if token's glyph can break a specific rule"""
    if not hasattr(rule, 'breakable_by'):
        return False
    
    breakable_category, breakable_glyph = rule.breakable_by
    token_glyph = token.traits.get('Glyph', '')
    
    return token_glyph == breakable_glyph
```

#### C. Modify Compatibility Check

```python
def _is_compatible(self, token: Token, category: str, trait_value: str) -> bool:
    """Enhanced compatibility check with rule breaking"""
    # Existing compatibility checks...
    
    # Check incompatibility rules
    for rule in self.rules.incompatibilities:
        # Check if this trait would violate a rule
        if self._would_violate_rule(token, category, trait_value, rule):
            # Check if token can break this rule
            if not self._can_break_rule(token, rule):
                return False
            else:
                # Token can break rule - add to special abilities
                token.special_abilities.append(f"Rule Breaker: {rule.description}")
    
    return True
```

#### D. Add Trait Count Control

```python
def _assign_trait_count_target(self, token: Token) -> int:
    """Determine target trait count based on glyph"""
    power_tier, law_num = self._get_glyph_power_tier(token.traits.get('Glyph', ''))
    
    if law_num == 4:  # Law 4: Say Less Than Necessary
        return 6
    elif law_num == 6:  # Law 6: Court Attention
        return 13
    elif power_tier == "Sovereign":
        return 13
    elif power_tier == "Capo":
        return random.randint(11, 12)
    elif power_tier == "Soldier":
        return random.randint(10, 11)
    elif power_tier == "Street":
        return random.randint(8, 10)
    else:  # Unmarked
        return random.randint(7, 11)
```

### 3. Add Set Detection (`set_detector.py`)

Create a new module for detecting complete sets:

```python
THEMED_SETS = {
    "Yakuza": {
        "required": {
            "Hair Style": ["Topknot", "Double Bun"],
            "Outfit": ["Suit"],
            "Body": ["Augmented"]
        },
        "bonus": "Katana Proficiency"
    },
    "Shadow Ops": {
        "required": {
            "Masks": ["Ski Mask"],
            "Outfit": ["Techwear"],
            "Hair Color": ["Vantablack"]
        },
        "bonus": "Night Vision"
    },
    "Golden Don": {
        "required": {
            "Hat": ["Gray Homburg (Don's Variant)"],
            "Outfit": ["Zoot Suit"],
            "Accessory": ["Gold Watch"],
            "Weapon": ["Cane"]
        },
        "bonus": "Legendary Status"
    },
    "Cyber Enforcer": {
        "required": {
            "Body": ["Augmented"],
            "Eyes": ["Augmented - Bionic Eye"],
            "Outfit": ["Techwear"]
        },
        "bonus": "Tech Mastery"
    }
}

def detect_sets(token: Token) -> List[str]:
    """Detect which themed sets a token completes"""
    completed_sets = []
    
    for set_name, requirements in THEMED_SETS.items():
        if _matches_set(token, requirements):
            completed_sets.append(set_name)
            token.set_bonuses.append(requirements["bonus"])
    
    return completed_sets
```

### 4. Calculate Power Scores (`power_calculator.py`)

```python
def calculate_power_score(token: Token) -> int:
    """Calculate total power score for a token"""
    score = 0
    
    # Base statistical rarity (40% weight)
    statistical_score = calculate_statistical_rarity(token)
    score += statistical_score * 0.4
    
    # Glyph power (30% weight)
    glyph_power = get_glyph_power_value(token.traits.get('Glyph', ''))
    score += glyph_power * 0.3
    
    # Set bonuses (20% weight)
    set_score = len(token.set_bonuses) * 40
    score += set_score * 0.2
    
    # Trait count bonus (10% weight)
    trait_count_score = calculate_trait_count_score(token.trait_count)
    score += trait_count_score * 0.1
    
    # Special ability bonuses
    score += len(token.special_abilities) * 60
    
    return int(score)
```

### 5. Update Exporter (`exporter.py`)

Modify JSON output to include new fields:

```python
def _create_token_json(self, token: Token) -> dict:
    """Create enhanced JSON with power system data"""
    return {
        "token_id": token.token_id,
        "hash_id": token.hash_id,
        "traits": token.traits,
        "metadata": {
            "power_tier": token.power_tier,
            "power_score": token.power_score,
            "law_number": token.law_number,
            "trait_count": token.trait_count,
            "special_abilities": token.special_abilities,
            "set_bonuses": token.set_bonuses
        }
    }
```

### 6. Generation Order Strategy

Modify the generation order to ensure proper distribution:

1. **Generate Sovereign tokens first** (7 total)
   - Assign glyph_01 through glyph_07
   - Ensure Boss/Don or Underboss rank
   - Apply special abilities
   - Use rule-breaking as needed

2. **Generate Capo tokens** (35 total)
   - Assign glyph_08 through glyph_14
   - Ensure appropriate ranks
   - Higher trait counts

3. **Generate special combinations**
   - Joker/Wildcard (1)
   - Complete themed sets
   - Legendary item holders

4. **Fill remaining with standard distribution**
   - Soldier glyphs
   - Street glyphs
   - Unmarked (blank)

### 7. Validation Enhancements

Add validation for the new system:

```python
def validate_power_distribution(tokens: List[Token]) -> bool:
    """Ensure power distribution matches design"""
    power_tier_counts = Counter(t.power_tier for t in tokens)
    
    expected = {
        "Sovereign": 7,
        "Capo": 35,
        "Soldier": 84,
        "Street": 210,
        "Unmarked": 84
    }
    
    for tier, expected_count in expected.items():
        actual = power_tier_counts.get(tier, 0)
        tolerance = 5 if tier in ["Street", "Unmarked"] else 1
        
        if abs(actual - expected_count) > tolerance:
            return False
    
    return True
```

## Testing Considerations

1. **Test rule breaking mechanics** work correctly
2. **Verify trait count targets** are achieved
3. **Ensure set detection** works across gender variants
4. **Validate power score calculations**
5. **Test generation completes** with all constraints

## Summary

This implementation creates a multi-layered rarity system where:
- Statistical rarity provides the foundation
- The 48 Laws of Power add thematic depth
- Rule-breaking creates legendary outliers  
- Set bonuses reward aesthetic coherence
- Power scores unify all elements

The phased reveal system maintains engagement post-mint, while the generation algorithm ensures mathematical integrity.