"""Shared stylized NPR materials, outlines, world shaders, and Blender 5.2 compositor."""
import math
import bpy


def clear_scene(scene):
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def set_smooth(obj):
    if obj.type != "MESH" or not obj.data:
        return
    mesh = obj.data
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()


def make_outline_mat(name="Mat_Outline", color=(0.04, 0.045, 0.085, 1.0)):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def add_outline(obj, thickness=0.015, color=(0.04, 0.045, 0.085, 1.0)):
    if obj.type != "MESH":
        return
    mat = make_outline_mat(f"Mat_Outline_{int(color[0]*255)}_{int(color[2]*255)}", color)
    if len(obj.data.materials) == 0:
        obj.data.materials.append(make_painterly_mat("Mat_Fallback", (0.5, 0.5, 0.55)))
    if mat.name not in [m.name for m in obj.data.materials if m]:
        obj.data.materials.append(mat)
    mat_idx = [m.name for m in obj.data.materials if m].index(mat.name)
    mod = obj.modifiers.new("Outline", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.material_offset = mat_idx
    mod.use_rim = False


def make_emission_mat(name, color, strength=3.0, alpha=1.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    em.inputs["Strength"].default_value = strength
    if alpha < 0.999:
        trans = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = alpha
        nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
        mat.surface_render_method = "BLENDED"
    else:
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def make_painterly_mat(
    name,
    base_color,
    shadow_color=None,
    highlight_color=None,
    brush_scale=12.0,
    brush_amount=0.18,
    rim_color=(0.45, 0.58, 0.95),
    rim_strength=0.18,
    metallic=0.0,
    roughness=0.82,
    patina_color=None,
    patina_amount=0.0,
    brick_scale=0.0,
):
    """Stylized gouache/hand-painted cel shader using ShaderToRGB + multi-scale brush noise."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    r, g, b = base_color[:3]
    if shadow_color is None:
        # Cool indigo-shifted shadow for storybook dusk palette
        shadow_color = (r * 0.36 + 0.02, g * 0.38 + 0.03, min(1.0, b * 0.52 + 0.07))
    if highlight_color is None:
        highlight_color = (min(1.0, r * 1.28 + 0.05), min(1.0, g * 1.24 + 0.04), min(1.0, b * 1.18 + 0.03))

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (900, 0)

    # Coordinate + painterly brush noise
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-900, 100)

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.location = (-650, 220)
    noise1.inputs["Scale"].default_value = brush_scale
    noise1.inputs["Detail"].default_value = 6.0
    noise1.inputs["Roughness"].default_value = 0.65
    nt.links.new(tex_coord.outputs["Object"], noise1.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.location = (-650, -40)
    noise2.inputs["Scale"].default_value = brush_scale * 0.35
    noise2.inputs["Detail"].default_value = 3.0
    noise2.inputs["Roughness"].default_value = 0.5
    nt.links.new(tex_coord.outputs["Object"], noise2.inputs["Vector"])

    # Lighting response via Principled BSDF -> ShaderToRGB
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-400, 260)
    bsdf.inputs["Base Color"].default_value = (0.85, 0.85, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    # Subtle bump for painterly surface breakup
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-550, 120)
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(noise1.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    s2rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    s2rgb.location = (-130, 260)
    nt.links.new(bsdf.outputs["BSDF"], s2rgb.inputs["Shader"])

    rgb2bw = nt.nodes.new("ShaderNodeRGBToBW")
    rgb2bw.location = (40, 260)
    nt.links.new(s2rgb.outputs["Color"], rgb2bw.inputs["Color"])

    # Add painterly variation into light factor
    math_brush = nt.nodes.new("ShaderNodeMath")
    math_brush.location = (40, 100)
    math_brush.operation = "MULTIPLY_ADD"
    math_brush.inputs[1].default_value = brush_amount * 0.85
    math_brush.inputs[2].default_value = -brush_amount * 0.42
    nt.links.new(noise1.outputs["Fac"], math_brush.inputs[0])

    light_add = nt.nodes.new("ShaderNodeMath")
    light_add.location = (200, 220)
    light_add.operation = "ADD"
    light_add.use_clamp = True
    nt.links.new(rgb2bw.outputs["Val"], light_add.inputs[0])
    nt.links.new(math_brush.outputs["Value"], light_add.inputs[1])

    # 3-tone gouache color ramp
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (360, 240)
    ramp.color_ramp.interpolation = "B_SPLINE"
    e0 = ramp.color_ramp.elements[0]
    e0.position = 0.06
    e0.color = (shadow_color[0], shadow_color[1], shadow_color[2], 1.0)
    e1 = ramp.color_ramp.elements[1]
    e1.position = 0.42
    e1.color = (r, g, b, 1.0)
    e2 = ramp.color_ramp.elements.new(0.84)
    e2.color = (highlight_color[0], highlight_color[1], highlight_color[2], 1.0)
    nt.links.new(light_add.outputs["Value"], ramp.inputs["Fac"])

    current_color = ramp.outputs["Color"]

    # Optional stone/brick pattern (handles vertical cylinders nicely via X+Y horizontal, Z vertical)
    if brick_scale > 0.0:
        bsep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tex_coord.outputs["Object"], bsep.inputs["Vector"])
        badd = nt.nodes.new("ShaderNodeMath")
        badd.operation = "ADD"
        nt.links.new(bsep.outputs["X"], badd.inputs[0])
        nt.links.new(bsep.outputs["Y"], badd.inputs[1])
        bcomb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(badd.outputs["Value"], bcomb.inputs["X"])
        nt.links.new(bsep.outputs["Z"], bcomb.inputs["Y"])

        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.location = (-360, -240)
        brick.inputs["Scale"].default_value = brick_scale * 0.28
        brick.inputs["Mortar Size"].default_value = 0.022
        brick.inputs["Mortar Smooth"].default_value = 0.18
        brick.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
        brick.inputs["Color2"].default_value = (0.80, 0.82, 0.90, 1.0)
        brick.inputs["Mortar"].default_value = (0.34, 0.36, 0.48, 1.0)
        nt.links.new(bcomb.outputs["Vector"], brick.inputs["Vector"])

        bmix = nt.nodes.new("ShaderNodeMix")
        bmix.data_type = "RGBA"
        bmix.blend_type = "MULTIPLY"
        bmix.inputs["Factor"].default_value = 0.72
        nt.links.new(current_color, bmix.inputs["A"])
        nt.links.new(brick.outputs["Color"], bmix.inputs["B"])
        current_color = bmix.outputs["Result"]

    # Optional patina/weathering blotches (copper verdigris or scratched paint)
    if patina_color is not None and patina_amount > 0.0:
        pramp = nt.nodes.new("ShaderNodeValToRGB")
        pramp.location = (180, -180)
        pramp.color_ramp.elements[0].position = 0.50 - patina_amount * 0.25
        pramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        pramp.color_ramp.elements[1].position = 0.66
        pramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(noise2.outputs["Fac"], pramp.inputs["Fac"])

        pmix = nt.nodes.new("ShaderNodeMix")
        pmix.data_type = "RGBA"
        pmix.inputs["B"].default_value = (patina_color[0], patina_color[1], patina_color[2], 1.0)
        nt.links.new(pramp.outputs["Color"], pmix.inputs["Factor"])
        nt.links.new(current_color, pmix.inputs["A"])
        current_color = pmix.outputs["Result"]

    # Tint subtly by actual colored lights (warm lantern / golden starlight) without washing out shadows
    light_tint = nt.nodes.new("ShaderNodeMix")
    light_tint.data_type = "RGBA"
    light_tint.blend_type = "ADD"
    light_tint.inputs["Factor"].default_value = 0.14
    nt.links.new(current_color, light_tint.inputs["A"])
    nt.links.new(s2rgb.outputs["Color"], light_tint.inputs["B"])
    current_color = light_tint.outputs["Result"]

    # Soft Fresnel rim
    if rim_strength > 0.001:
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.28
        rramp = nt.nodes.new("ShaderNodeValToRGB")
        rramp.color_ramp.elements[0].position = 0.52
        rramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        rramp.color_ramp.elements[1].position = 0.90
        rramp.color_ramp.elements[1].color = (rim_strength, rim_strength, rim_strength, 1)
        nt.links.new(lw.outputs["Facing"], rramp.inputs["Fac"])

        rmix = nt.nodes.new("ShaderNodeMix")
        rmix.data_type = "RGBA"
        rmix.blend_type = "ADD"
        rmix.inputs["B"].default_value = (rim_color[0], rim_color[1], rim_color[2], 1.0)
        nt.links.new(rramp.outputs["Color"], rmix.inputs["Factor"])
        nt.links.new(current_color, rmix.inputs["A"])
        current_color = rmix.outputs["Result"]

    # Output via Emission so stylized colors stay crisp and true to palette
    em = nt.nodes.new("ShaderNodeEmission")
    em.location = (700, 0)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(current_color, em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def setup_world_sky(
    scene,
    name="World_Twilight",
    zenith=(0.035, 0.045, 0.13),
    horizon=(0.24, 0.21, 0.35),
    ground=(0.05, 0.055, 0.11),
    stars_strength=0.0,
    milky_way_strength=0.0,
    cloud_strength=0.35,
):
    """Procedural storybook twilight / starry Milky Way sky dome."""
    world = bpy.data.worlds.new(name)
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0

    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])

    # Sky vertical gradient
    grad = nt.nodes.new("ShaderNodeValToRGB")
    grad.color_ramp.interpolation = "B_SPLINE"
    e0 = grad.color_ramp.elements[0]
    e0.position = 0.0
    e0.color = (*ground, 1.0)
    e1 = grad.color_ramp.elements[1]
    e1.position = 0.08
    e1.color = (*horizon, 1.0)
    e2 = grad.color_ramp.elements.new(0.45)
    e2.color = (*zenith, 1.0)
    nt.links.new(sep.outputs["Z"], grad.inputs["Fac"])

    sky_col = grad.outputs["Color"]

    # Painted streaky twilight clouds
    if cloud_strength > 0.01:
        cmap = nt.nodes.new("ShaderNodeMapping")
        cmap.inputs["Scale"].default_value = (1.5, 4.5, 10.0)
        cmap.inputs["Rotation"].default_value = (0.0, 0.22, 0.3)
        nt.links.new(tc.outputs["Generated"], cmap.inputs["Vector"])

        cnoise = nt.nodes.new("ShaderNodeTexNoise")
        cnoise.inputs["Scale"].default_value = 3.2
        cnoise.inputs["Detail"].default_value = 7.0
        cnoise.inputs["Roughness"].default_value = 0.62
        nt.links.new(cmap.outputs["Vector"], cnoise.inputs["Vector"])

        cramp = nt.nodes.new("ShaderNodeValToRGB")
        cramp.color_ramp.elements[0].position = 0.54
        cramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        cramp.color_ramp.elements[1].position = 0.78
        cramp.color_ramp.elements[1].color = (cloud_strength, cloud_strength, cloud_strength, 1)
        nt.links.new(cnoise.outputs["Fac"], cramp.inputs["Fac"])

        cmix = nt.nodes.new("ShaderNodeMix")
        cmix.data_type = "RGBA"
        cmix.blend_type = "ADD"
        cmix.inputs["B"].default_value = (0.28, 0.27, 0.42, 1.0)
        nt.links.new(cramp.outputs["Color"], cmix.inputs["Factor"])
        nt.links.new(sky_col, cmix.inputs["A"])
        sky_col = cmix.outputs["Result"]

    # Milky Way diagonal nebula band
    if milky_way_strength > 0.01:
        mw_map = nt.nodes.new("ShaderNodeMapping")
        mw_map.inputs["Rotation"].default_value = (0.45, -0.55, 0.35)
        mw_map.inputs["Scale"].default_value = (1.2, 4.2, 1.2)
        nt.links.new(tc.outputs["Generated"], mw_map.inputs["Vector"])

        mw_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(mw_map.outputs["Vector"], mw_sep.inputs["Vector"])

        mw_abs = nt.nodes.new("ShaderNodeMath")
        mw_abs.operation = "ABSOLUTE"
        nt.links.new(mw_sep.outputs["Y"], mw_abs.inputs[0])

        mw_band = nt.nodes.new("ShaderNodeMapRange")
        mw_band.inputs["From Min"].default_value = 0.0
        mw_band.inputs["From Max"].default_value = 0.75
        mw_band.inputs["To Min"].default_value = 1.0
        mw_band.inputs["To Max"].default_value = 0.0
        nt.links.new(mw_abs.outputs["Value"], mw_band.inputs["Value"])

        mw_noise = nt.nodes.new("ShaderNodeTexNoise")
        mw_noise.inputs["Scale"].default_value = 7.5
        mw_noise.inputs["Detail"].default_value = 8.0
        mw_noise.inputs["Roughness"].default_value = 0.7
        nt.links.new(mw_map.outputs["Vector"], mw_noise.inputs["Vector"])

        mw_mul = nt.nodes.new("ShaderNodeMath")
        mw_mul.operation = "MULTIPLY"
        nt.links.new(mw_band.outputs["Result"], mw_mul.inputs[0])
        nt.links.new(mw_noise.outputs["Fac"], mw_mul.inputs[1])

        mw_str = nt.nodes.new("ShaderNodeMath")
        mw_str.operation = "MULTIPLY"
        mw_str.inputs[1].default_value = milky_way_strength
        nt.links.new(mw_mul.outputs["Value"], mw_str.inputs[0])

        mw_mix = nt.nodes.new("ShaderNodeMix")
        mw_mix.data_type = "RGBA"
        mw_mix.blend_type = "ADD"
        mw_mix.inputs["B"].default_value = (0.55, 0.58, 0.85, 1.0)
        nt.links.new(mw_str.outputs["Value"], mw_mix.inputs["Factor"])
        nt.links.new(sky_col, mw_mix.inputs["A"])
        sky_col = mw_mix.outputs["Result"]

    # Crisp twinkling stars via Voronoi
    if stars_strength > 0.01:
        vor = nt.nodes.new("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 135.0
        nt.links.new(tc.outputs["Generated"], vor.inputs["Vector"])

        sramp = nt.nodes.new("ShaderNodeValToRGB")
        sramp.color_ramp.elements[0].position = 0.0
        sramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
        sramp.color_ramp.elements[1].position = 0.055
        sramp.color_ramp.elements[1].color = (0.0, 0.0, 0.0, 1.0)
        nt.links.new(vor.outputs["Distance"], sramp.inputs["Fac"])

        # Mask below horizon
        hmask = nt.nodes.new("ShaderNodeMapRange")
        hmask.inputs["From Min"].default_value = 0.02
        hmask.inputs["From Max"].default_value = 0.14
        hmask.inputs["To Min"].default_value = 0.0
        hmask.inputs["To Max"].default_value = stars_strength
        nt.links.new(sep.outputs["Z"], hmask.inputs["Value"])

        smul = nt.nodes.new("ShaderNodeMath")
        smul.operation = "MULTIPLY"
        nt.links.new(sramp.outputs["Color"], smul.inputs[0])
        nt.links.new(hmask.outputs["Result"], smul.inputs[1])

        smix = nt.nodes.new("ShaderNodeMix")
        smix.data_type = "RGBA"
        smix.blend_type = "ADD"
        smix.inputs["B"].default_value = (1.0, 0.97, 0.88, 1.0)
        nt.links.new(smul.outputs["Value"], smix.inputs["Factor"])
        nt.links.new(sky_col, smix.inputs["A"])
        sky_col = smix.outputs["Result"]

    nt.links.new(sky_col, bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def configure_render_and_compositor(scene, res_x=1280, res_y=720, samples=24, glare_threshold=1.35, streak_threshold=4.8):
    """Configure Blender 5.2 EEVEE + AgX + Bloom/Star-Streak Compositor."""
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = "PNG"

    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = samples
    if hasattr(scene.eevee, "use_volumetric_shadows"):
        scene.eevee.use_volumetric_shadows = False

    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    scene.view_settings.exposure = -0.35

    # Blender 5.2 Compositor Node Group
    ng_name = f"Comp_{scene.name}"
    if ng_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[ng_name])
    ng = bpy.data.node_groups.new(ng_name, "CompositorNodeTree")
    scene.compositing_node_group = ng
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")

    rl = ng.nodes.new("CompositorNodeRLayers")
    rl.scene = scene
    rl.location = (-500, 0)

    # Fog Glow Bloom
    bloom = ng.nodes.new("CompositorNodeGlare")
    bloom.location = (-200, 0)
    bloom.inputs["Type"].default_value = "Fog Glow"
    bloom.inputs["Quality"].default_value = "Medium"
    bloom.inputs["Threshold"].default_value = glare_threshold
    bloom.inputs["Strength"].default_value = 0.52
    bloom.inputs["Size"].default_value = 0.68
    nt_links = ng.links
    nt_links.new(rl.outputs["Image"], bloom.inputs["Image"])

    # Delicate 4-point star streaks only on brightest hero stars
    streaks = ng.nodes.new("CompositorNodeGlare")
    streaks.location = (80, 0)
    streaks.inputs["Type"].default_value = "Streaks"
    streaks.inputs["Quality"].default_value = "Medium"
    streaks.inputs["Threshold"].default_value = streak_threshold
    streaks.inputs["Strength"].default_value = 0.30
    streaks.inputs["Streaks"].default_value = 4
    streaks.inputs["Streaks Angle"].default_value = 0.0
    streaks.inputs["Fade"].default_value = 0.80
    nt_links.new(bloom.outputs["Image"], streaks.inputs["Image"])

    out = ng.nodes.new("NodeGroupOutput")
    out.location = (380, 0)
    nt_links.new(streaks.outputs["Image"], out.inputs["Image"])


def link_to_scene(scene, obj):
    if obj.name not in scene.collection.objects:
        scene.collection.objects.link(obj)
    return obj


def make_empty(scene, name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    link_to_scene(scene, obj)
    if parent:
        obj.parent = parent
    return obj
