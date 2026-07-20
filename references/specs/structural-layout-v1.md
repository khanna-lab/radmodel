# Structural Layout Specification v1

Source-grounded specification of the John J. Moran Medium Security facility's
spatial organization, derived from the *RIDOC Inmate Rule Book — March 2013*
(`references/literature/`) and the project paper draft.

This document covers **structural layout only**. Scheduling, mod-to-shared-place
rotation, housing-category movement rules, and visitor/staff modeling are out
of scope and handled by separate specs.

---

## 1. Place hierarchy

```
Facility (Moran Medium)
├── Module × 10         (housing units; letters A–J)
│   ├── Cells × 58      (29 per tier × 2 tiers; double-bunked)
│   ├── Dayroom × 1
│   └── Shower area × 1
└── Shared places (facility-level, one each unless noted)
    ├── Dining Room × 2     (rule book uses plural; eating paired A+B / C+D etc.)
    ├── Gym × 1
    ├── Yard × 1
    ├── Education Building × 1
    ├── Industries Building × 1
    ├── Visiting Room × 1
    ├── Medical × 1         (contains the MI isolation cells)
    ├── Barber × 1
    ├── Chapel × 1
    └── Segregation Unit × 1 (contains the RH cells)
```

## 2. Committed cardinalities

| Quantity | Value | Source |
|---|---|---|
| Modules | **10** (A–J) | Derived: 1200 residents ÷ ~116 per mod ≈ 10; consistent with paper's A+B/C+D pairing implying even count |
| Tiers per module | **2** (top, bottom) | Rule book p.5 |
| Cells per tier | **29** | Paper §"How is the Medium Security Facility organized?" — "Larger Blocks: 29 cells on bottom, 29 cells on top" |
| Cells per module | **58** | 29 × 2 |
| Bunks per cell | **2** | Rule book p.5 "Most cells in this facility are double bunked" |
| Module capacity (nominal) | **116** | 58 × 2 |
| Total cell capacity | **1160** | 10 × 116 |
| Total residents | **1200** | Paper Table 1 |
| Overflow handling | ~40 cells triple-bunked | Paper: "Only time there were 3 people in a cell was due to overcrowding" |
| Dining rooms | **2** | Rule book plural; "each side of the dining rooms" (p.19) |
| Segregation cells (RH) | **30** | ~2.5% of population, typical for medium-security |
| Medical isolation cells (MI) | **20** | Reserved within Medical for COVID protocol overlay |

## 3. Entity model

```
Module
  - module_id (int)
  - letter (str)            # A..J
  - n_cells = 58

Cell
  - cell_id (int)           # also a place_id
  - module_id (FK)
  - tier ∈ {top, bottom}
  - cell_number (int)       # 1..29 within tier
  - housing_category ∈ {GP, RH, MI}
  - bunk_capacity = 2       # 3 for overflow cells

SharedPlace                  # dining_room, gym, yard, education, industry, visit, medical, chapel, barber, segregation, dayroom, shower
  - place_id (int)
  - name (str)
  - place_type (str)
  - parent_module_id (FK, nullable)   # non-null only for dayroom and shower
  - capacity (int, nullable)

Resident
  - person_id (int)
  - cell_id (FK)
  - bunk_position ∈ {top, bottom, third}
```

## 4. CSV schema (additive — coexists with current sim inputs)

```
ng_modules.csv (new):
  module_id, letter
  # 10 rows

ng_places.csv (extended — adds columns and rows):
  place_id, name, type, parent_module_id, capacity
  # existing rows preserved; new rows added for dayrooms, showers,
  # segregation cells (RH), and medical isolation cells (MI).

ng_cells.csv (new — cell-specific extension):
  place_id, module_id, tier, cell_number, housing_category, bunk_capacity

ng_residents.csv (extended — adds columns):
  # existing columns preserved (the running sim still depends on them);
  # adds: bunk_position
```

`place_type` is a closed enum grounded in the rule book:
`cell, dayroom, shower, dining_room, gym, yard, education, industry,
 visit_room, medical, chapel, barber, segregation`.

## 5. Place_id allocation

Sequential, deterministic, ordered by:

1. Module cells (`module A` bottom tier 1–29, then top tier 1–29; module B …): place_ids 0–579
2. Segregation cells (RH): place_ids 580–609
3. Medical isolation cells (MI): place_ids 610–629
4. Module sub-places (dayroom A, shower A, dayroom B, shower B, …): place_ids 630–649
5. Facility-shared places (2× dining, gym, yard, education, industries, visit, medical, chapel, barber, segregation): place_ids 650+

Stable across re-runs given the same seed.

## 6. Overflow placement

1200 residents − 1160 nominal capacity = 40 surplus.
Distributed evenly: 4 triple-bunked cells per module, picked deterministically
as the lowest cell_numbers in the bottom tier of each module.

## 7. Decisions deferred (explicit, not gaps)

These are out of scope for the structural layer and will be settled by other specs:

- **Capacity values** for gym, yard, dining, education, industries — schema
  supports it; values stay null in v1.
- **Mod-to-shared-place rotation** (which mod uses gym when) — schedule-layer
  concern, handled by a future schedule spec.
- **RH/MI placement rules** (when a resident moves to seg or isolation) —
  behavior, not structure.
- **Internal subdivision** of Education or Industries into rooms — v1 treats
  each as a single place; can split later if a scenario needs per-shop
  occupancy.

## 8. Scope boundary

This spec adds **descriptive metadata** about facility structure. It does not
modify the simulation's runtime data shape or the disease-dynamics layer.
The current `ng_residents.csv` and `ng_schedules.csv` continue to drive the
simulation unchanged; the new structural data sits alongside, ready for
schedule/movement work to reference.
