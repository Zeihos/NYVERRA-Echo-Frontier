"""Apply NYVERRA PBR056 materials only to recognized test/landscape surfaces.

Run INSIDE the Unreal Editor AFTER import_visual_polish_056.py.
Preserves non-NYVERRA custom Landscape materials and DOES NOT auto-save the map.
Undo or close the map without saving to discard placement changes.
"""
import unreal

MD = "/Game/NYVERRA/VisualPolish/Materials"
E = unreal.EditorAssetLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def load(name):
    path = MD + "/" + name
    asset = E.load_asset(path)
    if asset is None:
        raise RuntimeError("Missing imported PBR material: " + path)
    return asset


def main():
    landscape = load("M_NyLandscape_PBR056")
    grass = load("M_NyGrass_PBR056")
    rock = load("M_NyRock_PBR056")
    soil = load("M_NySoil_PBR056")
    changed = 0
    for actor in ACTORS.get_all_level_actors():
        label = actor.get_actor_label()
        name = actor.get_class().get_name()
        if name.startswith("Landscape") and "Gizmo" not in name:
            old = actor.get_editor_property("landscape_material")
            old_path = old.get_path_name() if old else ""
            if old_path and "/NYVERRA/Materials/" not in old_path \
                    and "/NYVERRA/VisualPolish/" not in old_path:
                unreal.log_warning("[NYVERRA VISUAL] Custom landscape preserved: " + label)
                continue
            if old_path == landscape.get_path_name():
                continue
            actor.set_editor_property("landscape_material", landscape)
            changed += 1
            unreal.log("[NYVERRA VISUAL] New landscape material: " + label)
        elif isinstance(actor, unreal.StaticMeshActor):
            if label == "NY_PersistentGround_NavCollision":
                comp = actor.static_mesh_component
                comp.set_material(0, grass)
                changed += 1
            elif label.startswith("NY_Visual_Rock"):
                actor.static_mesh_component.set_material(0, rock)
                changed += 1
            elif label.startswith("NY_Visual_Soil"):
                actor.static_mesh_component.set_material(0, soil)
                changed += 1
    unreal.log_warning(
        "[NYVERRA VISUAL] %d actors modified in CURRENT LEVEL (not saved). "
        "Check texture scale and colors in viewport; press Ctrl+S only when satisfied."
        % changed
    )


if __name__ == "__main__":
    main()
