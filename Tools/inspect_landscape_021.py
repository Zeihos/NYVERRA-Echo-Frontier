# Run inside Unreal Editor via Tools > Execute Python Script. Read-only diagnostics.
import unreal
actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actor_system.get_all_level_actors()
starts = [a for a in actors if isinstance(a, unreal.PlayerStart)]
navs = [a for a in actors if isinstance(a, unreal.NavMeshBoundsVolume)]
landscapes = [a for a in actors if "Landscape" in a.get_class().get_name() and "Gizmo" not in a.get_class().get_name()]
static_floors = [a for a in actors if isinstance(a, unreal.StaticMeshActor) and a.get_actor_label().startswith("NY_PersistentGround")]
unreal.log("[NYVERRA 0.21] Landscape actors={} | PlayerStarts={} | NavMeshBounds={} | old floors={}".format(
    len(landscapes), len(starts), len(navs), len(static_floors)))
if not landscapes:
    unreal.log_warning("[NYVERRA] No Landscape found. Import the 505x505 R16 file and SAVE the level.")
if not starts:
    unreal.log_warning("[NYVERRA] Add at least one PlayerStart above terrain.")
if not navs:
    unreal.log_warning("[NYVERRA] Add NavMeshBoundsVolume, cover the terrain and Build Paths.")
if landscapes and static_floors:
    unreal.log_warning("[NYVERRA] Old flat ground overlaps Landscape: inspect/remove obsolete ground.")
unreal.log("[NYVERRA] Static inspection only. Verify PIE and dedicated server independently.")
