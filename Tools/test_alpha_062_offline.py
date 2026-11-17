"""NYVERRA Alpha 0.62: player persistence source regression checks.

Static invariants only: they do not compile Unreal Engine or validate
real disk writes, dedicated server authentication, or multiplayer behavior.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TestPersistentPlayerState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.save = read("Source/NYVERRA/Public/NyPlayerSaveGame.h")
        cls.charh = read("Source/NYVERRA/Public/NyCharacter.h")
        cls.char = read("Source/NYVERRA/Private/NyCharacter.cpp")
        cls.modeh = read("Source/NYVERRA/Public/NyGameMode.h")
        cls.mode = read("Source/NYVERRA/Private/NyGameMode.cpp")

    def test_separate_versioned_player_schema(self):
        self.assertIn("class NYVERRA_API UNyPlayerSaveGame : public USaveGame", self.save)
        self.assertIn("int32 FormatVersion=1", self.save)
        self.assertIn("int64 SaveRevision=0", self.save)
        self.assertIn("TArray<FNySavedPlayerStack> Inventory", self.save)
        for name in ("Health", "Hunger", "Thirst", "Stamina",
                     "DeathCount", "bWasDead", "OwnerDigest", "MapName"):
            self.assertIn(name, self.save)
        self.assertNotIn("FNySavedBuildPiece", self.save)

    def test_no_untrusted_rpc_can_override_inventory_on_load(self):
        self.assertIn("bool CapturePersistentState(UNyPlayerSaveGame* Save) const", self.charh)
        self.assertIn("bool ApplyPersistentState(const UNyPlayerSaveGame* Save)", self.charh)
        self.assertIn("if(!HasAuthority()||!IsValid(Save)", self.char)
        self.assertIn("if(!HasAuthority()||!IsValid(Save)", self.char)
        self.assertNotIn("UFUNCTION(Server", self.save)
        self.assertIn("Save->OwnerDigest=FMD5::HashAnsiString(*Key)", self.mode)

    def test_save_inventory_caps_invalid_items_and_dead_sessions(self):
        capture=self.char.split("bool ANyCharacter::CapturePersistentState(")[1].split(
            "bool ANyCharacter::ApplyPersistentState(")[0]
        restore=self.char.split("bool ANyCharacter::ApplyPersistentState(")[1].split(
            "void ANyCharacter::RefreshLegacyCounters(")[0]
        for token in ("Inventory.Num()>MaxSlots", "Stack.Quantity<1",
                      "Stack.Quantity>Limit", "ENyItemId::Water",
                      "Save->Inventory.Reset()", "if(!bIsDead)"):
            self.assertIn(token, capture)
        for token in ("if(!Save->bWasDead)", "Entry.Quantity>Limit",
                      "Inventory=MoveTemp(Restored)", "Health=Save->bWasDead?100.f",
                      "bIsDead=false", "RefreshLegacyCounters()", "ForceNetUpdate()"):
            self.assertIn(token, restore)

    def test_persistence_only_uses_server_authenticated_identity_or_standalone(self):
        self.assertIn("return ShouldPersistBases()",self.mode)
        self.assertIn("NyAllowAuthenticatedPlayerSaves",self.mode)
        self.assertIn("GetWorld()->GetNetMode()!=NM_Standalone",self.mode)
        self.assertIn("ANyBuildPiece::OnlineOwnerKey(Player)",self.mode)
        self.assertIn("if(!ShouldPersistPlayers()||!IsValid(Player)",self.mode)
        self.assertIn("FMD5::HashAnsiString(*(Map+TEXT(\"|\")+Key))",self.mode)
        self.assertNotIn("GetPlayerName()",self.mode)
        self.assertIn('const FString Map=UGameplayStatics::GetCurrentLevelName(this,true)',self.mode)

    def test_two_snapshots_validate_schema_content_and_identity(self):
        load=self.mode.split("void ANyGameMode::LoadPlayerState(")[1].split(
            "void ANyGameMode::SavePlayerState(")[0]
        checks=self.mode.split("static bool NyValidPlayerSnapshot(")[1].split(
            "void ANyGameMode::LoadPlayerState(")[0]
        self.assertIn('const FString SlotB=SlotA+TEXT("_B")',load)
        self.assertIn("const bool ValidA=HasA&&NyValidPlayerSnapshot(A,Map,Digest)",load)
        self.assertIn("const bool ValidB=HasB&&NyValidPlayerSnapshot(B,Map,Digest)",load)
        self.assertIn("B->SaveRevision>A->SaveRevision",load)
        self.assertIn("PlayerNextBackup.Add(SlotA,!UseB)",load)
        self.assertIn("ProtectedPlayerSlots.Add(SlotA)",load)
        for token in ("Save->OwnerDigest!=Digest","Save->MapName!=Map",
                      "Save->Inventory.Num()>16", "Save->SaveRevision<0",
                      "FMath::IsFinite(Value)", "Entry.ItemId>",
                      "Entry.Quantity<=0", "Save->bWasDead&&Save->Inventory.Num()>0"):
            self.assertIn(token,checks)

    def test_read_back_verifies_items_and_revision(self):
        save=self.mode.split("void ANyGameMode::SavePlayerState(")[1].split(
            "void ANyGameMode::SaveActivePlayers(")[0]
        self.assertIn("Save->SaveRevision=Revision+1",save)
        self.assertIn("SaveGameToSlot(Save,Target,0)",save)
        self.assertIn("LoadGameFromSlot(Target,0)",save)
        self.assertIn("Disk->SaveRevision!=Save->SaveRevision",save)
        self.assertIn("Disk->Inventory.Num()!=Save->Inventory.Num()",save)
        self.assertIn("Disk->Inventory[i].ItemId!=Save->Inventory[i].ItemId",save)
        self.assertIn("Disk->Inventory[i].Quantity!=Save->Inventory[i].Quantity",save)
        self.assertIn("PlayerSaveRevisions.Add(SlotA,Save->SaveRevision)",save)
        self.assertIn("PlayerNextBackup.Add(SlotA,!UseB)",save)
        self.assertIn("ProtectedPlayerSlots.Add(SlotA)",save)

    def test_login_logout_restart_and_shutdown_not_respawn_reload(self):
        self.assertIn("void ANyGameMode::RestartPlayer(AController* NewPlayer)",self.mode)
        self.assertIn("Super::RestartPlayer(NewPlayer)",self.mode)
        self.assertIn("PlayerLoadAttemptedControllers.Contains(NewPlayer)",self.mode)
        self.assertIn("LoadPlayerState(Pawn)",self.mode)
        self.assertIn("SavePlayerState(Pawn)",self.mode)
        self.assertIn("void ANyGameMode::EndPlay(",self.mode)
        self.assertIn("SaveActivePlayers()",self.mode)
        self.assertIn("PlayerLoadAttemptedControllers.Remove(Exiting)",self.mode)

    def test_dirty_saves_and_autosave_rate_limited(self):
        self.assertIn("&ANyGameMode::SaveActivePlayers,20.f,false",self.mode)
        self.assertIn("&ANyGameMode::SaveActivePlayers,60.f,true",self.mode)
        self.assertIn("IsTimerActive(PlayerDirtySaveTimer)",self.mode)
        self.assertIn("GM->RequestPlayerSave()",self.char)
        self.assertIn("void ANyCharacter::RefreshLegacyCounters()",self.char)
        self.assertIn("if((Hunger<=0.f||Thirst<=0.f)",self.char)
        self.assertIn("if(ANyGameMode* GM=GetWorld()->GetAuthGameMode<ANyGameMode>())GM->RequestPlayerSave()",self.char)

    def test_same_online_identity_cannot_write_two_sessions(self):
        self.assertIn("bool ANyGameMode::HasDuplicatePlayerIdentity(",self.mode)
        self.assertIn("if(HasDuplicatePlayerIdentity(Pawn,Key))",self.mode)
        self.assertIn("ProtectedPlayerSlots.Add(SlotA)",self.mode)
        self.assertIn("Concurrent owner identity: persistence disabled",self.mode)
        self.assertIn("Duplicate session detected; refusing snapshot write",self.mode)


if __name__ == "__main__":
    unittest.main(verbosity=2)
