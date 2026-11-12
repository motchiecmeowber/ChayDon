"""Sinh asset low-poly cho Chạy Đơn (bản 2, tham khảo phong cách Low Poly Worlds: cạnh vát, khối đa giác
lộ mặt, màu bão hòa mềm, nhiều chi tiết nhỏ). Hàng hóa 3 món x 3 trạng thái, nhà ống, xe shipper, xe máy AI,
cây, cột điện. Ô tô, xe buýt, xe tải dùng gói "Low Poly Cars" (Broken Vector); bàn ghế quán vỉa hè dùng gói
"Pho Dining Set" (AlleyBits) trên Unity Asset Store.
Chạy: blender --background --factory-startup --python tao_asset_lowpoly.py -- <thu_muc_goc_Art> [cu cong_trinh cong_vien hem duong]
Đơn vị 1 = 1 m; gốc tọa độ ở giữa đáy; mặt trước hướng -Y trong Blender.
Mọi model dùng chung một vật liệu và một ảnh bảng màu (Textures/BangMau_LowPoly.png): mỗi mặt lấy màu
bằng cách đặt UV vào ô màu tương ứng, nên Unity chỉ cần một material cho toàn bộ."""
import bpy, bmesh, sys, os, math, random, colorsys
from mathutils import Vector

ROOT = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(__file__)
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "XemTruoc")  # nơi lưu ảnh xem trước
os.makedirs(HERE, exist_ok=True)
PAL_PNG = os.path.join(ROOT, "Textures", "BangMau_LowPoly.png")

# Bảng màu sRGB; tường, đường, điểm nhấn lấy từ bảng màu 6.1.4 (sáng vắng / tan tầm)
HEX = {
    "vien": "2B2A33", "tuong_kem": "F2D7B6", "tuong_dao": "E9A98B", "tuong_mint": "A9D6C2", "tuong_vang": "F6D27A",
    "tuong_xanh": "A7CBE3", "trim": "FBF4E6", "ngoi": "C8623F", "ton": "4F8FA3", "kinh": "4E6A86", "kinh_sang": "A9D4EB",
    "sat": "3A3D46", "xam": "8C8E98", "xam_nhat": "C9CBD1", "la1": "63BF5E", "la2": "3E9B57", "la3": "9ACD5A",
    "than_cay": "7A5236", "dat": "B5643C", "nhan_do": "E76F51", "nhan_xanh": "3FA7D6", "vang": "FFD54F", "cam": "FF8A3D",
    "tim": "7E57C2", "da_nguoi": "F5CBA7", "quan": "3B4A6B", "banh": "26262B", "den_truoc": "FFF3B0", "den_sau": "E53935",
    "xanh_xe": "4A78C2", "la_dam": "3FA65A", "ly": "EEF4F7", "caphe": "5A3825", "caphe_nhat": "A47B5A", "da": "CFEFFF",
    "giay": "D7A86E", "hong": "F06292", "gom_trang": "F2EBDD", "gom_xanh": "2F6690", "duong": "63666B", "via_he": "D9C9B0",
    "bau_troi": "BFE3F2", "anh_sang": "FFE7A8",
    "be_tong": "D8D4CC", "kinh_xanh": "5FA3C4", "vang_phap": "F2C14E", "tuong_cu": "DCCBB0",
    "vo_dau": "A89A86", "co": "6DBA45", "gach": "C9785A", "do_dam": "C0392B", "nuoc": "4FB3D9",
    "nhua_hem": "74777C", "toc": "2A2420",
}
NAMES = list(HEX)
GRID = 8  # 8 x 8 ô, mỗi ô 16 px


TUOI = 1.3  # hệ số tăng độ bão hòa cho mọi màu có sắc (không áp cho màu xám, trắng, đen)


def srgb(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s > 0.12:
        s = min(1.0, s * TUOI + 0.04)
    return colorsys.hsv_to_rgb(hh, s, v)


def lin(h):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb(h))


def cell_uv(col):
    i = NAMES.index(col)
    return ((i % GRID + 0.5) / GRID, 1 - (i // GRID + 0.5) / GRID)


def make_palette():
    n = GRID * 16
    img = bpy.data.images.new("BangMau_LowPoly", n, n, alpha=False)
    px = [0.0] * (n * n * 4)
    for i, name in enumerate(NAMES):
        r, g, b = srgb(HEX[name])
        cx, cy = i % GRID, GRID - 1 - i // GRID  # hàng 0 của ảnh là đáy
        for y in range(cy * 16, cy * 16 + 16):
            for x in range(cx * 16, cx * 16 + 16):
                k = (y * n + x) * 4
                px[k:k + 4] = [r, g, b, 1.0]
    img.pixels = px
    os.makedirs(os.path.dirname(PAL_PNG), exist_ok=True)
    img.filepath_raw = PAL_PNG
    img.file_format = "PNG"
    img.save()
    print("BANG MAU", PAL_PNG)


def pal_mat():
    m = bpy.data.materials.get("BangMau_LowPoly")
    if m:
        return m
    m = bpy.data.materials.new("BangMau_LowPoly")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.85
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(PAL_PNG, check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    return m


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def paint(o, col):
    if not o.data.uv_layers:
        o.data.uv_layers.new(name="UVMap")
    u, v = cell_uv(col)
    for d in o.data.uv_layers.active.data:
        d.uv = (u, v)


def activate(o):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o


def fin(o, col, loc=(0, 0, 0), rot=None, bev=0.0, taper=None, jit=0.0, eul=None):
    """Hoàn thiện một khối: vuốt thon phần trên, vát cạnh, làm méo nhẹ cho khối hữu cơ, đặt vị trí, tô màu."""
    activate(o)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    me = o.data
    if taper:
        zs = [v.co.z for v in me.vertices]
        z0, z1 = min(zs), max(zs)
        for v in me.vertices:
            t = (v.co.z - z0) / (z1 - z0) if z1 > z0 else 0
            v.co.x *= 1 + (taper[0] - 1) * t
            v.co.y *= 1 + (taper[1] - 1) * t
            if len(taper) > 2:
                v.co.y += taper[2] * t
    if bev > 0:
        md = o.modifiers.new("vat", "BEVEL")
        md.width, md.segments, md.limit_method, md.angle_limit = bev, 1, "ANGLE", math.radians(40)
        bpy.ops.object.modifier_apply(modifier=md.name)
    if jit > 0:
        for v in me.vertices:
            v.co += Vector((random.uniform(-jit, jit), random.uniform(-jit, jit), random.uniform(-jit, jit)))
    o.location = loc
    if eul is not None:
        o.rotation_euler = eul
    elif rot:
        o.rotation_euler = [math.radians(a) for a in rot]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    paint(o, col)
    return o


def box(s, loc, col, rot=None, bev=0.0, taper=None, jit=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.scale = s
    return fin(o, col, loc, rot, bev, taper, jit)


def cyl(r, h, loc, col, v=8, rot=None, r2=None, bev=0.0, jit=0.0):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r, radius2=r2, depth=h)
    return fin(bpy.context.active_object, col, loc, rot, bev, None, jit)


def ball(r, loc, col, sub=1, scale=(1, 1, 1), jit=0.0, rot=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r)
    o = bpy.context.active_object
    o.scale = scale
    return fin(o, col, loc, rot, 0, None, jit)


def torus(R, r, loc, col, rot=None, jit=0.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=10, minor_segments=5)
    return fin(bpy.context.active_object, col, loc, rot, 0, None, jit)


def limb(a, b, t, col, bev=0.02):
    """Khối hộp nối hai điểm a, b (tay, chân, cành)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.active_object
    o.scale = (t, t, d.length + t * 0.5)
    return fin(o, col, (a + b) / 2, bev=bev, eul=d.to_track_quat("Z", "Y").to_euler())


def lathe(prof, col, seg=12, loc=(0, 0, 0), caps=(True, False), jit=0.0, rot=None, twist=0.0):
    """Tiện tròn một biên dạng [(bán kính, cao), ...] quanh trục Z."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * math.cos(i / seg * math.tau + twist), r * math.sin(i / seg * math.tau + twist), z))
                      for i in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if caps[0]:
        bm.faces.new(list(reversed(rings[0])))
    if caps[1]:
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("tien")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("tien", me)
    bpy.context.scene.collection.objects.link(o)
    return fin(o, col, loc, rot, 0, None, jit)


def done(name, folder, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    o.data.materials.clear()
    o.data.materials.append(pal_mat())
    for poly in o.data.polygons:
        poly.use_smooth = False
    d = os.path.join(ROOT, folder)
    os.makedirs(d, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(d, name + ".fbx"), use_selection=False,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             bake_space_transform=True, object_types={"MESH"}, mesh_smooth_type="FACE",
                             path_mode="RELATIVE")
    print("XUAT", folder, name, len(o.data.polygons), "mat")


# ---------- Hàng hóa (kích thước thật, khoảng 0,1–0,35 m) ----------
def caphe(state):
    reset()
    random.seed(10 + state)
    cup_r = lambda z: 0.042 + 0.013 * z / 0.15
    p = [lathe([(0.040, 0), (0.042, 0.004), (0.055, 0.15), (0.058, 0.152), (0.058, 0.157)], "ly", seg=14)]
    p.append(lathe([(cup_r(0.06) + 0.0015, 0.06), (cup_r(0.10) + 0.0015, 0.10)], "nhan_do", seg=14, caps=(False, False)))
    level = {0: 0.148, 1: 0.12, 2: 0.05}[state]
    p.append(lathe([(0.038, 0.004), (cup_r(level) - 0.0005, level)], "caphe" if state == 0 else "caphe_nhat",
                   seg=14, caps=(True, True)))
    for i in range({0: 4, 1: 2, 2: 0}[state]):
        s = 0.026 if state == 0 else 0.016
        p.append(box((s, s, s), (random.uniform(-0.018, 0.018), random.uniform(-0.018, 0.018), level + 0.004 + i * 0.003),
                     "da", rot=(random.uniform(0, 40), random.uniform(0, 40), random.uniform(0, 90)), bev=0.003))
    tilt = {0: 12, 1: 16, 2: 32}[state]
    p.append(cyl(0.0045, 0.22, (0.018, 0, 0.14), "nhan_xanh", v=6, rot=(0, tilt, 0)))
    if state == 2:  # cà phê đổ ra mặt đất
        p.append(cyl(0.085, 0.004, (0.11, -0.02, 0.002), "caphe", v=9, jit=0.012))
    done(f"CaPhe_{['Nguyen', 'HuMotPhan', 'SapHong'][state]}", "Models/HangHoa", p)


def bohoa(state):
    reset()
    random.seed(20 + state)
    pj = {0: 0.0, 1: 0.004, 2: 0.012}[state]
    p = [lathe([(0.02, 0), (0.03, 0.03), (0.10, 0.26), (0.115, 0.29)], "giay", seg=8, jit=pj),
         lathe([(0.035, 0.17), (0.11, 0.30), (0.13, 0.33)], "trim", seg=7, caps=(False, False), twist=0.4, jit=pj)]
    kr = lambda z: 0.03 + 0.07 * (z - 0.03) / 0.23
    p.append(lathe([(kr(0.10) + 0.003, 0.10), (kr(0.125) + 0.003, 0.125)], "nhan_do", seg=8, caps=(False, False)))
    p.append(box((0.03, 0.012, 0.05), (0.0, -kr(0.11) - 0.008, 0.095), "nhan_do", rot=(0, 25, 0), bev=0.003))
    p.append(box((0.03, 0.012, 0.05), (0.02, -kr(0.11) - 0.008, 0.09), "nhan_do", rot=(0, -25, 0), bev=0.003))
    spots = [(0, 0)] + [(0.06 * math.cos(i / 5 * math.tau), 0.06 * math.sin(i / 5 * math.tau)) for i in range(5)]
    cols = ["hong", "vang", "hong", "trim", "hong", "vang"]
    out = {0: 1.0, 1: 1.25, 2: 1.6}[state]
    drop = {0: 0.0, 1: 0.02, 2: 0.07}[state]
    for i, (x, y) in enumerate(spots):
        z = 0.33 + (0.02 if i == 0 else 0) - drop * (0 if i == 0 else 1)
        sq = 0.75 if state < 2 else 0.5
        p.append(ball(0.042, (x * out, y * out, z), cols[i], scale=(1, 1, sq), jit=0.005))
        p.append(ball(0.014, (x * out, y * out, z + 0.03 * sq), "vien" if cols[i] == "vang" else "vang"))
    for i in range(6):  # lá
        a = (i + 0.5) / 6 * math.tau
        lean = 35 + (25 if state == 2 else 0)
        p.append(cyl(0.024, 0.11, (0.09 * math.cos(a), 0.09 * math.sin(a), 0.29), "la2" if i % 2 else "la1", v=4, r2=0.0,
                     rot=(lean * -math.sin(a), lean * math.cos(a), 0)))
    for i in range({0: 0, 1: 1, 2: 4}[state]):  # cánh hoa rơi
        p.append(ball(0.016, (random.uniform(-0.14, 0.14), random.uniform(-0.14, 0.14), 0.004), "hong", scale=(1, 1, 0.25)))
    done(f"BoHoa_{['Nguyen', 'HuMotPhan', 'SapHong'][state]}", "Models/HangHoa", p)


def gom(state):
    reset()
    random.seed(30 + state)
    prof = [(0.05, 0), (0.075, 0.03), (0.095, 0.09), (0.088, 0.15), (0.05, 0.20), (0.036, 0.235), (0.048, 0.255), (0.05, 0.26)]
    if state < 2:
        p = [lathe(prof, "gom_trang", seg=12), cyl(0.034, 0.004, (0, 0, 0.255), "vien", v=12)]
        p.append(lathe([(0.0375, 0.228), (0.0365, 0.238)], "gom_xanh", seg=12, caps=(False, False), loc=(0, 0, 0)))
        for i in range(6):  # họa tiết cánh sen xanh quanh thân
            a = i / 6 * math.tau
            p.append(ball(0.03, (0.093 * math.cos(a), 0.093 * math.sin(a), 0.115), "gom_xanh", scale=(0.35, 0.8, 1.2),
                          rot=(0, 0, math.degrees(a))))
    else:  # vỡ: còn nửa dưới, miệng răng cưa, mảnh vỡ dưới đất
        p = [lathe(prof[:3] + [(0.093, 0.12)], "gom_trang", seg=12, jit=0.004), cyl(0.088, 0.003, (0, 0, 0.1), "vien", v=12)]
        for i in range(5):
            a = random.uniform(0, math.tau)
            d = random.uniform(0.15, 0.24)
            p.append(ball(0.03, (d * math.cos(a), d * math.sin(a), 0.006), "gom_trang" if i % 2 else "gom_xanh",
                          scale=(1.2, 0.8, 0.25), jit=0.008, rot=(0, 0, random.uniform(0, 180))))
        p.append(lathe(prof[4:], "gom_trang", seg=12, loc=(-0.06, 0.2, 0.05), rot=(90, 0, 25)))
    p.append(lathe([(0.0952, 0.085), (0.0948, 0.097)], "gom_xanh", seg=12, caps=(False, False)) if state < 2 else
             lathe([(0.0952, 0.085), (0.0948, 0.097)], "gom_xanh", seg=12, caps=(False, False), jit=0.002))
    p.append(lathe([(0.0615, 0.012), (0.067, 0.02)], "gom_xanh", seg=12, caps=(False, False)))
    if state == 1:  # vết nứt zigzag mặt trước
        pts = [(0.02, 0.17), (0.0, 0.14), (0.025, 0.11), (0.005, 0.075), (0.02, 0.045)]
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            y0 = -math.sqrt(max(0.0, 0.094 ** 2 - x0 ** 2)) - 0.001
            y1 = -math.sqrt(max(0.0, 0.094 ** 2 - x1 ** 2)) - 0.001
            p.append(limb((x0, y0, z0), (x1, y1, z1), 0.005, "vien", bev=0))
    done(f"BinhGom_{['Nguyen', 'Nut', 'Vo'][state]}", "Models/HangHoa", p)


# ---------- Nhà ống (rộng 4 m, sâu 10 m, mặt tiền ở y = 0 quay về -Y) ----------
def chau_cay(x, y, z, s=1.0):
    return [cyl(0.15 * s, 0.3 * s, (x, y, z + 0.15 * s), "dat", v=7, r2=0.19 * s, bev=0.01),
            ball(0.25 * s, (x, y, z + 0.42 * s), "la1", jit=0.04 * s, scale=(1, 1, 0.85)),
            ball(0.16 * s, (x + 0.12 * s, y - 0.05, z + 0.55 * s), "la2", jit=0.03 * s)]


def nha(idx, floors, wall, awn, shutter, roof):
    reset()
    random.seed(40 + idx)
    W, D, F = 4.0, 10.0, 3.2
    H = floors * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04)]
    # Tầng trệt: cột, khoảng cửa hàng tối, cửa cuốn kéo lưng chừng, tấm bạt sọc
    for s in (-1, 1):
        p.append(box((0.32, 0.22, F), (s * (W / 2 - 0.16), -0.1, F / 2), "trim", bev=0.03))
    p.append(box((W - 0.64, 0.1, 2.6), (0, -0.02, 1.3), "sat"))
    p.append(box((W - 0.64, 0.14, 0.75), (0, -0.05, 2.25), "xam_nhat", bev=0.02))
    for k in range(4):
        p.append(box((W - 0.64, 0.16, 0.03), (0, -0.05, 1.95 + k * 0.18), "xam"))
    p.append(box((1.0, 0.6, 0.7), (-1.0, -0.4, 0.35), "kinh", bev=0.03))  # tủ kính bày hàng
    p.append(box((1.06, 0.66, 0.06), (-1.0, -0.4, 0.73), "trim", bev=0.02))
    n = 8
    for k in range(n):
        x = -W / 2 + (k + 0.5) * W / n
        c = awn[k % 2]
        p.append(box((W / n + 0.002, 1.5, 0.05), (x, -0.7, 2.62), c, rot=(22, 0, 0)))
        p.append(box((W / n + 0.002, 0.04, 0.22), (x, -1.4, 2.25), c))
    # Các tầng trên
    for f in range(1, floors):
        z = f * F
        p.append(box((W + 0.04, 0.08, 0.14), (0, -0.02, z - 0.1), "trim"))
        p.append(box((W, 1.0, 0.16), (0, -0.5, z), "trim", bev=0.03))
        if f == 1:  # biển hiệu trên lan can tầng 2
            p.append(box((W - 0.1, 0.14, 0.9), (0, -1.02, z + 0.55), awn[0], bev=0.04))
            p.append(box((W - 0.4, 0.04, 0.6), (0, -1.1, z + 0.55), "trim", bev=0.01))
            for k, w in enumerate((0.5, 0.35, 0.6, 0.4)):
                p.append(box((w, 0.03, 0.22), (-1.2 + k * 0.8, -1.13, z + 0.55), awn[0] if k != 2 else "vien"))
        else:
            p.append(box((W, 0.07, 0.07), (0, -0.97, z + 0.95), "sat", bev=0.01))
            for k in range(19):
                p.append(box((0.03, 0.03, 0.85), (-W / 2 + 0.1 + k * 0.2, -0.97, z + 0.5), "sat"))
        for x in (-0.9, 0.9):  # cửa sổ: khung, kính, chớp hai bên
            p.append(box((1.2, 0.06, 2.1), (x, -0.02, z + 1.2), "trim", bev=0.02))
            p.append(box((0.95, 0.1, 1.85), (x, -0.03, z + 1.15), "kinh"))
            p.append(box((0.04, 0.12, 1.85), (x, -0.04, z + 1.15), "trim"))
        for x in (-1.75, -0.05, 0.05, 1.75):
            p.append(box((0.22, 0.06, 1.85), (x + (0.1 if x < 0 and x > -1 else 0) - (0.1 if 0 < x < 1 else 0), -0.06, z + 1.15),
                         shutter, bev=0.01))
        if (f + idx) % 2 == 0:  # cục nóng máy lạnh
            p.append(box((0.8, 0.32, 0.55), (1.35, -0.18, z + 2.7), "trim", bev=0.03))
            p.append(cyl(0.18, 0.04, (1.47, -0.35, z + 2.7), "xam", v=10, rot=(90, 0, 0)))
            p.append(cyl(0.05, 0.05, (1.47, -0.37, z + 2.7), "sat", v=6, rot=(90, 0, 0)))
        if f > 1 or floors == 2:
            p += chau_cay(-1.5 + random.uniform(0, 0.3), -0.75, z + 0.08, 1.0)
            if random.random() < 0.6:
                p += chau_cay(1.4, -0.7, z + 0.08, 0.8)
    # Mái: sàn mái, lan can mái, bồn nước inox hoặc mái tôn
    p.append(box((W + 0.1, D + 0.1, 0.2), (0, D / 2, H + 0.1), "trim", bev=0.04))
    p.append(box((W + 0.1, 0.18, 0.7), (0, 0.04, H + 0.55), wall, bev=0.04))
    p.append(box((W + 0.14, 0.24, 0.08), (0, 0.04, H + 0.92), "trim", bev=0.02))
    if roof == "bon":
        p.append(cyl(0.5, 1.2, (0.8, 2.2, H + 1.05), "xam_nhat", v=10, rot=(0, 90, 0), bev=0.03))
        for x in (0.35, 1.25):
            p.append(box((0.08, 0.8, 0.5), (x, 2.2, H + 0.45), "sat"))
        p += chau_cay(-1.2, 1.0, H + 0.2, 1.2)
    else:
        p.append(box((W + 0.3, 3.5, 0.08), (0, 3.6, H + 1.2), roof, rot=(-14, 0, 0), bev=0.02))
        for x in (-1.8, 1.8):
            p.append(box((0.1, 0.1, 1.1), (x, 2.3, H + 0.75), "sat"))
    done(f"NhaOng_{idx}", "Models/Pho", p)


# ---------- Xe máy tay ga và người lái (đầu xe hướng -Y) ----------
def xe_may(name, folder, body, helmet, shirt, cargo=False, rider=True):
    reset()
    p = []
    for y in (-0.62, 0.58):
        p.append(cyl(0.26, 0.11, (0, y, 0.26), "banh", v=12, rot=(0, 90, 0), bev=0.02))
        p.append(cyl(0.13, 0.125, (0, y, 0.26), "xam_nhat", v=8, rot=(0, 90, 0)))
    p += [box((0.16, 0.45, 0.06), (0, -0.62, 0.55), body, bev=0.02),
          box((0.42, 0.14, 0.62), (0, -0.42, 0.66), body, rot=(-15, 0, 0), taper=(0.7, 1), bev=0.04),
          box((0.36, 0.48, 0.08), (0, -0.12, 0.32), "sat", bev=0.02),
          box((0.40, 0.75, 0.38), (0, 0.33, 0.55), body, taper=(0.8, 0.9), bev=0.06),
          box((0.32, 0.62, 0.10), (0, 0.25, 0.79), "vien", bev=0.04),
          box((0.26, 0.20, 0.18), (0, -0.48, 1.0), body, bev=0.04),
          box((0.14, 0.04, 0.08), (0, -0.59, 1.0), "den_truoc", bev=0.01),
          cyl(0.016, 0.62, (0, -0.44, 1.06), "sat", v=6, rot=(0, 90, 0)),
          box((0.2, 0.04, 0.07), (0, 0.71, 0.66), "den_sau", bev=0.01),
          cyl(0.04, 0.35, (0.2, 0.45, 0.3), "xam_nhat", v=8, rot=(90, 0, 0))]
    for s in (-1, 1):
        p.append(cyl(0.024, 0.1, (s * 0.28, -0.44, 1.06), "vien", v=6, rot=(0, 90, 0)))
        p.append(limb((s * 0.18, -0.44, 1.06), (s * 0.22, -0.46, 1.22), 0.015, "sat", bev=0))
        p.append(cyl(0.045, 0.015, (s * 0.22, -0.47, 1.24), "kinh_sang", v=8, rot=(90, 0, 0)))
    if not rider:  # xe đậu: chân chống nghiêng, mũ bảo hiểm móc trên gương
        p.append(limb((-0.12, 0.15, 0.25), (-0.3, 0.2, 0.0), 0.03, "sat", bev=0))
        p.append(ball(0.13, (0.24, -0.47, 1.12), helmet, sub=2, scale=(1, 1.1, 0.85)))
    else:  # người lái
        for s in (-1, 1):
            p.append(limb((s * 0.11, 0.3, 0.9), (s * 0.12, -0.14, 0.9), 0.15, "quan"))
            p.append(limb((s * 0.12, -0.14, 0.9), (s * 0.12, -0.2, 0.42), 0.12, "quan"))
            p.append(box((0.12, 0.22, 0.08), (s * 0.12, -0.25, 0.4), "vien", bev=0.02))
            p.append(limb((s * 0.2, 0.22, 1.33), (s * 0.27, -0.4, 1.07), 0.1, shirt))
            p.append(ball(0.045, (s * 0.28, -0.44, 1.07), "da_nguoi"))
        p.append(box((0.38, 0.24, 0.5), (0, 0.25, 1.15), shirt, rot=(10, 0, 0), taper=(1.12, 1), bev=0.05))
        p.append(ball(0.11, (0, 0.18, 1.5), "da_nguoi", sub=2))
        p.append(ball(0.135, (0, 0.2, 1.55), helmet, sub=2, scale=(1, 1.1, 0.85)))
        p.append(box((0.2, 0.09, 0.02), (0, 0.06, 1.55), helmet, bev=0.005))
        p.append(box((0.18, 0.02, 0.05), (0, 0.075, 1.5), "vien"))  # kính chắn gió mini
    if cargo:  # thùng giao hàng
        p += [box((0.36, 0.3, 0.03), (0, 0.62, 0.84), "sat"),
              box((0.46, 0.42, 0.42), (0, 0.62, 1.07), "vang", bev=0.03),
              box((0.47, 0.43, 0.07), (0, 0.62, 1.02), "cam", bev=0.01),
              box((0.48, 0.44, 0.04), (0, 0.62, 1.29), "vien", bev=0.01),
              cyl(0.08, 0.01, (0, 0.835, 1.15), "trim", v=10, rot=(90, 0, 0))]
    done(name, folder, p)


# ---------- Đồ dựng phố ----------
def cay(idx):
    reset()
    random.seed(60 + idx)
    h = 2.6 if idx == 1 else 4.6
    p = [cyl(0.16, h, (0, 0, h / 2), "than_cay", v=6, r2=0.1, jit=0.02)]
    for s in (-1, 1):
        p.append(limb((0, 0, h * 0.75), (s * 0.6, 0.1 * s, h + 0.3), 0.09, "than_cay", bev=0))
    blobs = [(0, 0, h + 0.7, 1.1), (0.7, 0.2, h + 0.3, 0.8), (-0.7, -0.1, h + 0.35, 0.85), (0.1, -0.5, h + 0.2, 0.7),
             (0.2, 0.3, h + 1.4, 0.75)]
    if idx == 2:
        blobs += [(0, 0, h + 2.0, 0.6), (-0.4, 0.3, h - 0.4, 0.6)]
    for i, (x, y, z, r) in enumerate(blobs):
        p.append(ball(r, (x, y, z), ["la1", "la2", "la3"][i % 3], sub=1, jit=r * 0.12, scale=(1, 1, 0.85)))
    for x, y, sx, sy in ((0, -0.6, 1.3, 0.1), (0, 0.6, 1.3, 0.1), (-0.6, 0, 0.1, 1.1), (0.6, 0, 0.1, 1.1)):
        p.append(box((sx, sy, 0.12), (x, y, 0.06), "xam", bev=0.02))  # bó gốc cây
    p.append(box((1.1, 1.1, 0.04), (0, 0, 0.02), "dat"))
    done(f"CayXanh_{idx}", "Models/Pho", p)


def cot_dien():
    reset()
    random.seed(70)
    p = [box((0.26, 0.26, 8.0), (0, 0, 4.0), "xam_nhat", taper=(0.6, 0.6), bev=0.02)]
    for z, w in ((7.4, 1.8), (6.8, 1.3)):
        p.append(box((w, 0.1, 0.1), (0, 0, z), "sat", bev=0.01))
        for x in (-w / 2 + 0.1, w / 2 - 0.1):
            p.append(cyl(0.05, 0.14, (x, 0, z + 0.12), "trim", v=6))
    for i, z in enumerate((5.2, 5.0, 4.7)):  # búi dây điện đặc trưng
        p.append(torus(0.32 + i * 0.06, 0.05, (0.05 * i, 0, z), "vien", rot=(random.uniform(-25, 25), random.uniform(-25, 25), 0),
                       jit=0.04))
    p.append(box((0.32, 0.22, 0.45), (0, -0.22, 2.9), "xam", bev=0.03))
    p.append(box((0.34, 0.24, 0.05), (0, -0.22, 3.15), "sat"))
    done("CotDien", "Models/Pho", p)


# ---------- Công trình lớn Quận 1 (mặt tiền ở y = 0 quay về -Y, gốc ở giữa mép mặt tiền) ----------
def cao_oc_kinh():
    """Cao ốc văn phòng: chân đế 2 tầng, thân kính thon dần, đỉnh bậc và cột ăng-ten. Rộng 20 m, cao ~75 m."""
    reset()
    p = [box((20, 18, 8), (0, 9, 4), "be_tong", bev=0.1),
         box((18, 0.1, 5), (0, -0.05, 2.8), "kinh_sang"),
         box((10, 3, 0.25), (0, -1.5, 5.6), "trim", bev=0.05),
         box((6, 0.2, 1.2), (0, -0.1, 7), "nhan_xanh", bev=0.03)]
    for x in (-4.5, 4.5):
        p.append(cyl(0.15, 5.5, (x, -2.8, 2.75), "sat", v=6))
    H = 56
    p.append(box((14, 14, H), (0, 9, 8 + H / 2), "kinh_xanh", taper=(0.88, 0.88), bev=0.15))
    for k in range(1, 14):  # dải sàn mỗi 4 m
        w = 14 * (1 - 0.12 * k * 4 / H)
        p.append(box((w + 0.2, w + 0.2, 0.3), (0, 9, 8 + k * 4), "trim"))
    p += [box((11.5, 11.5, 3), (0, 9, 8 + H + 1.5), "trim", taper=(0.7, 0.7), bev=0.1),
          cyl(0.25, 8, (0, 9, 8 + H + 7), "xam_nhat", v=6, r2=0.05),
          ball(0.35, (0, 9, 8 + H + 11), "den_sau")]
    done("CaoOc_Kinh", "Models/Pho", p)


def chung_cu_cu():
    """Chung cư cũ 9 tầng: mỗi căn một ban công màu riêng (quán cà phê, cửa hàng), tầng trệt cửa hàng có bạt."""
    reset()
    random.seed(80)
    W, D, F, n = 20.0, 14.0, 3.2, 9
    H = n * F
    p = [box((W, D, H), (0, D / 2, H / 2), "tuong_cu", bev=0.06)]
    mau = ["sat", "trim", "vang", "nhan_do", "la_dam", "nhan_xanh", "tim", "cam"]
    for i in range(5):
        x = -8 + 4 * i
        c = random.choice(["nhan_do", "vang", "nhan_xanh", "la1"])
        p += [box((3.4, 0.1, 2.5), (x, -0.03, 1.25), "sat"),
              box((3.6, 1.4, 0.06), (x, -0.7, 2.75), c, rot=(18, 0, 0)),
              box((3.0, 0.12, 0.45), (x, -0.08, 3.0 - 0.1), c, bev=0.02)]
    for f in range(1, n):
        z = f * F
        p.append(box((W + 0.05, 0.1, 0.18), (0, -0.04, z - 0.1), "trim"))
        for i in range(5):
            x = -8 + 4 * i
            p += [box((3.4, 1.0, 0.12), (x, -0.5, z), "trim"),
                  box((3.4, 0.06, 0.9), (x, -0.98, z + 0.5), random.choice(mau), bev=0.01),
                  box((2.0, 0.1, 2.2), (x, -0.03, z + 1.2), "kinh")]
            r = random.random()
            if r < 0.35:
                p += chau_cay(x - 1.1, -0.65, z + 0.06, 0.6)
            elif r < 0.6:
                p.append(box((3.4, 1.1, 0.05), (x, -0.55, z + 2.6), random.choice(["nhan_do", "vang", "la_dam"]), rot=(15, 0, 0)))
            elif r < 0.8:
                p.append(box((0.7, 0.3, 0.5), (x + 1.2, -0.18, z + 2.5), "trim", bev=0.03))
    for x in (-5, 5):  # bồn nước và lan can mái
        p.append(cyl(0.6, 1.4, (x, 4, H + 1.0), "xam_nhat", v=10, rot=(0, 90, 0)))
        p.append(box((1.4, 0.6, 0.4), (x, 4, H + 0.2), "sat"))
    p.append(box((W, 0.2, 0.8), (0, 0.1, H + 0.4), "tuong_cu"))
    p.append(cyl(0.05, 4, (7, 8, H + 2), "sat", v=5))
    done("ChungCu_Cu", "Models/Pho", p)


def phap_thuoc():
    """Công trình kiểu Pháp thuộc: tường vàng, cột trắng, cửa sổ vòm, cửa chớp xanh, mái ngói, gian giữa có đồng hồ."""
    reset()
    W, D, F, b = 32.0, 14.0, 4.5, 0.8
    p = [box((W + 0.6, D + 0.6, b), (0, D / 2, b / 2), "xam", bev=0.05),
         box((W, D, 2 * F), (0, D / 2, b + F), "vang_phap", bev=0.05),
         box((W + 0.3, D + 0.3, 0.35), (0, D / 2, b + F), "trim"),
         box((W + 0.4, D + 0.4, 0.45), (0, D / 2, b + 2 * F), "trim"),
         box((W, D, 2.6), (0, D / 2, b + 2 * F + 1.5), "ngoi", taper=(0.9, 0.5))]

    def cua_so(x, y, z):
        return [box((1.2, 0.12, 2.3), (x, y, z + 1.35), "kinh"),
                cyl(0.6, 0.12, (x, y, z + 2.5), "kinh", v=10, rot=(90, 0, 0)),
                box((1.6, 0.14, 0.18), (x, y - 0.01, z + 0.15), "trim"),
                box((0.35, 0.1, 2.3), (x - 0.82, y - 0.02, z + 1.35), "la_dam"),
                box((0.35, 0.1, 2.3), (x + 0.82, y - 0.02, z + 1.35), "la_dam")]
    for s in (-1, 1):  # hai cánh
        for k in range(4):
            x = s * (6.5 + k * 2.9)
            p.append(box((0.45, 0.3, 2 * F), (x - s * 1.45, -0.1, b + F), "trim"))
            for f in range(2):
                p += cua_so(x, -0.06, b + f * F + 0.4)
        p.append(box((9.5, 0.9, 0.9), (s * 11, -1.3, 0.45), "la2", jit=0.06))
    # Gian giữa nhô ra 1,5 m, cao 3 tầng, mái mansard và đồng hồ
    Hc = 3 * F
    p += [box((10, D + 1.5, Hc), (0, (D + 1.5) / 2 - 1.5, b + Hc / 2), "vang_phap", bev=0.05),
          box((10.4, D + 1.9, 0.45), (0, (D + 1.5) / 2 - 1.5, b + Hc), "trim"),
          box((10, 9, 3.2), (0, 5, b + Hc + 1.6), "ton", taper=(0.72, 0.72), bev=0.05),
          cyl(0.15, 2.5, (0, 5, b + Hc + 4.4), "sat", v=6),
          cyl(1.2, 0.2, (0, -1.62, b + 2 * F + 2.2), "trim", v=16, rot=(90, 0, 0)),
          cyl(1.4, 0.15, (0, -1.56, b + 2 * F + 2.2), "vien", v=16, rot=(90, 0, 0)),
          limb((0, -1.75, b + 2 * F + 2.2), (0, -1.75, b + 2 * F + 2.9), 0.08, "vien", bev=0),
          limb((0, -1.75, b + 2 * F + 2.2), (0.5, -1.75, b + 2 * F + 2.2), 0.08, "vien", bev=0)]
    for x in (-3.4, 3.4):
        p.append(box((0.5, 0.3, Hc), (x, -1.65, b + Hc / 2), "trim"))
        p += cua_so(x * 0.6, -1.56, b + F + 0.4)
    # Cửa vòm chính, hàng cột và bậc thềm
    p += [box((3, 0.15, 3.4), (0, -1.58, b + 1.7), "sat"),
          cyl(1.5, 0.15, (0, -1.58, b + 3.4), "sat", v=12, rot=(90, 0, 0)),
          box((8.4, 1.8, 0.4), (0, -2.4, b + 4.4), "trim", bev=0.05),
          box((8.6, 1.4, 0.4), (0, -2.2, 0.2), "xam_nhat"),
          box((8.6, 1.0, 0.4), (0, -2.0, 0.6), "xam_nhat")]
    for x in (-3.6, -1.6, 1.6, 3.6):
        p.append(cyl(0.28, 4.0, (x, -2.8, b + 2.2), "trim", v=10))
    done("ToaNha_PhapThuoc", "Models/Pho", p)


def plaza():
    """Trung tâm thương mại: khối 5 tầng, góc kính bo tròn, màn hình quảng cáo, mái che lối vào, biển trên mái."""
    reset()
    W, D, F, n = 32.0, 24.0, 4.5, 5
    H = n * F
    R = 6.0
    p = [box((W - R, D, H), (-R / 2, D / 2, H / 2), "be_tong", bev=0.1),
         box((R, D - R, H), (W / 2 - R / 2, R + (D - R) / 2, H / 2), "be_tong", bev=0.1),
         cyl(R, H, (W / 2 - R, R, H / 2), "kinh_xanh", v=20),
         box((W - R - 2, 0.1, H - 5.5), (-R / 2 - 1, -0.05, 5 + (H - 5.5) / 2), "kinh_xanh")]
    for k in range(1, n + 1):
        z = k * F
        p.append(box((W - R + 0.3, 0.35, 0.4), (-R / 2, -0.15, z), "trim"))
        p.append(cyl(R + 0.15, 0.4, (W / 2 - R, R, z), "trim", v=20))
    p += [box((W - R - 2, 0.15, 4.2), (-R / 2 - 1, -0.08, 2.1), "kinh_sang"),
          box((12, 4, 0.4), (-4, -2, 5.0), "trim", bev=0.1),
          box((0.3, 0.3, 4.8), (-9.6, -3.7, 2.4), "sat"),
          box((0.3, 0.3, 4.8), (1.6, -3.7, 2.4), "sat"),
          box((9, 0.4, 6.4), (-9, -0.25, 13.5), "sat", bev=0.05),
          box((8.4, 0.2, 5.8), (-9, -0.5, 13.5), "nhan_xanh"),
          box((7, 0.4, 5.4), (3, -0.25, 13.5), "sat", bev=0.05),
          box((6.4, 0.2, 4.8), (3, -0.5, 13.5), "tim"),
          box((2, 1.2, 14), (-W / 2 + 1, -0.6, H - 7), "nhan_do", bev=0.05)]
    for k in range(5):  # chữ dọc trên biển
        p.append(box((1.2, 0.1, 1.4), (-W / 2 + 1, -1.25, H - 2 - k * 2.6), "trim", bev=0.02))
    p += [box((12, 0.5, 2.6), (-4, 2, H + 1.9), "vang", bev=0.05)]
    for x in (-8, 0):
        p.append(box((0.3, 0.3, 1.2), (x, 2.2, H + 0.6), "sat"))
    for x, y in ((6, 12), (-10, 16), (-2, 18)):  # thiết bị trên mái
        p.append(box((3, 2.5, 1.6), (x, y, H + 0.8), "xam_nhat", bev=0.05))
    done("TTTM_Plaza", "Models/Pho", p)


def khach_san_mini():
    """Khách sạn mini 9 tầng mặt tiền 6 m: kính và ban công xen kẽ, biển đứng phát sáng, quầy bar trên mái."""
    reset()
    random.seed(90)
    W, D, F, n = 6.0, 14.0, 3.2, 9
    H = n * F
    p = [box((W, D, H), (0, D / 2, H / 2), "trim", bev=0.05),
         box((4.4, 0.12, 2.6), (-0.4, -0.05, 1.3), "kinh_sang"),
         box((5.4, 1.6, 0.2), (-0.2, -0.8, 2.9), "nhan_xanh", bev=0.03),
         box((1.0, 0.1, 2.4), (2.3, -0.05, 1.2), "sat")]
    for f in range(1, n):
        z = f * F
        p.append(box((W + 0.05, 0.12, 0.25), (0, -0.05, z), "nhan_xanh" if f % 3 == 0 else "be_tong"))
        p.append(box((4.6, 0.1, 2.5), (-0.4, -0.04, z + 1.4), "kinh"))
        if f % 2 == 1:
            p += [box((4.8, 0.9, 0.12), (-0.4, -0.45, z + 0.1), "trim"),
                  box((4.8, 0.05, 0.9), (-0.4, -0.88, z + 0.6), "kinh_sang")]
            if random.random() < 0.6:
                p += chau_cay(-2.2, -0.55, z + 0.16, 0.55)
    p.append(box((0.9, 0.6, 13), (2.55, -0.9, H - 9), "nhan_do", bev=0.05))
    for k in range(5):
        p.append(box((0.6, 0.1, 1.6), (2.55, -1.25, H - 4 - k * 2.5), "vang", bev=0.02))
    p.append(box((W, D, 0.2), (0, D / 2, H + 0.1), "be_tong"))
    for x in (-2.6, 2.6):  # giàn che quầy bar trên mái
        for y in (0.4, 5.0):
            p.append(box((0.15, 0.15, 2.6), (x, y, H + 1.4), "sat"))
    p.append(box((5.8, 5.2, 0.15), (0, 2.7, H + 2.7), "than_cay"))
    p += chau_cay(-2.2, 1.0, H + 0.2, 0.8) + chau_cay(2.0, 1.0, H + 0.2, 0.8)
    p.append(cyl(0.5, 1.2, (0, 10, H + 0.8), "xam_nhat", v=10))
    done("KhachSan_Mini", "Models/Pho", p)


# ---------- Cây cao và công viên ----------
def cay_cao(kind):
    """Cây cổ thụ đường phố Quận 1. dau: thân thẳng ~18 m, tán rộng cao ~26 m. sao: tán hẹp xếp tầng.
    bang: cây bàng tán tầng ngang, thấp, dùng trong công viên."""
    reset()
    random.seed({"dau": 100, "sao": 110, "bang": 120}[kind])
    p = []
    if kind == "dau":
        p += [cyl(0.5, 18, (0, 0, 9), "vo_dau", v=7, r2=0.28, jit=0.03),
              cyl(0.85, 0.8, (0, 0, 0.4), "vo_dau", v=7, r2=0.5)]
        for a, b in (((0, 0, 15), (3, 0.6, 20)), ((0, 0, 15.5), (-3, -0.5, 20.5)), ((0, 0, 16), (0.4, 3, 21)),
                     ((0, 0, 16.5), (-0.4, -3, 20.5))):
            p.append(limb(a, b, 0.28, "vo_dau", bev=0))
        blobs = [(0, 0, 23, 3.4), (3, 0.5, 20.5, 2.6), (-3, -0.5, 21, 2.8), (0.5, 3, 21.5, 2.5),
                 (-0.5, -3, 20.5, 2.5), (1.5, -1.5, 24.5, 2.2), (-1.8, 1.6, 24, 2.2)]
        name = "CayDau_Cao"
    elif kind == "sao":
        p += [cyl(0.45, 15, (0, 0, 7.5), "than_cay", v=7, r2=0.25, jit=0.03),
              cyl(0.75, 0.7, (0, 0, 0.35), "than_cay", v=7, r2=0.45)]
        for z, s in ((10, 1), (12.5, -1), (15, 1)):
            p.append(limb((0, 0, z), (s * 1.8, 0.5 * s, z + 1.5), 0.18, "than_cay", bev=0))
        blobs = [(1.8, 0.5, 12, 1.6), (-1.8, -0.5, 14.5, 1.7), (1.6, 0.4, 17, 1.6), (0, 0, 16, 2.2),
                 (0, 0, 19, 2.4), (0.3, -0.2, 21.5, 1.8), (-0.6, 0.8, 18, 1.8)]
        name = "CaySao_Cao"
    else:
        p.append(cyl(0.28, 4.2, (0, 0, 2.1), "than_cay", v=6, r2=0.18, jit=0.02))
        for z, r, n in ((3.6, 2.6, 4), (4.8, 1.9, 3)):
            for k in range(n):
                a = k / n * math.tau + z
                p.append(limb((0, 0, z - 0.4), (r * math.cos(a), r * math.sin(a), z), 0.1, "than_cay", bev=0))
        blobs = []
        for z, r, c in ((4.0, 3.3, "la2"), (5.2, 2.5, "la1"), (6.2, 1.6, "la3")):
            p.append(ball(r, (0, 0, z), c, sub=2, scale=(1, 1, 0.28), jit=r * 0.06))
        name = "CayBang"
    for i, (x, y, z, r) in enumerate(blobs):
        p.append(ball(r, (x, y, z), ["la1", "la2", "la3"][i % 3], sub=1, jit=r * 0.14, scale=(1, 1, 0.78)))
    if kind != "bang":
        for x, y, sx, sy in ((0, -0.8, 1.7, 0.12), (0, 0.8, 1.7, 0.12), (-0.8, 0, 0.12, 1.5), (0.8, 0, 0.12, 1.5)):
            p.append(box((sx, sy, 0.12), (x, y, 0.06), "xam", bev=0.02))
        p.append(box((1.5, 1.5, 0.04), (0, 0, 0.02), "dat"))
    done(name, "Models/Pho" if kind != "bang" else "Models/CongVien", p)


def ghe_da():
    reset()
    p = [box((1.8, 0.5, 0.1), (0, 0, 0.45), "xam_nhat", bev=0.02)]
    for x in (-0.7, 0.7):
        p.append(box((0.12, 0.42, 0.4), (x, 0, 0.2), "xam", bev=0.01))
    done("GheDa", "Models/CongVien", p)


def den_cong_vien():
    reset()
    p = [cyl(0.18, 0.4, (0, 0, 0.2), "la_dam", v=8, r2=0.12, bev=0.01),
         cyl(0.07, 3.4, (0, 0, 2.1), "la_dam", v=8),
         cyl(0.16, 0.08, (0, 0, 3.8), "la_dam", v=8),
         box((0.34, 0.34, 0.5), (0, 0, 4.1), "den_truoc", taper=(1.25, 1.25)),
         cyl(0.34, 0.3, (0, 0, 4.5), "la_dam", v=4, r2=0.02, rot=(0, 0, 45)),
         ball(0.05, (0, 0, 4.68), "la_dam")]
    for x, y in ((-0.19, -0.19), (0.19, -0.19), (-0.19, 0.19), (0.19, 0.19)):
        p.append(limb((x * 0.75, y * 0.75, 3.85), (x * 1.1, y * 1.1, 4.35), 0.025, "la_dam", bev=0))
    done("DenCongVien", "Models/CongVien", p)


def bon_hoa():
    reset()
    random.seed(130)
    p = [box((3, 1.2, 0.5), (0, 0, 0.25), "xam_nhat", bev=0.04),
         box((2.8, 1.0, 0.05), (0, 0, 0.5), "dat")]
    for x in (-1.0, 0.0, 1.0):
        p.append(ball(0.42, (x, 0.2, 0.75), "la2", jit=0.05, scale=(1, 0.8, 0.8)))
    for i in range(16):
        x, y = -1.25 + (i % 8) * 0.36, -0.3 + (i // 8) * 0.22
        p.append(ball(0.1, (x, y, 0.6), random.choice(["hong", "vang", "nhan_do", "trim", "tim"]), scale=(1, 1, 0.7)))
    done("BonHoa", "Models/CongVien", p)


def dai_phun_nuoc():
    reset()
    p = [lathe([(2.6, 0), (2.65, 0.5), (2.45, 0.6), (2.4, 0.3)], "trim", seg=16),
         cyl(2.42, 0.05, (0, 0, 0.42), "nuoc", v=16),
         lathe([(0.5, 0), (0.32, 0.5), (0.25, 1.2), (0.9, 1.4), (0.95, 1.55)], "trim", seg=12),
         cyl(0.85, 0.05, (0, 0, 1.5), "nuoc", v=12),
         cyl(0.12, 1.0, (0, 0, 2.0), "nuoc", v=6, r2=0.02)]
    for k in range(8):  # tia nước rơi xuống bể dưới
        a = k / 8 * math.tau
        p.append(limb((0.85 * math.cos(a), 0.85 * math.sin(a), 1.5), (1.3 * math.cos(a), 1.3 * math.sin(a), 0.45), 0.06,
                      "nuoc", bev=0))
    done("DaiPhunNuoc", "Models/CongVien", p)


def hang_rao():
    reset()
    p = [box((4, 0.3, 0.35), (0, 0, 0.175), "trim", bev=0.02)]
    for x in (-1.95, 0, 1.95):
        p.append(box((0.12, 0.12, 1.25), (x, 0, 0.95), "la_dam", bev=0.01))
    for z in (0.5, 1.2):
        p.append(box((4, 0.05, 0.06), (0, 0, z), "la_dam"))
    for k in range(26):
        x = -1.85 + k * 0.148
        p.append(box((0.025, 0.025, 0.85), (x, 0, 0.82), "la_dam"))
        p.append(cyl(0.035, 0.08, (x, 0, 1.28), "la_dam", v=4, r2=0.0))
    done("HangRao_4m", "Models/CongVien", p)


def tham_co():
    """Ô công viên 20 x 20 m: thảm cỏ, lối đi gạch hình chữ thập, viền đá. Gốc ở tâm ô."""
    reset()
    p = [box((20, 20, 0.12), (0, 0, 0.06), "co"),
         box((20, 2.4, 0.14), (0, 0, 0.07), "gach"),
         box((2.4, 20, 0.14), (0, 0, 0.07), "gach")]
    for s in (-1, 1):
        p.append(box((20, 0.2, 0.2), (0, s * 1.3, 0.1), "trim"))
        p.append(box((0.2, 20, 0.2), (s * 1.3, 0, 0.1), "trim"))
    done("ThamCo_20m", "Models/CongVien", p)


# ---------- Hẻm (rộng ~3,5 m như Hem_50m) ----------
def cong_hem():
    """Cổng hẻm: hai trụ, xà ngang có mái ngói, biển tên hẻm ở cả hai mặt."""
    reset()
    p = []
    for x in (-2.25, 2.25):
        p += [box((0.5, 0.5, 4.2), (x, 0, 2.1), "trim", bev=0.03),
              box((0.62, 0.62, 0.2), (x, 0, 0.1), "xam"),
              box((0.62, 0.62, 0.15), (x, 0, 4.25), "trim")]
    p += [box((5.2, 0.4, 0.5), (0, 0, 4.3), "trim", bev=0.03),
          box((5.6, 0.9, 0.18), (0, 0, 4.65), "ngoi", taper=(0.92, 0.5))]
    for s in (-1, 1):
        p.append(box((3.4, 0.12, 0.8), (0, s * 0.26, 3.7), "nhan_xanh", bev=0.03))
        for k, w in enumerate((0.55, 0.4, 0.7, 0.45)):
            p.append(box((w, 0.04, 0.3), (-1.1 + k * 0.75, s * 0.33, 3.7), "trim"))
    done("CongHem", "Models/Hem", p)


def nha_hem(idx, floors, wall, roof):
    """Nhà trong hẻm rộng 4 m: cửa sắt xếp, mái tôn che cửa, cửa sổ có song sắt, ban công phơi đồ, đồng hồ điện."""
    reset()
    random.seed(140 + idx)
    W, D, F = 4.0, 8.0, 3.0
    H = floors * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((3.0, 0.08, 2.4), (-0.3, -0.02, 1.2), "vien"),
         box((W, 1.0, 0.05), (0, -0.48, 2.75), "ton", rot=(15, 0, 0)),
         box((0.3, 0.12, 0.4), (1.6, -0.06, 1.6), "xam", bev=0.02),
         box((0.35, 0.04, 0.22), (1.6, -0.04, 2.25), "nhan_xanh")]
    for k in range(25):  # cửa sắt xếp
        p.append(box((0.03, 0.06, 2.4), (-1.75 + k * 0.12, -0.08, 1.2), "sat"))
    for z in (0.05, 2.35):
        p.append(box((3.0, 0.08, 0.08), (-0.3, -0.08, z), "sat"))
    for f in range(1, floors):
        z = f * F
        p.append(box((W + 0.04, 0.1, 0.15), (0, -0.04, z - 0.05), "trim"))
        if f % 2 == 1:  # ban công phơi đồ
            p += [box((W, 0.8, 0.12), (0, -0.4, z + 0.05), "trim"),
                  box((W, 0.05, 0.9), (0, -0.78, z + 0.55), "sat"),
                  box((1.4, 0.08, 2.1), (-0.8, -0.03, z + 1.15), "kinh"),
                  limb((-1.9, -0.6, z + 1.9), (1.9, -0.6, z + 1.9), 0.02, "sat", bev=0)]
            for k in range(5):
                x = -1.5 + k * 0.7
                p.append(box((0.4, 0.04, 0.55), (x, -0.6, z + 1.6),
                             random.choice(["nhan_do", "vang", "nhan_xanh", "trim", "tim", "hong"])))
            p += chau_cay(1.4, -0.5, z + 0.11, 0.6)
        else:  # cửa sổ song sắt
            p.append(box((1.6, 0.08, 1.4), (0, -0.03, z + 1.4), "kinh"))
            for k in range(7):
                p.append(box((0.03, 0.06, 1.4), (-0.7 + k * 0.233, -0.08, z + 1.4), "sat"))
            p.append(box((0.7, 0.3, 0.45), (1.3, -0.17, z + 2.4), "trim", bev=0.03))
    p.append(box((W, 0.15, 0.6), (0, 0.05, H + 0.3), wall))
    if roof == "bon":
        p.append(cyl(0.45, 1.0, (0.8, 2.0, H + 0.75), "xam_nhat", v=10, rot=(0, 90, 0)))
        p.append(box((1.0, 0.6, 0.25), (0.8, 2.0, H + 0.12), "sat"))
    else:
        p.append(box((W + 0.2, 3.0, 0.06), (0, 2.5, H + 0.9), "ton", rot=(-12, 0, 0)))
    p.append(cyl(0.03, 2.5, (-1.5, 4.0, H + 1.25), "sat", v=4))
    done(f"NhaHem_{idx}", "Models/Hem", p)


def day_dien_hem():
    """Bó dây điện võng ngang hẻm, dài 5 m, cao ~5,5 m. Gốc ở mặt đất giữa hẻm."""
    reset()
    random.seed(150)
    p = []
    for k in range(5):
        y = -0.15 + k * 0.08
        z0 = 5.5 + random.uniform(-0.2, 0.2)
        sag = random.uniform(0.3, 0.6)
        pts = [(-2.6 + i * 0.65, y + random.uniform(-0.03, 0.03), z0 - sag * (1 - ((i - 4) / 4) ** 2)) for i in range(9)]
        for a, b in zip(pts, pts[1:]):
            p.append(limb(a, b, 0.03, "vien", bev=0))
    p.append(torus(0.25, 0.05, (0.6, 0, 5.0), "vien", rot=(70, 0, 20), jit=0.03))
    p.append(box((0.25, 0.18, 0.3), (-1.2, 0, 4.9), "xam", bev=0.02))
    done("DayDien_Hem", "Models/Hem", p)


def mieu_nho():
    """Miếu nhỏ đặt sát tường, góc hẻm: bệ, khám đỏ mái ngói, lư hương, nến."""
    reset()
    p = [box((0.55, 0.45, 0.9), (0, 0, 0.45), "trim", bev=0.02),
         box((0.7, 0.5, 0.55), (0, 0, 1.18), "do_dam", bev=0.02),
         box((0.4, 0.05, 0.38), (0, -0.25, 1.16), "vien"),
         box((0.9, 0.7, 0.2), (0, 0, 1.55), "ngoi", taper=(0.6, 0.35)),
         cyl(0.07, 0.08, (0, -0.32, 0.94), "vang", v=8)]
    for x in (-0.15, 0.15):
        p.append(cyl(0.025, 0.12, (x, -0.32, 0.96), "nhan_do", v=6))
    for k in range(3):
        p.append(cyl(0.006, 0.18, (-0.02 + k * 0.02, -0.32, 1.06), "than_cay", v=4))
    done("MieuNho", "Models/Hem", p)


def guong_cau_loi():
    reset()
    p = [cyl(0.05, 3.0, (0, 0, 1.5), "cam", v=6),
         limb((0, 0, 2.95), (0, -0.15, 3.0), 0.04, "sat", bev=0),
         cyl(0.4, 0.06, (0, -0.2, 3.0), "kinh_sang", v=14, rot=(80, 0, 0)),
         cyl(0.45, 0.05, (0, -0.17, 3.0), "cam", v=14, rot=(80, 0, 0))]
    done("GuongCauLoi", "Models/Hem", p)


def xe_banh_mi():
    """Xe đẩy bánh mì: tủ kính, bảng hiệu vàng, hai bánh, tay đẩy, dù che."""
    reset()
    p = [box((1.2, 0.6, 0.6), (0, 0, 0.75), "trim", bev=0.03),
         box((1.1, 0.55, 0.55), (0, 0, 1.33), "kinh_sang", bev=0.02),
         box((1.2, 0.6, 0.05), (0, 0, 1.63), "nhan_do", bev=0.01),
         box((1.0, 0.03, 0.2), (0, -0.31, 0.85), "vang"),
         limb((0.6, 0.0, 0.9), (0.95, 0.0, 1.0), 0.04, "sat", bev=0),
         cyl(0.04, 2.0, (-0.4, 0.2, 1.7), "sat", v=5),
         cyl(1.0, 0.4, (-0.4, 0.2, 2.8), "nhan_do", v=8, r2=0.05)]
    for y in (-0.33, 0.33):
        p.append(cyl(0.25, 0.06, (0.15, y, 0.25), "banh", v=10, rot=(90, 0, 0)))
    p.append(box((0.06, 0.06, 0.45), (-0.5, 0, 0.23), "sat"))
    done("XeBanhMi", "Models/Hem", p)


# ---------- Đường (thay greybox; mặt đường ở z = 0, đoạn kéo dài về -Y = +Z trong Unity) ----------
def duong_lon(loi_hem=None):
    """Đường lớn 3 làn x 3 m, dài 100 m, vỉa hè 2 m cao 0,25 m có bó vỉa.
    loi_hem = "trai" / "phai": ở giữa đoạn (z = 50 trong Unity) vỉa hè phía đó được thay bằng mặt nhựa rộng 4 m
    nối thẳng vào miệng hẻm, để xe rẽ vào hẻm không phải leo vỉa hè."""
    reset()
    L, lane, le = 100.0, 3.0, 2.0
    x_le = 1.5 * lane + le / 2
    p = [box((3 * lane, L, 0.2), (0, -L / 2, -0.1), "duong")]
    for x in (-lane / 2, lane / 2):
        for i in range(0, int(L), 6):
            p.append(box((0.15, 3.0, 0.02), (x, -(i + 1.5), 0.01), "trim"))
    for s in (-1, 1):
        x = s * x_le
        doan = [(0, L)]
        if (loi_hem == "trai" and s > 0) or (loi_hem == "phai" and s < 0):  # +X Blender = bên trái người lái trong Unity
            doan = [(0, 48), (52, L)]
            p.append(box((le, 4, 0.2), (x, -50, -0.1), "duong"))  # mặt nhựa nối vào hẻm
        for a, b in doan:
            n = b - a
            p.append(box((le - 0.2, n, 0.45), (x + s * 0.1, -(a + n / 2), 0.025), "via_he"))
            p.append(box((0.2, n, 0.47), (x - s * (le / 2 - 0.1), -(a + n / 2), 0.035), "xam_nhat"))
            for k in range(int(a) + 1, int(b), 2):  # mạch gạch lát
                p.append(box((le - 0.2, 0.04, 0.005), (x + s * 0.1, -k, 0.25), "xam_nhat"))
    ten = "DuongLon_100m" + {None: "", "trai": "_HemTrai", "phai": "_HemPhai"}[loi_hem]
    done(ten, "Models/Duong", p)


def hem_duong():
    """Mặt hẻm 3,5 m x 50 m trải nhựa, có miếng vá, nắp cống và rãnh thoát nước hai bên; không có tường."""
    reset()
    random.seed(160)
    L, W = 50.0, 3.5
    p = [box((W, L, 0.2), (0, -L / 2, -0.1), "nhua_hem")]
    for s in (-1, 1):
        p.append(box((0.25, L, 0.03), (s * (W / 2 - 0.125), -L / 2, 0.005), "xam"))
    for k in range(6):
        p.append(box((random.uniform(0.6, 1.4), random.uniform(0.5, 1.2), 0.01),
                     (random.uniform(-1, 1), -random.uniform(3, L - 3), 0.003), "duong",
                     rot=(0, 0, random.uniform(0, 40))))
    for y in (-12, -30, -44):
        p.append(cyl(0.35, 0.02, (0.6, y, 0.005), "sat", v=10))
    done("Hem_50m", "Models/Duong", p)


def dai_cay_le():
    """Dải bồn cây dài 10 m đặt sát bó vỉa, thay lan can giữa vỉa hè và làn xe: viền bê tông, bụi tỉa, hoa."""
    reset()
    random.seed(170)
    p = [box((10, 0.9, 0.4), (0, 0, 0.2), "xam_nhat", bev=0.03),
         box((9.8, 0.75, 0.05), (0, 0, 0.4), "dat")]
    for k in range(9):
        x = -4.4 + k * 1.1
        p.append(box((1.0, 0.65, 0.5), (x, 0, 0.68), "la2" if k % 2 else "la1", bev=0.12, jit=0.03))
        if k % 3 == 1:
            for j in range(3):
                p.append(ball(0.08, (x + random.uniform(-0.35, 0.35), random.uniform(-0.25, 0.25), 0.95),
                              random.choice(["hong", "vang", "nhan_do"])))
    done("DaiCay_Le_10m", "Models/Duong", p)


def khuon_vien(W):
    """Khuôn viên trước tòa nhà, rộng W, sâu 8 m: cỏ, lối đi giữa, viền thấp, bụi cây, bồn hoa, 2 cây tán tròn.
    Gốc ở giữa mép giáp vỉa hè; tòa nhà đặt lùi vào 8 m phía sau."""
    reset()
    random.seed(180 + int(W))
    D = 8.0
    p = [box((W, D, 0.15), (0, D / 2, 0.075), "co"),
         box((2.6, D, 0.17), (0, D / 2, 0.085), "gach")]
    for s in (-1, 1):
        p.append(box((W / 2 - 1.6, 0.25, 0.45), (s * (W / 4 + 0.8), 0.125, 0.225), "trim", bev=0.02))
        p.append(box((0.25, D, 0.45), (s * (W / 2 - 0.125), D / 2, 0.225), "trim", bev=0.02))
        for k in range(int((W / 2 - 3) / 1.2)):  # hàng bụi sát tường rào
            x = s * (2.2 + k * 1.2)
            p.append(box((1.0, 0.7, 0.6), (x, 0.8, 0.5), "la2" if k % 2 else "la1", bev=0.12, jit=0.03))
        cx = s * W / 4
        p += [cyl(0.2, 3.0, (cx, D / 2, 1.6), "than_cay", v=6, r2=0.13),
              ball(1.6, (cx, D / 2, 4.0), "la1", jit=0.15, scale=(1, 1, 0.85)),
              ball(1.1, (cx + 0.8, D / 2 + 0.3, 3.4), "la3", jit=0.1),
              box((2.4, 1.2, 0.35), (s * (W / 2 - 2), D - 1.2, 0.3), "xam_nhat", bev=0.03)]
        for j in range(5):
            p.append(ball(0.12, (s * (W / 2 - 2) - 0.9 + j * 0.45, D - 1.2, 0.55),
                          random.choice(["hong", "vang", "nhan_do", "tim"])))
    done(f"KhuonVien_{int(W)}m", "Models/Duong", p)


# ---------- Người đi bộ (dáng đang bước, mặt hướng -Y) ----------
def nguoi(name, ao, quan, kieu="thuong", k=1.0):
    """kieu: thuong (tóc ngắn), toc_dai, ganh (nón lá, đòn gánh hai thúng), hoc_sinh (nhỏ hơn, cặp, khăn quàng)."""
    reset()
    v = lambda x, y, z: (x * k, y * k, z * k)
    p = []
    for s, dy in ((-1, -0.22), (1, 0.2)):  # chân: một chân bước tới, một chân sau
        p.append(limb(v(s * 0.09, 0, 0.92), v(s * 0.09, dy, 0.1), 0.13 * k, quan))
        p.append(box((0.11 * k, 0.24 * k, 0.08 * k), v(s * 0.09, dy - 0.04, 0.04), "vien", bev=0.01))
    p.append(box((0.36 * k, 0.22 * k, 0.56 * k), v(0, 0, 1.2), ao, taper=(1.12, 1), bev=0.04 * k))
    p.append(ball(0.12 * k, v(0, 0, 1.62), "da_nguoi", sub=2))
    if kieu == "ganh":
        p += [limb(v(0.21, 0, 1.42), v(0.2, -0.3, 1.5), 0.09 * k, ao),
              ball(0.045 * k, v(0.2, -0.32, 1.5), "da_nguoi"),
              limb(v(-0.21, 0, 1.42), v(-0.25, 0.15, 1.0), 0.09 * k, ao),
              cyl(0.34 * k, 0.2 * k, v(0, 0, 1.8), "giay", v=12, r2=0.0),
              limb(v(0.2, -0.9, 1.5), v(0.2, 0.9, 1.5), 0.045 * k, "than_cay", bev=0)]
        for y in (-0.85, 0.85):
            for dx in (-0.12, 0.12):
                p.append(limb(v(0.2, y, 1.5), v(0.2 + dx, y, 0.62), 0.012 * k, "than_cay", bev=0))
            p.append(cyl(0.27 * k, 0.22 * k, v(0.2, y, 0.5), "giay", v=10, r2=0.2 * k))
            for j in range(4):
                p.append(ball(0.07 * k, v(0.2 + (j % 2 - 0.5) * 0.15, y + (j // 2 - 0.5) * 0.15, 0.64),
                              ["vang", "nhan_do", "la1", "cam"][j]))
    else:
        for s, dy in ((1, -0.18), (-1, 0.18)):  # tay đánh ngược chân
            p.append(limb(v(s * 0.21, 0, 1.42), v(s * 0.24, dy, 0.98), 0.09 * k, ao))
            p.append(ball(0.045 * k, v(s * 0.25, dy * 1.05, 0.94), "da_nguoi"))
        p.append(ball(0.125 * k, v(0, 0.02, 1.66), "toc", sub=2, scale=(1, 1, 0.8)))
        if kieu == "toc_dai":
            p.append(box((0.22 * k, 0.08 * k, 0.42 * k), v(0, 0.1, 1.45), "toc", bev=0.02))
        if kieu == "hoc_sinh":
            p += [box((0.3 * k, 0.16 * k, 0.34 * k), v(0, 0.19, 1.22), "nhan_xanh", bev=0.03),
                  box((0.12 * k, 0.03 * k, 0.16 * k), v(0, -0.12, 1.36), "nhan_do")]
    done(name, "Models/Nguoi", p)


# ---------- Ảnh xem trước ----------
def setup_render(png, res, world_hex, cam_loc, target, ortho, world_strength=0.55, sun_rot=(48, 8, -35)):
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    try:
        sc.eevee.taa_render_samples = 64
    except AttributeError:
        pass
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Punchy"
    except TypeError:
        pass
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*lin(world_hex), 1)
    bg.inputs["Strength"].default_value = world_strength
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 5.5
    sun.data.color = lin(HEX["anh_sang"])
    sun.data.angle = math.radians(3)
    sun.rotation_euler = [math.radians(a) for a in sun_rot]
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    cam.location = cam_loc
    cam.rotation_euler = (Vector(target) - Vector(cam_loc)).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho
    else:  # phối cảnh như camera trong game
        cam.data.lens = 22
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    print("ANH", png, sc.render.engine)


def place(f, loc, rz=0, s=1.0):
    bpy.ops.import_scene.fbx(filepath=os.path.join(ROOT, f))
    o = bpy.context.selected_objects[0]
    o.location = loc
    o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], math.radians(rz))
    o.scale = (s * o.scale[0], s * o.scale[1], s * o.scale[2])


def ground(size, loc, col):
    o = box(size, loc, col)
    o.data.materials.append(pal_mat())


def preview_pho(png):
    reset()
    ground((34, 10, 0.2), (0, -8, -0.1), "duong")
    ground((34, 3, 0.15), (0, -1.5, 0.075), "via_he")
    ground((34, 0.25, 0.2), (0, -3.05, 0.1), "trim")
    for x in range(-16, 17, 4):
        ground((2.0, 0.15, 0.02), (x, -8, 0.01), "trim")
    for i, n in enumerate((1, 2, 3, 4, 2, 1, 4, 3)):
        place(f"Models/Pho/NhaOng_{n}.fbx", (-14 + i * 4, 0, 0))
    place("Models/Pho/CayXanh_1.fbx", (-7, -2.2, 0.15))
    place("Models/Pho/CayXanh_2.fbx", (7, -2.2, 0.15))
    place("Models/Pho/CotDien.fbx", (2.1, -2.6, 0.15))
    place("Models/XeShipper/XeShipper.fbx", (-2.0, -5.2, 0), 90)
    place("Models/XeAI/XeMayAI_1.fbx", (1.5, -4.8, 0), 90)
    place("Models/XeAI/XeMayAI_2.fbx", (4.0, -6.2, 0), 90)
    setup_render(png, (1920, 1080), HEX["bau_troi"], (-16, -30, 17), (0, -3.5, 3.0), 21)


def preview_quan1(png):
    """Một dãy phố Quận 1 ghép từ nhà ống và các công trình lớn."""
    reset()
    ground((150, 16, 0.2), (0, -11, -0.1), "duong")
    ground((150, 4, 0.15), (0, -2, 0.075), "via_he")
    ground((150, 0.25, 0.2), (0, -4.1, 0.1), "trim")
    for x in range(-72, 73, 6):
        ground((3.0, 0.2, 0.02), (x, -11, 0.01), "trim")
    for f, x in (("CaoOc_Kinh", -58), ("ChungCu_Cu", -35), ("NhaOng_2", -22), ("NhaOng_1", -18),
                 ("KhachSan_Mini", -13), ("NhaOng_4", -8), ("ToaNha_PhapThuoc", 13), ("NhaOng_3", 32),
                 ("TTTM_Plaza", 52)):
        place(f"Models/Pho/{f}.fbx", (x, 0, 0))
    for i, x in enumerate((-46, -26, -3, 26, 42)):
        place("Models/Pho/CayDau_Cao.fbx" if i % 2 == 0 else "Models/Pho/CaySao_Cao.fbx", (x, -3.0, 0.15), i * 40)
    place("Models/Pho/CotDien.fbx", (-16, -3.6, 0.15))
    place("Models/XeShipper/XeShipper.fbx", (-10, -8, 0), 90)
    setup_render(png, (1920, 1080), HEX["bau_troi"], (-70, -150, 80), (-3, 0, 28), 140)


def preview_congvien(png):
    """Góc công viên 40 x 40 m: 4 ô cỏ, đài phun nước ở giữa, ghế đá, đèn, bồn hoa, hàng rào, cây cao."""
    reset()
    ground((80, 80, 0.1), (0, 0, -0.06), "via_he")
    for x in (-10, 10):
        for y in (-10, 10):
            place("Models/CongVien/ThamCo_20m.fbx", (x, y, 0))
    place("Models/CongVien/DaiPhunNuoc.fbx", (0, 0, 0.12))
    for x, y, rz in ((-6, -2.2, 0), (6, -2.2, 0), (-6, 2.2, 180), (6, 2.2, 180), (2.2, -7, 90), (-2.2, 7, -90)):
        place("Models/CongVien/GheDa.fbx", (x, y, 0.12), rz)
    for x, y in ((-4, -2), (4, 2), (-2, 12), (2, -12), (14, -2), (-14, 2)):
        place("Models/CongVien/DenCongVien.fbx", (x, y, 0.12))
    for x, y in ((-6, -6), (6, 6), (-6, 6), (6, -6)):
        place("Models/CongVien/BonHoa.fbx", (x, y, 0.12), 45 if x * y > 0 else -45)
    for k in range(10):
        place("Models/CongVien/HangRao_4m.fbx", (-18 + k * 4, -20.2, 0))
    for x, y, f in ((-13, -13, "Pho/CayDau_Cao"), (13, 13, "Pho/CayDau_Cao"), (-13, 13, "Pho/CaySao_Cao"),
                    (13, -13, "Pho/CaySao_Cao"), (-6, -14, "CongVien/CayBang"), (7, 15, "CongVien/CayBang"),
                    (15, 5, "CongVien/CayBang")):
        place(f"Models/{f}.fbx", (x, y, 0.12))
    place("Models/XeShipper/XeShipper.fbx", (-1.2, -16, 0.12), 0)
    setup_render(png, (1920, 1080), HEX["bau_troi"], (-38, -62, 52), (0, 0, 5), 52)


def preview_hem(png):
    """Nhìn dọc hẻm như góc camera trong game: hai dãy nhà hẻm, dây điện, cổng hẻm, đồ đạc hai bên."""
    reset()
    ground((80, 120, 0.1), (0, -30, -0.08), "duong")
    place("Models/Duong/Hem_50m.fbx", (0, 0, 0))
    place("Models/Duong/Hem_50m.fbx", (0, -50, 0))
    ground((30, 8, 0.1), (0, 6, -0.05), "duong")
    nha = [1, 2, 3, 2, 1, 3, 2, 3, 1, 2, 3, 1]
    for k in range(12):
        y = -2 - k * 4
        place(f"Models/Hem/NhaHem_{nha[k]}.fbx", (-1.75, y, 0), 90)
        place(f"Models/Hem/NhaHem_{nha[(k + 5) % 12]}.fbx", (1.75, y - 4, 0), -90)
    place("Models/Hem/CongHem.fbx", (0, 0, 0))
    for y in (-7, -17, -29, -40):
        place("Models/Hem/DayDien_Hem.fbx", (0, y, 0), 90)
    place("Models/Hem/MieuNho.fbx", (1.5, -1.2, 0), -90)
    place("Models/Hem/GuongCauLoi.fbx", (-1.5, -13, 0), -60)
    place("Models/Hem/XeBanhMi.fbx", (-1.1, -9, 0), 90)
    for x, y, f in ((1.2, -5, "XeMayDau_1"), (1.25, -6.2, "XeMayDau_2"), (-1.3, -21, "XeMayDau_1")):
        place(f"Models/Hem/{f}.fbx", (x, y, 0), 180 + (8 if x > 0 else -8))
    for x, y, f, rz in ((0.6, -11, "NguoiDiBo_1", 0), (-0.7, -16, "NguoiDiBo_2", 180), (0.9, -24, "NguoiGanhHang", 0),
                        (-0.4, -31, "HocSinh", 180), (0.2, -38, "NguoiDiBo_1", 180)):
        place(f"Models/Nguoi/{f}.fbx", (x, y, 0), rz)
    place("Models/XeShipper/XeShipper.fbx", (0, 2.5, 0), 0)
    setup_render(png, (1080, 1920), HEX["bau_troi"], (0, 7.5, 4.2), (0, -14, 1.2), None, 1.1, (18, 0, -25))


def preview_duong(png):
    """Đoạn đường lớn có lối vào hẻm bên phải người lái: mặt nhựa nối vào hẻm, khuôn viên trước tòa Pháp, dải bụi cây sát lề."""
    reset()
    place("Models/Duong/DuongLon_100m_HemPhai.fbx", (0, 0, 0))
    place("Models/Duong/Hem_50m.fbx", (-6.5, -50, 0), -90)
    for k in range(6):  # nhà hai bên hẻm
        x = -8.5 - k * 4
        place(f"Models/Hem/NhaHem_{k % 3 + 1}.fbx", (x, -48.25, 0), 0)
        place(f"Models/Hem/NhaHem_{(k + 1) % 3 + 1}.fbx", (x, -51.75, 0), 180)
    place("Models/Hem/CongHem.fbx", (-6.9, -50, 0), 90)
    for k in range(11):  # bên trái: dãy nhà ống, chừa miệng hẻm
        place(f"Models/Pho/NhaOng_{k % 4 + 1}.fbx", (-6.5, -2 - k * 4, 0), 90)
    place("Models/Pho/KhachSan_Mini.fbx", (-6.5, -57, 0), 90)
    place("Models/Pho/ChungCu_Cu.fbx", (-6.5, -72, 0), 90)
    place("Models/Pho/NhaOng_2.fbx", (-6.5, -84, 0), 90)
    place("Models/Pho/NhaOng_3.fbx", (-6.5, -88, 0), 90)
    place("Models/Duong/KhuonVien_32m.fbx", (6.5, -24, 0), -90)  # bên phải: tòa Pháp có khuôn viên
    place("Models/Pho/ToaNha_PhapThuoc.fbx", (14.5, -24, 0), -90)
    place("Models/Pho/CaoOc_Kinh.fbx", (6.5, -62, 0), -90)       # cao ốc không có khuôn viên
    place("Models/Duong/KhuonVien_20m.fbx", (6.5, -86, 0), -90)
    place("Models/Pho/ChungCu_Cu.fbx", (14.5, -86, 0), -90)
    for y in (-8, -20, -32, -64, -76, -92):
        place("Models/Duong/DaiCay_Le_10m.fbx", (-5.0 if y > -40 else 5.0, y, 0.25), 90)
    for x, y in ((-5.9, -14), (-5.9, -22), (5.9, -40), (5.9, -74), (-5.9, -66), (-5.9, -94)):
        place("Models/Pho/CayDau_Cao.fbx" if y % 4 else "Models/Pho/CaySao_Cao.fbx", (x, y, 0.25), y * 7)
    place("Models/XeShipper/XeShipper.fbx", (-2.4, -44, 0), 0)
    place("Models/XeAI/XeMayAI_1.fbx", (0.5, -30, 0), 0)
    place("Models/XeAI/XeMayAI_2.fbx", (3.0, -60, 0), 180)
    place("Models/Nguoi/NguoiDiBo_2.fbx", (-12, -49.5, 0), -90)
    place("Models/Nguoi/NguoiGanhHang.fbx", (-5.7, -58, 0.25), 0)
    setup_render(png, (1080, 1350), HEX["bau_troi"], (10, -30, 30), (-6, -50, 0), 26)


def preview_hanghoa(png):
    reset()
    ground((1.4, 1.2, 0.04), (0, 0, -0.02), "tuong_kem")
    for r, kind in enumerate(("BoHoa", "BinhGom", "CaPhe")):
        states = ["Nguyen", "HuMotPhan", "SapHong"] if kind != "BinhGom" else ["Nguyen", "Nut", "Vo"]
        for c, st in enumerate(states):
            place(f"Models/HangHoa/{kind}_{st}.fbx", (-0.38 + c * 0.38, 0.33 - r * 0.33, 0))
    setup_render(png, (1600, 1200), "FBE3C8", (-1.3, -2.4, 1.9), (0, 0.03, 0.12), 1.4)


# Tham số sau thư mục Art chọn nhóm cần dựng: cu, cong_trinh, cong_vien, hem (bỏ trống là dựng tất cả)
NHOM = set(sys.argv[sys.argv.index("--") + 2:]) if "--" in sys.argv else set()
lam = lambda g: not NHOM or g in NHOM

make_palette()
if lam("cu"):
    for s in range(3):
        caphe(s); bohoa(s); gom(s)
    for i, (fl, wall, awn, sh, roof) in enumerate([(3, "tuong_kem", ("nhan_do", "trim"), "la_dam", "bon"),
                                                   (4, "tuong_dao", ("nhan_xanh", "trim"), "trim", "ton"),
                                                   (2, "tuong_mint", ("vang", "nhan_do"), "nhan_xanh", "ngoi"),
                                                   (5, "tuong_vang", ("la_dam", "trim"), "ton", "bon")]):
        nha(i + 1, fl, wall, awn, sh, roof)
    xe_may("XeShipper", "Models/XeShipper", "cam", "tim", "cam", cargo=True)
    xe_may("XeMayAI_1", "Models/XeAI", "xanh_xe", "nhan_do", "quan")
    xe_may("XeMayAI_2", "Models/XeAI", "trim", "nhan_xanh", "nhan_do")
    cay(1); cay(2); cot_dien()
    preview_pho(os.path.join(HERE, "xem_truoc_asset.png"))
    preview_hanghoa(os.path.join(HERE, "xem_truoc_hanghoa.png"))
if lam("cong_vien"):
    cay_cao("dau"); cay_cao("sao"); cay_cao("bang")
    ghe_da(); den_cong_vien(); bon_hoa(); dai_phun_nuoc(); hang_rao(); tham_co()
    preview_congvien(os.path.join(HERE, "xem_truoc_congvien.png"))
if lam("cong_trinh"):
    cao_oc_kinh(); chung_cu_cu(); phap_thuoc(); plaza(); khach_san_mini()
    preview_quan1(os.path.join(HERE, "xem_truoc_quan1.png"))
if lam("hem"):
    cong_hem()
    for i, (fl, wall, roof) in enumerate([(2, "tuong_mint", "ton"), (3, "tuong_dao", "bon"), (4, "tuong_vang", "bon")]):
        nha_hem(i + 1, fl, wall, roof)
    day_dien_hem(); mieu_nho(); guong_cau_loi(); xe_banh_mi()
    xe_may("XeMayDau_1", "Models/Hem", "nhan_do", "vang", "quan", rider=False)
    xe_may("XeMayDau_2", "Models/Hem", "xanh_xe", "trim", "quan", rider=False)
    nguoi("NguoiDiBo_1", "nhan_xanh", "quan")
    nguoi("NguoiDiBo_2", "hong", "vien", "toc_dai")
    nguoi("NguoiGanhHang", "nhan_do", "vien", "ganh")
    nguoi("HocSinh", "trim", "quan", "hoc_sinh", k=0.72)
if lam("duong"):
    duong_lon(); duong_lon("trai"); duong_lon("phai"); hem_duong()
    dai_cay_le(); khuon_vien(20); khuon_vien(32)
    preview_duong(os.path.join(HERE, "xem_truoc_duong.png"))
if lam("hem"):
    preview_hem(os.path.join(HERE, "xem_truoc_hem.png"))
