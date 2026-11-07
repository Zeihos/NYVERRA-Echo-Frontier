"""NYVERRA 0.22: prepare the CURRENT OPEN Landscape map for first playable test.
Run via Unreal Editor > Tools > Execute Python Script AFTER importing heightmap.
Adds only missing test infrastructure, without changing Landscape or existing actors.
SAVE the level manually after reviewing. Undo is available in editor.
"""
import unreal

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = actors_api.get_all_level_actors()
landscapes = [a for a in all_actors if a.get_class().get_name().startswith('Landscape') and 'Gizmo' not in a.get_class().get_name()]
if not landscapes:
    raise RuntimeError('No Landscape in currently open map. Import R16 heightmap and save a new level first.')

def existing(actor_class):
    return [a for a in all_actors if isinstance(a, actor_class)]

def spawn(actor_class, name, position):
    actor = actors_api.spawn_actor_from_class(actor_class, unreal.Vector(*position))
    if actor is None:
        raise RuntimeError('Could not spawn '+name)
    actor.set_actor_label(name)
    unreal.log('[NYVERRA 0.22] Added '+name)
    return actor

# Large enough to cover the 100m test map (+ border); adjust manually to fit terrain.
if not existing(unreal.NavMeshBoundsVolume):
    nav = spawn(unreal.NavMeshBoundsVolume, 'NY_NavMeshBounds_Landscape', (0, 0, 1000))
    nav.set_actor_scale3d(unreal.Vector(110, 110, 35), False)

# Spawn points well separated from each other; the pawn spawn uses its own floor checks.
if not existing(unreal.PlayerStart):
    for i,(x,y) in enumerate([(0,0),(250,0),(-250,0),(0,250)]):
        spawn(unreal.PlayerStart, 'NY_PlayerStart_%02d'%(i+1), (x,y,350))

if not existing(unreal.DirectionalLight):
    sun=spawn(unreal.DirectionalLight,'NY_Sun',(0,0,2500))
    sun.set_actor_rotation(unreal.Rotator(-40,-35,0),False)
if not existing(unreal.SkyLight):
    spawn(unreal.SkyLight,'NY_Skylight',(0,0,2300))
if not existing(unreal.ExponentialHeightFog):
    spawn(unreal.ExponentialHeightFog,'NY_AtmosphericFog',(0,0,100))

unreal.log_warning('[NYVERRA 0.22] REVIEW: PlayerStart heights, NavMesh volume coverage and Landscape collision.')
unreal.log_warning('[NYVERRA 0.22] Then Build Paths, press P to view navmesh, SAVE map, set it as startup map.')
