"""Execute inside Unreal Editor, AFTER the project compiles.
Creates a 3-layer Landscape material with named paint layers: Soil, Grass, Rock.
It does not edit level actors, landscapes or the imported weightmaps.
"""
import unreal

ROOT = '/Game/NYVERRA/Materials'
ASSET = ROOT + '/M_NyLandscape'
editor = unreal.EditorAssetLibrary
assets = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def make_color(mat, name, color, x, y):
    node = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
    node.set_editor_property('parameter_name', name)
    node.set_editor_property('default_value', unreal.LinearColor(*color, 1.0))
    return node


def weight_blend(mat, layer_name, previous, layer_color, x, y):
    layer = mel.create_material_expression(mat, unreal.MaterialExpressionLandscapeLayerWeight, x, y)
    layer.set_editor_property('parameter_name', layer_name)
    layer.set_editor_property('preview_weight', 0.0)
    mel.connect_material_expressions(previous, '', layer, 'Base')
    mel.connect_material_expressions(layer_color, '', layer, 'Layer')
    return layer


def main():
    if editor.does_asset_exist(ASSET):
        unreal.log_warning('NYVERRA 0.24: material already exists, unchanged: ' + ASSET)
        return
    if not editor.does_directory_exist(ROOT):
        editor.make_directory(ROOT)
    mat = assets.create_asset('M_NyLandscape', ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError('Could not create M_NyLandscape')
    soil = make_color(mat, 'SoilColor', (0.21, 0.15, 0.105), -900, -300)
    grass = make_color(mat, 'GrassColor', (0.10, 0.19, 0.09), -900, -60)
    rock = make_color(mat, 'RockColor', (0.24, 0.26, 0.27), -900, 200)
    # Soil is the fallback color; the Grass and Rock weightmaps layer on top.
    w_grass = weight_blend(mat, 'Grass', soil, grass, -450, -100)
    w_rock = weight_blend(mat, 'Rock', w_grass, rock, -150, 0)
    mel.connect_material_property(w_rock, '', unreal.MaterialProperty.MP_BASE_COLOR)
    roughness = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 320)
    roughness.set_editor_property('parameter_name', 'Roughness')
    roughness.set_editor_property('default_value', 0.91)
    mel.connect_material_property(roughness, '', unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    editor.save_loaded_asset(mat)
    unreal.log('NYVERRA: created ' + ASSET + '; assign to Landscape, create weight-blended Layer Infos and import Grass/Rock maps')


main()
