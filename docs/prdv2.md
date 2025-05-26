# nft\_metadata\_generator\_prd\_v2.3

# purpose: machine‑readable spec for an llm‑driven generator that mints **exactly 420** metadata files.

# scope: implements the final numerology.yaml + rules.yaml provided 2025‑05‑24.

---

root:
collection\_size: 420
deterministic\_seed: true            # generator must accept --seed and reproduce byte‑identical output
output\_formats: \[json, csv]         # see exporter section
required\_modules: \[pre\_validator, generator, exporter]

numerology\_spec:
source\_file: numerology.yaml         # authoritative counts / tolerances
invariant\_checks:
\- root.target\_count == 420
\- for each category: sum(traits\[\*].target\_count) == 420
\- glyph\_distribution == {sovereign:7, capo:35, soldier:84, street:210, blank:84}
\- street\_tier\_split: exactly 10 glyphs with 10 and 10 glyphs with 11 target\_count

rules\_spec:
source\_file: rules.yaml
schema:
incompatibilities:
\- trait\_a: \[<category>, <value>]
trait\_b: \[<category>, <value>]
breakable\_by: \[Glyph, \<glyph\_id>]  # optional
description: <string>              # optional
invariant\_checks:
\- every referenced trait exists in numerology\_spec
\- if breakable\_by present ⇒ glyph\_id is sovereign tier

power\_system:
glyph\_tiers:
sovereign: {laws: 1‑7,  count: 1,  power: 100}
capo:      {laws: 8‑14, count: 5,  power:  50}
soldier:   {laws:15‑28, count: 6,  power:  25}
street:    {laws:29‑48, count: 10|11, power: 10}
blank:     {law: null,  count: 84, power\_range: \[5,50]}
sovereign\_overrides:
glyph\_04: {trait\_count\_target: 6}
glyph\_05: {forced\_rank: "Boss / Don"}
glyph\_06: {trait\_count\_target: 13}
rule\_break\_map:
glyph\_01: \[\[Rank,"Boss / Don"],\[Outfit,"Tracksuit"]]
glyph\_02: \[\[Body,"Zombie"],\[Eyes,"Sunglasses"]]
glyph\_03: \[\[Masks,"Imperial Skull"],\[Hat,"\*"]]      # \* = any hat
power\_score:
weights: {statistical: 0.4, glyph\_power: 0.3, set\_bonus: 0.2, trait\_count: 0.1}
rule\_break\_bonus: 60      # per legitimate break instance

trait\_count\_target:
sovereign\_default: 13       # except glyph\_04 override
capo\_range: \[11,12]
soldier\_range: \[10,11]
street\_range: \[8,10]
blank\_range:  \[7,11]

sets:

* name: Yakuza
  required: {Hair Style:\[Topknot,Double Bun], Outfit:\[Suit], Body:\[Augmented]}
  bonus: "Katana Proficiency"
* name: Shadow Ops
  required: {Masks:\[Ski Mask], Outfit:\[Techwear], Hair Color:\[Vantablack]}
  bonus: "Night Vision"
* name: Golden Don
  required: {Hat:\[Gray Homburg (Don's Variant)], Outfit:\[Zoot Suit], Accessory:\[Gold Watch], Weapon:\[Cane]}
  bonus: "Legendary Status"
* name: Cyber Enforcer
  required: {Body:\[Augmented], Eyes:\[Augmented - Bionic Eye], Outfit:\[Techwear]}
  bonus: "Tech Mastery"

pre\_validator:
fail\_if\_any:
\- category\_sum\_mismatch
\- tolerance\_field\_missing\_or\_non\_int
\- street\_tier\_split\_incorrect
\- glyph\_reference\_in\_rules\_not\_found
\- gender\_specific\_trait\_overflow

generator\_algorithm:
phase\_order:
1: seed\_sovereign
2: seed\_capo
3: seed\_special\_singletons   # joker / wildcard etc.
4: themed\_set\_prefill         # optional, can run zero times if counts constrained
5: weighted\_random\_fill       # soldier, street, blank
6: adjustment\_loop            # swaps until all counts within tolerance and no invalid combos
adjustment\_loop:
max\_iterations: 1000
swap\_rules:
\- maintain\_gender\_validity
\- respect\_unbreakable\_rules
\- allow\_break\_via\_token\_glyph
\- keep\_set\_integrity\_if\_bonus\_applied

exporter:
json\_path: output/json/{token\_id}.json
csv\_path:  output/metadata.csv
json\_schema:
token\_id: str
hash\_id: str
traits: {<category>: <value>}
metadata:
power\_tier: str
power\_score: int
law\_number: int|null
trait\_count: int
special\_abilities: \[str]
set\_bonuses: \[str]

cli\_flags:
\--seed: int
\--numerology: path  # default numerology.yaml
\--rules: path       # default rules.yaml
\--relaxed\_tolerance: bool (default false)
\--prioritize\_sets: bool (default false)

tests:
unit:
\- validate\_numerology\_structure
\- validate\_rules\_structure
\- sovereign\_overrides\_apply
\- rule\_break\_logic
\- set\_detection
\- power\_score\_calculation
integration:
\- full\_generation\_no\_relax
\- full\_generation\_relaxed\_tolerance
\- regen\_with\_same\_seed\_equals\_previous

success\_criteria:

* 420\_unique\_tokens
* all\_category\_counts\_within\_tolerance
* glyph\_tier\_counts\_exact
* sovereign\_overrides\_respected
* zero\_unapproved\_rule\_violations
* json\_and\_csv\_export\_valid
* generation\_time\_sec <= 15

# eof
