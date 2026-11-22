"""Alpha 0.64 source regression: death tombstones reject contradictory HP.

These checks do not compile Unreal Engine or simulate actual save files.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class DeathSnapshotValidation(unittest.TestCase):
    def test_server_death_sets_zero_health_before_checkpoint(self):
        character = source("Source/NYVERRA/Private/NyCharacter.cpp")
        death = character.split("void ANyCharacter::ReceiveCombatDamage(")[1].split(
            "void ANyCharacter::RespawnAfterDeath()"
        )[0]
        self.assertLess(death.index("Health=FMath::Max(0.f"), death.index("bIsDead=true"))
        self.assertLess(death.index("bIsDead=true"), death.index("CheckpointPlayerDeath(this)"))

    def test_save_capture_rejects_dead_inventory(self):
        character = source("Source/NYVERRA/Private/NyCharacter.cpp")
        capture = character.split("bool ANyCharacter::CapturePersistentState(")[1].split(
            "bool ANyCharacter::ApplyPersistentState("
        )[0]
        self.assertIn("if(!bIsDead){", capture)
        self.assertIn("Save->Inventory.Reset()", capture)

    def test_validation_rejects_positive_health_on_dead_snapshot(self):
        mode = source("Source/NYVERRA/Private/NyGameMode.cpp")
        validation = mode.split("static bool NyValidPlayerSnapshot(")[1].split(
            "void ANyGameMode::LoadPlayerState("
        )[0]
        self.assertIn("Save->bWasDead&&(Save->Health>0.f||Save->Inventory.Num()>0)", validation)
        self.assertIn("!Save->bWasDead&&Save->Health<=0.f", validation)
        self.assertIn("!FMath::IsFinite(Value)", validation)

    def test_invalid_snapshot_cannot_overwrite_backup(self):
        mode = source("Source/NYVERRA/Private/NyGameMode.cpp")
        self.assertIn("ProtectedPlayerSlots.Add(SlotA)", mode)
        self.assertIn("if(!ValidA&&!ValidB)", mode)
        self.assertIn("SaveGameToSlot(Save,Target,0)", mode)


if __name__ == "__main__":
    unittest.main()
