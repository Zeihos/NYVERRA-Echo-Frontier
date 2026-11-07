"""Static regression checks for NYVERRA gameplay polish.

Does not compile C++, simulate UE networking, or prove behavior in Play-in-Editor.
Run: py -3 Tools/test_alpha_054_offline.py
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class TestGameplaySourceInvariants(unittest.TestCase):
    def test_depleted_resource_is_not_destroyed_and_replenishes(self):
        cpp = read("Source/NYVERRA/Private/NyResource.cpp")
        self.assertIn("ANyResource::RespawnResource()", cpp)
        self.assertIn("GetWorldTimerManager().SetTimer(RespawnTimer", cpp)
        self.assertIn("Remaining=FMath::Max(1,InitialRemaining)", cpp)
        harvest = cpp.split("bool ANyResource::Harvest(")[1].split("void ANyResource::RespawnResource")[0]
        self.assertNotIn("Destroy()", harvest)

    def test_resource_replenishment_is_server_authoritative(self):
        cpp = read("Source/NYVERRA/Private/NyResource.cpp")
        head = read("Source/NYVERRA/Public/NyResource.h")
        self.assertIn("if(!HasAuthority())return;", cpp.split("void ANyResource::RespawnResource()")[1])
        self.assertIn("int32 InitialRemaining", head)
        self.assertIn("FMath::Max(1,Amount)", cpp)
        self.assertIn("ForceNetUpdate();", cpp.split("void ANyResource::RespawnResource()")[1])

    def test_empty_resources_disable_collision_on_all_peers(self):
        cpp = read("Source/NYVERRA/Private/NyResource.cpp")
        self.assertIn("ANyResource::OnRep_Remaining(){UpdateAvailability();}", cpp)
        availability = cpp.split("void ANyResource::UpdateAvailability(){")[1].split("void ANyResource::OnRep_Remaining()")[0]
        self.assertIn("SetVisibility(bAvailable,true)", availability)
        self.assertIn("ECollisionEnabled::NoCollision", availability)

    def test_empty_loot_crates_disable_collision(self):
        cpp = read("Source/NYVERRA/Private/NyLootCrate.cpp")
        self.assertIn("ANyLootCrate::OnRep_LootState(){ApplyAppearance();}", cpp)
        appearance = cpp.split("void ANyLootCrate::ApplyAppearance(){")[1].split("void ANyLootCrate::GetLifetimeReplicatedProps")[0]
        self.assertIn("Mesh->SetVisibility(bAvailable,true)", appearance)
        self.assertIn("ECollisionEnabled::NoCollision", appearance)

    def test_last_resource_unit_with_tool_can_be_harvested(self):
        cpp = read("Source/NYVERRA/Private/NyCharacter.cpp")
        self.assertIn("const int32 Requested=FMath::Min(Award,Resource->Remaining)", cpp)
        self.assertIn("Resource->Harvest(Harvested, Requested)", cpp)
        self.assertNotIn("Resource->Remaining < Award || Capacity < Award", cpp)

    def test_pve_enemies_respawn_with_replication(self):
        cpp = read("Source/NYVERRA/Private/NyEnemy.cpp")
        head = read("Source/NYVERRA/Public/NyEnemy.h")
        self.assertIn("ReplicatedUsing=OnRep_Dead", head)
        self.assertIn("ANyEnemy::RespawnEnemy()", cpp)
        self.assertIn("GetWorldTimerManager().SetTimer(RespawnTimer", cpp)
        self.assertIn("Health=60.f", cpp.split("void ANyEnemy::RespawnEnemy()")[1])
        self.assertIn("SetMovementMode(MOVE_Walking)", cpp)
        self.assertIn("SetActorEnableCollision(!bDead)", cpp)
        self.assertIn("DOREPLIFETIME(ANyEnemy,bDead)", cpp)
        self.assertNotIn("SetTimer(DespawnTimer", cpp)

    def test_existing_sun_is_reused(self):
        cpp = read("Source/NYVERRA/Private/NyWorldState.cpp")
        atmosphere = cpp.split("void ANyWorldState::CreateAtmosphere(){")[1].split("void ANyWorldState::UpdateAtmosphere(){")[0]
        self.assertIn("TActorIterator<ADirectionalLight>", atmosphere)
        self.assertIn("TActorIterator<AExponentialHeightFog>", atmosphere)
        self.assertRegex(atmosphere, r"if\s*\(!Sun\)\s*\{")
        self.assertRegex(atmosphere, r"if\s*\(!Fog\)\s*\{")
        self.assertIn("SetMobility(EComponentMobility::Movable)", atmosphere)

    def test_editor_maps_not_assigned_without_saved_asset(self):
        script = read("Tools/bootstrap_alpha_053.py")
        self.assertLess(script.index("if not MAP_FILE.is_file()"), script.index("set_test_world_default.py"))
        self.assertIn("TestWorld exists", read("Tools/create_test_world.py"))

    def test_multiplayer_respawn_avoids_crowded_spawn(self):
        cpp = read("Source/NYVERRA/Private/NyCharacter.cpp")
        respawn = cpp.split("void ANyCharacter::RespawnAfterDeath(){")[1].split("void ANyCharacter::PlaceFoundation()")[0]
        self.assertIn("BestClearanceSquared", respawn)
        self.assertIn("TActorIterator<APlayerStart>", respawn)
        self.assertIn("TActorIterator<ANyCharacter>", respawn)
        self.assertIn("Other->bIsDead", respawn)
        self.assertIn("NearestPlayerSquared>BestClearanceSquared", respawn)

    def test_hud_does_not_draw_combat_crosshair_over_inventory(self):
        cpp = read("Source/NYVERRA/Private/NyHUD.cpp")
        self.assertIn("DEVELOPMENT BUILD", cpp)
        self.assertNotIn("ALPHA 0.11", cpp)
        self.assertIn("if(!LocalPawn || !LocalPawn->bInventoryOpen)", cpp)
        self.assertLess(cpp.index("if(!LocalPawn || !LocalPawn->bInventoryOpen)"), cpp.index("DrawLine(X*.5f-9"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
