"""Builds all 10 animated shots of 'The Last Star' (59.0s @ 24fps = 1416 frames)."""
import math
import random
import bpy
import bmesh
from mathutils import Vector
from npr import (
    clear_scene,
    setup_world_sky,
    configure_render_and_compositor,
    make_emission_mat,
    make_painterly_mat,
    link_to_scene,
    make_empty,
    set_smooth,
)
from robot import build_robot, animate_walk
from observatory import build_observatory_exterior, build_observatory_interior
from fx import (
    make_star_diamond,
    build_star_vortex,
    build_exterior_star_geyser,
    build_star_whale_and_aurora,
    build_title_calligraphy,
)


SHOT_SPECS = [
    ("01_ext_dusk", 96, 54),          # 00:00 - 00:04 (preview at f54: window lit)
    ("02_int_enter", 144, 110),       # 00:04 - 00:10 (preview at f110: robot inside looking up)
    ("03_robot_closeup", 96, 56),     # 00:10 - 00:14 (preview at f56: curious head tilt)
    ("04_ignite_lens", 168, 128),     # 00:14 - 00:21 (preview at f128: star beam hits dome)
    ("05_projector_awake", 144, 118), # 00:21 - 00:27 (preview at f118: all lenses blazing)
    ("06_dome_vortex", 144, 96),      # 00:27 - 00:33 (preview at f96: swirling golden dome opening)
    ("07_ext_eruption", 144, 48),     # 00:33 - 00:39 (preview at f48: star geyser bursting from dome)
    ("08_star_whale", 192, 152),      # 00:39 - 00:47 (preview at f152: whale + aurora across sky)
    ("09_balcony_catch", 120, 96),    # 00:47 - 00:52 (preview at f96: robot catches star)
    ("10_title_outro", 168, 125),     # 00:52 - 00:59 (preview at f125: full calligraphy title)
]


def _make_scene(name, frames, res_x, res_y, samples):
    if name in bpy.data.scenes:
        bpy.data.scenes.remove(bpy.data.scenes[name])
    sc = bpy.data.scenes.new(name)
    sc.frame_start = 1
    sc.frame_end = frames
    configure_render_and_compositor(sc, res_x=res_x, res_y=res_y, samples=samples)
    return sc


def _add_camera(scene, name, location, target, lens=35.0, dof_dist=None, fstop=2.8):
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens
    cam_data.clip_start = 0.05
    cam_data.clip_end = 400.0
    if dof_dist is not None:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_distance = dof_dist
        cam_data.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = location
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    link_to_scene(scene, cam)
    scene.camera = cam
    return cam


def _add_light(scene, name, ltype, location, energy, color=(1, 1, 1), rotation=(0, 0, 0), size=2.0):
    ld = bpy.data.lights.new(name, ltype)
    ld.energy = energy
    ld.color = color
    if ltype == "AREA":
        ld.size = size
    elif ltype == "POINT":
        ld.shadow_soft_size = size * 0.25
    lo = bpy.data.objects.new(name, ld)
    lo.location = location
    lo.rotation_euler = rotation
    link_to_scene(scene, lo)
    return lo


def _animate_camera_track(cam, f_start, f_end, loc_start, loc_end, tgt_start, tgt_end):
    for f, loc, tgt in ((f_start, loc_start, tgt_start), (f_end, loc_end, tgt_end)):
        cam.location = loc
        direction = Vector(tgt) - Vector(loc)
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)


def build_shot_01_ext_dusk(frames, res_x, res_y, samples):
    sc = _make_scene("01_ext_dusk", frames, res_x, res_y, samples)
    setup_world_sky(
        sc, "World_Dusk",
        zenith=(0.04, 0.05, 0.14),
        horizon=(0.28, 0.23, 0.37),
        ground=(0.06, 0.07, 0.14),
        stars_strength=0.18,
        cloud_strength=0.42,
    )
    obs = build_observatory_exterior(sc, "ExtDusk", night_mode=False)

    # Moonlight / twilight key + soft cool fill
    _add_light(sc, "SunDusk", "SUN", (0, 0, 20), 1.8, color=(0.72, 0.76, 1.0), rotation=(0.95, 0.2, -0.8))
    _add_light(sc, "FillDusk", "AREA", (-12, -14, 8), 650, color=(0.50, 0.46, 0.78), rotation=(1.1, 0, -0.6), size=8.0)

    # Animate right porthole window turning on warmly at frame 26 (1.1s)
    win_mat = obs["lit_window"].data.materials[0]
    em = [n for n in win_mat.node_tree.nodes if n.type == "EMISSION"][0]
    for f, val in ((1, 0.02), (24, 0.02), (30, 6.2), (34, 4.2), (40, 6.8), (frames, 6.8)):
        em.inputs["Strength"].default_value = val
        em.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # Warm glow point light outside the lit window
    win_light = _add_light(sc, "WinGlow", "POINT", (2.4, -4.6, 1.9), 0.0, color=(1.0, 0.74, 0.32), size=1.0)
    for f, en in ((1, 0.0), (24, 0.0), (32, 220.0), (frames, 240.0)):
        win_light.data.energy = en
        win_light.data.keyframe_insert("energy", frame=f)

    # Gentle wind sway on foreground reeds
    reeds = obs["reeds"]
    for i in range(0, frames + 1, 16):
        reeds.rotation_euler = (0.0, 0.032 * math.sin(i * 0.14), 0.0)
        reeds.keyframe_insert("rotation_euler", frame=i)

    cam = _add_camera(sc, "Cam_01", (-2.6, -21.8, 2.15), (0.8, 0.0, 3.85), lens=32.0)
    _animate_camera_track(cam, 1, frames, (-2.6, -21.8, 2.15), (-1.9, -20.6, 2.28), (0.8, 0.0, 3.85), (0.8, 0.0, 3.95))
    return sc


def build_shot_02_int_enter(frames, res_x, res_y, samples):
    sc = _make_scene("02_int_enter", frames, res_x, res_y, samples)
    setup_world_sky(sc, "World_IntDark", zenith=(0.015, 0.02, 0.06), horizon=(0.03, 0.04, 0.09), ground=(0.01, 0.015, 0.04), cloud_strength=0.0)
    obs = build_observatory_interior(sc, "IntEnter")

    # Cool skylight shaft from dome slit + subtle interior blue ambient
    _add_light(sc, "DomeSlitKey", "AREA", (-1.2, 0.2, 7.6), 750, color=(0.56, 0.72, 1.0), rotation=(0.15, 0.35, 0), size=2.4)
    _add_light(sc, "IntAmbient", "AREA", (0.0, -4.5, 3.8), 160, color=(0.30, 0.36, 0.62), rotation=(1.1, 0, 0), size=6.0)

    robot = build_robot(sc, "Rob02", location=(-3.4, -2.5, 0.0), rotation_z=2.45, scale=0.88)
    # Robot enters from bottom-left holding lantern and walks clearly into lower-left foreground looking up at starball!
    animate_walk(robot, 8, 86, (-3.4, -2.5, 0.0), (-1.95, -1.75, 0.0), rot_z=2.45, steps=7)
    robot["head"].rotation_euler = (0.0, 0.0, 0.0)
    robot["head"].keyframe_insert("rotation_euler", frame=80)
    robot["head"].rotation_euler = (0.34, 0.0, -0.18)
    robot["head"].keyframe_insert("rotation_euler", frame=118)

    cam = _add_camera(sc, "Cam_02", (-0.65, -6.45, 1.68), (0.10, 0.6, 2.05), lens=24.0)
    _animate_camera_track(cam, 1, frames, (-0.65, -6.45, 1.68), (-0.45, -5.85, 1.75), (0.10, 0.6, 2.05), (0.20, 0.6, 2.15))
    return sc


def build_shot_03_robot_closeup(frames, res_x, res_y, samples):
    sc = _make_scene("03_robot_closeup", frames, res_x, res_y, samples)
    setup_world_sky(sc, "World_CU", zenith=(0.02, 0.03, 0.08), horizon=(0.04, 0.05, 0.12), ground=(0.015, 0.02, 0.05), cloud_strength=0.0)
    obs = build_observatory_interior(sc, "IntCU")
    # Hide starball behind robot so background is purely blurred scroll shelves with warm bokeh!
    obs["starball"]["root"].location = (0, 20, -20)

    _add_light(sc, "BackWarmBokeh", "POINT", (2.6, 4.8, 1.6), 550, color=(1.0, 0.68, 0.30), size=0.8)
    _add_light(sc, "KeyCU", "AREA", (-1.8, -2.4, 2.2), 200, color=(0.72, 0.82, 1.0), rotation=(1.1, 0, -0.7), size=1.8)
    _add_light(sc, "WarmRimCU", "POINT", (1.2, -1.6, 0.5), 140, color=(1.0, 0.72, 0.34), size=0.4)

    robot = build_robot(sc, "Rob03", location=(0.0, -0.5, 0.0), rotation_z=0.14, scale=1.0)
    for f, rot in ((1, (0.04, 0.02, 0.0)), (28, (0.08, -0.14, 0.06)), (62, (0.14, -0.19, 0.08)), (frames, (0.12, -0.16, 0.05))):
        robot["head"].rotation_euler = rot
        robot["head"].keyframe_insert("rotation_euler", frame=f)
    for f, sc_val in ((1, 0.90), (32, 1.0), (54, 1.15), (frames, 1.13)):
        robot["iris"].scale = (sc_val, 1.0, sc_val)
        robot["iris"].keyframe_insert("scale", frame=f)
    for f, rz in ((1, 0.0), (35, -0.12), (70, 0.08), (frames, -0.04)):
        robot["antenna"].rotation_euler = (0, rz, 0)
        robot["antenna"].keyframe_insert("rotation_euler", frame=f)

    # Framed with full dome head + glowing antenna orb + teal chest stripe visible!
    cam = _add_camera(sc, "Cam_03", (0.10, -2.75, 0.92), (0.0, -0.45, 0.88), lens=54.0, dof_dist=2.25, fstop=1.8)
    _animate_camera_track(cam, 1, frames, (0.10, -2.75, 0.92), (0.04, -2.58, 0.95), (0.0, -0.45, 0.88), (0.0, -0.45, 0.90))
    return sc


def build_shot_04_ignite_lens(frames, res_x, res_y, samples):
    sc = _make_scene("04_ignite_lens", frames, res_x, res_y, samples)
    setup_world_sky(sc, "World_Ignite", zenith=(0.02, 0.03, 0.08), horizon=(0.04, 0.05, 0.12), ground=(0.02, 0.02, 0.05), cloud_strength=0.0)
    obs = build_observatory_interior(sc, "IntIgnite")
    starball = obs["starball"]

    _add_light(sc, "SlitKey04", "AREA", (-1.0, 0.2, 7.6), 750, color=(0.60, 0.74, 1.0), rotation=(0.15, 0.35, 0), size=2.4)
    _add_light(sc, "Fill04", "AREA", (-2.0, -4.0, 2.8), 210, color=(0.45, 0.50, 0.75), rotation=(1.1, 0, -0.4), size=4.0)

    # Robot standing on the two stacked wooden crates next to the lower patina sphere!
    robot = build_robot(sc, "Rob04", location=(-1.22, 0.58, 1.00), rotation_z=1.35, scale=0.86)
    # Place lantern on floor glowing warmly
    robot["lantern"].parent = None
    robot["lantern"].location = (0.95, -0.55, 0.22)
    robot["lantern_light"].data.energy = 260.0

    # Reach right arm out to tap the starball lens around frame 68!
    for f, rot in ((1, (0.0, 0.0, 0.0)), (32, (0.75, 0.0, 0.25)), (56, (1.35, 0.0, 0.30)), (76, (1.28, 0.0, 0.28)), (frames, (0.85, 0.0, 0.15))):
        robot["arm_R"].rotation_euler = rot
        robot["arm_R"].keyframe_insert("rotation_euler", frame=f)

    # Hero lens lights up golden at frame 68
    hero_em = starball["hero_lens_em"]
    for f, s in ((1, 0.05), (64, 0.05), (72, 16.0), (frames, 14.0)):
        hero_em.inputs["Strength"].default_value = s
        hero_em.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # Thin golden laser beam shooting up from lower starball lens to the dome panel!
    beam_start = Vector((0.05, 0.75, 1.65))
    beam_end = Vector((0.65, 2.2, 8.2))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.018, radius2=0.025, depth=(beam_end - beam_start).length)
    m_beam = bpy.data.meshes.new("StarBeam")
    bm.to_mesh(m_beam); bm.free()
    beam = bpy.data.objects.new("StarBeam", m_beam)
    beam.location = (beam_start + beam_end) * 0.5
    beam.rotation_euler = (beam_end - beam_start).normalized().to_track_quat("Z", "Y").to_euler()
    beam.data.materials.append(make_emission_mat("Mat_StarBeam", (1.0, 0.94, 0.72), strength=14.0))
    link_to_scene(sc, beam)

    for f, sc_val in ((1, 0.0), (68, 0.0), (74, 1.0), (145, 1.0), (frames, 0.2)):
        beam.scale = (sc_val, sc_val, sc_val)
        beam.keyframe_insert("scale", frame=f)

    # Brilliant 4-pointed star flare blooming on the dome panel where the beam hits!
    flare = make_star_diamond(sc, "DomeFlare", beam_end - Vector((0, 0.1, 0.2)), size=0.85, color=(1.0, 0.96, 0.85), strength=18.0)
    flare.rotation_euler = (0.35, 0, 0)
    for f, sc_val in ((1, 0.0), (72, 0.0), (88, 1.45), (120, 1.05), (frames, 1.25)):
        flare.scale = (sc_val, sc_val, sc_val)
        flare.keyframe_insert("scale", frame=f)

    # Camera 1 (frames 1-82): Medium shot of robot on crates reaching to touch the starball
    # Camera 2 (frames 83-168): Dramatic tilt up following the golden beam to the star flare on the dome!
    cam = _add_camera(sc, "Cam_04", (-0.35, -2.55, 1.55), (-0.25, 0.75, 1.45), lens=38.0)
    _animate_camera_track(cam, 1, 78, (-0.35, -2.55, 1.55), (-0.28, -2.30, 1.60), (-0.25, 0.75, 1.45), (-0.15, 0.80, 1.52))
    _animate_camera_track(cam, 82, 168, (-0.15, -1.85, 2.2), (0.15, -1.45, 3.0), (0.35, 1.5, 5.2), (0.65, 2.1, 7.9))
    return sc


def build_shot_05_projector_awake(frames, res_x, res_y, samples):
    sc = _make_scene("05_projector_awake", frames, res_x, res_y, samples)
    setup_world_sky(sc, "World_Awake", zenith=(0.02, 0.03, 0.08), horizon=(0.04, 0.05, 0.12), ground=(0.02, 0.02, 0.05), cloud_strength=0.0)
    obs = build_observatory_interior(sc, "IntAwake")
    starball = obs["starball"]

    _add_light(sc, "SlitKey05", "AREA", (-1.2, 0.2, 7.6), 800, color=(0.62, 0.76, 1.0), rotation=(0.15, 0.35, 0), size=2.4)
    # Warm golden radial light blooming from the waking starball projector
    proj_light = _add_light(sc, "ProjWakeLight", "POINT", (0.65, 0.95, 2.6), 0.0, color=(1.0, 0.78, 0.35), size=1.2)
    for f, en in ((1, 20.0), (35, 80.0), (75, 480.0), (frames, 950.0)):
        proj_light.data.energy = en
        proj_light.data.keyframe_insert("energy", frame=f)

    # Robot stepped back holding lantern, gazing up
    robot = build_robot(sc, "Rob05", location=(-2.2, -1.9, 0.0), rotation_z=2.35, scale=0.84)
    robot["head"].rotation_euler = (0.38, 0, -0.15)

    # Hero lens already lit; ALL 36 lenses power up across frames 30 -> 130!
    starball["hero_lens_em"].inputs["Strength"].default_value = 14.0
    all_em = starball["all_lens_em"]
    for f, s in ((1, 0.15), (28, 0.4), (58, 4.5), (96, 12.0), (frames, 18.0)):
        all_em.inputs["Strength"].default_value = s
        all_em.inputs["Strength"].keyframe_insert("default_value", frame=f)

    # Starball gimbal starts gently rotating alive!
    gimbal = starball["gimbal"]
    gimbal.rotation_euler = (0.0, 0.42, -0.15)
    gimbal.keyframe_insert("rotation_euler", frame=1)
    gimbal.rotation_euler = (0.05, 0.38, 0.45)
    gimbal.keyframe_insert("rotation_euler", frame=frames)

    # Rising hero shot of the giant glowing starball with robot gazing up
    cam = _add_camera(sc, "Cam_05", (-0.9, -5.6, 1.55), (0.40, 0.85, 2.55), lens=28.0)
    _animate_camera_track(cam, 1, frames, (-0.9, -5.6, 1.55), (-0.55, -4.95, 1.75), (0.40, 0.85, 2.55), (0.50, 0.85, 2.75))
    return sc


def build_shot_06_dome_vortex(frames, res_x, res_y, samples):
    sc = _make_scene("06_dome_vortex", frames, res_x, res_y, samples)
    setup_world_sky(
        sc, "World_DomeSky",
        zenith=(0.10, 0.16, 0.38),
        horizon=(0.18, 0.24, 0.46),
        ground=(0.04, 0.06, 0.14),
        stars_strength=1.1,
        cloud_strength=0.10,
    )

    # Build upward-view ribbed observatory dome with animated sliding shutter doors!
    mat_rib = make_painterly_mat(
        "Mat_VortexDome",
        base_color=(0.24, 0.22, 0.30),
        shadow_color=(0.07, 0.08, 0.16),
        highlight_color=(0.56, 0.44, 0.36),
        brush_scale=6.0,
        patina_color=(0.42, 0.28, 0.20),
        patina_amount=0.30,
    )
    mat_metal = make_painterly_mat(
        "Mat_ShutterMetal",
        base_color=(0.18, 0.21, 0.32),
        shadow_color=(0.05, 0.07, 0.14),
        highlight_color=(0.38, 0.42, 0.56),
    )

    # Hemispherical ribbed dome shell with wide central slit along X axis (y in [-1.1, 1.1])
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=18, radius=7.5)
    for f in list(bm.faces):
        c = f.calc_center_median()
        if c.z < 0.0 or (abs(c.y) < 1.10 and c.z > 1.8):
            bm.faces.remove(f)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    m = bpy.data.meshes.new("VortexDome")
    bm.to_mesh(m); bm.free()
    dome = bpy.data.objects.new("VortexDome", m)
    dome.location = (0, 0, 2.0)
    dome.data.materials.append(mat_rib)
    link_to_scene(sc, dome)

    # Radial structural ribs inside dome for that unmistakable cathedral-like ceiling!
    for i in range(18):
        ang = 2 * math.pi * i / 18
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 0.12; v.co.y *= 14.2; v.co.z *= 0.18
        mr = bpy.data.meshes.new(f"Rib_{i}")
        bm.to_mesh(mr); bm.free()
        rib = bpy.data.objects.new(f"Rib_{i}", mr)
        rib.location = (0, 0, 8.8)
        rib.rotation_euler = (0, 0, ang)
        rib.data.materials.append(mat_metal)
        link_to_scene(sc, rib)

    # Two sliding shutter halves covering the slit at frame 1, sliding wide open by frame 115!
    for side, sy in (("L", -0.58), ("R", 0.58)):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 13.0; v.co.y *= 1.18; v.co.z *= 0.16
        ms = bpy.data.meshes.new(f"Shutter_{side}")
        bm.to_mesh(ms); bm.free()
        sh = bpy.data.objects.new(f"Shutter_{side}", ms)
        sh.data.materials.append(mat_metal)
        link_to_scene(sc, sh)
        sh.location = (0, sy, 9.25)
        sh.keyframe_insert("location", frame=1)
        sh.location = (0, sy, 9.25)
        sh.keyframe_insert("location", frame=24)
        sh.location = (0, sy * 4.5, 9.25)
        sh.keyframe_insert("location", frame=118)

    # Clean dark steel rail beams bordering the open dome slit (frames the sky opening crisply!)
    for sy in (-1.08, 1.08):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 15.0; v.co.y *= 0.24; v.co.z *= 0.35
        mb = bpy.data.meshes.new(f"SlitBeam_{int(sy*10)}")
        bm.to_mesh(mb); bm.free()
        beam_o = bpy.data.objects.new(f"SlitBeam_{int(sy*10)}", mb)
        beam_o.location = (0, sy, 9.0)
        beam_o.data.materials.append(mat_metal)
        link_to_scene(sc, beam_o)

    # Swirling golden-white starlight vortex (delicate luminous threads!)
    vortex_root, layers = build_star_vortex(sc, "DomeVortex", center=(0, 0, 5.4), count=135, radius_max=6.3, height=6.0)
    for idx, layer in enumerate(layers):
        speed = (1.8 + idx * 0.55) * math.pi
        layer.rotation_euler = (0, 0, 0)
        layer.keyframe_insert("rotation_euler", frame=1)
        layer.rotation_euler = (0, 0, speed)
        layer.keyframe_insert("rotation_euler", frame=frames)

    # White light flood bloom plane near camera surging to pure white at end of shot (frame 122 -> 144)!
    mat_flash = bpy.data.materials.new("Mat_WhiteFlash")
    mat_flash.use_nodes = True
    mat_flash.surface_render_method = "BLENDED"
    nt = mat_flash.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.99, 0.96, 1.0)
    em.inputs["Strength"].default_value = 5.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=8.0)
    mf = bpy.data.meshes.new("FlashPlane")
    bm.to_mesh(mf); bm.free()
    fp = bpy.data.objects.new("FlashPlane", mf)
    fp.location = (0, 0, 1.8)
    fp.data.materials.append(mat_flash)
    link_to_scene(sc, fp)
    for f, fac in ((1, 0.0), (120, 0.0), (138, 0.92), (frames, 1.0)):
        mix.inputs["Fac"].default_value = fac
        mix.inputs["Fac"].keyframe_insert("default_value", frame=f)

    # Dramatic warm center light lighting up the dome ribs
    _add_light(sc, "VortexGlow", "POINT", (0, 0, 4.0), 1600, color=(1.0, 0.84, 0.50), size=2.0)

    # FIXED: Camera looking STRAIGHT UP (X = pi!) into the spinning cathedral dome ceiling!
    cam_data = bpy.data.cameras.new("Cam_06")
    cam_data.lens = 18.0
    cam = bpy.data.objects.new("Cam_06", cam_data)
    cam.location = (0.0, 0.0, 0.4)
    link_to_scene(sc, cam)
    sc.camera = cam
    cam.rotation_euler = (math.pi, 0.0, -0.35)
    cam.keyframe_insert("rotation_euler", frame=1)
    cam.rotation_euler = (math.pi, 0.0, 0.35)
    cam.keyframe_insert("rotation_euler", frame=frames)
    return sc


def build_shot_07_ext_eruption(frames, res_x, res_y, samples):
    sc = _make_scene("07_ext_eruption", frames, res_x, res_y, samples)
    setup_world_sky(
        sc, "World_EruptNight",
        zenith=(0.03, 0.05, 0.16),
        horizon=(0.14, 0.18, 0.36),
        ground=(0.04, 0.05, 0.12),
        stars_strength=1.25,
        milky_way_strength=0.65,
        cloud_strength=0.12,
    )
    obs = build_observatory_exterior(sc, "ExtErupt", night_mode=True)
    # Open the dome shutter wide!
    obs["shutter"].rotation_euler = (0, 0, 0.85)
    # Bright glowing light inside the open dome slit
    _add_light(sc, "DomeBurstLight", "POINT", (0, -0.8, 6.2), 4500, color=(1.0, 0.94, 0.78), size=2.5)
    _add_light(sc, "StarSkyFill", "SUN", (0, 0, 20), 1.4, color=(0.65, 0.76, 1.0), rotation=(0.8, 0.1, -0.5))

    # Glowing white emission sphere inside dome so the open slit blazes with light!
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=3.7)
    mc = bpy.data.meshes.new("DomeInnerGlow")
    bm.to_mesh(mc); bm.free()
    inner = bpy.data.objects.new("DomeInnerGlow", mc)
    inner.location = (0, 0, 4.1)
    inner.data.materials.append(make_emission_mat("Mat_InnerBurst", (1.0, 0.98, 0.92), strength=10.0))
    link_to_scene(sc, inner)

    # Massive starlight geyser erupting out of the dome into the night sky!
    geyser = build_exterior_star_geyser(sc, "SkyGeyser", origin=(0, -0.3, 7.2))
    geyser.rotation_euler = (0, 0, 0)
    geyser.keyframe_insert("rotation_euler", frame=1)
    geyser.rotation_euler = (0, 0, 0.55)
    geyser.keyframe_insert("rotation_euler", frame=frames)

    # Tiny robot standing on the left catwalk looking up in awe (zero railing clipping!)
    robot = build_robot(sc, "Rob07", location=(-4.78, -1.65, 3.70), rotation_z=-0.55, scale=0.84)
    robot["lantern"].scale = (0, 0, 0)
    robot["lantern_light"].data.energy = 0.0
    robot["head"].rotation_euler = (0.34, -0.08, 0.12)
    # Wave right arm joyfully in the second half (close-up beat)
    for f, rot in ((1, (0.0, 0, 0)), (68, (0.0, 0, 0)), (96, (-1.45, 0, -0.30)), (120, (-1.75, 0, -0.10)), (frames, (-1.55, 0, -0.25))):
        robot["arm_R"].rotation_euler = rot
        robot["arm_R"].keyframe_insert("rotation_euler", frame=f)

    # First half (1-72): Wide exterior shot of observatory erupting a starry galaxy vortex
    # Second half (75-144): Close-up from INSIDE the catwalk arc looking slightly UP at robot & starry sky — ZERO railing bar in front of face!
    cam = _add_camera(sc, "Cam_07", (-2.2, -19.8, 2.4), (0.5, 0.0, 6.0), lens=31.0)
    _animate_camera_track(cam, 1, 72, (-2.2, -19.8, 2.4), (-1.8, -18.8, 2.7), (0.5, 0.0, 6.0), (0.5, 0.0, 6.4))
    _animate_camera_track(cam, 75, frames, (-4.72, -3.15, 4.46), (-4.62, -3.02, 4.50), (-4.82, -1.45, 4.58), (-4.78, -1.40, 4.65))
    return sc


def build_shot_08_star_whale(frames, res_x, res_y, samples):
    sc = _make_scene("08_star_whale", frames, res_x, res_y, samples)
    setup_world_sky(
        sc, "World_WhaleSky",
        zenith=(0.025, 0.045, 0.15),
        horizon=(0.15, 0.18, 0.34),
        ground=(0.04, 0.05, 0.11),
        stars_strength=1.45,
        milky_way_strength=0.95,
        cloud_strength=0.06,
    )

    # Vast desert plain with tiny distant observatory on far bottom-left!
    obs = build_observatory_exterior(sc, "TinyObs", location=(-15.5, 16.0, 0.0), night_mode=True)
    obs["root"].scale = (0.32, 0.32, 0.32)
    obs["shutter"].rotation_euler = (0, 0, 0.85)
    # Tiny glowing star beacon at the distant observatory
    make_star_diamond(sc, "ObsBeacon", (-15.5, 15.8, 2.6), size=0.45, color=(1.0, 0.96, 0.85), strength=14.0)

    _add_light(sc, "WhaleMoon", "SUN", (0, 0, 30), 1.1, color=(0.60, 0.72, 1.0), rotation=(0.8, 0.2, -0.5))

    # Scattered delicate stars across panoramic sky (mix of small pinpoints and a few hero stars)
    rng = random.Random(2026)
    for i in range(60):
        is_hero = (i % 10 == 0)
        make_star_diamond(
            sc, f"SkyStar_{i}",
            (rng.uniform(-28.0, 30.0), rng.uniform(22.0, 34.0), rng.uniform(2.5, 19.0)),
            size=rng.uniform(0.24, 0.36) if is_hero else rng.uniform(0.08, 0.16),
            strength=8.0 if is_hero else 3.2
        )

    # The Star Whale constellation + trailing Aurora Borealis!
    whale = build_star_whale_and_aurora(sc, "CelestialWhale", location=(-1.5, 24.0, 9.6))

    # Choreograph:
    # frames 1-42: stars gather & shimmer (lines & nebula hidden)
    # frames 42-86: constellation lines draw in + translucent nebula whale materializes
    # frames 86-192: whale glides gracefully rightwards while glowing Aurora ribbons trail from its tail!
    for f, la in ((1, 0.0), (36, 0.0), (74, 0.88), (frames, 0.90)):
        whale["line_alpha"].default_value = la
        whale["line_alpha"].keyframe_insert("default_value", frame=f)

    for f, ba in ((1, 0.0), (54, 0.0), (96, 0.48), (frames, 0.50)):
        whale["body_alpha"].default_value = ba
        whale["body_alpha"].keyframe_insert("default_value", frame=f)

    for f, aa in ((1, 0.0), (88, 0.0), (138, 0.78), (frames, 0.82)):
        whale["aurora_alpha"].default_value = aa
        whale["aurora_alpha"].keyframe_insert("default_value", frame=f)

    # Graceful whale swimming motion across the starry sky!
    wroot = whale["root"]
    for i in range(0, frames + 1, 24):
        t = i / frames
        wx = -4.0 + t * 9.5
        wz = 9.4 + math.sin(t * 2.2 * math.pi) * 0.75
        pitch = 0.06 * math.cos(t * 2.2 * math.pi)
        wroot.location = (wx, 24.0, wz)
        wroot.rotation_euler = (0.0, pitch, 0.0)
        wroot.keyframe_insert("location", frame=i)
        wroot.keyframe_insert("rotation_euler", frame=i)

    cam = _add_camera(sc, "Cam_08", (0.0, -14.0, 4.2), (1.0, 24.0, 8.8), lens=26.0)
    _animate_camera_track(cam, 1, frames, (0.0, -14.0, 4.2), (1.5, -13.5, 4.4), (0.5, 24.0, 8.6), (2.2, 24.0, 9.0))
    return sc


def build_shot_09_balcony_catch(frames, res_x, res_y, samples):
    sc = _make_scene("09_balcony_catch", frames, res_x, res_y, samples)
    setup_world_sky(
        sc, "World_Balcony",
        zenith=(0.03, 0.06, 0.20),
        horizon=(0.12, 0.18, 0.38),
        ground=(0.05, 0.07, 0.16),
        stars_strength=1.45,
        milky_way_strength=0.95,
        cloud_strength=0.05,
    )
    obs = build_observatory_exterior(sc, "BalcObs", night_mode=True)
    obs["shutter"].rotation_euler = (0, 0, 0.85)

    _add_light(sc, "StarRim09", "AREA", (2.0, -7.5, 6.2), 420, color=(0.70, 0.82, 1.0), rotation=(1.0, 0, 0.4), size=4.0)

    # Robot on curved stone catwalk railing facing 3/4 forward-right toward the starry sky!
    robot = build_robot(sc, "Rob09", location=(4.76, 0.18, 3.69), rotation_z=0.92, scale=0.88)
    robot["lantern"].scale = (0, 0, 0)
    robot["lantern_light"].data.energy = 0.0

    # Robot raises its front-side arm (arm_L) gracefully forward-up ABOVE the sleek railing so zero clipping!
    for f, rot in ((1, (0.0, 0, 0)), (32, (-0.75, 0.18, 0.0)), (76, (-1.62, 0.16, 0.0)), (frames, (-1.58, 0.16, 0.0))):
        robot["arm_L"].rotation_euler = rot
        robot["arm_L"].keyframe_insert("rotation_euler", frame=f)
    for f, rot in ((1, (0.18, 0, -0.05)), (65, (0.04, -0.08, -0.14)), (frames, (0.02, -0.10, -0.16))):
        robot["head"].rotation_euler = rot
        robot["head"].keyframe_insert("rotation_euler", frame=f)

    # Delicate glowing star drifting gently down to hover right ABOVE the robot's outstretched pincer (well ABOVE the z=4.18 rail!)
    catch_star = make_star_diamond(sc, "CaughtStar", (5.38, -0.25, 5.35), size=0.11, color=(1.0, 0.96, 0.85), strength=9.5)
    catch_star.rotation_euler = (0, 0, -0.50)
    catch_light = _add_light(sc, "CaughtStarLight", "POINT", (5.38, -0.25, 5.35), 65.0, color=(1.0, 0.90, 0.68), size=0.25)
    for f, pos in ((1, (5.55, -0.40, 5.45)), (46, (5.26, -0.14, 4.86)), (82, (5.08, -0.03, 4.46)), (frames, (5.08, -0.03, 4.46))):
        catch_star.location = pos
        catch_star.keyframe_insert("location", frame=f)
        catch_light.location = pos
        catch_light.keyframe_insert("location", frame=f)

    # Drifting delicate sparkle motes around the balcony
    rng = random.Random(55)
    for i in range(42):
        mote = make_star_diamond(
            sc, f"BalcMote_{i}",
            (rng.uniform(4.2, 11.5), rng.uniform(-2.0, 6.5), rng.uniform(3.9, 6.8)),
            size=rng.uniform(0.03, 0.08), strength=4.5
        )
        mote.rotation_euler = (0, 0, -0.50)

    # Clean framing: stone tower left, robot mid-left, outstretched hand + glowing star CLEARLY above sleek railing against starry night sky!
    cam = _add_camera(sc, "Cam_09", (4.16, -2.18, 4.42), (5.35, 1.05, 4.46), lens=28.0)
    _animate_camera_track(cam, 1, frames, (4.16, -2.18, 4.42), (4.26, -2.02, 4.46), (5.35, 1.05, 4.46), (5.40, 1.05, 4.50))
    return sc


def build_shot_10_title_outro(frames, res_x, res_y, samples):
    sc = _make_scene("10_title_outro", frames, res_x, res_y, samples)
    setup_world_sky(sc, "World_Title", zenith=(0.06, 0.08, 0.18), horizon=(0.06, 0.08, 0.18), ground=(0.06, 0.08, 0.18), cloud_strength=0.0)
    title = build_title_calligraphy(sc)

    _add_light(sc, "TitleTopLight", "AREA", (-1.5, -1.0, 5.0), 380, color=(0.70, 0.80, 1.0), size=5.0)
    _add_light(sc, "TitleStarGlow", "POINT", (-2.6, -0.9, 1.0), 160, color=(1.0, 0.90, 0.65), size=0.8)

    # Animate glowing starlight wisp drawing upward (frames 8 -> 38)
    wisp_curve = title["wisp"].data
    for f, bev in ((1, 0.0), (8, 0.0), (38, 1.0), (frames, 1.0)):
        wisp_curve.bevel_factor_end = bev
        wisp_curve.keyframe_insert("bevel_factor_end", frame=f)

    # Animate "The Last Star" handwriting reveal (frames 32 -> 86)
    for f, v in ((1, -0.05), (32, -0.05), (86, 1.15), (frames, 1.15)):
        title["title_rev"].default_value = v
        title["title_rev"].keyframe_insert("default_value", frame=f)

    # Animate "Every sky begins with one light." subtitle reveal (frames 88 -> 124)
    for f, v in ((1, -0.05), (88, -0.05), (124, 1.15), (frames, 1.15)):
        title["sub_rev"].default_value = v
        title["sub_rev"].keyframe_insert("default_value", frame=f)

    # Subtle fade-to-black curtain plane at frames 146 -> 168
    mat_blk = bpy.data.materials.new("Mat_FadeBlack")
    mat_blk.use_nodes = True
    mat_blk.surface_render_method = "BLENDED"
    nt = mat_blk.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    em.inputs["Strength"].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=8.0)
    mb = bpy.data.meshes.new("FadeBlackPlane")
    bm.to_mesh(mb); bm.free()
    bp = bpy.data.objects.new("FadeBlackPlane", mb)
    bp.location = (0, 0, 4.2)
    bp.data.materials.append(mat_blk)
    link_to_scene(sc, bp)
    for f, fac in ((1, 0.0), (144, 0.0), (frames, 1.0)):
        mix.inputs["Fac"].default_value = fac
        mix.inputs["Fac"].keyframe_insert("default_value", frame=f)

    # Overhead orthographic-feel camera looking down at stone tiles
    cam = _add_camera(sc, "Cam_10", (0.0, 0.0, 7.6), (0.0, 0.0, 0.0), lens=42.0)
    return sc


SHOT_BUILDERS = {
    "01_ext_dusk": build_shot_01_ext_dusk,
    "02_int_enter": build_shot_02_int_enter,
    "03_robot_closeup": build_shot_03_robot_closeup,
    "04_ignite_lens": build_shot_04_ignite_lens,
    "05_projector_awake": build_shot_05_projector_awake,
    "06_dome_vortex": build_shot_06_dome_vortex,
    "07_ext_eruption": build_shot_07_ext_eruption,
    "08_star_whale": build_shot_08_star_whale,
    "09_balcony_catch": build_shot_09_balcony_catch,
    "10_title_outro": build_shot_10_title_outro,
}
