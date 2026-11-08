"""Alpha 0.57: static regression checks for the renewable-water gameplay loop.

These inspect committed Unreal C++/config source. They DO NOT compile UE5, run
PIE or simulate actual server replication; validate that separately on Windows.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class TestWaterSurvivalLoop(unittest.TestCase):
    def test_enums_extend_without_renumbering_old_items(self):
        items = source("Source/NYVERRA/Public/NyCharacter.h")
        resources = source("Source/NYVERRA/Public/NyResource.h")
        self.assertIn(
            "enum class ENyItemId : uint8 { Wood, Stone, EchoShard, Berries, Axe, Pickaxe, Water };",
            items,
        )
        self.assertIn(
            "enum class ENyResourceKind : uint8 { Wood, Stone, EchoShard, Berries, Water };",
            resources,
        )

    def test_drinking_is_server_authoritative_and_uses_inventory(self):
        header = source("Source/NYVERRA/Public/NyCharacter.h")
        impl = source("Source/NYVERRA/Private/NyCharacter.cpp")
        self.assertIn("UFUNCTION(Server,Reliable) void ServerDrinkWater();", header)
        drink = impl.split("void ANyCharacter::ServerDrinkWater_Implementation(){")[1].split(
            "void ANyCharacter::Tick(float DT)")[0]
        self.assertIn("!HasAuthority()", drink)
        self.assertIn("bIsDead", drink)
        self.assertIn("Thirst>=100.f", drink)
        self.assertIn("CountItem(ENyItemId::Water)<1", drink)
        self.assertIn("SpendItems(ENyItemId::Water,1,", drink)
        self.assertLess(drink.index("SpendItems("), drink.index("Thirst=FMath::Min(100.f,Thirst+35.f)"))
        self.assertIn("ForceNetUpdate()", drink)
        self.assertIn("Now-LastDrinkTime<0.6f", drink)
        self.assertNotIn("AddItem(", drink)

    def test_water_gather_uses_existing_atomic_server_transaction(self):
        impl = source("Source/NYVERRA/Private/NyCharacter.cpp")
        interact = impl.split("void ANyCharacter::ServerInteract_Implementation(){")[1].split(
            "void ANyCharacter::GetLifetimeReplicatedProps")[0]
        self.assertIn("Kind==ENyResourceKind::Water?ENyItemId::Water", interact)
        self.assertIn("Capacity<Requested", interact)
        self.assertIn("Resource->Harvest(Harvested, Requested)", interact)
        self.assertIn("AddItem(Item, Harvested)", interact)

    def test_renewable_water_is_present_near_spawn_and_pois(self):
        cpp = source("Source/NYVERRA/Private/NyGameMode.cpp")
        self.assertIn("i%13==0?ENyResourceKind::Water", cpp)
        self.assertIn("Type==ENyResourceKind::Water?8", cpp)
        guaranteed = []
        for x, y in re.findall(
            r"FVector\((-?\d+)\.f,(-?\d+)\.f,65\.f\), ENyResourceKind::Water, 8",
            cpp,
        ):
            guaranteed.append((int(x), int(y)))
        self.assertGreaterEqual(len(guaranteed), 6)
        self.assertGreaterEqual(sum(x*x+y*y < 750*750 for x,y in guaranteed), 4)
        resource = source("Source/NYVERRA/Private/NyResource.cpp")
        self.assertIn("SetTimer(RespawnTimer,this,&ANyResource::RespawnResource", resource)
        self.assertIn("Remaining=FMath::Max(1,InitialRemaining)", resource)

    def test_input_and_hud_advertise_drinking(self):
        inp = source("Config/DefaultInput.ini")
        header = source("Source/NYVERRA/Public/NyCharacter.h")
        impl = source("Source/NYVERRA/Private/NyCharacter.cpp")
        hud = source("Source/NYVERRA/Private/NyHUD.cpp")
        self.assertIn('ActionMappings=(ActionName="DrinkWater",Key=Q)', inp)
        self.assertIn("void DrinkWater();", header)
        self.assertIn('BindAction(TEXT("DrinkWater")', impl)
        self.assertIn("Q DRINK", hud)
        self.assertIn("CountItem(ENyItemId::Water)", hud)
        self.assertIn("E  GATHER %s", hud)
        self.assertIn("Crate->bAvailable", hud)
        self.assertIn("Kind==ENyResourceKind::Water?ENyItemId::Water", hud)

    def test_inventory_focus_blocks_gameplay_controls(self):
        cpp = source("Source/NYVERRA/Private/NyCharacter.cpp")
        for signature in (
            "void ANyCharacter::Forward(float V)",
            "void ANyCharacter::Right(float V)",
            "void ANyCharacter::MeleeAttack()",
            "void ANyCharacter::Interact()",
            "void ANyCharacter::PlaceFoundation()",
            "void ANyCharacter::PlaceWall()",
            "void ANyCharacter::DrinkWater()",
        ):
            part = cpp.split(signature)[1].split("}")[0]
            self.assertIn("!bInventoryOpen", part, signature)
        self.assertIn("if(bInventoryOpen){StopJumping();StopSprint();}", cpp)
        self.assertIn("if(bInventoryOpen)return; // Cursor state", cpp)


    def test_optional_new_resource_materials_are_versioned_and_non_destructive(self):
        material_script = source("Tools/create_consumable_materials_057.py")
        finalizer = source("Tools/finalize_visual_polish_056.py")
        resources = source("Source/NYVERRA/Private/NyResource.cpp")
        for kind in ("Water", "Berries", "Echo"):
            self.assertIn('("'+kind+'"', material_script)
            self.assertIn("M_Ny"+kind+"_Proto057", resources)
        self.assertIn("if E.does_asset_exist(path):", material_script)
        self.assertIn("create_consumable_materials_057.py", finalizer)
        self.assertIn("MaterialProperty.MP_EMISSIVE_COLOR", material_script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
