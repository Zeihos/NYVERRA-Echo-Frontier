"""Create a minimal persistent map in Unreal Editor (Tools > Execute Python Script).
Run only after a successful C++ module compile. Does not overwrite an existing map.
"""
import unreal

MAP_PATH = '/Game/Maps/TestWorld'
editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assets = unreal.EditorAssetLibrary
if assets.does_asset_exist(MAP_PATH):
    raise RuntimeError('TestWorld exists: open it instead of overwriting it.')
if not editor.new_level(MAP_PATH):
    raise RuntimeError('Could not create ' + MAP_PATH)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mesh = unreal.load_asset('/Engine/BasicShapes/Cube')
if mesh is None:
    raise RuntimeError('Missing Engine cube mesh')

def actor(cls, loc, label):
    a = actors.spawn_actor_from_class(cls, unreal.Vector(*loc))
    if a is None:
        raise RuntimeError('Failed to spawn ' + label)
    a.set_actor_label(label)
    return a

floor = actor(unreal.StaticMeshActor, (0, 0, -115), 'NY_PersistentGround_NavCollision')
floor.static_mesh_component.set_editor_property('static_mesh', mesh)
floor.static_mesh_component.set_collision_profile_name('BlockAll')
floor.set_actor_scale3d(unreal.Vector(85, 85, 2))
nav = actor(unreal.NavMeshBoundsVolume, (0, 0, 150), 'NY_NavMeshBounds')
nav.set_actor_scale3d(unreal.Vector(100, 100, 6))
for i, point in enumerate(((0, 0, 200), (220, 0, 200), (-220, 0, 200), (0, 220, 200))):
    actor(unreal.PlayerStart, point, 'NY_PlayerStart_%02d' % (i+1))
if not editor.save_current_level():
    raise RuntimeError('Map was created but could not be saved.')
unreal.log('NYVERRA: TestWorld created. Build navigation paths, inspect P overlay, save again.')
unreal.log('Then run the Windows script Tools/set_test_world_default.py outside Unreal Editor.')
