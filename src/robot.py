"""Articulated cyclops retro robot hero character and glowing lantern prop."""
import math
import bpy
import bmesh
from npr import (
    make_painterly_mat,
    make_emission_mat,
    add_outline,
    set_smooth,
    link_to_scene,
    make_empty,
)


def _create_mesh_obj(scene, name, bm, mat, parent=None, location=(0, 0, 0), rotation=(0, 0, 0), outline=0.012):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    link_to_scene(scene, obj)
    if parent:
        obj.parent = parent
    obj.data.materials.append(mat)
    set_smooth(obj)
    if outline > 0:
        add_outline(obj, thickness=outline)
    return obj


def _uv_sphere_bm(radius, segs=24, rings=16, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=radius)
    if scale != (1, 1, 1):
        for v in bm.verts:
            v.co.x *= scale[0]
            v.co.y *= scale[1]
            v.co.z *= scale[2]
    return bm


def _cyl_bm(r1, r2, depth, segs=20):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=depth)
    return bm


def build_robot(scene, name="Robot", location=(0, 0, 0), rotation_z=0.0, scale=1.0):
    """Build the cute white/teal one-eyed robot with animated head, eye, antenna, arms, legs, and lantern."""
    mat_white = make_painterly_mat(
        "Mat_RobotWhite",
        base_color=(0.86, 0.85, 0.82),
        shadow_color=(0.35, 0.39, 0.52),
        highlight_color=(0.98, 0.96, 0.90),
        brush_scale=18.0,
        brush_amount=0.14,
        patina_color=(0.62, 0.58, 0.52),
        patina_amount=0.18,
        rim_color=(0.65, 0.78, 1.0),
        rim_strength=0.28,
    )
    mat_teal = make_painterly_mat(
        "Mat_RobotTeal",
        base_color=(0.24, 0.62, 0.60),
        shadow_color=(0.10, 0.28, 0.34),
        highlight_color=(0.40, 0.78, 0.74),
        brush_scale=20.0,
        rim_strength=0.22,
    )
    mat_dark = make_painterly_mat(
        "Mat_RobotDark",
        base_color=(0.22, 0.25, 0.32),
        shadow_color=(0.08, 0.10, 0.16),
        highlight_color=(0.40, 0.44, 0.54),
        brush_scale=16.0,
        rim_strength=0.20,
    )
    mat_brass = make_painterly_mat(
        "Mat_RobotBrass",
        base_color=(0.68, 0.52, 0.26),
        shadow_color=(0.28, 0.20, 0.12),
        highlight_color=(0.92, 0.78, 0.45),
        metallic=0.35,
        brush_scale=22.0,
    )
    mat_eye_black = make_painterly_mat(
        "Mat_RobotEyeBlack",
        base_color=(0.04, 0.05, 0.08),
        shadow_color=(0.02, 0.02, 0.04),
        highlight_color=(0.14, 0.16, 0.22),
        rim_strength=0.15,
    )
    mat_iris = make_emission_mat("Mat_RobotIris", (1.0, 0.76, 0.18), strength=2.6)
    mat_pupil = make_emission_mat("Mat_RobotPupil", (0.04, 0.04, 0.06), strength=0.4)
    mat_glint = make_emission_mat("Mat_RobotGlint", (1.0, 0.98, 0.92), strength=3.5)
    mat_antenna = make_emission_mat("Mat_RobotAntenna", (1.0, 0.78, 0.22), strength=5.0)
    mat_lantern_glass = make_emission_mat("Mat_LanternGlow", (1.0, 0.80, 0.36), strength=8.0)

    root = make_empty(scene, f"{name}_Root", location=location)
    root.rotation_euler = (0, 0, rotation_z)
    root.scale = (scale, scale, scale)

    # Torso pivot (for gentle bounce/lean)
    body_piv = make_empty(scene, f"{name}_Body", location=(0, 0, 0.36), parent=root)

    # Cylindrical slightly tapered torso (height ~0.34, radius ~0.18)
    bm = _cyl_bm(0.165, 0.185, 0.34, segs=28)
    _create_mesh_obj(scene, f"{name}_Torso", bm, mat_white, parent=body_piv, location=(0, 0, 0.17), outline=0.011)

    # Bottom hip cap
    bm = _uv_sphere_bm(0.165, segs=24, rings=12, scale=(1.0, 1.0, 0.35))
    _create_mesh_obj(scene, f"{name}_HipCap", bm, mat_dark, parent=body_piv, location=(0, 0, 0.01), outline=0.008)

    # Teal chest stripe band
    bm = _cyl_bm(0.178, 0.183, 0.068, segs=28)
    _create_mesh_obj(scene, f"{name}_TealStripe", bm, mat_teal, parent=body_piv, location=(0, 0, 0.16), outline=0.004)

    # Small chest gauge dial on upper right front (-Y is forward)
    bm = _cyl_bm(0.036, 0.036, 0.02, segs=20)
    _create_mesh_obj(
        scene, f"{name}_ChestDial", bm, mat_dark, parent=body_piv,
        location=(0.055, -0.175, 0.255), rotation=(math.pi / 2, 0, 0.25), outline=0.003
    )

    # Neck collar
    bm = _cyl_bm(0.125, 0.13, 0.06, segs=24)
    _create_mesh_obj(scene, f"{name}_Neck", bm, mat_dark, parent=body_piv, location=(0, 0, 0.35), outline=0.007)

    # Head pivot
    head_piv = make_empty(scene, f"{name}_Head", location=(0, 0, 0.39), parent=body_piv)

    # Dome-shaped head: lower cylinder + upper hemisphere
    bm = _cyl_bm(0.245, 0.25, 0.19, segs=32)
    _create_mesh_obj(scene, f"{name}_HeadBase", bm, mat_white, parent=head_piv, location=(0, 0, 0.10), outline=0.013)

    bm = _uv_sphere_bm(0.25, segs=32, rings=20, scale=(1.0, 1.0, 0.88))
    for v in list(bm.verts):
        if v.co.z < -0.02:
            v.co.z = -0.02
    _create_mesh_obj(scene, f"{name}_HeadDome", bm, mat_white, parent=head_piv, location=(0, 0, 0.19), outline=0.013)

    # Side ear bolts / headphones
    for side, sx in (("L", -1), ("R", 1)):
        bm = _cyl_bm(0.052, 0.044, 0.06, segs=18)
        _create_mesh_obj(
            scene, f"{name}_Ear_{side}", bm, mat_dark, parent=head_piv,
            location=(sx * 0.255, 0.0, 0.17), rotation=(0, math.pi / 2, 0), outline=0.007
        )

    # Antenna with glowing amber orb
    ant_piv = make_empty(scene, f"{name}_AntennaPiv", location=(-0.06, 0.0, 0.39), parent=head_piv)
    bm = _cyl_bm(0.009, 0.006, 0.15, segs=10)
    _create_mesh_obj(
        scene, f"{name}_AntennaStem", bm, mat_dark, parent=ant_piv,
        location=(-0.025, 0, 0.07), rotation=(0, -0.35, 0), outline=0.003
    )
    bm = _uv_sphere_bm(0.036, segs=18, rings=12)
    ant_orb = _create_mesh_obj(
        scene, f"{name}_AntennaOrb", bm, mat_antenna, parent=ant_piv,
        location=(-0.052, 0, 0.145), outline=0.0
    )

    # Giant expressive cyclops eye (facing -Y)
    eye_piv = make_empty(scene, f"{name}_Eye", location=(0.0, -0.225, 0.20), parent=head_piv)

    # Outer brass rim
    bm = _cyl_bm(0.148, 0.142, 0.065, segs=32)
    _create_mesh_obj(
        scene, f"{name}_EyeRim", bm, mat_brass, parent=eye_piv,
        location=(0, -0.01, 0), rotation=(math.pi / 2, 0, 0), outline=0.008
    )
    # Dark inner socket
    bm = _cyl_bm(0.125, 0.125, 0.05, segs=32)
    _create_mesh_obj(
        scene, f"{name}_EyeSocket", bm, mat_eye_black, parent=eye_piv,
        location=(0, -0.022, 0), rotation=(math.pi / 2, 0, 0), outline=0.0
    )
    # Glowing amber iris ring (scaled to animate curiosity/awe!)
    iris_piv = make_empty(scene, f"{name}_IrisPiv", location=(0, -0.048, 0), parent=eye_piv)
    bm = _cyl_bm(0.088, 0.088, 0.012, segs=28)
    _create_mesh_obj(
        scene, f"{name}_EyeIris", bm, mat_iris, parent=iris_piv,
        location=(0, 0, 0), rotation=(math.pi / 2, 0, 0), outline=0.0
    )
    # Dark center pupil
    bm = _cyl_bm(0.044, 0.044, 0.016, segs=24)
    _create_mesh_obj(
        scene, f"{name}_EyePupil", bm, mat_pupil, parent=iris_piv,
        location=(0, -0.004, 0), rotation=(math.pi / 2, 0, 0), outline=0.0
    )
    # Cute white specular eye highlight dot
    bm = _uv_sphere_bm(0.020, segs=12, rings=8)
    _create_mesh_obj(
        scene, f"{name}_EyeGlint", bm, mat_glint, parent=iris_piv,
        location=(-0.032, -0.012, 0.032), outline=0.0
    )

    # Arms + pincer claws
    arms = {}
    for side, sx in (("L", -1), ("R", 1)):
        arm_piv = make_empty(scene, f"{name}_Arm_{side}", location=(sx * 0.195, 0, 0.27), parent=body_piv)
        # Shoulder joint
        bm = _uv_sphere_bm(0.032, segs=14, rings=10)
        _create_mesh_obj(scene, f"{name}_Shoulder_{side}", bm, mat_dark, parent=arm_piv, outline=0.005)
        # Slender pipe arm
        bm = _cyl_bm(0.016, 0.018, 0.26, segs=12)
        _create_mesh_obj(
            scene, f"{name}_ArmTube_{side}", bm, mat_dark, parent=arm_piv,
            location=(sx * 0.02, 0, -0.13), rotation=(0, sx * 0.14, 0), outline=0.005
        )
        # Teal wrist cuff
        bm = _cyl_bm(0.028, 0.028, 0.042, segs=16)
        _create_mesh_obj(
            scene, f"{name}_Wrist_{side}", bm, mat_teal, parent=arm_piv,
            location=(sx * 0.038, 0, -0.25), outline=0.005
        )
        # Pincer fingers (two rounded cream prongs like the close-up!)
        for fidx, dy in ((0, -0.026), (1, 0.026)):
            bm = _uv_sphere_bm(0.022, segs=12, rings=10, scale=(0.65, 0.75, 2.1))
            _create_mesh_obj(
                scene, f"{name}_Claw_{side}_{fidx}", bm, mat_white, parent=arm_piv,
                location=(sx * 0.042, dy, -0.305), rotation=(dy * 4.5, 0, 0), outline=0.004
            )
        arms[side] = arm_piv

    # Legs + rounded shoes
    legs = {}
    for side, sx in (("L", -1), ("R", 1)):
        leg_piv = make_empty(scene, f"{name}_Leg_{side}", location=(sx * 0.075, 0, 0.34), parent=root)
        bm = _cyl_bm(0.024, 0.028, 0.24, segs=14)
        _create_mesh_obj(scene, f"{name}_LegTube_{side}", bm, mat_dark, parent=leg_piv, location=(0, 0, -0.12), outline=0.006)
        bm = _uv_sphere_bm(0.068, segs=18, rings=12, scale=(0.82, 1.35, 0.55))
        _create_mesh_obj(
            scene, f"{name}_Foot_{side}", bm, mat_white, parent=leg_piv,
            location=(0, -0.025, -0.29), outline=0.007
        )
        legs[side] = leg_piv

    # Warm glowing lantern prop (can be parented to hand or placed on floor)
    lantern_piv = make_empty(scene, f"{name}_Lantern", location=(0.04, 0.0, -0.34), parent=arms["R"])
    # Handle ring
    bm = _cyl_bm(0.045, 0.045, 0.012, segs=16)
    _create_mesh_obj(scene, f"{name}_LanternTop", bm, mat_brass, parent=lantern_piv, location=(0, 0, -0.03), outline=0.004)
    # Glowing core glass
    bm = _cyl_bm(0.050, 0.055, 0.12, segs=18)
    _create_mesh_obj(scene, f"{name}_LanternGlass", bm, mat_lantern_glass, parent=lantern_piv, location=(0, 0, -0.10), outline=0.0)
    # Bottom cap
    bm = _cyl_bm(0.060, 0.058, 0.025, segs=18)
    _create_mesh_obj(scene, f"{name}_LanternBase", bm, mat_dark, parent=lantern_piv, location=(0, 0, -0.17), outline=0.005)
    # Warm point light inside lantern
    l_data = bpy.data.lights.new(f"{name}_LanternLight", "POINT")
    l_data.energy = 140.0
    l_data.color = (1.0, 0.72, 0.30)
    l_data.shadow_soft_size = 0.15
    l_obj = bpy.data.objects.new(f"{name}_LanternLight", l_data)
    l_obj.location = (0, 0, -0.10)
    link_to_scene(scene, l_obj)
    l_obj.parent = lantern_piv

    return {
        "root": root,
        "body": body_piv,
        "head": head_piv,
        "eye": eye_piv,
        "iris": iris_piv,
        "antenna": ant_piv,
        "antenna_orb": ant_orb,
        "arm_L": arms["L"],
        "arm_R": arms["R"],
        "leg_L": legs["L"],
        "leg_R": legs["R"],
        "lantern": lantern_piv,
        "lantern_light": l_obj,
    }


def animate_walk(rig, f_start, f_end, pos_start, pos_end, rot_z=0.0, steps=6):
    """Animate cute waddling robot walk cycle between two positions."""
    root = rig["root"]
    root.rotation_euler = (0, 0, rot_z)
    root.location = pos_start
    root.keyframe_insert("location", frame=f_start)
    root.location = pos_end
    root.keyframe_insert("location", frame=f_end)

    dur = max(1, f_end - f_start)
    for i in range(steps + 1):
        t = i / steps
        f = int(round(f_start + t * dur))
        swing = 0.42 * math.sin(t * steps * math.pi)
        bob = abs(math.sin(t * steps * math.pi)) * 0.032
        waddle = 0.06 * math.sin(t * steps * math.pi)

        rig["leg_L"].rotation_euler = (swing, 0, 0)
        rig["leg_R"].rotation_euler = (-swing, 0, 0)
        rig["body"].location = (0, 0, 0.36 + bob)
        rig["body"].rotation_euler = (0, waddle, 0)
        rig["arm_L"].rotation_euler = (-swing * 0.55, 0, 0)

        rig["leg_L"].keyframe_insert("rotation_euler", frame=f)
        rig["leg_R"].keyframe_insert("rotation_euler", frame=f)
        rig["body"].keyframe_insert("location", frame=f)
        rig["body"].keyframe_insert("rotation_euler", frame=f)
        rig["arm_L"].keyframe_insert("rotation_euler", frame=f)

    # Settle back to neutral standing pose at end
    rig["leg_L"].rotation_euler = (0, 0, 0)
    rig["leg_R"].rotation_euler = (0, 0, 0)
    rig["body"].location = (0, 0, 0.36)
    rig["body"].rotation_euler = (0, 0, 0)
    rig["leg_L"].keyframe_insert("rotation_euler", frame=f_end + 4)
    rig["leg_R"].keyframe_insert("rotation_euler", frame=f_end + 4)
    rig["body"].keyframe_insert("location", frame=f_end + 4)
    rig["body"].keyframe_insert("rotation_euler", frame=f_end + 4)
