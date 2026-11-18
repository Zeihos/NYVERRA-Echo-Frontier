"""NYVERRA Alpha 0.63 — bandages, private inventory and death persistence.

Source-invariant regression gates; not an Unreal compilation or gameplay test.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT/path).read_text(encoding="utf-8")


class TestBandageAndPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header=read("Source/NYVERRA/Public/NyCharacter.h")
        cls.char=read("Source/NYVERRA/Private/NyCharacter.cpp")
        cls.mode=read("Source/NYVERRA/Private/NyGameMode.cpp")
        cls.modeh=read("Source/NYVERRA/Public/NyGameMode.h")
        cls.ini=read("Config/DefaultInput.ini")
        cls.hud=read("Source/NYVERRA/Private/NyHUD.cpp")

    def test_item_ids_appended_without_breaking_v1_savegames(self):
        self.assertIn(
            "enum class ENyItemId : uint8 { Wood, Stone, EchoShard, Berries, Axe, Pickaxe, Water, Bandage };",
            self.header)
        self.assertIn("case ENyItemId::Bandage: return TEXT(\"BANDAGE\")",self.char)
        self.assertIn("Id>static_cast<uint8>(ENyItemId::Bandage)",self.char)
        self.assertIn("Entry.ItemId>static_cast<uint8>(ENyItemId::Bandage)",self.char)
        self.assertIn("Entry.ItemId>static_cast<uint8>(ENyItemId::Bandage)",self.mode)
        self.assertIn("int32 FormatVersion=1",read("Source/NYVERRA/Public/NyPlayerSaveGame.h"))

    def test_bandage_recipe_cannot_overflow_inventory(self):
        code=self.char.split("void ANyCharacter::ServerCraftBandage_Implementation(){")[1].split(
            "void ANyCharacter::ServerUseBandage_Implementation(){")[0]
        for token in (
            "!HasAuthority()", "bIsDead", "Health<=0.f",
            "CountItem(ENyItemId::Berries)<2", "CountItem(ENyItemId::Water)<1",
            "TArray<FNyItemStack> Preview=Inventory",
            "PreviewRemove(ENyItemId::Berries,2)", "PreviewRemove(ENyItemId::Water,1)",
            "Preview.Num()<MaxSlots", "Stack.Item==ENyItemId::Bandage&&Stack.Quantity<100",
            "if(!bCapacity)return",
            "SpendItems(ENyItemId::Berries,2,ENyItemId::Water,1)",
            "AddItem(ENyItemId::Bandage,1)",
            "AddItem(ENyItemId::Berries,2)", "AddItem(ENyItemId::Water,1)",
        ):
            self.assertIn(token,code)
        self.assertLess(code.index("if(!bCapacity)return"),code.index("SpendItems("))
        self.assertLess(code.index("SpendItems("),code.index("AddItem(ENyItemId::Bandage,1)"))

    def test_healing_requires_server_owned_bandage_and_cooldown(self):
        code=self.char.split("void ANyCharacter::ServerUseBandage_Implementation(){")[1].split(
            "void ANyCharacter::Tick(")[0]
        for token in (
            "!HasAuthority()", "bIsDead", "Health<=0.f", "Health>=100.f",
            "CountItem(ENyItemId::Bandage)<1", "Now-LastBandageTime<4.f",
            "SpendItems(ENyItemId::Bandage,1,ENyItemId::Wood,0)",
            "Health=FMath::Min(100.f,Health+35.f)", "ForceNetUpdate()",
            "GM->RequestPlayerSave()",
        ):
            self.assertIn(token,code)
        self.assertLess(code.index("SpendItems("),code.index("Health=FMath::Min"))

    def test_inventory_and_resource_totals_are_owner_only(self):
        for name in ("Inventory","Wood","Stone","Echo","Berries"):
            self.assertIn(f"DOREPLIFETIME_CONDITION(ANyCharacter,{name},COND_OwnerOnly)",self.char)
            self.assertNotIn(f"DOREPLIFETIME(ANyCharacter,{name})",self.char)
        for name in ("Health","Hunger","Thirst","Stamina"):
            self.assertIn(f"DOREPLIFETIME(ANyCharacter,{name})",self.char)

    def test_death_checkpoint_after_death_state_before_respawn(self):
        death=self.char.split("void ANyCharacter::ReceiveCombatDamage(")[1].split(
            "void ANyCharacter::RespawnAfterDeath()")[0]
        self.assertLess(death.index("bIsDead=true"),death.index("GM->CheckpointPlayerDeath(this)"))
        self.assertIn("void CheckpointPlayerDeath(ANyCharacter* Player)",self.modeh)
        body=self.mode.split("void ANyGameMode::CheckpointPlayerDeath(")[1].split(
            "void ANyGameMode::RequestPlayerSave(")[0]
        self.assertIn("!Player->bIsDead",body)
        self.assertIn("SavePlayerState(Player)",body)
        self.assertIn("if(!bIsDead){",self.char.split("CapturePersistentState(")[1].split(
            "bool ANyCharacter::ApplyPersistentState(")[0])
        self.assertIn("Save->Inventory.Reset()",self.char)

    def test_actions_bound_and_guarded_client_side(self):
        for action,key in (("CraftBandage","Six"),("UseBandage","H")):
            self.assertIn(f'ActionMappings=(ActionName="{action}",Key={key})',self.ini)
            self.assertIn(f'BindAction(TEXT("{action}")',self.char)
            self.assertIn(f"void {action}();",self.header)
        self.assertIn("if(!bIsDead&&!bInventoryOpen)ServerCraftBandage()",self.char)
        self.assertIn("if(!bIsDead&&!bInventoryOpen)ServerUseBandage()",self.char)
        self.assertIn("UFUNCTION(Server,Reliable) void ServerCraftBandage()",self.header)
        self.assertIn("UFUNCTION(Server,Reliable) void ServerUseBandage()",self.header)

    def test_hud_exposes_recipe_and_healing_usage(self):
        for token in ("6 BANDAGE", "H HEAL", "BANDAGES %d",
                      "CountItem(ENyItemId::Bandage)",
                      "BANDAGE: 2 BERRIES + 1 WATER", "[H] USE +35 HP"):
            self.assertIn(token,self.hud)

    def test_player_save_remains_two_slots_with_readback(self):
        self.assertIn('const FString SlotB=SlotA+TEXT("_B")',self.mode)
        self.assertIn("SaveGameToSlot(Save,Target,0)",self.mode)
        self.assertIn("LoadGameFromSlot(Target,0)",self.mode)
        self.assertIn("ProtectedPlayerSlots.Add(SlotA)",self.mode)
        self.assertIn("NyAllowAuthenticatedPlayerSaves",self.mode)


if __name__=="__main__":
    unittest.main(verbosity=2)
