"""Offline tests of the UE Editor bootstrap using a mock Unreal Python API.
These do not compile C++ or run Unreal Engine.
"""
from pathlib import Path
from types import ModuleType, SimpleNamespace
from tempfile import TemporaryDirectory
from unittest.mock import patch
import runpy
import shutil
import sys
import unittest

REAL_ROOT = Path(__file__).resolve().parents[1]


class FakeActor:
    def __init__(self):
        self.static_mesh_component = SimpleNamespace(
            set_editor_property=lambda *_args: None,
            set_collision_profile_name=lambda *_args: None,
        )

    def set_actor_label(self, label):
        self.label = label

    def set_actor_scale3d(self, scale):
        self.scale = scale


class MockUnreal(ModuleType):
    def __init__(self, root, existing=False, fail_new=False):
        super().__init__('unreal')
        self.root = Path(root)
        self.existing = existing
        self.fail_new = fail_new
        self.new_level_calls = 0
        self.save_calls = 0
        self.actors = []
        self.Paths = SimpleNamespace(project_dir=lambda: str(self.root))
        self.EditorAssetLibrary = SimpleNamespace(does_asset_exist=lambda path: self.existing)
        self.LevelEditorSubsystem = type('LevelEditorSubsystem', (), {})
        self.EditorActorSubsystem = type('EditorActorSubsystem', (), {})
        self.StaticMeshActor = type('StaticMeshActor', (), {})
        self.NavMeshBoundsVolume = type('NavMeshBoundsVolume', (), {})
        self.PlayerStart = type('PlayerStart', (), {})
        self.Vector = lambda *args: args
        self.load_asset = lambda path: object()
        self.log = lambda message: None
        self.log_warning = lambda message: None

    def get_editor_subsystem(self, kind):
        if kind is self.LevelEditorSubsystem:
            return SimpleNamespace(new_level=self.new_level, save_current_level=self.save_level)
        if kind is self.EditorActorSubsystem:
            return SimpleNamespace(spawn_actor_from_class=self.spawn_actor)
        raise AssertionError('Unexpected subsystem')

    def spawn_actor(self, cls, location):
        actor = FakeActor()
        self.actors.append(actor)
        return actor

    def new_level(self, asset_path):
        self.new_level_calls += 1
        if self.fail_new:
            return False
        path = self.root / 'Content' / 'Maps' / 'TestWorld.umap'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'MOCK MAP, NOT A REAL UE .umap')
        self.existing = True
        return True

    def save_level(self):
        self.save_calls += 1
        return True


class TestEditorBootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'NYVERRA.uproject').write_text('{}', encoding='utf-8')
        (self.root / 'Tools').mkdir()
        (self.root / 'Config').mkdir()
        for name in ('bootstrap_alpha_053.py', 'create_test_world.py', 'set_test_world_default.py'):
            shutil.copyfile(REAL_ROOT / 'Tools' / name, self.root / 'Tools' / name)
        shutil.copyfile(REAL_ROOT / 'Config' / 'DefaultEngine.ini', self.root / 'Config' / 'DefaultEngine.ini')

    def run_mock(self, mock):
        with patch.dict(sys.modules, {'unreal': mock}):
            runpy.run_path(str(self.root / 'Tools' / 'bootstrap_alpha_053.py'), run_name='__main__')

    def test_creates_level_and_sets_three_default_maps(self):
        u = MockUnreal(self.root)
        self.run_mock(u)
        self.assertEqual(u.new_level_calls, 1)
        self.assertEqual(u.save_calls, 1)
        self.assertEqual(len(u.actors), 6)  # Floor, NavMeshBounds, 4 PlayerStarts
        self.assertTrue((self.root / 'Content/Maps/TestWorld.umap').is_file())
        ini = (self.root / 'Config/DefaultEngine.ini').read_text()
        for key in ('GameDefaultMap', 'EditorStartupMap', 'ServerDefaultMap'):
            self.assertIn(f'{key}=/Game/Maps/TestWorld', ini)
        self.assertTrue((self.root / 'Config/DefaultEngine.ini.bak').exists())

    def test_rerun_does_not_overwrite_existing_map(self):
        map_file = self.root / 'Content/Maps/TestWorld.umap'
        map_file.parent.mkdir(parents=True)
        map_file.write_bytes(b'USER AUTHORED MAP MUST SURVIVE')
        u = MockUnreal(self.root, existing=True)
        self.run_mock(u)
        self.run_mock(u)
        self.assertEqual(u.new_level_calls, 0)
        self.assertEqual(u.save_calls, 0)
        self.assertEqual(map_file.read_bytes(), b'USER AUTHORED MAP MUST SURVIVE')

    def test_missing_map_aborts_before_any_ini_edits(self):
        path = self.root / 'Config/DefaultEngine.ini'
        original = path.read_bytes()
        u = MockUnreal(self.root, fail_new=True)
        with self.assertRaises(RuntimeError):
            self.run_mock(u)
        self.assertEqual(path.read_bytes(), original)

    def test_missing_ini_key_aborts_without_partial_rewrite(self):
        map_file = self.root / 'Content/Maps/TestWorld.umap'
        map_file.parent.mkdir(parents=True)
        map_file.write_bytes(b'EXISTING MAP')
        path = self.root / 'Config/DefaultEngine.ini'
        invalid = path.read_text().replace('ServerDefaultMap=/Engine/Maps/Entry\n', '')
        path.write_text(invalid)
        with self.assertRaises(SystemExit):
            self.run_mock(MockUnreal(self.root, existing=True))
        self.assertEqual(path.read_text(), invalid)

    def test_cpp_default_foundation_scale_and_static_ground(self):
        build = (REAL_ROOT / 'Source/NYVERRA/Private/NyBuildPiece.cpp').read_text()
        world = (REAL_ROOT / 'Source/NYVERRA/Private/NyWorldState.cpp').read_text()
        self.assertIn('SetActorScale3D(FVector(3.f,3.f,.3f));', build.split('ANyBuildPiece::Initialize')[0])
        ground = world.split('void ANyWorldState::CreateCollisionGround(){')[1].split('void ANyWorldState::CreateExplorationSites()')[0]
        self.assertIn('Mesh->SetMobility(EComponentMobility::Static);', ground)


if __name__ == '__main__':
    unittest.main(verbosity=2)
