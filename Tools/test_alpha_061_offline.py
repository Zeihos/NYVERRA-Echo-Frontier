"""NYVERRA Alpha 0.61 — A/B world snapshot source regressions.

Tests intentionally inspect committed source invariants; they do NOT execute
Unreal Engine C++, simulate disk power loss, or prove multiplayer behavior.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class TestRotatingBaseSaves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.save=read("Source/NYVERRA/Public/NyBaseSaveGame.h")
        cls.game=read("Source/NYVERRA/Private/NyGameMode.cpp")
        cls.header=read("Source/NYVERRA/Public/NyGameMode.h")
        cls.piece=read("Source/NYVERRA/Private/NyBuildPiece.cpp")
        cls.character=read("Source/NYVERRA/Private/NyCharacter.cpp")

    def test_legacy_v1_revision_defaults_zero(self):
        self.assertIn("int32 FormatVersion=1",self.save)
        self.assertIn("int64 SaveRevision=0",self.save)
        self.assertIn("BaseSaveRevision=0",self.header)

    def test_two_slots_and_monotonic_revisions(self):
        self.assertIn('const FString SlotB=SlotA+TEXT("_B")',self.game)
        self.assertIn('PrimarySlot+TEXT("_B"):PrimarySlot',self.game)
        self.assertIn("Save->SaveRevision=BaseSaveRevision+1",self.game)
        self.assertIn("bNextSaveToBackup=!bNextSaveToBackup",self.game)
        self.assertIn("BaseSaveRevision=Save->SaveRevision",self.game)
        self.assertIn("BaseSaveRevision==MAX_int64",self.game)

    def test_loads_latest_valid_snapshot_and_preserves_other_copy(self):
        self.assertIn("const bool bValidA=bHaveA&&IsValidSnapshot(SaveA)",self.game)
        self.assertIn("const bool bValidB=bHaveB&&IsValidSnapshot(SaveB)",self.game)
        self.assertIn("SaveB->SaveRevision>SaveA->SaveRevision",self.game)
        self.assertIn("bNextSaveToBackup=!bUseB",self.game)
        self.assertIn("Snapshot->FormatVersion!=1",self.game)
        self.assertIn("Snapshot->SaveRevision<0",self.game)
        self.assertIn("Snapshot->MapName!=CurrentMap",self.game)

    def test_both_invalid_is_readonly_without_spawning(self):
        load=self.game.split("void ANyGameMode::LoadBases(){")[1].split(
            "void ANyGameMode::BindPlayerToSavedBases(")[0]
        self.assertIn("if(!bValidA&&!bValidB)",load)
        self.assertLess(load.index("if(!bValidA&&!bValidB)"),load.index("bLoadingBases=true"))
        self.assertIn("bBaseSaveReadOnly=true",load)
        self.assertIn("Seen.Contains(E.PersistentId)",load)
        self.assertIn("Save->Pieces.Num()",load)

    def test_a_write_must_be_read_back_before_advancing_revision(self):
        save=self.game.split("void ANyGameMode::SaveBases(){")[1].split(
            "void ANyGameMode::LoadBases(){")[0]
        self.assertIn("SaveGameToSlot(Save,TargetSlot,0)",save)
        self.assertIn("LoadGameFromSlot(TargetSlot,0)",save)
        self.assertIn("Verified->SaveRevision!=Save->SaveRevision",save)
        self.assertIn("Verified->Pieces.Num()!=Save->Pieces.Num()",save)
        self.assertIn("Original.PersistentId!=Disk.PersistentId",save)
        self.assertIn("Original.OwnerNetworkId!=Disk.OwnerNetworkId",save)
        self.assertIn("!Original.Location.Equals(Disk.Location",save)
        self.assertIn("Record mismatch after read-back",save)
        self.assertLess(save.index("LoadGameFromSlot(TargetSlot,0)"),
                        save.index("BaseSaveRevision=Save->SaveRevision"))
        self.assertIn("bBaseSaveReadOnly=true",save)

    def test_fail_closed_for_all_structure_mutations(self):
        self.assertIn("bool CanMutateBaseWorld() const",self.header)
        self.assertIn("if(!Mode->CanPlaceBasePieces())return;",self.character)
        self.assertIn("Mode->CanMutateBaseWorld()",self.piece)
        self.assertIn("if(!Mode->CanMutateBaseWorld())return 0.f",self.piece)
        self.assertIn("if(!Mode->CanMutateBaseWorld())return false",self.piece)

    def test_existing_backup_ignores_private_save_files_in_git(self):
        backup=read("Tools/Backup-NyverraBaseSaves.ps1")
        ignore=read(".gitignore")
        self.assertIn("NYVERRA_Bases_v1_*.sav",backup)
        self.assertIn("Get-FileHash",backup)
        self.assertIn("Saved/",ignore)

if __name__=="__main__":
    unittest.main(verbosity=2)
