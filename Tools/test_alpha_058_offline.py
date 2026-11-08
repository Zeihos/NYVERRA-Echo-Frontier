"""Alpha 0.58 — structural regression checks for multiplayer base durability.

These are source-invariant checks, not a UE C++ build or a simulated network test.
Run: py -3 Tools/test_alpha_058_offline.py
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def src(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TestRaidingAndRepair(unittest.TestCase):
    def setUp(self):
        self.header = src("Source/NYVERRA/Public/NyBuildPiece.h")
        self.build = src("Source/NYVERRA/Private/NyBuildPiece.cpp")
        self.pawn = src("Source/NYVERRA/Private/NyCharacter.cpp")

    def test_replicated_durability_max_and_builder(self):
        for name in ("PieceType", "Durability", "MaxDurability", "BuilderPlayerState"):
            self.assertIn(f"DOREPLIFETIME(ANyBuildPiece,{name})", self.build)
        self.assertIn("APlayerState* BuilderPlayerState", self.header)
        self.assertIn("void Initialize(uint8 NewType, APlayerState* InBuilder)", self.header)
        self.assertIn("Piece->Initialize(Type,GetPlayerState())", self.pawn)
        self.assertIn("MaxDurability=NewType==0?600.f:NewType==1?360.f:280.f", self.build)

    def test_damage_server_validated_and_bounded(self):
        damage = self.build.split("float ANyBuildPiece::TakeDamage(")[1].split(
            "bool ANyBuildPiece::CanRepair(")[0]
        for expect in (
            "!HasAuthority()", "!FMath::IsFinite(DamageAmount)",
            "DamageAmount<=0.f", "Cast<ANyCharacter>(DamageCauser)",
            "Raider->bIsDead", "Raider->GetController()!=EventInstigator",
            "FMath::Min(Durability,FMath::Min(DamageAmount,50.f))",
            "Durability=FMath::Max(0.f,Durability-Applied)",
            "LastDamageTime=GetWorld()->GetTimeSeconds()", "ForceNetUpdate()",
            "Destroy()",
        ):
            self.assertIn(expect, damage)

    def test_repair_server_owned_and_not_during_active_raid(self):
        validation = self.build.split("bool ANyBuildPiece::CanRepair(")[1].split(
            "bool ANyBuildPiece::Repair(")[0]
        for expect in (
            "!HasAuthority()", "BuilderPlayerState!=Requester",
            "Durability<=0.f", "Durability>=MaxDurability",
            "GetWorld()->GetTimeSeconds()-LastDamageTime>=12.f",
        ):
            self.assertIn(expect, validation)
        repair = self.build.split("bool ANyBuildPiece::Repair(")[1].split(
            "void ANyBuildPiece::GetLifetimeReplicatedProps")[0]
        self.assertIn("if(!CanRepair(Requester)", repair)
        self.assertIn("FMath::Min(MaxDurability,Durability+FMath::Min(Amount,75.f))", repair)
        self.assertIn("ForceNetUpdate()", repair)

    def test_server_makes_raid_hit_first_line_trace_only(self):
        attack = self.pawn.split("void ANyCharacter::ServerMeleeAttack_Implementation(){")[1].split(
            "void ANyCharacter::ReceiveCombatDamage(")[0]
        self.assertIn("LineTraceSingleByChannel(Hit,Eye,End,ECC_Visibility,Params)", attack)
        self.assertIn("Cast<ANyBuildPiece>(Hit.GetActor())", attack)
        self.assertIn("UGameplayStatics::ApplyDamage(Piece,35.f,Controller,this,nullptr)", attack)
        self.assertLess(attack.index("Cast<ANyBuildPiece>"),attack.index("ANyCharacter* Victim"))
        self.assertIn("LastAttackTime<0.75f", attack)

    def test_server_repair_requires_line_of_sight_owner_resources(self):
        repair = self.pawn.split("void ANyCharacter::ServerRepairPiece_Implementation(){")[1].split(
            "void ANyCharacter::ServerInteract_Implementation()")[0]
        for expect in (
            "!HasAuthority()", "bIsDead", "!Controller", "Now-LastRepairTime<0.65f",
            "LineTraceSingleByChannel(Hit,Eye,End,ECC_Visibility,Params)",
            "Cast<ANyBuildPiece>(Hit.GetActor())",
            "Piece->CanRepair(GetPlayerState())",
            "CountItem(ENyItemId::Wood)<1", "CountItem(ENyItemId::Stone)<1",
            "SpendItems(ENyItemId::Wood,1,ENyItemId::Stone,1)",
            "Piece->Repair(GetPlayerState(),75.f)",
            "AddItem(ENyItemId::Wood,1)", "AddItem(ENyItemId::Stone,1)",
        ):
            self.assertIn(expect,repair)
        self.assertNotIn("FHitResult Client",repair)
        self.assertLess(repair.index("Piece->CanRepair(GetPlayerState())"),repair.index("SpendItems("))

    def test_input_hud_and_inventory_guard(self):
        keys=src("Config/DefaultInput.ini")
        hud=src("Source/NYVERRA/Private/NyHUD.cpp")
        pawnhead=src("Source/NYVERRA/Public/NyCharacter.h")
        self.assertIn('ActionMappings=(ActionName="RepairPiece",Key=R)', keys)
        self.assertIn('BindAction(TEXT("RepairPiece")', self.pawn)
        self.assertIn("UFUNCTION(Server,Reliable) void ServerRepairPiece()", pawnhead)
        self.assertIn("if(!bInventoryOpen&&!bIsDead)ServerRepairPiece()",self.pawn)
        self.assertIn("R REPAIR",hud)
        self.assertIn("Piece->Durability",hud)
        self.assertIn("Piece->MaxDurability",hud)
        self.assertIn("Piece->BuilderPlayerState==P->GetPlayerState()",hud)

    def test_building_size_and_placement_regression(self):
        self.assertIn("FVector(3.f,3.f,.3f)",self.build)
        self.assertIn("FVector(2.4f,.3f,2.5f)",self.build)
        self.assertIn("FVector(120.f,15.f,125.f)",self.pawn)
        self.assertIn("Type==1 && Foundation",self.pawn)
        self.assertIn("Foundation->PieceType!=0",self.pawn)


if __name__ == "__main__":
    unittest.main(verbosity=2)
