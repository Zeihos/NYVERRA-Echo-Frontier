"""Alpha 0.64: reject invalid loot rewards before inventory/save pollution.

Source invariants only: no Unreal C++ compilation is performed.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LootValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        actor=(ROOT/"Source/NYVERRA/Private/NyCharacter.cpp").read_text(encoding="utf-8")
        crate=(ROOT/"Source/NYVERRA/Private/NyLootCrate.cpp").read_text(encoding="utf-8")
        cls.add=actor.split("bool ANyCharacter::AddItem(")[1].split(
            "bool ANyCharacter::SpendItems(")[0]
        cls.configure=crate.split("void ANyLootCrate::Configure(")[1].split(
            "bool ANyLootCrate::TryLoot(")[0]

    def test_inventory_does_not_accept_future_or_invalid_ids(self):
        self.assertIn("!HasAuthority()",self.add)
        self.assertIn("Quantity<=0",self.add)
        self.assertIn("static_cast<uint8>(Item)>static_cast<uint8>(ENyItemId::Bandage)",self.add)
        self.assertLess(self.add.index("static_cast<uint8>(Item)>"),
                        self.add.index("Inventory.Add(Stack)"))

    def test_crate_reward_configuration_rejects_invalid_values(self):
        for token in ("!HasAuthority()", "static_cast<uint8>(Item)>static_cast<uint8>(ENyItemId::Bandage)",
                      "Count<=0", "!FMath::IsFinite(Seconds)"):
            self.assertIn(token,self.configure)
        self.assertLess(self.configure.index("Count<=0"),self.configure.index("RewardItem=Item"))

    def test_valid_crate_amount_is_still_limited(self):
        self.assertIn("RewardCount=FMath::Clamp(Count,1,100)",self.configure)
        self.assertIn("RespawnSeconds=FMath::Max(10.f,Seconds)",self.configure)


if __name__ == "__main__":
    unittest.main()
