"""EXP-001 synthetic event-representation simulator.

The package implements the bounded comparison authorized by DEC-003.  It is
not a target-device radiation model and intentionally contains no L3-E model.
"""

from .model import (
    JointImpactEvent,
    MemorySpec,
    PeriodicScrub,
    PhysicalEvent,
    PhysicalMapping,
    SimulationResult,
    WordImpact,
    simulate_joint_events,
    simulate_physical_events,
)

__all__ = [
    "JointImpactEvent",
    "MemorySpec",
    "PeriodicScrub",
    "PhysicalEvent",
    "PhysicalMapping",
    "SimulationResult",
    "WordImpact",
    "simulate_joint_events",
    "simulate_physical_events",
]
