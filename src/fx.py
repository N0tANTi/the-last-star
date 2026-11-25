"""VFX builders: starlight vortex, Star Whale constellation + aurora borealis, and glowing calligraphic title."""
import math
import random
import bpy
import bmesh
from mathutils import Vector
from npr import (
    make_emission_mat,
    make_painterly_mat,
    set_smooth,
    link_to_scene,
    make_empty,
)


def make_star_diamond(scene, name, location, size=0.15, color=(1.0, 0.96, 0.85), strength=8.0, parent=None):
    """Create a crisp 4-pointed glowing star sprite/mesh."""
    mat = make_emission_mat(f"Mat_Star_{int(strength*10)}_{int(color[2]*100)}", color, strength=strength)
    bm = bmesh.new()
    # 3D 4-point starburst octahedron-star
    c_f = bm.verts.new((0, -size * 0.14, 0))
    c_b = bm.verts.new((0, size * 0.14, 0))
    pts = [
        (0, 0, size),
        (size * 0.22, 0, size * 0.22),
        (size, 0, 0),
        (size * 0.22, 0, -size * 0.22),
        (0, 0, -size),
        (-size * 0.22, 0, -size * 0.22),
        (-size, 0, 0),
        (-size * 0.22, 0, size * 0.22),
    ]
    ring = [bm.verts.new(p) for p in pts]
    for i in range(len(ring)):
        v1 = ring[i]
        v2 = ring[(i + 1) % len(ring)]
        bm.faces.new((c_f, v1, v2))
        bm.faces.new((c_b, v2, v1))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    link_to_scene(scene, obj)
    if parent:
        obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def build_star_vortex(scene, name="StarVortex", center=(0, 0, 0), count=140, radius_max=6.5, height=7.0, spiral_turns=2.4):
    """Build smooth swirling golden-white starlight streaks with glowing heads for the dome eruption shots."""
    root = make_empty(scene, f"{name}_Root", location=center)
    mat_trail = make_emission_mat("Mat_VortexTrail", (1.0, 0.86, 0.52), strength=3.4, alpha=0.68)
    mat_head = make_emission_mat("Mat_VortexHead", (1.0, 0.97, 0.86), strength=9.5)

    rng = random.Random(108)
    layers = []
    for l_idx in range(3):
        layer = make_empty(scene, f"{name}_Layer_{l_idx}", parent=root)
        bm_trails = bmesh.new()
        bm_heads = bmesh.new()
        n_layer = count // 3
        for i in range(n_layer):
            t0 = rng.uniform(0.05, 0.88)
            base_ang = rng.uniform(0, 2 * math.pi)
            r_mult = rng.uniform(0.32, 1.05)
            arc_len = rng.uniform(0.10, 0.24)
            segs = 20
            prev_pts = None
            for s in range(segs + 1):
                u = s / segs
                t = t0 + u * arc_len
                r = radius_max * (0.14 + 0.88 * t) * r_mult
                ang = base_ang + t * spiral_turns * 2 * math.pi
                z = (t - 0.35) * height + math.sin(ang * 2) * 0.22
                x = r * math.cos(ang)
                y = r * math.sin(ang)
                # Fine tapered starlight thread
                w = (0.008 + 0.022 * u) * (1.0 if s < segs else 1.1)
                p_a = bm_trails.verts.new((x, y, z - w))
                p_b = bm_trails.verts.new((x, y, z + w))
                if prev_pts is not None:
                    bm_trails.faces.new((prev_pts[0], prev_pts[1], p_b, p_a))
                prev_pts = (p_a, p_b)
                if s == segs:
                    hs = rng.uniform(0.05, 0.11)
                    ret = bmesh.ops.create_icosphere(bm_heads, subdivisions=1, radius=hs)
                    for v in ret["verts"]:
                        v.co += Vector((x, y, z))

        m_tr = bpy.data.meshes.new(f"{name}_Trails_{l_idx}")
        bm_trails.to_mesh(m_tr)
        bm_trails.free()
        o_tr = bpy.data.objects.new(f"{name}_Trails_{l_idx}", m_tr)
        o_tr.data.materials.append(mat_trail)
        link_to_scene(scene, o_tr)
        o_tr.parent = layer

        m_hd = bpy.data.meshes.new(f"{name}_Heads_{l_idx}")
        bm_heads.to_mesh(m_hd)
        bm_heads.free()
        o_hd = bpy.data.objects.new(f"{name}_Heads_{l_idx}", m_hd)
        o_hd.data.materials.append(mat_head)
        link_to_scene(scene, o_hd)
        o_hd.parent = layer
        layers.append(layer)

    return root, layers


def build_exterior_star_geyser(scene, name="StarGeyser", origin=(0, 0, 7.6)):
    """Build a dreamy galactic river of twinkling stardust, soft nebula swirls, and hero stars flowing out of the dome."""
    root = make_empty(scene, f"{name}_Root", location=origin)
    rng = random.Random(33)

    # 1. Soft translucent nebula swirl ribbon curving gracefully up and across the sky (zero hard broom lines!)
    mat_neb = bpy.data.materials.new("Mat_GeyserNebula")
    mat_neb.use_nodes = True
    mat_neb.surface_render_method = "BLENDED"
    nt = mat_neb.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 3.2
    mix = nt.nodes.new("ShaderNodeMixShader")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], sep.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6.5
    noise.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])

    # Color transitions from warm golden-cream at slit -> luminous sky blue -> soft violet mist
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = (1.0, 0.95, 0.80, 1.0)
    cm = cr.color_ramp.elements.new(0.42)
    cm.color = (0.68, 0.82, 1.0, 1.0)
    cr.color_ramp.elements[2].position = 0.90
    cr.color_ramp.elements[2].color = (0.48, 0.56, 0.96, 1.0)
    nt.links.new(sep.outputs["X"], cr.inputs["Fac"])
    nt.links.new(cr.outputs["Color"], em.inputs["Color"])

    # Soft fade across ribbon width (UV.y: 0 -> 1 -> 0) and tail end (UV.x: 0 -> 1 -> 0)
    vf = nt.nodes.new("ShaderNodeValToRGB")
    vf.color_ramp.elements[0].position = 0.0
    vf.color_ramp.elements[0].color = (0, 0, 0, 1)
    vm = vf.color_ramp.elements.new(0.5)
    vm.color = (1, 1, 1, 1)
    vf.color_ramp.elements[2].position = 1.0
    vf.color_ramp.elements[2].color = (0, 0, 0, 1)
    nt.links.new(sep.outputs["Y"], vf.inputs["Fac"])

    uf = nt.nodes.new("ShaderNodeValToRGB")
    uf.color_ramp.elements[0].position = 0.0
    uf.color_ramp.elements[0].color = (0.85, 0.85, 0.85, 1)
    um = uf.color_ramp.elements.new(0.35)
    um.color = (0.70, 0.70, 0.70, 1)
    uf.color_ramp.elements[2].position = 1.0
    uf.color_ramp.elements[2].color = (0, 0, 0, 1)
    nt.links.new(sep.outputs["X"], uf.inputs["Fac"])

    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(vf.outputs["Color"], m1.inputs[0]); nt.links.new(uf.outputs["Color"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs["Value"], m2.inputs[0]); nt.links.new(noise.outputs["Fac"], m2.inputs[1])
    nt.links.new(m2.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    # Build 3 sweeping galactic mist bands curving smoothly left & right out of the dome
    for b_idx, (dir_x, arc_z, spread_w) in enumerate([(-1.0, 4.8, 1.8), (0.85, 4.2, 1.5), (-0.35, 5.4, 2.0)]):
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")
        segs = 32
        prev = None
        for s in range(segs + 1):
            t = s / segs
            # Graceful galactic S-curve rising from dome slit and flowing into the night sky
            cx = dir_x * (12.5 * (t ** 1.35)) + math.sin(t * 4.5 + b_idx) * (0.9 * t)
            cy = 1.8 * t + math.cos(t * 3.5 + b_idx) * 0.5
            cz = -0.3 + arc_z * (1.0 - (1.0 - t) ** 1.8) + math.sin(t * math.pi) * 0.9
            w = 0.55 + spread_w * (t ** 0.85)
            va = bm.verts.new((cx, cy, cz - w))
            vb = bm.verts.new((cx, cy, cz + w))
            if prev is not None:
                f = bm.faces.new((prev[0], va, vb, prev[1]))
                u0, u1 = (s - 1) / segs, t
                f.loops[0][uv_layer].uv = (u0, 0.0)
                f.loops[1][uv_layer].uv = (u1, 0.0)
                f.loops[2][uv_layer].uv = (u1, 1.0)
                f.loops[3][uv_layer].uv = (u0, 1.0)
            prev = (va, vb)
        m = bpy.data.meshes.new(f"{name}_NebBand_{b_idx}")
        bm.to_mesh(m); bm.free()
        o = bpy.data.objects.new(f"{name}_NebBand_{b_idx}", m)
        o.data.materials.append(mat_neb)
        set_smooth(o)
        link_to_scene(scene, o)
        o.parent = root

    # 2. Dense sparkling river of 340+ tiny-to-medium starlight particles spiraling out of the dome!
    bm_pts = bmesh.new()
    bm_gold = bmesh.new()
    for i in range(340):
        t = rng.random() ** 0.78
        branch = -1.0 if (i % 3 != 0) else 0.85
        cx = branch * (14.0 * (t ** 1.30)) + math.sin(t * 5.0 + (i % 7)) * (0.9 * t)
        cy = 1.6 * t + rng.uniform(-1.0, 2.2) * t
        cz = -0.2 + 4.9 * (1.0 - (1.0 - t) ** 1.8) + math.sin(t * math.pi) * 0.9
        # Scatter radially around the galactic stream (tight at slit, starry swirl wider out!)
        jitter = 0.35 + 2.4 * (t ** 0.95)
        px = cx + rng.gauss(0, jitter * 0.65)
        py = cy + rng.gauss(0, jitter * 0.25)
        pz = cz + rng.gauss(0, jitter * 0.55)
        rad = rng.uniform(0.035, 0.11) * (1.2 - 0.5 * t)
        target_bm = bm_gold if (t < 0.35 or i % 4 == 0) else bm_pts
        ret = bmesh.ops.create_icosphere(target_bm, subdivisions=1, radius=rad)
        for v in ret["verts"]:
            v.co += Vector((px, py, pz))

    for tag, bm_cur, col, strength in (
        ("DustWhite", bm_pts, (0.92, 0.96, 1.0), 6.2),
        ("DustGold", bm_gold, (1.0, 0.93, 0.72), 8.2),
    ):
        mp = bpy.data.meshes.new(f"{name}_{tag}")
        bm_cur.to_mesh(mp); bm_cur.free()
        op = bpy.data.objects.new(f"{name}_{tag}", mp)
        op.data.materials.append(make_emission_mat(f"Mat_{tag}", col, strength=strength))
        link_to_scene(scene, op)
        op.parent = root

    # 3. Delicate crisp 4-pointed hero star flares twinkling along the galaxy arc!
    for i in range(44):
        t = rng.uniform(0.08, 1.0)
        branch = -1.0 if (i % 3 != 0) else 0.9
        sx = branch * (14.5 * t) + rng.uniform(-3.0, 3.0)
        sy = rng.uniform(1.0, 6.0)
        sz = 0.2 + 5.2 * (t ** 0.65) + rng.uniform(-1.6, 2.0)
        is_hero = (i % 6 == 0)
        make_star_diamond(
            scene, f"{name}_Star_{i}", (sx, sy, sz),
            size=rng.uniform(0.20, 0.38) if is_hero else rng.uniform(0.08, 0.16),
            color=(1.0, 0.97, 0.88) if is_hero else (0.90, 0.95, 1.0),
            strength=8.0 if is_hero else 4.2,
            parent=root
        )

    return root


def build_star_whale_and_aurora(scene, name="StarWhale", location=(2.0, 24.0, 9.5)):
    """Build a majestic smooth humpback Star Whale constellation with cosmic nebula fill, micro-stars, and 3-layer Aurora Borealis."""
    root = make_empty(scene, f"{name}_Root", location=location)

    # Smooth 30-point anatomical humpback whale silhouette (rounded whale head, sleek back, arching tail, crescent fluke, sweeping flipper!)
    nodes = [
        # 0..10: Smooth dorsal outline from tail peduncle -> sleek arched back -> broad rounded whale forehead -> blunt whale nose
        (-8.6, 0.0, 0.55),   # 0 tail peduncle top
        (-6.8, 0.0, 0.72),   # 1 slender tail stock
        (-4.6, 0.0, 1.15),   # 2 rear dorsal curve
        (-2.2, 0.0, 1.72),   # 3 subtle dorsal fin bump
        (0.2, 0.0, 2.20),    # 4 mid-back arch
        (2.8, 0.0, 2.48),    # 5 upper shoulder arch
        (5.2, 0.0, 2.38),    # 6 broad whale brow
        (7.1, 0.0, 1.88),    # 7 forehead curve
        (8.4, 0.0, 1.02),    # 8 upper rostrum
        (8.8, 0.0, 0.05),    # 9 blunt rounded whale nose
        (8.0, 0.0, -0.95),   # 10 rounded lower jaw front
        # 11..15: Smooth ventral belly curving cleanly back into the slender tail stock
        (6.0, 0.0, -1.78),   # 11 chin / pleated throat
        (3.4, 0.0, -2.18),   # 12 deep chest
        (0.4, 0.0, -1.92),   # 13 belly mid
        (-3.2, 0.0, -1.05),  # 14 lower rear flank
        (-6.5, 0.0, -0.15),  # 15 lower tail stock
        # 16..20: Sweeping crescent whale tail fluke!
        (-9.7, 0.0, 0.55),   # 16 fluke center notch
        (-10.4, 0.0, 2.05),  # 17 upper fluke mid
        (-11.8, 0.0, 3.35),  # 18 upper fluke tip
        (-9.6, 0.0, -1.15),  # 19 lower fluke mid
        (-10.6, 0.0, -2.55), # 20 lower fluke tip
        # 21..24: Iconic long sweeping humpback pectoral fin (gracefully curved backward!)
        (3.2, 0.0, -1.70),   # 21 flipper front root
        (0.8, 0.0, -3.25),   # 22 flipper leading curve
        (-2.4, 0.0, -4.45),  # 23 sweeping flipper tip
        (-0.3, 0.0, -2.25),  # 24 flipper trailing curve
        # 25..26: Subtle far-side upper flipper peeking over shoulder
        (-0.8, 0.0, 3.15),   # 25 far flipper tip
        (1.4, 0.0, 2.35),    # 26 far flipper front base
        # 27..30: Interior constellation guide stars (eye, heart, chest, mid-spine)
        (6.2, -0.18, 0.25),  # 27 whale eye star
        (3.2, -0.18, 0.45),  # 28 heart star
        (-0.6, -0.18, 0.42), # 29 mid-body spine star
        (-4.6, -0.18, 0.30), # 30 rear spine star
    ]

    edges = [
        # Outer smooth whale contour
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10),
        (10, 11), (11, 12), (12, 13), (13, 14), (14, 15), (15, 0),
        # Crescent tail fluke
        (0, 17), (17, 18), (18, 16), (16, 20), (20, 19), (19, 15), (0, 16),
        # Sweeping humpback pectoral fin
        (21, 22), (22, 23), (23, 24), (24, 13),
        # Subtle far-side flipper
        (3, 25), (25, 26),
        # Elegant internal celestial constellation lines
        (8, 27), (27, 6), (27, 10), (27, 11), (27, 28),
        (28, 5), (28, 12), (28, 21), (28, 29),
        (29, 4), (29, 3), (29, 13), (29, 30),
        (30, 2), (30, 14), (30, 1), (30, 15),
    ]

    # Rich glowing cosmic nebula fill inside the whale (periwinkle blue + soft lavender + glowing stardust veins!)
    mat_nebula = bpy.data.materials.new("Mat_WhaleNebula")
    mat_nebula.use_nodes = True
    mat_nebula.surface_render_method = "BLENDED"
    nt = mat_nebula.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.6
    mix = nt.nodes.new("ShaderNodeMixShader")
    tc = nt.nodes.new("ShaderNodeTexCoord")

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 0.35
    noise1.inputs["Detail"].default_value = 7.0
    noise1.inputs["Roughness"].default_value = 0.65
    nt.links.new(tc.outputs["Object"], noise1.inputs["Vector"])

    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.24, 0.32, 0.82, 1.0)
    emid = ramp.color_ramp.elements.new(0.55)
    emid.color = (0.56, 0.50, 0.96, 1.0)
    ramp.color_ramp.elements[2].position = 0.85
    ramp.color_ramp.elements[2].color = (0.84, 0.90, 1.0, 1.0)
    nt.links.new(noise1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], em.inputs["Color"])

    alpha_val = nt.nodes.new("ShaderNodeValue")
    alpha_val.outputs[0].default_value = 0.45

    amul = nt.nodes.new("ShaderNodeMath")
    amul.operation = "MULTIPLY"
    nt.links.new(alpha_val.outputs[0], amul.inputs[0])
    # Modulate nebula opacity softly so it looks cloud-like, not like solid paper
    n_map = nt.nodes.new("ShaderNodeMapRange")
    n_map.inputs["From Min"].default_value = 0.15
    n_map.inputs["From Max"].default_value = 0.85
    n_map.inputs["To Min"].default_value = 0.55
    n_map.inputs["To Max"].default_value = 1.15
    nt.links.new(noise1.outputs["Fac"], n_map.inputs["Value"])
    nt.links.new(n_map.outputs["Result"], amul.inputs[1])

    nt.links.new(amul.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

    # Clean triangulated whale body polygon mesh
    bm = bmesh.new()
    bverts = [bm.verts.new(p) for p in nodes]
    body_faces = [
        # Head & chest
        (6, 7, 27), (7, 8, 27), (8, 9, 27), (9, 10, 27), (10, 11, 27),
        (5, 6, 27, 28), (11, 12, 28, 27),
        # Mid torso
        (4, 5, 28, 29), (12, 13, 29, 28),
        # Rear body & slender tail
        (3, 4, 29), (2, 3, 29, 30), (13, 14, 30, 29),
        (1, 2, 30), (0, 1, 30, 15), (14, 15, 30),
        # Crescent tail fluke
        (0, 17, 16), (17, 18, 16), (0, 16, 15), (15, 16, 19), (19, 16, 20),
        # Sweeping pectoral flipper
        (21, 12, 13, 24), (21, 24, 22), (22, 24, 23),
        # Subtle far flipper
        (3, 25, 26, 4),
    ]
    for fidx in body_faces:
        bm.faces.new([bverts[i] for i in fidx])
    m_body = bpy.data.meshes.new(f"{name}_Body")
    bm.to_mesh(m_body); bm.free()
    whale_body = bpy.data.objects.new(f"{name}_Body", m_body)
    whale_body.data.materials.append(mat_nebula)
    link_to_scene(scene, whale_body)
    whale_body.parent = root

    # Delicate luminous constellation lines
    mat_line = bpy.data.materials.new("Mat_ConstellationLine")
    mat_line.use_nodes = True
    mat_line.surface_render_method = "BLENDED"
    ntl = mat_line.node_tree
    ntl.nodes.clear()
    outl = ntl.nodes.new("ShaderNodeOutputMaterial")
    transl = ntl.nodes.new("ShaderNodeBsdfTransparent")
    eml = ntl.nodes.new("ShaderNodeEmission")
    eml.inputs["Color"].default_value = (0.86, 0.93, 1.0, 1.0)
    eml.inputs["Strength"].default_value = 3.0
    mixl = ntl.nodes.new("ShaderNodeMixShader")
    line_alpha = ntl.nodes.new("ShaderNodeValue")
    line_alpha.outputs[0].default_value = 0.85
    ntl.links.new(line_alpha.outputs[0], mixl.inputs["Fac"])
    ntl.links.new(transl.outputs["BSDF"], mixl.inputs[1])
    ntl.links.new(eml.outputs["Emission"], mixl.inputs[2])
    ntl.links.new(mixl.outputs["Shader"], outl.inputs["Surface"])

    bm_lines = bmesh.new()
    for a, b in edges:
        pa, pb = Vector(nodes[a]), Vector(nodes[b])
        d = pb - pa
        perp = Vector((-d.z, 0, d.x)).normalized() * 0.032
        v0 = bm_lines.verts.new(pa - perp + Vector((0, -0.05, 0)))
        v1 = bm_lines.verts.new(pa + perp + Vector((0, -0.05, 0)))
        v2 = bm_lines.verts.new(pb + perp + Vector((0, -0.05, 0)))
        v3 = bm_lines.verts.new(pb - perp + Vector((0, -0.05, 0)))
        bm_lines.faces.new((v0, v1, v2, v3))
    m_lines = bpy.data.meshes.new(f"{name}_Lines")
    bm_lines.to_mesh(m_lines); bm_lines.free()
    whale_lines = bpy.data.objects.new(f"{name}_Lines", m_lines)
    whale_lines.data.materials.append(mat_line)
    link_to_scene(scene, whale_lines)
    whale_lines.parent = root

    # Star diamonds at constellation nodes (varied sizes so it feels celestial and organic!)
    star_objs = []
    major_idxs = {6, 9, 18, 20, 23, 25, 27, 28}
    for idx, pos in enumerate(nodes):
        is_major = idx in major_idxs
        sz = 0.48 if is_major else 0.20
        st = make_star_diamond(
            scene, f"{name}_Node_{idx}", (pos[0], pos[1] - 0.12, pos[2]),
            size=sz, color=(1.0, 0.98, 0.92), strength=8.5 if is_major else 3.8, parent=root
        )
        star_objs.append(st)

    # Embedded micro-stardust shimmering inside the whale's nebula body!
    rng_w = random.Random(77)
    bm_micro = bmesh.new()
    for _ in range(75):
        mx = rng_w.uniform(-7.0, 7.5)
        max_z = 1.8 * math.sqrt(max(0.02, 1.0 - ((mx - 1.5) / 8.5) ** 2))
        mz = rng_w.uniform(-max_z * 0.75, max_z * 0.85)
        ret = bmesh.ops.create_icosphere(bm_micro, subdivisions=1, radius=rng_w.uniform(0.035, 0.08))
        for v in ret["verts"]:
            v.co += Vector((mx, -0.08, mz))
    m_mic = bpy.data.meshes.new(f"{name}_MicroStars")
    bm_micro.to_mesh(m_mic); bm_micro.free()
    o_mic = bpy.data.objects.new(f"{name}_MicroStars", m_mic)
    o_mic.data.materials.append(make_emission_mat("Mat_WhaleMicro", (0.95, 0.97, 1.0), strength=6.5))
    link_to_scene(scene, o_mic)
    o_mic.parent = root

    # 3-layer shimmering Aurora Borealis curtains trailing organically behind the whale's tail!
    mat_aurora = bpy.data.materials.new("Mat_Aurora")
    mat_aurora.use_nodes = True
    mat_aurora.surface_render_method = "BLENDED"
    nta = mat_aurora.node_tree
    nta.nodes.clear()
    outa = nta.nodes.new("ShaderNodeOutputMaterial")
    transa = nta.nodes.new("ShaderNodeBsdfTransparent")
    ema = nta.nodes.new("ShaderNodeEmission")
    ema.inputs["Strength"].default_value = 3.6
    mixa = nta.nodes.new("ShaderNodeMixShader")

    tca = nta.nodes.new("ShaderNodeTexCoord")
    sepa = nta.nodes.new("ShaderNodeSeparateXYZ")
    nta.links.new(tca.outputs["UV"], sepa.inputs["Vector"])

    amap = nta.nodes.new("ShaderNodeMapping")
    amap.inputs["Scale"].default_value = (26.0, 0.65, 1.0)
    nta.links.new(tca.outputs["UV"], amap.inputs["Vector"])
    anoise = nta.nodes.new("ShaderNodeTexNoise")
    anoise.inputs["Scale"].default_value = 3.6
    anoise.inputs["Detail"].default_value = 6.0
    nta.links.new(amap.outputs["Vector"], anoise.inputs["Vector"])

    # Vivid emerald-aqua core -> cyan-blue -> ethereal lavender-violet rays!
    aramp = nta.nodes.new("ShaderNodeValToRGB")
    aramp.color_ramp.elements[0].position = 0.06
    aramp.color_ramp.elements[0].color = (0.12, 0.98, 0.76, 1.0)
    e_mid = aramp.color_ramp.elements.new(0.40)
    e_mid.color = (0.18, 0.68, 1.0, 1.0)
    aramp.color_ramp.elements[2].position = 0.86
    aramp.color_ramp.elements[2].color = (0.50, 0.26, 0.96, 1.0)
    nta.links.new(sepa.outputs["Y"], aramp.inputs["Fac"])
    nta.links.new(aramp.outputs["Color"], ema.inputs["Color"])

    # Soft vertical fade (glowing lower ribbon fading upward into wispy vertical rays)
    zf = nta.nodes.new("ShaderNodeValToRGB")
    zf.color_ramp.elements[0].position = 0.0
    zf.color_ramp.elements[0].color = (0, 0, 0, 1)
    zm = zf.color_ramp.elements.new(0.16)
    zm.color = (1, 1, 1, 1)
    zf.color_ramp.elements[2].position = 0.96
    zf.color_ramp.elements[2].color = (0, 0, 0, 1)
    nta.links.new(sepa.outputs["Y"], zf.inputs["Fac"])

    # Ultra-soft horizontal feathering at BOTH ends so zero boxy edges!
    xf = nta.nodes.new("ShaderNodeValToRGB")
    xf.color_ramp.elements[0].position = 0.0
    xf.color_ramp.elements[0].color = (0, 0, 0, 1)
    xm1 = xf.color_ramp.elements.new(0.28)
    xm1.color = (1, 1, 1, 1)
    xm2 = xf.color_ramp.elements.new(0.76)
    xm2.color = (1, 1, 1, 1)
    xf.color_ramp.elements[3].position = 1.0
    xf.color_ramp.elements[3].color = (0, 0, 0, 1)
    nta.links.new(sepa.outputs["X"], xf.inputs["Fac"])

    aurora_strength = nta.nodes.new("ShaderNodeValue")
    aurora_strength.outputs[0].default_value = 0.62

    amul0 = nta.nodes.new("ShaderNodeMath"); amul0.operation = "MULTIPLY"
    nta.links.new(zf.outputs["Color"], amul0.inputs[0]); nta.links.new(xf.outputs["Color"], amul0.inputs[1])
    amul1 = nta.nodes.new("ShaderNodeMath"); amul1.operation = "MULTIPLY"
    nta.links.new(amul0.outputs["Value"], amul1.inputs[0]); nta.links.new(anoise.outputs["Fac"], amul1.inputs[1])
    amul2 = nta.nodes.new("ShaderNodeMath"); amul2.operation = "MULTIPLY"
    nta.links.new(amul1.outputs["Value"], amul2.inputs[0]); nta.links.new(aurora_strength.outputs[0], amul2.inputs[1])

    nta.links.new(amul2.outputs["Value"], mixa.inputs["Fac"])
    nta.links.new(transa.outputs["BSDF"], mixa.inputs[1])
    nta.links.new(ema.outputs["Emission"], mixa.inputs[2])
    nta.links.new(mixa.outputs["Shader"], outa.inputs["Surface"])

    # 3 layered sinusoidal aurora ribbons weaving gracefully behind the whale's tail
    aurora_objs = []
    for l_idx, (x0, x1, y_off, z_off, height, phase) in enumerate([
        (-26.0, -9.2, 0.6, -1.2, 6.8, 0.0),
        (-23.5, -9.8, 1.8, -0.2, 5.8, 1.4),
        (-28.0, -11.5, -0.5, -1.8, 5.2, 2.7),
    ]):
        bm_au = bmesh.new()
        uv_layer = bm_au.loops.layers.uv.new("UVMap")
        segs_x = 36
        segs_z = 8
        grid_v = []
        for ix in range(segs_x + 1):
            u = ix / segs_x
            x = x0 + u * (x1 - x0)
            y = y_off + math.sin(u * 6.0 + phase) * 1.6
            base_z = z_off + math.sin(u * 4.5 + phase) * 1.45 + u * 0.9
            col = []
            for iz in range(segs_z + 1):
                v = iz / segs_z
                z = base_z + v * height * (0.65 + 0.35 * math.sin(u * math.pi))
                col.append(bm_au.verts.new((x, y, z)))
            grid_v.append(col)
        for ix in range(segs_x):
            for iz in range(segs_z):
                f = bm_au.faces.new((grid_v[ix][iz], grid_v[ix + 1][iz], grid_v[ix + 1][iz + 1], grid_v[ix][iz + 1]))
                u0, u1 = ix / segs_x, (ix + 1) / segs_x
                v0, v1 = iz / segs_z, (iz + 1) / segs_z
                f.loops[0][uv_layer].uv = (u0, v0)
                f.loops[1][uv_layer].uv = (u1, v0)
                f.loops[2][uv_layer].uv = (u1, v1)
                f.loops[3][uv_layer].uv = (u0, v1)
        m_au = bpy.data.meshes.new(f"{name}_Aurora_{l_idx}")
        bm_au.to_mesh(m_au); bm_au.free()
        ao = bpy.data.objects.new(f"{name}_Aurora_{l_idx}", m_au)
        ao.data.materials.append(mat_aurora)
        set_smooth(ao)
        link_to_scene(scene, ao)
        ao.parent = root
        aurora_objs.append(ao)

    return {
        "root": root,
        "body": whale_body,
        "lines": whale_lines,
        "stars": star_objs,
        "aurora": aurora_objs[0],
        "body_alpha": alpha_val.outputs[0],
        "line_alpha": line_alpha.outputs[0],
        "aurora_alpha": aurora_strength.outputs[0],
    }


def build_title_calligraphy(scene, font_path=r"C:\Windows\Fonts\simkai.ttf"):
    """Build the deep-indigo cobblestone backdrop, visible robot pincer hand, glowing starlight trail, and handwritten 'The Last Star' title."""
    # Deep painterly Voronoi flagstone shader (rich slate-blue stones with dark mortar crevices)
    mat_stones = bpy.data.materials.new("Mat_TitleStones")
    mat_stones.use_nodes = True
    nt = mat_stones.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")

    vor_edge = nt.nodes.new("ShaderNodeTexVoronoi")
    vor_edge.feature = "DISTANCE_TO_EDGE"
    vor_edge.inputs["Scale"].default_value = 1.15
    nt.links.new(tc.outputs["Object"], vor_edge.inputs["Vector"])

    vor_col = nt.nodes.new("ShaderNodeTexVoronoi")
    vor_col.feature = "F1"
    vor_col.inputs["Scale"].default_value = 1.15
    nt.links.new(tc.outputs["Object"], vor_col.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.5
    noise.inputs["Detail"].default_value = 6.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])

    stone_ramp = nt.nodes.new("ShaderNodeValToRGB")
    stone_ramp.color_ramp.elements[0].position = 0.1
    stone_ramp.color_ramp.elements[0].color = (0.08, 0.11, 0.22, 1.0)
    stone_ramp.color_ramp.elements[1].position = 0.9
    stone_ramp.color_ramp.elements[1].color = (0.19, 0.24, 0.40, 1.0)
    nt.links.new(vor_col.outputs["Color"], stone_ramp.inputs["Fac"])

    mortar_ramp = nt.nodes.new("ShaderNodeValToRGB")
    mortar_ramp.color_ramp.elements[0].position = 0.012
    mortar_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    mortar_ramp.color_ramp.elements[1].position = 0.038
    mortar_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(vor_edge.outputs["Distance"], mortar_ramp.inputs["Fac"])

    mix_m = nt.nodes.new("ShaderNodeMix")
    mix_m.data_type = "RGBA"
    mix_m.inputs["A"].default_value = (0.03, 0.04, 0.09, 1.0)
    nt.links.new(mortar_ramp.outputs["Color"], mix_m.inputs["Factor"])
    nt.links.new(stone_ramp.outputs["Color"], mix_m.inputs["B"])

    mix_n = nt.nodes.new("ShaderNodeMix")
    mix_n.data_type = "RGBA"
    mix_n.blend_type = "MULTIPLY"
    mix_n.inputs["Factor"].default_value = 0.35
    nt.links.new(mix_m.outputs["Result"], mix_n.inputs["A"])
    nt.links.new(noise.outputs["Color"], mix_n.inputs["B"])

    em.inputs["Strength"].default_value = 1.0
    nt.links.new(mix_n.outputs["Result"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=16, y_segments=10, size=10.0)
    m = bpy.data.meshes.new("TitleFloor")
    bm.to_mesh(m)
    bm.free()
    floor = bpy.data.objects.new("TitleFloor", m)
    floor.data.materials.append(mat_stones)
    link_to_scene(scene, floor)

    # Robot pincer hand clearly framed at bottom-left releasing the glowing star!
    hand_piv = make_empty(scene, "TitleHand", location=(-3.05, -1.35, 0.35))
    hand_piv.rotation_euler = (0, 0, 0.62)
    mat_white = make_painterly_mat("Mat_HandWhite", (0.84, 0.82, 0.76), shadow_color=(0.32, 0.34, 0.46), brush_scale=16.0)
    mat_teal = make_painterly_mat("Mat_HandTeal", (0.20, 0.56, 0.55), shadow_color=(0.08, 0.24, 0.30))
    mat_dark = make_painterly_mat("Mat_HandDark", (0.18, 0.20, 0.28), shadow_color=(0.06, 0.07, 0.14))

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.11, radius2=0.11, depth=2.2)
    m_arm = bpy.data.meshes.new("HandArm")
    bm.to_mesh(m_arm); bm.free()
    o_arm = bpy.data.objects.new("HandArm", m_arm)
    o_arm.location = (-1.1, 0, 0); o_arm.rotation_euler = (0, math.pi / 2, 0)
    o_arm.data.materials.append(mat_dark); link_to_scene(scene, o_arm); o_arm.parent = hand_piv

    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=18, radius1=0.20, radius2=0.20, depth=0.30)
    m_wr = bpy.data.meshes.new("HandWrist")
    bm.to_mesh(m_wr); bm.free()
    o_wr = bpy.data.objects.new("HandWrist", m_wr)
    o_wr.location = (0.05, 0, 0); o_wr.rotation_euler = (0, math.pi / 2, 0)
    o_wr.data.materials.append(mat_teal); link_to_scene(scene, o_wr); o_wr.parent = hand_piv

    for idx, dy, rz in ((0, 0.26, 0.22), (1, -0.26, -0.22)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=0.18)
        for v in bm.verts:
            v.co.x *= 2.5; v.co.y *= 1.0; v.co.z *= 0.6
        mc = bpy.data.meshes.new(f"HandClaw_{idx}")
        bm.to_mesh(mc); bm.free()
        oc = bpy.data.objects.new(f"HandClaw_{idx}", mc)
        oc.location = (0.58, dy, 0); oc.rotation_euler = (0, 0, rz)
        oc.data.materials.append(mat_white); set_smooth(oc); link_to_scene(scene, oc); oc.parent = hand_piv

    # Glowing star orb held in the pincer (rotated into X-Y plane for overhead camera!)
    star_orb = make_star_diamond(scene, "HandStarOrb", (-2.42, -0.88, 0.44), size=0.34, color=(1.0, 0.96, 0.85), strength=8.5)
    star_orb.rotation_euler = (math.pi / 2, 0, 0)

    # Flowing curved starlight wisp connecting the hand up into the 'T' of "The Last Star"
    curve_data = bpy.data.curves.new("TitleWispCurve", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.022
    curve_data.bevel_resolution = 4
    spline = curve_data.splines.new("BEZIER")
    wisp_pts = [
        (-2.42, -0.88, 0.44),
        (-2.55, 0.05, 0.44),
        (-2.38, 0.72, 0.44),
        (-2.02, 0.96, 0.44),
        (-1.62, 0.82, 0.44),
    ]
    spline.bezier_points.add(len(wisp_pts) - 1)
    for i, p in enumerate(wisp_pts):
        bp = spline.bezier_points[i]
        bp.co = p
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    wisp_obj = bpy.data.objects.new("TitleWisp", curve_data)
    wisp_obj.data.materials.append(make_emission_mat("Mat_Wisp", (1.0, 0.96, 0.84), strength=3.2))
    link_to_scene(scene, wisp_obj)

    # Handwritten glowing text with animated left-to-right reveal shader!
    try:
        font = bpy.data.fonts.load(font_path)
    except Exception:
        font = bpy.data.fonts.get("Bfont")

    def _make_reveal_text(tname, body, loc, size, reveal_val_name):
        tdata = bpy.data.curves.new(tname, "FONT")
        tdata.body = body
        tdata.align_x = "CENTER"
        tdata.align_y = "CENTER"
        tdata.size = size
        if font:
            tdata.font = font
        tobj = bpy.data.objects.new(tname, tdata)
        tobj.location = loc
        link_to_scene(scene, tobj)

        mat = bpy.data.materials.new(f"Mat_{tname}")
        mat.use_nodes = True
        mat.surface_render_method = "BLENDED"
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        trans = nt.nodes.new("ShaderNodeBsdfTransparent")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (1.0, 0.96, 0.86, 1.0)
        em.inputs["Strength"].default_value = 2.8
        mix = nt.nodes.new("ShaderNodeMixShader")

        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])

        rev_node = nt.nodes.new("ShaderNodeValue")
        rev_node.name = reveal_val_name
        rev_node.outputs[0].default_value = 0.0

        sub = nt.nodes.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        nt.links.new(rev_node.outputs[0], sub.inputs[0])
        nt.links.new(sep.outputs["X"], sub.inputs[1])

        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.use_clamp = True
        mul.inputs[1].default_value = 12.0
        nt.links.new(sub.outputs["Value"], mul.inputs[0])

        nt.links.new(mul.outputs["Value"], mix.inputs["Fac"])
        nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])

        tobj.data.materials.append(mat)
        return tobj, rev_node.outputs[0]

    title_obj, title_rev = _make_reveal_text("TitleMain", "最后一颗星", (0.58, 0.56, 0.45), 0.96, "RevealMain")
    sub_obj, sub_rev = _make_reveal_text("TitleSub", "每一片星空，都始于一束微光。", (0.58, -0.68, 0.45), 0.34, "RevealSub")

    # Small delicate sparkle stars over the stone floor (rotated flat for overhead camera!)
    rng = random.Random(99)
    for i in range(18):
        sp = make_star_diamond(
            scene, f"TitleSpark_{i}",
            (rng.uniform(-4.2, 4.2), rng.uniform(-2.2, 2.2), 0.35),
            size=rng.uniform(0.07, 0.16), strength=4.8
        )
        sp.rotation_euler = (math.pi / 2, 0, 0)

    return {
        "hand": hand_piv,
        "star_orb": star_orb,
        "wisp": wisp_obj,
        "title_rev": title_rev,
        "sub_rev": sub_rev,
    }
