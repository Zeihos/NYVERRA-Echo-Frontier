"""Alpha 0.64 death inventory regression (source checks, not UE integration)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeathLootSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = (ROOT / "Source/NYVERRA/Private/NyCharacter.cpp").read_text(encoding="utf-8")
        cls.death = text.split("void ANyCharacter::ReceiveCombatDamage(")[1].split(
            "void ANyCharacter::RespawnAfterDeath()"
        )[0]
        cls.respawn = text.split("void ANyCharacter::RespawnAfterDeath()")[1].split(
            "void ANyCharacter::PlaceFoundation()"
        )[0]

    def test_inventory_cleared_on_authoritative_death_not_delayed(self):
        death = self.death
        for token in ("if(!HasAuthority()", "bIsDead=true", "Inventory.Reset();",
                      "RefreshLegacyCounters();", "CheckpointPlayerDeath(this)"):
            self.assertIn(token, death)
        self.assertLess(death.index("bIsDead=true"), death.index("Inventory.Reset();"))
        self.assertLess(death.index("Inventory.Reset();"), death.index("CheckpointPlayerDeath(this)"))
        self.assertLess(death.index("RefreshLegacyCounters();"), death.index("CheckpointPlayerDeath(this)"))

    def test_respawn_remains_defensively_empty(self):
        self.assertIn("Inventory.Reset();RefreshLegacyCounters();", self.respawn)
        self.assertLess(self.respawn.index("Inventory.Reset();"),
                        self.respawn.index("bIsDead=false"))


if __name__ == "__main__":
    unittest.main()
