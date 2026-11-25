"""Observatory exterior and interior 3D environments + Zeiss dual-sphere star projector."""
import math
import random
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


def _obj_from_bm(scene, name, bm, mat, parent=None, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), outline=0.0):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    link_to_scene(scene, obj)
    if parent:
        obj.parent = parent
    obj.data.materials.append(mat)
    set_smooth(obj)
    if outline > 0:
        add_outline(obj, thickness=outline)
    return obj


def _cyl(r1, r2, h, segs=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h)
    return bm


def _box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    return bm


def build_observatory_exterior(scene, name="ObsExt", location=(0, 0, 0), night_mode=False):
    """Build the cylindrical stone observatory, ribbed metal dome with opening slit, side shed, dish, poles, and swaying reeds."""
    root = make_empty(scene, f"{name}_Root", location=location)

    mat_stone = make_painterly_mat(
        "Mat_ObsStone",
        base_color=(0.30, 0.32, 0.42),
        shadow_color=(0.09, 0.11, 0.21),
        highlight_color=(0.48, 0.50, 0.60),
        brush_scale=8.0,
        brick_scale=4.2,
        rim_color=(0.40, 0.52, 0.88),
        rim_strength=0.18,
    )
    mat_dome = make_painterly_mat(
        "Mat_ObsDome",
        base_color=(0.36, 0.40, 0.50),
        shadow_color=(0.10, 0.13, 0.25),
        highlight_color=(0.64, 0.68, 0.78),
        brush_scale=5.5,
        patina_color=(0.18, 0.21, 0.32),
        patina_amount=0.30,
        metallic=0.25,
        rim_color=(0.48, 0.66, 0.96),
        rim_strength=0.26,
    )
    mat_rust = make_painterly_mat(
        "Mat_ObsRust",
        base_color=(0.44, 0.23, 0.16),
        shadow_color=(0.14, 0.07, 0.09),
        highlight_color=(0.66, 0.38, 0.24),
        brush_scale=14.0,
    )
    mat_dark = make_painterly_mat(
        "Mat_ObsDark",
        base_color=(0.10, 0.12, 0.21),
        shadow_color=(0.03, 0.04, 0.09),
        highlight_color=(0.20, 0.22, 0.34),
    )
    mat_ground = make_painterly_mat(
        "Mat_PlainsGround",
        base_color=(0.12, 0.13, 0.23) if not night_mode else (0.06, 0.08, 0.17),
        shadow_color=(0.04, 0.05, 0.12),
        highlight_color=(0.24, 0.24, 0.36),
        brush_scale=2.5,
        brush_amount=0.22,
        rim_strength=0.04,
    )
    mat_path = make_painterly_mat(
        "Mat_DirtPath",
        base_color=(0.22, 0.22, 0.32),
        shadow_color=(0.09, 0.10, 0.19),
        highlight_color=(0.35, 0.34, 0.45),
        brush_scale=6.0,
        rim_strength=0.04,
    )
    mat_reed = make_painterly_mat(
        "Mat_Reeds",
        base_color=(0.09, 0.10, 0.20),
        shadow_color=(0.03, 0.04, 0.10),
        highlight_color=(0.22, 0.24, 0.38),
        brush_scale=10.0,
        rim_color=(0.42, 0.50, 0.80),
        rim_strength=0.22,
    )
    mat_win_dark = make_painterly_mat("Mat_WinDark", (0.06, 0.08, 0.16), shadow_color=(0.02, 0.03, 0.08))
    mat_win_lit = make_emission_mat("Mat_WinLit", (1.0, 0.78, 0.34), strength=5.0)

    # Huge ground terrain plane so panoramic horizons never show a cut-off edge!
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=40, size=340.0)
    for v in bm.verts:
        d = math.hypot(v.co.x, v.co.y)
        if d > 12.0:
            v.co.z = 0.22 * math.sin(v.co.x * 0.08) * math.cos(v.co.y * 0.07)
    _obj_from_bm(scene, f"{name}_Ground", bm, mat_ground, parent=root, location=(0, 0, 0))

    # Distant painterly layered mountain ridge silhouette along the horizon
    bm_mtn = bmesh.new()
    m_segs = 48
    for i in range(m_segs + 1):
        u = i / m_segs
        mx = -130.0 + u * 260.0
        my = 65.0 + math.sin(u * 9.0) * 8.0
        hz = max(0.3, 2.2 + 1.8 * math.sin(u * 14.0 + 0.5) + 1.1 * math.cos(u * 27.0) + 0.6 * math.sin(u * 41.0))
        bm_mtn.verts.new((mx, my, -0.5))
        bm_mtn.verts.new((mx, my, hz))
    bm_mtn.verts.ensure_lookup_table()
    for i in range(m_segs):
        v0, v1 = bm_mtn.verts[2 * i], bm_mtn.verts[2 * i + 1]
        v2, v3 = bm_mtn.verts[2 * (i + 1) + 1], bm_mtn.verts[2 * (i + 1)]
        bm_mtn.faces.new((v0, v3, v2, v1))
    _obj_from_bm(scene, f"{name}_HorizonRidge", bm_mtn, mat_dark, parent=root)

    # Dirt path curving from foreground to observatory door
    bm = bmesh.new()
    steps = 18
    for i in range(steps):
        t = i / (steps - 1)
        y = -5.5 - t * 24.0
        x = -1.2 * math.sin(t * 2.2) - t * 1.5
        w = 1.4 + t * 0.9
        bm.verts.new((x - w, y, 0.04))
        bm.verts.new((x + w, y, 0.04))
    bm.verts.ensure_lookup_table()
    for i in range(steps - 1):
        v0, v1 = bm.verts[2 * i], bm.verts[2 * i + 1]
        v2, v3 = bm.verts[2 * (i + 1) + 1], bm.verts[2 * (i + 1)]
        bm.faces.new((v0, v1, v2, v3))
    _obj_from_bm(scene, f"{name}_Path", bm, mat_path, parent=root)

    # Main cylindrical stone wall (radius 4.6, height 3.5)
    bm = _cyl(4.65, 4.55, 3.5, segs=36)
    _obj_from_bm(scene, f"{name}_StoneWall", bm, mat_stone, parent=root, location=(0, 0, 1.75), outline=0.035)

    # Catwalk stone ledge at z=3.55
    bm = _cyl(5.25, 5.15, 0.28, segs=36)
    _obj_from_bm(scene, f"{name}_Catwalk", bm, mat_stone, parent=root, location=(0, 0, 3.55), outline=0.025)

    # Sleek, delicate rusty-iron handrail around catwalk (proportionate waist height so it never clips robot face!)
    for rz in (3.92, 4.18):
        bm = bmesh.new()
        segs = 48
        r_rail = 5.14
        for i in range(segs):
            a0 = 2 * math.pi * i / segs
            a1 = 2 * math.pi * (i + 1) / segs
            p0 = (r_rail * math.cos(a0), r_rail * math.sin(a0), rz)
            p1 = (r_rail * math.cos(a1), r_rail * math.sin(a1), rz)
            v0 = bm.verts.new((p0[0], p0[1], p0[2] - 0.014))
            v1 = bm.verts.new((p0[0], p0[1], p0[2] + 0.014))
            v2 = bm.verts.new((p1[0], p1[1], p1[2] + 0.014))
            v3 = bm.verts.new((p1[0], p1[1], p1[2] - 0.014))
            bm.faces.new((v0, v1, v2, v3))
        _obj_from_bm(scene, f"{name}_Rail_{int(rz*100)}", bm, mat_rust, parent=root)

    # Slender vertical railing posts
    for i in range(28):
        ang = 2 * math.pi * i / 28
        bm = _cyl(0.016, 0.015, 0.62, segs=8)
        _obj_from_bm(
            scene, f"{name}_Post_{i}", bm, mat_rust, parent=root,
            location=(5.14 * math.cos(ang), 5.14 * math.sin(ang), 3.92)
        )

    # Arched front entrance doorway (-Y facing camera)
    bm = _box(1.35, 0.55, 2.05)
    _obj_from_bm(scene, f"{name}_DoorFrame", bm, mat_stone, parent=root, location=(-0.15, -4.45, 1.02), outline=0.02)
    bm = _box(1.05, 0.45, 1.85)
    _obj_from_bm(scene, f"{name}_DoorPanel", bm, mat_dark, parent=root, location=(-0.15, -4.52, 0.92))

    # Porthole round windows around the wall; right-front porthole lights up!
    lit_win_obj = None
    porthole_angles = [-2.25, -1.90, -1.10, -0.68]  # -pi/2 is front (-Y)
    for idx, ang in enumerate(porthole_angles):
        wx = 4.62 * math.cos(ang)
        wy = 4.62 * math.sin(ang)
        rot_z = ang + math.pi / 2
        bm = _cyl(0.56, 0.56, 0.28, segs=22)
        _obj_from_bm(
            scene, f"{name}_PortRim_{idx}", bm, mat_dark, parent=root,
            location=(wx, wy, 1.85), rotation=(math.pi / 2, 0, rot_z), outline=0.015
        )
        bm = _cyl(0.45, 0.45, 0.30, segs=22)
        is_hero_win = (idx == 2)
        win_obj = _obj_from_bm(
            scene, f"{name}_PortGlass_{idx}", bm, mat_win_lit if is_hero_win else mat_win_dark, parent=root,
            location=(wx, wy, 1.85), rotation=(math.pi / 2, 0, rot_z)
        )
        if is_hero_win:
            lit_win_obj = win_obj

    # Side annex shed on right (+X)
    bm = _box(3.4, 2.6, 2.2)
    _obj_from_bm(scene, f"{name}_Shed", bm, mat_stone, parent=root, location=(5.6, -0.9, 1.1), rotation=(0, 0, -0.15), outline=0.025)
    bm = _box(3.9, 3.0, 0.22)
    _obj_from_bm(scene, f"{name}_ShedRoof", bm, mat_rust, parent=root, location=(5.65, -0.9, 2.35), rotation=(0.12, 0.18, -0.15), outline=0.02)

    # Hemispherical metal observatory dome (with built-in openable slit!)
    dome_piv = make_empty(scene, f"{name}_DomePiv", location=(0, 0, 3.68), parent=root)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=18, radius=4.52)
    # Remove bottom half AND create a clean front slit gap (x in [-0.75, 0.75], y < 0.2, z > 0.2)
    for f in list(bm.faces):
        c = f.calc_center_median()
        if c.z < -0.05:
            bm.faces.remove(f)
        elif abs(c.x) < 0.72 and c.y < 0.45 and c.z > 0.15:
            bm.faces.remove(f)
    _obj_from_bm(scene, f"{name}_DomeShell", bm, mat_dome, parent=dome_piv, outline=0.035)

    # Sliding dome shutter door (covers the slit when closed, slides aside when opened)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=18, radius=4.60)
    for f in list(bm.faces):
        c = f.calc_center_median()
        if not (abs(c.x) < 0.85 and c.y < 0.65 and c.z > 0.05):
            bm.faces.remove(f)
    shutter_obj = _obj_from_bm(scene, f"{name}_DomeShutter", bm, mat_dome, parent=dome_piv, outline=0.025)

    # Top dome finial / lightning rod
    bm = _cyl(0.45, 0.20, 0.38, segs=16)
    _obj_from_bm(scene, f"{name}_DomeCap", bm, mat_dome, parent=dome_piv, location=(0, 0, 4.62), outline=0.015)
    bm = _cyl(0.03, 0.015, 1.0, segs=8)
    _obj_from_bm(scene, f"{name}_Finial", bm, mat_dark, parent=dome_piv, location=(0, 0, 5.25))

    # Left satellite dish on tripod
    dish_piv = make_empty(scene, f"{name}_Dish", location=(-8.8, 1.5, 0), parent=root)
    bm = _cyl(0.22, 0.16, 2.5, segs=12)
    _obj_from_bm(scene, f"{name}_DishStand", bm, mat_dark, parent=dish_piv, location=(0, 0, 1.25), outline=0.015)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=2.1)
    for f in list(bm.faces):
        if f.calc_center_median().z > -1.05:
            bm.faces.remove(f)
    _obj_from_bm(
        scene, f"{name}_DishBowl", bm, mat_dome, parent=dish_piv,
        location=(0, 0, 3.7), rotation=(0.95, 0.45, -0.5), outline=0.02
    )

    # Right utility poles
    for idx, (px, py) in enumerate([(9.5, -2.5), (14.5, 4.5)]):
        bm = _cyl(0.14, 0.10, 7.2, segs=10)
        _obj_from_bm(scene, f"{name}_Pole_{idx}", bm, mat_dark, parent=root, location=(px, py, 3.6))
        bm = _box(1.9, 0.12, 0.12)
        _obj_from_bm(scene, f"{name}_Crossbar_{idx}", bm, mat_dark, parent=root, location=(px, py, 6.6))

    # Foreground + midground swaying reed/grass tufts (rich framing at left & right bottom!)
    rng = random.Random(42)
    bm_reeds = bmesh.new()
    for _ in range(520):
        rx = rng.uniform(-17.5, 17.5)
        ry = rng.uniform(-21.5, -5.5)
        if abs(rx + 0.8) < 1.8 and ry > -17.0:
            continue
        h = rng.uniform(1.0, 2.8) if abs(rx) > 5.0 else rng.uniform(0.7, 1.8)
        lean_x = rng.uniform(-0.45, 0.55)
        lean_y = rng.uniform(-0.2, 0.2)
        w = rng.uniform(0.05, 0.13)
        v0 = bm_reeds.verts.new((rx - w, ry, 0.0))
        v1 = bm_reeds.verts.new((rx + w, ry, 0.0))
        v2 = bm_reeds.verts.new((rx + lean_x * 0.4 + w * 0.5, ry + lean_y * 0.4, h * 0.55))
        v3 = bm_reeds.verts.new((rx + lean_x * 0.4 - w * 0.5, ry + lean_y * 0.4, h * 0.55))
        vt = bm_reeds.verts.new((rx + lean_x, ry + lean_y, h))
        bm_reeds.faces.new((v0, v1, v2, v3))
        bm_reeds.faces.new((v3, v2, vt))
    reeds_obj = _obj_from_bm(scene, f"{name}_Reeds", bm_reeds, mat_reed, parent=root)

    # Dark metallic seam ribs curving over the dome exterior for realistic panel lines!
    for r_ang in (-1.2, -0.65, -0.18, 0.18, 0.65, 1.2):
        bm_rib = bmesh.new()
        r_d = 4.56
        segs_r = 14
        prev = None
        for i in range(segs_r + 1):
            phi = (i / segs_r) * (math.pi * 0.48)
            rr = r_d * math.cos(phi)
            zz = r_d * math.sin(phi)
            cx = rr * math.sin(r_ang)
            cy = -rr * math.cos(r_ang)
            va = bm_rib.verts.new((cx - 0.03, cy - 0.02, zz))
            vb = bm_rib.verts.new((cx + 0.03, cy + 0.02, zz))
            if prev:
                bm_rib.faces.new((prev[0], prev[1], vb, va))
            prev = (va, vb)
        _obj_from_bm(scene, f"{name}_DomeRib_{int(r_ang*100)}", bm_rib, mat_dark, parent=dome_piv)

    return {
        "root": root,
        "dome_piv": dome_piv,
        "shutter": shutter_obj,
        "lit_window": lit_win_obj,
        "reeds": reeds_obj,
    }


def build_starball_projector(scene, name="Starball", location=(0.6, 1.2, 0.0), parent=None):
    """Build the iconic rusty-copper/verdigris Zeiss dual-sphere planetarium projector with brass gears and animatable glowing lenses."""
    root = make_empty(scene, f"{name}_Root", location=location, parent=parent)

    mat_patina = make_painterly_mat(
        "Mat_ProjectorPatina",
        base_color=(0.48, 0.36, 0.28),
        shadow_color=(0.14, 0.14, 0.22),
        highlight_color=(0.72, 0.54, 0.36),
        brush_scale=9.0,
        patina_color=(0.24, 0.48, 0.44),  # verdigris copper patina!
        patina_amount=0.45,
        metallic=0.35,
        rim_color=(0.60, 0.72, 0.95),
        rim_strength=0.28,
    )
    mat_brass = make_painterly_mat(
        "Mat_ProjectorBrass",
        base_color=(0.66, 0.50, 0.24),
        shadow_color=(0.22, 0.16, 0.12),
        highlight_color=(0.94, 0.78, 0.44),
        metallic=0.45,
        brush_scale=16.0,
    )
    mat_iron = make_painterly_mat(
        "Mat_ProjectorIron",
        base_color=(0.18, 0.22, 0.32),
        shadow_color=(0.06, 0.08, 0.16),
        highlight_color=(0.35, 0.40, 0.54),
        metallic=0.3,
    )
    mat_lens_off = make_painterly_mat(
        "Mat_LensOff",
        base_color=(0.12, 0.15, 0.22),
        shadow_color=(0.04, 0.05, 0.10),
        highlight_color=(0.45, 0.52, 0.68),
        rim_strength=0.35,
    )

    # Circular floor plinth
    bm = _cyl(1.55, 1.48, 0.20, segs=32)
    _obj_from_bm(scene, f"{name}_Plinth", bm, mat_iron, parent=root, location=(0, 0, 0.10), outline=0.02)

    # Heavy tripod / A-frame legs
    for ang in (-0.8, 0.8, math.pi):
        bm = _cyl(0.14, 0.10, 2.75, segs=12)
        lx = 0.65 * math.cos(ang)
        ly = 0.65 * math.sin(ang)
        _obj_from_bm(
            scene, f"{name}_Leg_{int(ang*10)}", bm, mat_iron, parent=root,
            location=(lx, ly, 1.35), rotation=(-0.38 * math.sin(ang), 0.38 * math.cos(ang), 0), outline=0.015
        )

    # Central tilted gimbal assembly (tilted ~26 deg like reference!)
    gimbal = make_empty(scene, f"{name}_Gimbal", location=(0, 0, 2.55), parent=root)
    gimbal.rotation_euler = (0.0, 0.42, -0.15)

    # Central spine truss between lower and upper star spheres
    bm = _cyl(0.32, 0.32, 2.75, segs=16)
    _obj_from_bm(scene, f"{name}_Spine", bm, mat_iron, parent=gimbal, outline=0.015)

    # Brass gear rings and arc rail
    for gz in (-0.65, 0.0, 0.65):
        bm = _cyl(0.68, 0.68, 0.10, segs=28)
        _obj_from_bm(scene, f"{name}_Gear_{int(gz*10)}", bm, mat_brass, parent=gimbal, location=(0, 0, gz), outline=0.01)

    # Curved brass quadrant gear arc + handwheel
    bm = bmesh.new()
    segs = 24
    for i in range(segs):
        a0 = -1.1 + 2.2 * i / segs
        a1 = -1.1 + 2.2 * (i + 1) / segs
        r_in, r_out = 1.25, 1.42
        for yoff in (-0.05, 0.05):
            pass
        v0 = bm.verts.new((r_in * math.cos(a0), -0.05, r_in * math.sin(a0)))
        v1 = bm.verts.new((r_out * math.cos(a0), -0.05, r_out * math.sin(a0)))
        v2 = bm.verts.new((r_out * math.cos(a1), -0.05, r_out * math.sin(a1)))
        v3 = bm.verts.new((r_in * math.cos(a1), -0.05, r_in * math.sin(a1)))
        bm.faces.new((v0, v1, v2, v3))
    _obj_from_bm(scene, f"{name}_ArcGear", bm, mat_brass, parent=root, location=(0, 0, 2.55), rotation=(0, 0.35, 0), outline=0.01)

    # Two iconic patina spheres (lower and upper starballs)
    lens_mats = []
    hero_lens_mat = None
    hero_lens_obj = None

    # Create a dedicated emissive material for the hero lens and another for all remaining lenses
    hero_lens_mat = bpy.data.materials.new(f"{name}_HeroLensMat")
    hero_lens_mat.use_nodes = True
    nt = hero_lens_mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.85, 0.42, 1.0)
    em.inputs["Strength"].default_value = 0.05
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    hero_lens_em = em

    all_lens_mat = bpy.data.materials.new(f"{name}_AllLensMat")
    all_lens_mat.use_nodes = True
    nt2 = all_lens_mat.node_tree
    nt2.nodes.clear()
    out2 = nt2.nodes.new("ShaderNodeOutputMaterial")
    em2 = nt2.nodes.new("ShaderNodeEmission")
    em2.inputs["Color"].default_value = (1.0, 0.82, 0.38, 1.0)
    em2.inputs["Strength"].default_value = 0.05
    nt2.links.new(em2.outputs["Emission"], out2.inputs["Surface"])
    all_lens_em = em2

    # Fibonacci sphere points for projection lenses
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    for s_idx, sz in enumerate((-1.42, 1.42)):
        sphere_r = 0.86
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=28, v_segments=18, radius=sphere_r)
        _obj_from_bm(scene, f"{name}_Sphere_{s_idx}", bm, mat_patina, parent=gimbal, location=(0, 0, sz), outline=0.022)

        # Riveted metal seam belt around sphere
        bm = _cyl(sphere_r + 0.025, sphere_r + 0.025, 0.11, segs=28)
        _obj_from_bm(scene, f"{name}_Belt_{s_idx}", bm, mat_brass, parent=gimbal, location=(0, 0, sz), outline=0.008)

        n_lenses = 18
        for i in range(n_lenses):
            y = 1.0 - (i / float(n_lenses - 1)) * 2.0
            rad = math.sqrt(max(0.0, 1.0 - y * y))
            theta = golden_angle * i + s_idx * 1.1
            nx = math.cos(theta) * rad
            ny = math.sin(theta) * rad
            nz = y
            pos = (nx * sphere_r, ny * sphere_r, sz + nz * sphere_r)
            # Align cylinder Z axis with outward normal
            from mathutils import Vector
            rot_quat = Vector((0, 0, 1)).rotation_difference(Vector((nx, ny, nz)))
            rot_eul = rot_quat.to_euler()

            # Brass lens barrel
            bm = _cyl(0.14, 0.125, 0.16, segs=16)
            _obj_from_bm(
                scene, f"{name}_LensBarrel_{s_idx}_{i}", bm, mat_brass, parent=gimbal,
                location=pos, rotation=rot_eul, outline=0.007
            )
            # Inner glowing lens glass
            is_hero = (s_idx == 0 and i == 7)
            bm = _cyl(0.095, 0.095, 0.18, segs=14)
            l_obj = _obj_from_bm(
                scene, f"{name}_LensGlass_{s_idx}_{i}", bm,
                hero_lens_mat if is_hero else all_lens_mat,
                parent=gimbal, location=pos, rotation=rot_eul
            )
            if is_hero:
                hero_lens_obj = l_obj

    return {
        "root": root,
        "gimbal": gimbal,
        "hero_lens_em": hero_lens_em,
        "all_lens_em": all_lens_em,
        "hero_lens_obj": hero_lens_obj,
    }


def build_observatory_interior(scene, name="ObsInt"):
    """Build the cylindrical wood/book-lined observatory interior, balcony, scroll cubbies, crates, orrery, telescope, and dome ceiling."""
    root = make_empty(scene, f"{name}_Root")

    mat_wood = make_painterly_mat(
        "Mat_IntWood",
        base_color=(0.30, 0.24, 0.24),
        shadow_color=(0.09, 0.09, 0.16),
        highlight_color=(0.50, 0.38, 0.32),
        brush_scale=9.0,
        brick_scale=4.0,
        rim_strength=0.10,
    )
    mat_wall = make_painterly_mat(
        "Mat_IntWall",
        base_color=(0.14, 0.17, 0.28),
        shadow_color=(0.04, 0.06, 0.12),
        highlight_color=(0.24, 0.28, 0.42),
        brush_scale=6.0,
        rim_strength=0.06,
    )
    mat_crate = make_painterly_mat(
        "Mat_Crate",
        base_color=(0.48, 0.34, 0.24),
        shadow_color=(0.18, 0.13, 0.14),
        highlight_color=(0.72, 0.54, 0.36),
        brush_scale=12.0,
        rim_color=(0.85, 0.72, 0.50),
        rim_strength=0.18,
    )
    mat_scroll = make_painterly_mat(
        "Mat_ScrollPaper",
        base_color=(0.76, 0.66, 0.48),
        shadow_color=(0.32, 0.28, 0.26),
        highlight_color=(0.94, 0.86, 0.68),
        brush_scale=15.0,
    )
    mat_sheet = make_painterly_mat(
        "Mat_DustSheet",
        base_color=(0.30, 0.35, 0.48),
        shadow_color=(0.11, 0.14, 0.24),
        highlight_color=(0.52, 0.58, 0.72),
        brush_scale=8.0,
        rim_strength=0.22,
    )
    mat_brass = make_painterly_mat(
        "Mat_IntBrass",
        base_color=(0.68, 0.52, 0.25),
        shadow_color=(0.24, 0.18, 0.12),
        highlight_color=(0.92, 0.76, 0.44),
        metallic=0.4,
    )
    mat_dome_in = make_painterly_mat(
        "Mat_IntDomeRib",
        base_color=(0.12, 0.15, 0.25),
        shadow_color=(0.04, 0.06, 0.13),
        highlight_color=(0.24, 0.27, 0.38),
        brush_scale=3.0,
        brick_scale=1.6,
        patina_color=(0.18, 0.15, 0.18),
        patina_amount=0.14,
        rim_strength=0.05,
    )

    # Circular wooden plank floor
    bm = _cyl(7.2, 7.2, 0.2, segs=40)
    _obj_from_bm(scene, f"{name}_Floor", bm, mat_wood, parent=root, location=(0, 0, -0.1))

    # Outer cylindrical dark interior wall (open inside)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=40, radius1=7.0, radius2=7.0, depth=6.5)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    _obj_from_bm(scene, f"{name}_Wall", bm, mat_wall, parent=root, location=(0, 0, 3.25))

    # Upper circular library balcony ledge & wooden railing
    bm = bmesh.new()
    segs = 40
    for i in range(segs):
        a0 = 2 * math.pi * i / segs
        a1 = 2 * math.pi * (i + 1) / segs
        r1, r2 = 5.65, 7.0
        v0 = bm.verts.new((r1 * math.cos(a0), r1 * math.sin(a0), 4.1))
        v1 = bm.verts.new((r2 * math.cos(a0), r2 * math.sin(a0), 4.1))
        v2 = bm.verts.new((r2 * math.cos(a1), r2 * math.sin(a1), 4.1))
        v3 = bm.verts.new((r1 * math.cos(a1), r1 * math.sin(a1), 4.1))
        bm.faces.new((v0, v1, v2, v3))
    _obj_from_bm(scene, f"{name}_Balcony", bm, mat_wood, parent=root)

    # Interior ribbed dome ceiling (with slit opening)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=7.0)
    for f in list(bm.faces):
        c = f.calc_center_median()
        if c.z < -0.1:
            bm.faces.remove(f)
        elif abs(c.x + 1.4) < 0.55 and c.y > -1.0 and c.z > 2.2:
            bm.faces.remove(f)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    _obj_from_bm(scene, f"{name}_DomeCeiling", bm, mat_dome_in, parent=root, location=(0, 0, 5.2))

    # Scattered wooden crates on left (and two stacked crates near projector for Shot 4)
    for idx, (cx, cy, cz, sx, sy, sz, rz) in enumerate([
        (-4.0, -1.6, 0.55, 1.3, 1.1, 1.1, 0.15),
        (-3.8, -1.4, 1.50, 1.0, 0.9, 0.85, -0.08),
        (-1.25, 0.55, 0.28, 0.95, 0.82, 0.56, 0.08),
        (-1.22, 0.58, 0.78, 0.72, 0.65, 0.44, -0.05),
    ]):
        bm = _box(sx, sy, sz)
        _obj_from_bm(
            scene, f"{name}_Crate_{idx}", bm, mat_crate, parent=root,
            location=(cx, cy, cz), rotation=(0, 0, rz), outline=0.015
        )

    # Dust-sheet covered mysterious mounds in midground
    for idx, (sx, sy, rad, h) in enumerate([(-2.8, 3.2, 0.95, 2.3), (-1.2, 4.0, 0.85, 2.1)]):
        bm = _cyl(rad, rad * 0.38, h, segs=18)
        _obj_from_bm(scene, f"{name}_Sheet_{idx}", bm, mat_sheet, parent=root, location=(sx, sy, h * 0.5), outline=0.018)

    # Scattered parchment scrolls on floor
    rng = random.Random(7)
    for i in range(14):
        px = rng.uniform(-3.8, 3.6)
        py = rng.uniform(-3.6, 2.2)
        if math.hypot(px - 0.6, py - 1.2) < 1.8:
            continue
        rz = rng.uniform(0, math.pi)
        if i % 2 == 0:
            bm = _cyl(0.065, 0.065, 0.58, segs=12)
            _obj_from_bm(scene, f"{name}_Scroll_{i}", bm, mat_scroll, parent=root, location=(px, py, 0.065), rotation=(math.pi / 2, 0, rz), outline=0.006)
        else:
            bm = _box(0.45, 0.34, 0.015)
            _obj_from_bm(scene, f"{name}_Page_{i}", bm, mat_scroll, parent=root, location=(px, py, 0.012), rotation=(0, 0, rz), outline=0.004)

    # Scroll cubby wall shelves along the back arc (gives awesome bokeh in robot close-up!)
    scroll_colors = [
        (0.55, 0.52, 0.46),
        (0.32, 0.48, 0.52),
        (0.46, 0.38, 0.34),
        (0.40, 0.44, 0.58),
    ]
    scroll_mats = [make_painterly_mat(f"Mat_CubbyScroll_{i}", c, brush_scale=16.0) for i, c in enumerate(scroll_colors)]
    bm_shelf = bmesh.new()
    for row in range(6):
        z = 0.65 + row * 0.55
        for col in range(16):
            ang = 0.25 + col * (math.pi - 0.5) / 15.0
            sx = 6.25 * math.cos(ang)
            sy = 6.25 * math.sin(ang)
            # Place rolled scroll tubes facing inward
            if rng.random() > 0.22:
                bm = _cyl(0.11, 0.11, 0.35, segs=10)
                _obj_from_bm(
                    scene, f"{name}_WallScroll_{row}_{col}", bm, scroll_mats[(row + col) % len(scroll_mats)],
                    parent=root, location=(sx, sy, z), rotation=(math.pi / 2, 0, ang + math.pi / 2)
                )

    # Solar-system Orrery table on the right (+X)
    orrery_piv = make_empty(scene, f"{name}_Orrery", location=(3.4, -0.5, 0.0), parent=root)
    bm = _cyl(0.68, 0.65, 0.09, segs=22)
    _obj_from_bm(scene, f"{name}_OrreryTable", bm, mat_crate, parent=orrery_piv, location=(0, 0, 1.05), outline=0.012)
    bm = _cyl(0.10, 0.12, 1.05, segs=14)
    _obj_from_bm(scene, f"{name}_OrreryLeg", bm, mat_crate, parent=orrery_piv, location=(0, 0, 0.52), outline=0.01)
    # Central golden sun sphere + orbiting brass arms + planets
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=0.17)
    _obj_from_bm(scene, f"{name}_OrrerySun", bm, mat_brass, parent=orrery_piv, location=(0, 0, 1.62), outline=0.008)
    for pidx, (dist, pz, prad, pcol) in enumerate([
        (0.32, 1.50, 0.065, (0.76, 0.78, 0.84)),
        (0.54, 1.68, 0.095, (0.42, 0.56, 0.80)),
        (0.75, 1.44, 0.075, (0.78, 0.44, 0.40)),
    ]):
        ang = pidx * 2.1 + 0.4
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=prad)
        pmat = make_painterly_mat(f"Mat_Planet_{pidx}", pcol, brush_scale=18.0)
        _obj_from_bm(
            scene, f"{name}_Planet_{pidx}", bm, pmat, parent=orrery_piv,
            location=(dist * math.cos(ang), dist * math.sin(ang), pz), outline=0.006
        )

    # Brass telescope on right background
    bm = _cyl(0.11, 0.065, 2.2, segs=16)
    _obj_from_bm(
        scene, f"{name}_Telescope", bm, mat_scroll, parent=root,
        location=(2.8, 2.2, 1.65), rotation=(0.65, -0.55, 0.2), outline=0.012
    )

    # Volumetric god-ray light shaft streaming from dome slit down onto starball
    mat_godray = make_emission_mat("Mat_GodRay", (0.62, 0.76, 1.0), strength=0.65, alpha=0.16)
    bm = _cyl(1.45, 0.35, 9.2, segs=24)
    godray = _obj_from_bm(
        scene, f"{name}_GodRay", bm, mat_godray, parent=root,
        location=(-0.4, 0.5, 4.6), rotation=(0.15, 0.38, 0.0)
    )

    # Build the centerpiece starball projector
    starball = build_starball_projector(scene, name=f"{name}_Starball", location=(0.65, 0.95, 0.0), parent=root)

    return {
        "root": root,
        "starball": starball,
        "godray": godray,
        "orrery": orrery_piv,
    }
