"""PvE attack geometry regression: a player on a high platform is not in melee reach.

Source invariant checks only; collision, navigation and damage still need UE5.8 tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EnemyMeleeRange(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cpp = (ROOT / "Source/NYVERRA/Private/NyEnemy.cpp").read_text(encoding="utf-8")
        cls.think = cpp.split("void ANyEnemy::Think()")[1].split(
            "float ANyEnemy::TakeDamage(")[0]

    def test_melee_uses_3d_distance_not_horizontal_distance(self):
        code = self.think
        self.assertIn("const FVector Delta=Victim->GetActorLocation()-GetActorLocation()", code)
        self.assertIn("const float Distance=Delta.Size();", code)
        self.assertNotIn("const float Distance=Delta.Size2D();", code)
        self.assertIn("if(Distance>AttackRadius){MoveToward(Victim->GetActorLocation());return;}", code)

    def test_range_gate_runs_before_line_of_sight_and_damage(self):
        code = self.think
        self.assertLess(code.index("if(Distance>AttackRadius)"),
                        code.index("SCENE_QUERY_STAT(NyEnemyAttackSight)"))
        self.assertLess(code.index("SCENE_QUERY_STAT(NyEnemyAttackSight)"),
                        code.index("Victim->ReceiveCombatDamage(10.f,nullptr)"))

    def test_open_line_of_sight_still_required(self):
        self.assertIn("ECC_Visibility,Sight)", self.think)
        self.assertIn("Sight.AddIgnoredActor(Victim)", self.think)


if __name__ == "__main__":
    unittest.main()
