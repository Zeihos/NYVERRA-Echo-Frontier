"""Alpha 0.57: create non-destructive prototype PBR material assets.

No PNG dependencies; this makes Water, Berries and EchoShard visually
distinguishable from neutral BasicShapes even before final 3D models arrive.
Only creates M_NyWater_Proto057, M_NyBerries_Proto057, M_NyEcho_Proto057
if missing. Run from Unreal Editor's Python plugin. No level changes.
"""
import unreal

DEST = "/Game/NYVERRA/VisualPolish/Materials"
E = unreal.EditorAssetLibrary
A = unreal.AssetToolsHelpers.get_asset_tools()
M = unreal.MaterialEditingLibrary

SURFACES = (
    ("Water", (0.025, 0.20, 0.62), 0.24, 0.025),
    ("Berries", (0.42, 0.035, 0.075), 0.55, 0.0),
    ("Echo", (0.005, 0.50, 0.66), 0.30, 0.62),
)


def create_surface(kind, rgb, roughness, emission):
    name = "M_Ny%s_Proto057" % kind
    path = DEST + "/" + name
    if E.does_asset_exist(path):
        unreal.log("[NYVERRA 057] Existing material preserved: " + path)
        return
    mat = A.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError("Could not create " + path)
    albedo = M.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -550, -160)
    albedo.set_editor_property("parameter_name", "Color")
    albedo.set_editor_property("default_value", unreal.LinearColor(*rgb, 1.0))
    M.connect_material_property(albedo, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough = M.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -520, 80)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", roughness)
    M.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

    glow_strength = M.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -520, 360)
    glow_strength.set_editor_property("parameter_name", "Glow")
    glow_strength.set_editor_property("default_value", emission)
    glow = M.create_material_expression(mat, unreal.MaterialExpressionMultiply, -120, 270)
    M.connect_material_expressions(albedo, "", glow, "A")
    M.connect_material_expressions(glow_strength, "", glow, "B")
    M.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat)
    if not E.save_loaded_asset(mat):
        raise RuntimeError("Material created but not saved: " + path)
    unreal.log("[NYVERRA 057] New resource material created: " + path)


def main():
    if not E.does_directory_exist(DEST):
        E.make_directory(DEST)
    for name, color, roughness, emission in SURFACES:
        create_surface(name, color, roughness, emission)


if __name__ == "__main__":
    main()
