#!/usr/bin/env python3
"""Offline smoke tests; does not claim Unreal compilation."""
from pathlib import Path
import json, zipfile, sys, re
root=Path(__file__).resolve().parents[1]
checks={}
def check(label, condition):
 checks[label]=bool(condition)
cpp=(root/'Source/NYVERRA/Private/NyGameMode.cpp').read_text(encoding='utf-8')
world=(root/'Source/NYVERRA/Private/NyWorldState.cpp').read_text(encoding='utf-8')
check('project_descriptor', (root/'NYVERRA.uproject').is_file())
check('unreal_module', (root/'Source/NYVERRA/NYVERRA.Build.cs').is_file())
check('ground_site_filter', 'ActorHasTag(TEXT("NYVERRA_SiteGeometry"))' in cpp and 'Query.AddIgnoredActor(Obstacle)' in cpp)
check('site_actor_tagging', 'Tags.AddUnique(TEXT("NYVERRA_SiteGeometry"))' in world)
check('ground_fallback_warning', '[NYVERRA 0.42]' in cpp)
check('cpp_braces', all((p.read_text(encoding='utf-8').count('{') == p.read_text(encoding='utf-8').count('}')) for p in (root/'Source/NYVERRA').rglob('*.cpp')))
check('landscape_heightmap', (root/'Content/TerrainSource/NyverraTestLandscape_505x505_R16.png').is_file())
check('project_source_files', len(list((root/'Source/NYVERRA').rglob('*.cpp')))>=8)
for key,passed in checks.items(): print(('PASS' if passed else 'FAIL'),key)
print('INFO: Unreal C++ compilation, editor scripts and multiplayer have NOT been tested.')
sys.exit(0 if all(checks.values()) else 1)
