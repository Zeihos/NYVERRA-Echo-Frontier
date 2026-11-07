"""Run in Unreal Editor with Python Editor Script Plugin enabled.
Creates a new material; leaves previous version untouched.
After running, assign /Game/NYVERRA/Materials/M_NyLandscape_Surface026 to Landscape.
"""
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'Content'/'TerrainSource'/'Textures'
E=unreal.EditorAssetLibrary
A=unreal.AssetToolsHelpers.get_asset_tools()
M=unreal.MaterialEditingLibrary
TD='/Game/NYVERRA/Textures'
MD='/Game/NYVERRA/Materials'
NAME='M_NyLandscape_Surface026'

def texture(name):
    dest=TD+'/'+name
    if E.does_asset_exist(dest):
        return E.load_asset(dest)
    task=unreal.AssetImportTask()
    for key,value in [('filename',str(SRC/(name+'.png'))),('destination_path',TD),('automated',True),('save',True),('replace_existing',False)]:
        task.set_editor_property(key,value)
    A.import_asset_tasks([task])
    t=E.load_asset(dest)
    if not t: raise RuntimeError('Failed to import '+name)
    if name.endswith('_Normal'):
        t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property('srgb',False)
        E.save_loaded_asset(t)
    if name.endswith('_Roughness'):
        t.set_editor_property('srgb',False)
        E.save_loaded_asset(t)
    return t

def main():
    for p in [TD,MD]:
        if not E.does_directory_exist(p): E.make_directory(p)
    textures={(kind,channel):texture('T_Ny'+kind+'_'+channel) for kind in ('Soil','Grass','Rock') for channel in ('Albedo','Normal','Roughness')}
    path=MD+'/'+NAME
    if E.does_asset_exist(path):
        unreal.log_warning('NYVERRA: material exists, will not overwrite '+path)
        return
    mat=A.create_asset(NAME,MD,unreal.Material,unreal.MaterialFactoryNew())
    # TextureCoordinate scaling: 1 UV per 4 metres at Landscape XY scale 100 cm.
    # This is an artistic starting point; adjust UV scale for your Landscape section dimensions.
    texcoord=M.create_material_expression(mat,unreal.MaterialExpressionTextureCoordinate,-1150,-450)
    texcoord.set_editor_property('u_tiling',0.25)
    texcoord.set_editor_property('v_tiling',0.25)
    for chan,prop in [('Albedo',unreal.MaterialProperty.MP_BASE_COLOR),('Normal',unreal.MaterialProperty.MP_NORMAL),('Roughness',unreal.MaterialProperty.MP_ROUGHNESS)]:
        samples={}
        for i,kind in enumerate(('Soil','Grass','Rock')):
            sample=M.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-900,i*320+({'Albedo':-100,'Normal':900,'Roughness':1850}[chan]))
            sample.set_editor_property('texture',textures[(kind,chan)])
            M.connect_material_expressions(texcoord,'',sample,'Coordinates')
            samples[kind]=sample
        previous=samples['Soil']
        for i,kind in enumerate(('Grass','Rock')):
            layer=M.create_material_expression(mat,unreal.MaterialExpressionLandscapeLayerWeight,-480+i*230,i*210+({'Albedo':0,'Normal':1000,'Roughness':1950}[chan]))
            layer.set_editor_property('parameter_name',kind)
            layer.set_editor_property('preview_weight',0.)
            M.connect_material_expressions(previous,'RGB' if i==0 and chan!='Roughness' else ('R' if i==0 else ''),layer,'Base')
            M.connect_material_expressions(samples[kind],'R' if chan=='Roughness' else 'RGB',layer,'Layer')
            previous=layer
        M.connect_material_property(previous,'',prop)
    M.recompile_material(mat)
    E.save_loaded_asset(mat)
    unreal.log('NYVERRA: surface material created '+path)

main()
