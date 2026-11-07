"""Run in Unreal Editor Python console after 0.24 material is available.
Creates a NEW material rather than overwriting the legacy fallback.
Textures are imported into /Game/NYVERRA/Textures, not used at runtime as source PNG.
"""
import unreal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'Content'/'TerrainSource'/'Textures'
DEST='/Game/NYVERRA/Textures'
MAT_DIR='/Game/NYVERRA/Materials'
MAT_PATH=MAT_DIR+'/M_NyLandscape_Textured'
E=unreal.EditorAssetLibrary
A=unreal.AssetToolsHelpers.get_asset_tools()
M=unreal.MaterialEditingLibrary


def import_texture(name):
    path=DEST+'/'+name
    if E.does_asset_exist(path):
        return E.load_asset(path)
    task=unreal.AssetImportTask()
    task.set_editor_property('filename',str(SRC/(name+'.png')))
    task.set_editor_property('destination_path',DEST)
    task.set_editor_property('automated',True)
    task.set_editor_property('replace_existing',False)
    task.set_editor_property('save',True)
    A.import_asset_tasks([task])
    obj=E.load_asset(path)
    if obj is None: raise RuntimeError('Texture import failed: '+name)
    return obj


def main():
    for p in (DEST,MAT_DIR):
        if not E.does_directory_exist(p): E.make_directory(p)
    textures={key:import_texture('T_Ny'+key+'_Albedo') for key in ('Soil','Grass','Rock')}
    if E.does_asset_exist(MAT_PATH):
        unreal.log_warning('NYVERRA: existing textured material left unchanged: '+MAT_PATH)
        return
    mat=A.create_asset('M_NyLandscape_Textured',MAT_DIR,unreal.Material,unreal.MaterialFactoryNew())
    if not mat: raise RuntimeError('Unable to create landscape material')
    samples={}
    for i,key in enumerate(('Soil','Grass','Rock')):
        sample=M.create_material_expression(mat,unreal.MaterialExpressionTextureSampleParameter2D,-920,i*280-280)
        sample.set_editor_property('parameter_name',key+'Albedo')
        sample.set_editor_property('texture',textures[key])
        samples[key]=sample
    prev=samples['Soil']
    for key,x,y in (('Grass',-500,-20),('Rock',-220,140)):
        blend=M.create_material_expression(mat,unreal.MaterialExpressionLandscapeLayerWeight,x,y)
        blend.set_editor_property('parameter_name',key)
        blend.set_editor_property('preview_weight',0.0)
        M.connect_material_expressions(prev,'RGB',blend,'Base') if prev == samples['Soil'] else M.connect_material_expressions(prev,'',blend,'Base')
        M.connect_material_expressions(samples[key],'RGB',blend,'Layer')
        prev=blend
    M.connect_material_property(prev,'',unreal.MaterialProperty.MP_BASE_COLOR)
    rough=M.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-240,390)
    rough.set_editor_property('parameter_name','Roughness')
    rough.set_editor_property('default_value',0.87)
    M.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    M.recompile_material(mat)
    E.save_loaded_asset(mat)
    unreal.log('NYVERRA: Textured landscape material ready: '+MAT_PATH)
    unreal.log('Assign it to Landscape; keep existing Grass/Rock LayerInfo and 0.24 weightmaps')

main()
