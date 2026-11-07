# Execute from Unreal Editor: Tools -> Execute Python Script.
# Non-destructive read-only map readiness report.
import unreal
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
navs = [a for a in actors if isinstance(a, unreal.NavMeshBoundsVolume)]
floors = [a for a in actors if isinstance(a, unreal.StaticMeshActor) and a.get_actor_label().startswith("NY_PersistentGround")]
unreal.log("[NYVERRA 0.18] Map: {}".format(world.get_name() if world else "NONE"))
unreal.log("[NYVERRA 0.18] PlayerStarts: {}, NavBounds: {}, PersistentGround: {}".format(len(starts),len(navs),len(floors)))
if not starts or not navs or not floors:
    unreal.log_warning("[NYVERRA] Missing mandatory map components; run create_test_world.py in a NEW map, or add manually.")
else:
    unreal.log("[NYVERRA] Mandatory actors present. Still verify Build Paths, movement, and AI in PIE.")
