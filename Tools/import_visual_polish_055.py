"""NYVERRA visual pass 0.55 — import 3 coherent PBR terrain sets into UE 5.8.

Run INSIDE Unreal Editor (Tools > Execute Python Script), after placing the
Content/VisualPolishSource/Terrain PNG files in this checkout.

Creates only new /Game/NYVERRA/VisualPolish assets. Does NOT overwrite old
materials or alter an authored map. Safe to rerun. No third-party Python deps.
"""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / "Content" / "VisualPolishSource" / "Terrain"
DEST_TEX = "/Game/NYVERRA/VisualPolish/Textures"
DEST_MAT = "/Game/NYVERRA/VisualPolish/Materials"
VERSION = "055"
TYPES = ("Soil", "Grass", "Rock")
CHANNELS = ("Albedo", "Normal", "Roughness")
EDITOR = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary


def require_sources():
    missing = [
        str(SOURCE / ("T_Ny%s_%s.png" % (kind, channel)))
        for kind in TYPES for channel in CHANNELS
        if not (SOURCE / ("T_Ny%s_%s.png" % (kind, channel))).is_file()
    ]
    if missing:
        raise RuntimeError("Visual polish textures not installed. Missing:\n" + "\n".join(missing))


def import_texture(kind, channel):
    name = "T_Ny%s_%s" % (kind, channel)
    path = DEST_TEX + "/" + name
    if EDITOR.does_asset_exist(path):
        texture = EDITOR.load_asset(path)
        if not isinstance(texture, unreal.Texture2D):
            raise RuntimeError("Unexpected asset type at " + path)
        # Never overwrite an asset that may be customized by the artist.
        unreal.log("[NYVERRA VISUAL] Existing texture preserved: " + path)
        return texture
    task = unreal.AssetImportTask()
    for key, value in (
        ("filename", str(SOURCE / (name + ".png"))),
        ("destination_path", DEST_TEX),
        ("destination_name", name),
        ("automated", True),
        ("save", True),
        ("replace_existing", False),
    ):
        task.set_editor_property(key, value)
    TOOLS.import_asset_tasks([task])
    texture = EDITOR.load_asset(path)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError("Import failed: " + name)
    if channel == "Normal":
        texture.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_NORMALMAP)
        texture.set_editor_property("srgb", False)
    elif channel == "Roughness":
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("compression_settings",
                                    unreal.TextureCompressionSettings.TC_MASKS)
    EDITOR.save_loaded_asset(texture)
    return texture


def coordinates(material, x, y):
    # World-space planar UV: one repeat every 4 m, independent of Landscape size.
    world = MEL.create_material_expression(
        material, unreal.MaterialExpressionWorldPosition, x, y)
    mask = MEL.create_material_expression(
        material, unreal.MaterialExpressionComponentMask, x + 180, y)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", True)
    mask.set_editor_property("b", False)
    MEL.connect_material_expressions(world, "", mask, "")
    uv_scale = MEL.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, x + 180, y + 180)
    uv_scale.set_editor_property("parameter_name", "UVWorldScale")
    uv_scale.set_editor_property("default_value", 0.0025)
    multiply = MEL.create_material_expression(
        material, unreal.MaterialExpressionMultiply, x + 420, y)
    MEL.connect_material_expressions(mask, "", multiply, "A")
    MEL.connect_material_expressions(uv_scale, "", multiply, "B")
    return multiply


def sample(material, tex, coords, x, y, channel):
    node = MEL.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, x, y)
    node.set_editor_property("texture", tex)
    if channel == "Normal":
        node.set_editor_property("sampler_type",
                                 unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif channel == "Roughness":
        node.set_editor_property("sampler_type",
                                 unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    MEL.connect_material_expressions(coords, "", node, "Coordinates")
    return node


def wire_sample(material, node, channel):
    prop = {
        "Albedo": unreal.MaterialProperty.MP_BASE_COLOR,
        "Normal": unreal.MaterialProperty.MP_NORMAL,
        "Roughness": unreal.MaterialProperty.MP_ROUGHNESS,
    }[channel]
    MEL.connect_material_property(node, "R" if channel == "Roughness" else "RGB", prop)


def create_surface(kind, textures):
    name = "M_Ny%s_PBR%s" % (kind, VERSION)
    path = DEST_MAT + "/" + name
    if EDITOR.does_asset_exist(path):
        unreal.log_warning("[NYVERRA VISUAL] Material preserved: " + path)
        return
    mat = TOOLS.create_asset(name, DEST_MAT, unreal.Material,
                             unreal.MaterialFactoryNew())
    if not mat:
        raise RuntimeError("Could not create " + path)
    coords = coordinates(mat, -1500, -400)
    for index, channel in enumerate(CHANNELS):
        node = sample(mat, textures[(kind, channel)], coords,
                      -400, -400 + 380 * index, channel)
        wire_sample(mat, node, channel)
    MEL.recompile_material(mat)
    if not EDITOR.save_loaded_asset(mat):
        raise RuntimeError("Could not save " + path)
    unreal.log("[NYVERRA VISUAL] New surface material: " + path)


def create_landscape(textures):
    name = "M_NyLandscape_PBR%s" % VERSION
    path = DEST_MAT + "/" + name
    if EDITOR.does_asset_exist(path):
        unreal.log_warning("[NYVERRA VISUAL] Existing Landscape preserved: " + path)
        return
    mat = TOOLS.create_asset(name, DEST_MAT, unreal.Material,
                             unreal.MaterialFactoryNew())
    if not mat:
        raise RuntimeError("Could not create " + path)
    coords = coordinates(mat, -2300, -800)
    for ci, channel in enumerate(CHANNELS):
        yy = ci * 1200 - 800
        samples = {
            kind: sample(mat, textures[(kind, channel)], coords,
                         -1050, yy + i * 300, channel)
            for i, kind in enumerate(TYPES)
        }
        # LandscapeLayerWeight is ADDITIVE (Base + Layer * Weight). Using it
        # here would oversaturate albedo and produce invalid PBR normals.
        # Blend with explicit Lerp (A + (B-A) * Alpha) instead.
        previous = samples["Soil"]
        for j, kind in enumerate(("Grass", "Rock")):
            weight = MEL.create_material_expression(
                mat, unreal.MaterialExpressionLandscapeLayerSample,
                -810 + j * 300, yy + 520)
            weight.set_editor_property("parameter_name", kind)
            weight.set_editor_property("preview_weight", 0.0)
            node = MEL.create_material_expression(
                mat, unreal.MaterialExpressionLinearInterpolate,
                -580 + j * 300, yy + j * 150)
            output = "R" if channel == "Roughness" else "RGB"
            MEL.connect_material_expressions(
                previous, output if j == 0 else "", node, "A")
            MEL.connect_material_expressions(samples[kind], output, node, "B")
            MEL.connect_material_expressions(weight, "", node, "Alpha")
            previous = node
        prop = {
            "Albedo": unreal.MaterialProperty.MP_BASE_COLOR,
            "Normal": unreal.MaterialProperty.MP_NORMAL,
            "Roughness": unreal.MaterialProperty.MP_ROUGHNESS,
        }[channel]
        MEL.connect_material_property(previous, "", prop)
    MEL.recompile_material(mat)
    if not EDITOR.save_loaded_asset(mat):
        raise RuntimeError("Could not save " + path)
    unreal.log("[NYVERRA VISUAL] New Landscape PBR: " + path)


def main():
    require_sources()  # Fail before creating assets if package is incomplete.
    for directory in (DEST_TEX, DEST_MAT):
        if not EDITOR.does_directory_exist(directory):
            EDITOR.make_directory(directory)
    textures = {
        (kind, channel): import_texture(kind, channel)
        for kind in TYPES for channel in CHANNELS
    }
    for kind in TYPES:
        create_surface(kind, textures)
    create_landscape(textures)
    unreal.log_warning(
        "[NYVERRA VISUAL] Import complete. Open TestWorld or Landscape map, "
        "run Tools/apply_visual_polish_055.py, review and SAVE the level."
    )


if __name__ == "__main__":
    main()
