"""PvE line-of-sight regression: dynamic cover must obstruct enemy acquisition/attacks.

Offline source invariant only. Validate in a real UE5.8 2-player build before release.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class EnemyCover(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "Source/NYVERRA/Private/NyEnemy.cpp").read_text(encoding="utf-8")

    def test_target_acquisition_respects_visibility_blockers(self):
        body = self.source.split("void ANyEnemy::Think()")[1].split(
            "float ANyEnemy::TakeDamage(")[0]
        self.assertIn("SCENE_QUERY_STAT(NyEnemySight)", body)
        self.assertIn("LineTraceSingleByChannel(Hit,Eye,TargetEye,ECC_Visibility,Params)", body)
        self.assertNotIn("ECC_WorldStatic", body)

    def test_enemy_attack_requires_clear_visibility(self):
        body = self.source.split("void ANyEnemy::Think()")[1].split(
            "float ANyEnemy::TakeDamage(")[0]
        self.assertIn("SCENE_QUERY_STAT(NyEnemyAttackSight)", body)
        self.assertIn(
            "Victim->GetActorLocation()+FVector(0,0,50.f),ECC_Visibility,Sight)",
            body)
        self.assertLess(body.index("ECC_Visibility,Sight)"),body.index("ReceiveCombatDamage(10.f,nullptr)"))

    def test_target_is_excluded_from_blocker_trace(self):
        self.assertIn("Params.AddIgnoredActor(Candidate)", self.source)
        self.assertIn("Sight.AddIgnoredActor(Victim)", self.source)


if __name__ == "__main__":
    unittest.main()
