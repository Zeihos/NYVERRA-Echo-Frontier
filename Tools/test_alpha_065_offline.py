"""Alpha 0.65: server-owned foundation attachment guard (source invariant only)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FoundationAuthorization(unittest.TestCase):
    def test_wall_and_door_attach_requires_server_owner(self):
        character = (ROOT / "Source/NYVERRA/Private/NyCharacter.cpp").read_text(encoding="utf-8")
        placement = character.split("void ANyCharacter::ServerPlacePiece_Implementation(")[1].split(
            "void ANyCharacter::ServerRepairPiece_Implementation("
        )[0]
        require_foundation = "if(Type==2 && (!Foundation || Foundation->PieceType!=0))return;"
        refuse_foreign = "if(Foundation && !Foundation->IsBuildOwner(GetPlayerState()))return;"
        resource_spend = "SpendItems(ENyItemId::Wood,WoodCost,ENyItemId::Stone,StoneCost)"
        self.assertIn(require_foundation, placement)
        self.assertIn(refuse_foreign, placement)
        self.assertLess(placement.index(require_foundation), placement.index(refuse_foreign))
        self.assertLess(placement.index(refuse_foreign), placement.index(resource_spend))

    def test_owner_method_is_server_authoritative(self):
        piece = (ROOT / "Source/NYVERRA/Private/NyBuildPiece.cpp").read_text(encoding="utf-8")
        owner = piece.split("bool ANyBuildPiece::IsBuildOwner(")[1].split(
            "void ANyBuildPiece::BindReturningOwner("
        )[0]
        self.assertIn("!HasAuthority()", owner)
        self.assertIn("BuilderPlayerState==Player", owner)
        self.assertIn("OnlineOwnerKey(Player)", owner)

    def test_failed_build_does_not_charge_resources(self):
        character = (ROOT / "Source/NYVERRA/Private/NyCharacter.cpp").read_text(encoding="utf-8")
        placement = character.split("void ANyCharacter::ServerPlacePiece_Implementation(")[1].split(
            "void ANyCharacter::ServerRepairPiece_Implementation("
        )[0]
        self.assertIn("if (!SpendItems(", placement)
        self.assertIn("Piece->Destroy(); return;", placement)


if __name__ == "__main__":
    unittest.main()
