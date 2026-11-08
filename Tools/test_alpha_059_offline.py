"""NYVERRA Alpha 0.59 — locked-door source regression gates.

Static checks only, not Unreal compilation, network simulation or game QA.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")

class TestLockedDoors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=read("Source/NYVERRA/Public/NyBuildPiece.h")
        cls.cpp=read("Source/NYVERRA/Private/NyBuildPiece.cpp")
        cls.charh=read("Source/NYVERRA/Public/NyCharacter.h")
        cls.char=read("Source/NYVERRA/Private/NyCharacter.cpp")
        cls.hud=read("Source/NYVERRA/Private/NyHUD.cpp")
        cls.input=read("Config/DefaultInput.ini")

    def test_existing_building_tiers_preserved(self):
        self.assertIn("PieceType==0?FVector(3.f,3.f,.3f)", self.cpp)
        self.assertIn("PieceType==1?FVector(2.4f,.3f,2.5f)", self.cpp)
        self.assertIn("PieceType==0?FVector(3.f,3.f,.3f)", self.cpp)
        self.assertIn("MaxDurability=NewType==0?600.f:NewType==1?360.f:280.f",self.cpp)
        self.assertIn("Piece->Initialize(Type,GetPlayerState())",self.char)

    def test_locked_door_has_distinct_replication_state(self):
        self.assertIn("ReplicatedUsing=OnRep_DoorOpen",self.h)
        self.assertIn("DOREPLIFETIME(ANyBuildPiece,bDoorOpen)",self.cpp)
        self.assertIn("void ANyBuildPiece::OnRep_DoorOpen()",self.cpp)
        self.assertIn("Mesh->SetVisibility(!bOpened,true)",self.cpp)
        self.assertIn("ECollisionEnabled::NoCollision",self.cpp)
        self.assertIn("ForceNetUpdate()",self.cpp)

    def test_only_authoritative_owner_opens(self):
        body=self.cpp.split("bool ANyBuildPiece::TryOpenDoor(")[1].split("void ANyBuildPiece::TryCloseDoor()")[0]
        for token in ("!HasAuthority()","PieceType!=2","!IsValid(Requester)",
                      "BuilderPlayerState!=Requester","Durability<=0.f",
                      "bDoorOpen=true","&ANyBuildPiece::TryCloseDoor","8.f,false"):
            self.assertIn(token,body)

    def test_door_waits_until_exit_clear_before_closing(self):
        body=self.cpp.split("void ANyBuildPiece::TryCloseDoor(){")[1].split("float ANyBuildPiece::TakeDamage(")[0]
        for token in ("!HasAuthority()","ECC_Pawn","ECC_WorldDynamic","OverlapAnyTestByObjectType",
                      "if(bOccupied)","&ANyBuildPiece::TryCloseDoor,1.f,false",
                      "bDoorOpen=false","OnRep_DoorOpen();","ForceNetUpdate();"):
            self.assertIn(token,body)

    def test_door_requires_grounded_foundation_and_exact_cost(self):
        code=self.char.split("void ANyCharacter::ServerPlacePiece_Implementation(")[1].split(
            "void ANyCharacter::ServerRepairPiece_Implementation")[0]
        for token in ("Type>2","Type==2?6:4","Type==2?4:2",
                      "if(Type==2 && (!Foundation || Foundation->PieceType!=0))return",
                      "FVector(90.f,12.5f,120.f)",
                      "(Type==1 && Foundation)||(Type==2 && Foundation)",
                      "SpendItems(ENyItemId::Wood,WoodCost,ENyItemId::Stone,StoneCost)"):
            self.assertIn(token,code)

    def test_interaction_is_server_ray_and_ownership_checked(self):
        interaction=self.char.split("void ANyCharacter::ServerInteract_Implementation(){")[1].split(
            "void ANyCharacter::GetLifetimeReplicatedProps(")[0]
        self.assertIn("LineTraceSingleByChannel(Hit,Eye,End,ECC_Visibility,Params)", interaction)
        self.assertIn("Cast<ANyBuildPiece>(Hit.GetActor())",interaction)
        self.assertIn("Door->TryOpenDoor(GetPlayerState())",interaction)
        self.assertIn("FVector::DistSquared(GetActorLocation(),Door->GetActorLocation())",interaction)
        self.assertLess(interaction.index("Door->TryOpenDoor"),interaction.index("Cast<ANyLootCrate>"))
        self.assertNotIn("UFUNCTION(Server",self.h)  # Not exposed on structure directly.

    def test_access_controls_and_hud(self):
        self.assertIn('ActionMappings=(ActionName="BuildDoor",Key=Five)',self.input)
        self.assertIn('BindAction(TEXT("BuildDoor")',self.char)
        self.assertIn("void PlaceDoor();",self.charh)
        self.assertIn("if(!bInventoryOpen&&!bIsDead)ServerPlacePiece(2)",self.char)
        self.assertIn("LOCKED DOOR",self.hud)
        self.assertIn("E OPEN (AUTO-CLOSE)",self.hud)
        self.assertIn("Piece->BuilderPlayerState==P->GetPlayerState()",self.hud)
        self.assertIn("5 DOOR",self.hud)

    def test_door_reuses_durability_raid_and_repair(self):
        self.assertIn("MaxDurability=NewType==0?600.f:NewType==1?360.f:280.f",self.cpp)
        self.assertIn("Durability=FMath::Max(0.f,Durability-Applied)",self.cpp)
        self.assertIn("if(Durability<=0.f){",self.cpp)
        self.assertIn("Destroy();",self.cpp)
        self.assertIn("BuilderPlayerState!=Requester",self.cpp)
        self.assertIn("GetWorld()->GetTimeSeconds()-LastDamageTime>=12.f",self.cpp)

if __name__=="__main__":
    unittest.main(verbosity=2)
