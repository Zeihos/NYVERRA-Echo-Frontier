"""Run inside Unreal Editor with the intended NYVERRA map open.
Read-only, does not modify the project or scene.
"""
import unreal

actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_api.get_all_level_actors()
labels = [a.get_actor_label() for a in actors]

def matches(class_name):
    return [a for a in actors if a.get_class().get_name() == class_name or a.get_class().get_name().endswith(class_name)]

starts = matches('PlayerStart')
nav = matches('NavMeshBoundsVolume')
landscape = [a for a in actors if 'Landscape' in a.get_class().get_name()]
collidable_ground = [a for a in actors if a.get_actor_label().startswith('NY_PersistentGround')]

unreal.log('[NYVERRA 0.34] Map audit: %d actors, %d PlayerStarts, %d nav volumes, %d landscapes, %d fallback grounds' % (len(actors), len(starts), len(nav), len(landscape), len(collidable_ground)))
if not starts:
    unreal.log_error('[NYVERRA 0.34] No PlayerStart; players may spawn at an undesired transform')
if not nav:
    unreal.log_warning('[NYVERRA 0.34] No NavMeshBoundsVolume; PvE pathfinding will not work')
if not landscape and not collidable_ground:
    unreal.log_error('[NYVERRA 0.34] No Landscape or NY_PersistentGround in current level')
if len(starts) != len(set((round(s.get_actor_location().x), round(s.get_actor_location().y), round(s.get_actor_location().z)) for s in starts)):
    unreal.log_warning('[NYVERRA 0.34] Some PlayerStarts share the same position')
if landscape and collidable_ground:
    unreal.log_warning('[NYVERRA 0.34] Landscape and test ground both exist. Check overlapping collision')
unreal.log('[NYVERRA 0.34] Audit finished; green NavMesh coverage must still be visually verified using P and runtime tested')
