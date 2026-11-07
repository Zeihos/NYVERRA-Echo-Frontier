"""NYVERRA 0.28 – editor-only placement of temporary foliage proxies.
Run in a SAVED Landscape level via Tools > Execute Python Script.
Uses CSV from 0.27 and basic ENGINE meshes: no external paid asset dependency.
This DOES NOT create a realistic forest and is not a runtime foliage system.
"""
import csv
import os
import unreal

# Set MAX_ACTORS=540 to place every CSV entry. Default is deliberately smaller for editor performance.
MAX_ACTORS = 120
# Heightmap Z positions are relative to imported landscape; adjust to match your Landscape transform.
HEIGHT_OFFSET_CM = 0.0
# Exact CSV is in Content/TerrainSource/Foliage027, not an Unreal .uasset.
PROJECT_DIR = unreal.Paths.project_dir()
CSV_PATH = os.path.join(PROJECT_DIR, 'Content', 'TerrainSource', 'Foliage027', 'FoliagePlacements.csv')
LABEL_PREFIX = 'NY28_PROXY_'
MESH_PATHS = {
    'Tree': '/Engine/BasicShapes/Cone.Cone',
    'Rock': '/Engine/BasicShapes/Sphere.Sphere',
    'Shrub': '/Engine/BasicShapes/Sphere.Sphere',
}
# Source heightmap elevation and mesh height may need adjustment in editor.
MESH_SCALES = {'Tree': (1.0, 1.0, 3.4), 'Rock': (0.9, 0.7, 0.45), 'Shrub': (0.55, 0.55, 0.32)}

def main():
    if not os.path.isfile(CSV_PATH):
        raise RuntimeError('Foliage placement CSV is missing: ' + CSV_PATH)
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = subsystem.get_all_level_actors()
    if not any('Landscape' in a.get_class().get_name() and 'Gizmo' not in a.get_class().get_name() for a in existing):
        raise RuntimeError('Import the heightmap into this map before running the foliage script.')
    if any(a.get_actor_label().startswith(LABEL_PREFIX) for a in existing):
        raise RuntimeError('Existing NY28 proxies detected. Delete them before rerunning to prevent duplicates.')
    meshes = {k: unreal.load_asset(v) for k,v in MESH_PATHS.items()}
    for k,v in meshes.items():
        if not v: raise RuntimeError('Engine test mesh not found for '+k)
    created = 0
    counts = {'Tree':0,'Rock':0,'Shrub':0}
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as fp:
        reader = csv.DictReader(fp)
        required = {'Kind','X_cm','Y_cm','Z_cm','Yaw_deg','UniformScale'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError('Unexpected CSV headers: '+str(reader.fieldnames))
        for row in reader:
            if created >= MAX_ACTORS: break
            kind = row['Kind']
            if kind not in meshes: continue
            x,y,z = (float(row[c]) for c in ('X_cm','Y_cm','Z_cm'))
            yaw = float(row['Yaw_deg'])
            uniform_scale = float(row['UniformScale'])
            actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x,y,z + HEIGHT_OFFSET_CM))
            if not actor: raise RuntimeError('Failed to spawn foliage proxy '+str(created))
            actor.set_actor_label('%s%s_%04d'%(LABEL_PREFIX,kind,created))
            component = actor.static_mesh_component
            component.set_static_mesh(meshes[kind])
            sx,sy,sz=MESH_SCALES[kind]
            actor.set_actor_scale3d(unreal.Vector(sx*uniform_scale,sy*uniform_scale,sz*uniform_scale))
            actor.set_actor_rotation(unreal.Rotator(0.0,yaw,0.0),False)
            # Decorative proxies should never obstruct player or AI movement.
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            counts[kind] += 1
            created += 1
    unreal.log('[NYVERRA 0.28] Placed %d foliage proxies: %s'%(created,counts))
    unreal.log_warning('Save this LEVEL manually. Verify mesh altitude, materials, framerate and NavMesh in UE Editor.')
    unreal.log_warning('Proxies are placeholders only. Replace with foliage instancing / real assets for production.')

main()
