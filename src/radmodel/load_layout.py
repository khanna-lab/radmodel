from dataclasses import dataclass
from typing import List

@dataclass
class Place:
    module_id: str
    capacity: int

@dataclass
class Module(Place):
    # """
    # Class to hold prison module details.

    # module_id: unique module identifier
    # children: list of tiers and shared spaces contained in this module
    # """
    letter: str
    children: List[Place] = []
    def add_tier(self, tier):
        self.children.append(tier)

@dataclass
class Tier(Place):
    tier_id: str
    children: List[Place]
    is_top: bool = False
    def add_cell(self, cell):
        self.children.append(cell)
    
@dataclass
class Cell(Place):
    tier_id: str
    occupants: List
    def add_occupant(self, agent):
        self.occupants.append(agent)

@dataclass
class Shared:
    type: str
    occupants: List
    capacity: int
    def add_occupant(self, agent):
        self.occupants.append(agent)


