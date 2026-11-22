"""Source invariants for shared server-authoritative craft throttling."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CraftCooldown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(ROOT/"Source/NYVERRA/Private/NyCharacter.cpp").read_text(encoding="utf-8")
        cls.header=(ROOT/"Source/NYVERRA/Public/NyCharacter.h").read_text(encoding="utf-8")
        cls.tools=source.split("void ANyCharacter::ServerCraft_Implementation(")[1].split(
            "void ANyCharacter::ServerEatBerries_Implementation(")[0]
        cls.bandage=source.split("void ANyCharacter::ServerCraftBandage_Implementation(")[1].split(
            "void ANyCharacter::ServerUseBandage_Implementation(")[0]

    def test_cooldown_is_server_owned_and_shared(self):
        self.assertIn("float LastCraftTime=-100.f;",self.header)
        for body in (self.tools,self.bandage):
            self.assertIn("!HasAuthority()",body)
            self.assertIn("GetWorld()->GetTimeSeconds()",body)
            self.assertIn("CraftNow-LastCraftTime<0.25f",body)
            self.assertIn("LastCraftTime=CraftNow",body)

    def test_ingredients_and_item_ids_unchanged(self):
        self.assertIn("const int32 WoodCost=RecipeId==0?3:2",self.tools)
        self.assertIn("const int32 StoneCost=RecipeId==0?2:4",self.tools)
        self.assertIn("PreviewRemove(ENyItemId::Berries,2)",self.bandage)
        self.assertIn("PreviewRemove(ENyItemId::Water,1)",self.bandage)

    def test_cooldown_applies_after_successful_reward_only(self):
        for body,reward in ((self.tools,"if (!AddItem(Result, 1))"),
                            (self.bandage,"if(!AddItem(ENyItemId::Bandage,1))")):
            self.assertLess(body.index(reward),body.index("LastCraftTime=CraftNow"))
            failure=body[body.index(reward):body.index("LastCraftTime=CraftNow")]
            self.assertIn("return;",failure)


if __name__=="__main__":
    unittest.main()
