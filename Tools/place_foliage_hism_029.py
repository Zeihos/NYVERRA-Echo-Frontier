"""NYVERRA 0.29 - place 540 decorative instances into three HISM components.

Requires a COMPILED NYVERRA C++ module and a saved map with an imported Landscape.
Run via Tools > Execute Python Script in the Unreal Editor (not normal Python).
No automatic deletion: rerunning refuses when the tagged cluster already exists.
The CSV Z assumes the Landscape import settings used to generate the data;
verify that the instances sit on the ground BEFORE saving the level.
"""
import csv
import os
import math
import unreal

PREFIX = 'NY29_FOLIAGE_HISM'
CSV_PATH = os.path.join(unreal.Paths.project_dir(), 'Content', 'TerrainSource', 'Foliage027', 'FoliagePlacements.csv')
MESH_SCALE = {'Tree': (1.0, 1.0, 3.4), 'Rock': (.9, .7, .45), 'Shrub': (.55, .55, .32)}
EXPECTED_COUNTS = {'Tree': 240, 'Rock': 110, 'Shrub': 190}
HEIGHT_OFFSET_CM = 0.0


def main():
    if not os.path.isfile(CSV_PATH):
        raise RuntimeError('Missing placement CSV: ' + CSV_PATH)
    editor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = editor.get_all_level_actors()
    if not any('Landscape' in a.get_class().get_name() and 'Gizmo' not in a.get_class().get_name() for a in actors):
        raise RuntimeError('Import and save the Landscape before placing foliage.')
    if any(a.get_actor_label().startswith(PREFIX) for a in actors):
        raise RuntimeError('NY29 foliage cluster already exists; aborting to prevent duplicates.')

    rows = []
    counts = {key: 0 for key in EXPECTED_COUNTS}
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        required = {'Kind', 'X_cm', 'Y_cm', 'Z_cm', 'Yaw_deg', 'UniformScale'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError('Invalid CSV headers')
        for row in reader:
            kind = row['Kind']
            if kind not in counts:
                raise RuntimeError('Unexpected foliage type: ' + kind)
            values = [float(row[key]) for key in ('X_cm', 'Y_cm', 'Z_cm', 'Yaw_deg', 'UniformScale')]
            if not all(math.isfinite(v) for v in values) or values[-1] <= 0:
                raise RuntimeError('Invalid transform in CSV')
            rows.append((kind, values))
            counts[kind] += 1
    if counts != EXPECTED_COUNTS:
        raise RuntimeError('Unexpected placement counts: ' + repr(counts))

    actor_class = unreal.load_class(None, '/Script/NYVERRA.NyFoliageCluster')
    if actor_class is None:
        raise RuntimeError('Compile the NYVERRA C++ module before running this script.')
    cluster = editor.spawn_actor_from_class(actor_class, unreal.Vector(0, 0, 0))
    if cluster is None:
        raise RuntimeError('Failed to spawn foliage cluster')
    cluster.set_actor_label(PREFIX)
    try:
        for kind, (x, y, z, yaw, factor) in rows:
            sx, sy, sz = MESH_SCALE[kind]
            transform = unreal.Transform(
                location=unreal.Vector(x, y, z + HEIGHT_OFFSET_CM),
                rotation=unreal.Rotator(0.0, yaw, 0.0),
                scale=unreal.Vector(sx * factor, sy * factor, sz * factor),
            )
            if not cluster.add_foliage_instance(kind, transform):
                raise RuntimeError('Failed to add instance of ' + kind)
    except Exception:
        editor.destroy_actor(cluster)
        raise
    unreal.log('[NYVERRA 0.29] HISM placement: ' + str(counts))
    unreal.log_warning('Check mesh Z, Landscape alignment and appearance. Save the map manually.')
    unreal.log_warning('HISM is decorative only: resources still use server-authoritative replicated actors.')


main()
