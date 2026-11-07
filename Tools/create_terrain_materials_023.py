"""Run inside Unreal Editor: Tools > Execute Python Script.
Creates simple material assets; no external dependencies, no modifications to existing level.
"""
import unreal

ROOT = '/Game/NYVERRA/Materials'
ASSETS = unreal.AssetToolsHelpers.get_asset_tools()
EDITOR = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary


def make_material(name, rgb, roughness):
    path = ROOT + '/' + name
    if EDITOR.does_asset_exist(path):
        unreal.log_warning('NYVERRA: existing material preserved: ' + path)
        return EDITOR.load_asset(path)
    material = ASSETS.create_asset(name, ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if not material:
        raise RuntimeError('Failed to create: ' + path)
    base = MEL.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -350, -50)
    base.set_editor_property('parameter_name', 'SurfaceColor')
    base.set_editor_property('default_value', unreal.LinearColor(*rgb, 1.0))
    MEL.connect_material_property(base, '', unreal.MaterialProperty.MP_BASE_COLOR)
    r = MEL.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -350, 130)
    r.set_editor_property('parameter_name', 'SurfaceRoughness')
    r.set_editor_property('default_value', roughness)
    MEL.connect_material_property(r, '', unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(material)
    EDITOR.save_loaded_asset(material)
    unreal.log('NYVERRA: created ' + path)
    return material


def main():
    if not EDITOR.does_directory_exist(ROOT):
        EDITOR.make_directory(ROOT)
    make_material('M_NySoil', (0.18, 0.14, 0.10), 0.93)
    make_material('M_NyRock', (0.23, 0.25, 0.26), 0.87)
    make_material('M_NyGrass', (0.105, 0.19, 0.085), 0.92)
    unreal.log('NYVERRA 0.23: 3 basic material assets ready. Assign in editor manually.')

main()
