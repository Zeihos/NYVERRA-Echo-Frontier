"""Alpha 0.60 persistence regression checks (offline source tests only).

These verify source invariants, NOT UE5.8 C++ compilation, save-file durability,
authenticated identity providers, or multiplayer behavior.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

class TestBasePersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.save = read("Source/NYVERRA/Public/NyBaseSaveGame.h")
        cls.game_h = read("Source/NYVERRA/Public/NyGameMode.h")
        cls.game = read("Source/NYVERRA/Private/NyGameMode.cpp")
        cls.piece_h = read("Source/NYVERRA/Public/NyBuildPiece.h")
        cls.piece = read("Source/NYVERRA/Private/NyBuildPiece.cpp")
        cls.char = read("Source/NYVERRA/Private/NyCharacter.cpp")

    def test_schema_version_and_required_fields(self):
        self.assertIn("class NYVERRA_API UNyBaseSaveGame : public USaveGame", self.save)
        for field in ("PersistentId", "PieceType", "Location", "Rotation",
                      "Durability", "OwnerNetworkId"):
            self.assertIn(field, self.save)
        self.assertIn("int32 FormatVersion=1", self.save)
        self.assertIn("TArray<FNySavedBuildPiece> Pieces", self.save)
        self.assertIn("UPROPERTY(SaveGame)", self.save)

    def test_persistence_is_map_scoped_server_side_and_pie_disabled(self):
        self.assertIn("!HasAuthority()", self.game)
        self.assertIn("W->WorldType==EWorldType::PIE", self.game)
        self.assertIn("NYVERRA_Bases_v1_", self.game)
        self.assertIn("GetCurrentLevelName(this,true)", self.game)
        self.assertIn("SaveGameToSlot(Save,Slot,0)", self.game)
        self.assertIn("LoadGameFromSlot(Slot,0)", self.game)
        self.assertIn("DoesSaveGameExist(Slot,0)", self.game)

    def test_incompatible_or_corrupt_save_never_overwritten(self):
        self.assertIn("Save->FormatVersion!=1", self.game)
        self.assertIn("Save->MapName!=CurrentMap", self.game)
        self.assertIn("Save->Pieces.Num()>1024", self.game)
        self.assertIn("bBaseSaveReadOnly=true", self.game)
        self.assertIn("if(!ShouldPersistBases()||bLoadingBases||bBaseSaveReadOnly)return;", self.game)
        self.assertIn("Seen.Contains(E.PersistentId)", self.game)
        self.assertIn("E.Location.ContainsNaN()", self.game)
        self.assertIn("E.Rotation.ContainsNaN()", self.game)
        self.assertIn("E.OwnerNetworkId.Len()>256", self.game)
        self.assertIn("FMath::IsFinite(E.Durability)", self.game)

    def test_save_tracks_actor_ids_and_reuses_them_after_restart(self):
        self.assertIn("PersistentId=FGuid::NewGuid()", self.piece)
        self.assertIn("PersistentId=SavedId", self.piece)
        self.assertIn("Entry.PersistentId=Piece->PersistentId", self.game)
        self.assertIn("Entry.Location=Piece->GetActorLocation()", self.game)
        self.assertIn("Entry.Rotation=Piece->GetActorRotation()", self.game)
        self.assertIn("Entry.Durability=Piece->Durability", self.game)
        self.assertIn("Piece->RestoreFromSave(E.PieceType,E.PersistentId,E.Durability,E.OwnerNetworkId)", self.game)
        self.assertIn("DOREPLIFETIME(ANyBuildPiece,PersistentId)", self.piece)

    def test_owner_is_not_client_writable_or_name_based(self):
        self.assertIn("BuilderNetworkId=OnlineOwnerKey(InBuilder)", self.piece)
        self.assertIn("const FUniqueNetIdRepl& NetId=Player->GetUniqueId()", self.piece)
        self.assertIn("NetId.IsValid()?NetId.ToString()", self.piece)
        self.assertIn("LOCAL_STANDALONE_OWNER_V1", self.piece)
        self.assertIn("W->GetNetMode()==NM_Standalone", self.piece)
        self.assertIn("UPROPERTY()\n FString BuilderNetworkId", self.piece_h)
        self.assertNotIn("DOREPLIFETIME(ANyBuildPiece,BuilderNetworkId)", self.piece)
        self.assertIn("IsBuildOwner(Requester)", self.piece)

    def test_rebind_owner_across_reconnect_and_existing_listen_login(self):
        self.assertIn("virtual void PostLogin(APlayerController* NewPlayer) override", self.game_h)
        self.assertIn("virtual void Logout(AController* Exiting) override", self.game_h)
        self.assertIn("for(APlayerState* Player:State->PlayerArray)", self.game)
        self.assertIn("BindPlayerToSavedBases(NewPlayer->GetPlayerState<APlayerState>())", self.game)
        self.assertIn("It->BindReturningOwner(Player)", self.game)
        self.assertIn("It->UnbindDepartingOwner(Departing)", self.game)
        self.assertIn("BuilderPlayerState=Player", self.piece)
        self.assertIn("BuilderPlayerState=nullptr", self.piece)

    def test_actor_changes_schedule_saves_and_autosave(self):
        self.assertIn("void ANyGameMode::RequestBaseSave()", self.game)
        self.assertIn("IsTimerActive(BaseDirtySaveTimer)", self.game)
        self.assertIn("&ANyGameMode::SaveBases,3.f,false", self.game)
        self.assertIn("&ANyGameMode::SaveBases,60.f,true", self.game)
        self.assertGreaterEqual(self.piece.count("GM->RequestBaseSave()"), 3)
        self.assertIn("bLoadingBases=true", self.game)
        self.assertIn("bLoadingBases=false", self.game)

    def test_no_piece_truncation_or_floating_door(self):
        self.assertIn("Save->Pieces.Num()>=1024", self.game)
        self.assertIn("LivePieces>=1024)return", self.char)
        self.assertIn("CanPlaceBasePieces()", self.char)
        self.assertIn("bool CanPlaceBasePieces() const", self.game_h)
        self.assertIn("Backups", read("Tools/Backup-NyverraBaseSaves.ps1"))
        self.assertIn("if(Type==2 && (!Foundation || Foundation->PieceType!=0))return", self.char)
        self.assertIn("bDoorOpen=false", self.piece.split("void ANyBuildPiece::RestoreFromSave(")[1])

if __name__ == "__main__":
    unittest.main(verbosity=2)
