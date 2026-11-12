"""Sinh asset low-poly cho Chạy Đơn (bản 2, tham khảo phong cách Low Poly Worlds: cạnh vát, khối đa giác
lộ mặt, màu bão hòa mềm, nhiều chi tiết nhỏ). Hàng hóa 3 món x 3 trạng thái, nhà ống, xe shipper, xe máy AI,
cây, cột điện. Ô tô, xe buýt, xe tải dùng gói "Low Poly Cars" (Broken Vector); bàn ghế quán vỉa hè dùng gói
"Pho Dining Set" (AlleyBits) trên Unity Asset Store.
Chạy: blender --background --factory-startup --python tao_asset_lowpoly.py -- <thu_muc_goc_Art> [cu cong_trinh cong_vien hem duong vat_can xe_ai dia_diem nha_o xe_dong cong_trinh2 hem2 nga_re]
Đơn vị 1 = 1 m; gốc tọa độ ở giữa đáy; mặt trước hướng -Y trong Blender.
Mọi model dùng chung một vật liệu và một ảnh bảng màu (Textures/BangMau_LowPoly.png): mỗi mặt lấy màu
bằng cách đặt UV vào ô màu tương ứng, nên Unity chỉ cần một material cho toàn bộ."""
import bpy, bmesh, sys, os, math, random, colorsys
from mathutils import Vector, Matrix

ROOT = os.path.abspath(sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(__file__))  # tuyệt đối để Blender lưu được ảnh
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
    "uot": "4A4D52", "men_nau": "B0703F",
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


# Bảng màu Quận 3 (bản tối thiểu, GDD 7.4): cùng bố cục ô với BangMau_LowPoly, chỉ đổi tông tường, mái,
# điểm nhấn, cây sang không khí biệt thự kiểu Pháp, hàng cây rợp. Trong Unity chỉ cần đổi ảnh của material.
QUAN3 = {"tuong_kem": "F3E6C8", "tuong_dao": "D8C3A5", "tuong_mint": "BFD8C4", "tuong_vang": "EED48A",
         "tuong_xanh": "A9C3D6", "tuong_cu": "D9CDB6", "ngoi": "A9573C", "ton": "6B8F7B", "nhan_do": "C85A44",
         "nhan_xanh": "3E7CB1", "vang": "F2C94C", "la1": "4E9B47", "la2": "2F7A3E", "la3": "7FB24C",
         "la_dam": "2E6B4F", "vang_phap": "E9C46A", "kinh_xanh": "6E9FB8"}


def make_palette(path=None, ghi_de=None):
    path = path or PAL_PNG
    ghi_de = ghi_de or {}
    n = GRID * 16
    img = bpy.data.images.new(os.path.splitext(os.path.basename(path))[0], n, n, alpha=False)
    px = [0.0] * (n * n * 4)
    for i, name in enumerate(NAMES):
        r, g, b = srgb(ghi_de.get(name, HEX[name]))
        cx, cy = i % GRID, GRID - 1 - i // GRID  # hàng 0 của ảnh là đáy
        for y in range(cy * 16, cy * 16 + 16):
            for x in range(cx * 16, cx * 16 + 16):
                k = (y * n + x) * 4
                px[k:k + 4] = [r, g, b, 1.0]
    img.pixels = px
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    print("BANG MAU", path)


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


def done(name, folder, parts, diem=None):
    """Gộp các khối thành một mesh và xuất FBX. diem = {tên: (x, y, z)} tạo Empty con làm điểm gắn trong Unity."""
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
    for ten, vt in (diem or {}).items():
        e = bpy.data.objects.new(ten, None)
        bpy.context.scene.collection.objects.link(e)
        e.location = vt[:3]
        if len(vt) > 3:  # góc xoay quanh trục đứng; trong Unity trục +Z của điểm là hướng đi tiếp
            e.rotation_euler = (0, 0, math.radians(vt[3]))
        e.parent = o
    d = os.path.join(ROOT, folder)
    os.makedirs(d, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(d, name + ".fbx"), use_selection=False,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             bake_space_transform=True, object_types={"MESH", "EMPTY"}, mesh_smooth_type="FACE",
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


# ---------- Mái nhà: mái hai dốc, mái một dốc có tường hồi đỡ, tum cầu thang trên sân thượng ----------
def lang_tru_yz(diem, x0, x1, col):
    """Lăng trụ có mặt cắt là đa giác `diem` [(y, z), ...] trong mặt phẳng YZ, kéo dài theo X từ x0 tới x1."""
    bm = bmesh.new()
    hai = [[bm.verts.new((x, y, z)) for y, z in diem] for x in (x0, x1)]
    n = len(diem)
    bm.faces.new(hai[0][::-1])
    bm.faces.new(hai[1])
    for k in range(n):
        bm.faces.new((hai[0][k], hai[0][(k + 1) % n], hai[1][(k + 1) % n], hai[1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("tru")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("tru", me)
    bpy.context.scene.collection.objects.link(o)
    return fin(o, col)


def tam_mai(W, ya, za, yb, zb, col, day=0.12, gan=None, buoc_gan=0.5, ong=False):
    """Một tấm mái phẳng nối mép (ya, za) với mép (yb, zb), rộng W theo X. gan: màu gờ ngói hoặc gân tôn chạy theo dốc;
    ong=True dùng ống ngói tròn (ngói âm dương)."""
    dy, dz = yb - ya, zb - za
    L = math.hypot(dy, dz)
    a = math.atan2(dz, dy)  # góc nghiêng so với trục +Y
    tam = Vector(((0, (ya + yb) / 2, (za + zb) / 2)))
    phap = Vector((0, -math.sin(a), math.cos(a)))
    if phap.z < 0:  # luôn lấy pháp tuyến hướng lên trên
        phap = -phap
    p = [box((W, L, day), tuple(tam + phap * day / 2), col, rot=(math.degrees(a), 0, 0), bev=0.02)]
    if gan:
        for k in range(int(W / buoc_gan)):
            x = -W / 2 + buoc_gan / 2 + k * buoc_gan
            vt = tam + phap * (day + 0.03) + Vector((x, 0, 0))
            if ong:
                p.append(cyl(0.06, L, tuple(vt), gan, v=6, rot=(math.degrees(a) - 90, 0, 0)))
            else:
                p.append(box((0.05, L, 0.05), tuple(vt), gan, rot=(math.degrees(a), 0, 0)))
    return p


def mai_hai_mai(W, y0, y1, z0, cao, wall, col="ngoi", gan="do_dam", ong=False, du=0.35):
    """Mái hai dốc, đỉnh chạy dọc mặt tiền (theo trục X) ở giữa y0..y1, chân mái ở z0. Bên dưới là tường hồi
    hình tam giác cùng màu tường nên mái luôn tựa lên nhà, không có khe hở."""
    ym = (y0 + y1) / 2
    zt = z0 + cao
    p = [lang_tru_yz([(y0, z0), (y1, z0), (ym, zt)], -W / 2, W / 2, wall)]
    k = du / (ym - y0)
    p += tam_mai(W + 2 * du, y0 - du, z0 - cao * k, ym, zt, col, gan=gan, ong=ong)
    p += tam_mai(W + 2 * du, y1 + du, z0 - cao * k, ym, zt, col, gan=gan, ong=ong)
    p.append(box((W + 2 * du + 0.1, 0.3, 0.22), (0, ym, zt + 0.1), gan, bev=0.04))
    return p


def mai_mot_mai(W, y0, y1, z0, cao, wall, col="xam_nhat", gan="xam", cao_truoc=False, du=0.25):
    """Mái tôn một dốc phủ y0..y1, thấp ở z0, cao hơn `cao` ở phía sau (hoặc phía trước nếu cao_truoc).
    Hai tường hồi tam giác vuông đỡ mái; gân sóng chạy theo dốc để nhìn ra là tôn."""
    yh, yl = (y0, y1) if cao_truoc else (y1, y0)
    p = [lang_tru_yz([(y0, z0), (y1, z0), (yh, z0 + cao)], -W / 2, W / 2, wall)]
    huong = 1 if yh > yl else -1
    p += tam_mai(W + 2 * du, yl - huong * du, z0 - cao * du / abs(y1 - y0), yh + huong * 0.05, z0 + cao, col,
                 day=0.06, gan=gan, buoc_gan=0.25)
    return p


def tum_thang(W, y, z0, wall, mai="xam_nhat", x=None):
    """Tum cầu thang trên sân thượng: khối 2,4 x 3 m cao 2,5 m có cửa, mái tôn một dốc."""
    x = -W / 2 + 1.4 if x is None else x
    p = [box((2.4, 3.0, 2.5), (x, y + 1.5, z0 + 1.25), wall, bev=0.03),
         box((0.8, 0.06, 1.9), (x + 0.4, y - 0.01, z0 + 0.95), "than_cay")]
    p += dich(mai_mot_mai(2.4, y, y + 3.0, z0 + 2.5, 0.4, wall, col=mai, gan="xam" if mai == "xam_nhat" else "do_dam"), dx=x)
    return p


def tra_sua(state):
    """Ly trà sữa trân châu nắp vòm: nguyên; nghiêng, nắp nứt, đổ ra một ít; đổ hẳn, trân châu văng ra đất."""
    reset()
    random.seed(700 + state)
    p = []
    cup = [lathe([(0.042, 0), (0.044, 0.004), (0.055, 0.17), (0.058, 0.172)], "ly", seg=14),
           lathe([(0.0505, 0.08), (0.0535, 0.13)], "hong", seg=14, caps=(False, False)),
           lathe([(0.05, 0.172), (0.058, 0.172), (0.045, 0.2), (0.02, 0.215)], "kinh_sang", seg=14, caps=(False, True)),
           cyl(0.006, 0.26, (0.012, 0, 0.22), "vien", v=6, rot=(0, 8, 0))]
    for i in range(10):  # trân châu ở đáy nhìn qua thành ly nhạt
        a = random.uniform(0, math.tau)
        cup.append(ball(0.012, (0.044 * math.cos(a), 0.044 * math.sin(a), 0.02 + random.uniform(0, 0.02)), "vien"))
    if state == 0:
        p += cup
    elif state == 1:
        p += [o for o in cup]
        for o in p:
            o.rotation_euler = (math.radians(10), 0, 0)
            activate(o)
            bpy.ops.object.transform_apply(rotation=True)
        p.append(cyl(0.07, 0.004, (0.0, -0.12, 0.002), "giay", v=9, jit=0.01))
    else:
        for o in cup:
            o.rotation_euler = (math.radians(90), 0, math.radians(25))
            o.location = (0, 0, 0.058)
            activate(o)
            bpy.ops.object.transform_apply(location=True, rotation=True)
        p += cup
        p.append(cyl(0.14, 0.004, (0.05, -0.17, 0.002), "giay", v=10, jit=0.02))
        for i in range(12):
            p.append(ball(0.012, (random.uniform(-0.05, 0.15), random.uniform(-0.28, -0.08), 0.01), "vien"))
    done(f"TraSua_{['Nguyen', 'HuMotPhan', 'SapHong'][state]}", "Models/HangHoa", p)


def banh_kem(state):
    """Bánh kem hai tầng trên đế giấy: nguyên; tầng trên lệch, kem quệt; sập bẹp, dâu rơi ra đế."""
    reset()
    random.seed(710 + state)
    p = [cyl(0.17, 0.01, (0, 0, 0.005), "giay", v=14)]
    if state < 2:
        lech = 0.0 if state == 0 else 0.035
        nghieng = 0 if state == 0 else 9
        p += [cyl(0.13, 0.08, (0, 0, 0.05), "trim", v=16, bev=0.008),
              lathe([(0.131, 0.085), (0.133, 0.095)], "hong", seg=16, caps=(False, False))]
        tren = [cyl(0.085, 0.07, (0, 0, 0.125), "trim", v=14, bev=0.006),
                lathe([(0.086, 0.155), (0.088, 0.163)], "hong", seg=14, caps=(False, False))]
        for k in range(6):
            a = k / 6 * math.tau
            tren.append(ball(0.016, (0.06 * math.cos(a), 0.06 * math.sin(a), 0.17), "nhan_do"))
        for x in (-0.02, 0.02):
            tren.append(cyl(0.004, 0.05, (x, 0, 0.185), "vang", v=5))
        for o in tren:
            o.location = (lech, 0, 0)
            o.rotation_euler = (0, math.radians(nghieng), 0)
            activate(o)
            bpy.ops.object.transform_apply(location=True, rotation=True)
        p += tren
        if state == 1:
            p.append(box((0.06, 0.02, 0.03), (-0.09, -0.11, 0.06), "trim", rot=(0, 0, 30), jit=0.004))
    else:
        p += [cyl(0.15, 0.05, (0, 0, 0.035), "trim", v=12, jit=0.012),
              cyl(0.1, 0.03, (0.05, 0.02, 0.07), "trim", v=10, jit=0.01, rot=(0, 15, 0))]
        for k in range(6):
            p.append(ball(0.016, (random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0.02), "nhan_do"))
        p.append(box((0.08, 0.06, 0.02), (-0.12, -0.08, 0.015), "hong", jit=0.006))
    done(f"BanhKem_{['Nguyen', 'HuMotPhan', 'SapHong'][state]}", "Models/HangHoa", p)


def vi_trung(state):
    """Vỉ trứng 3 x 4: nguyên; vài quả nứt rỉ lòng đỏ; vỡ nhiều, lòng trứng chảy ra ngoài vỉ."""
    reset()
    random.seed(720 + state)
    p = [box((0.22, 0.29, 0.03), (0, 0, 0.015), "giay", bev=0.005)]
    vi_tri = [(-0.07 + i * 0.07, -0.105 + j * 0.07) for i in range(3) for j in range(4)]
    vo = set() if state == 0 else set(random.sample(range(12), 2 if state == 1 else 7))
    for idx, (x, y) in enumerate(vi_tri):
        p.append(cyl(0.028, 0.02, (x, y, 0.035), "giay", v=8))
        if idx in vo and state == 2:
            p += [ball(0.026, (x, y, 0.045), "trim", scale=(1, 1, 0.45), jit=0.006),
                  cyl(0.018, 0.006, (x, y, 0.06), "vang", v=8)]
        else:
            p.append(ball(0.025, (x, y, 0.07), "trim", sub=2, scale=(0.85, 0.85, 1.15)))
            if idx in vo:
                p.append(limb((x - 0.015, y - 0.02, 0.08), (x + 0.01, y - 0.022, 0.065), 0.004, "vien", bev=0))
                p.append(cyl(0.012, 0.004, (x + 0.02, y - 0.03, 0.033), "vang", v=8))
    if state == 2:
        p += [cyl(0.09, 0.004, (0.14, -0.08, 0.002), "trim", v=10, jit=0.015),
              cyl(0.03, 0.006, (0.14, -0.08, 0.004), "vang", v=8)]
    done(f"ViTrung_{['Nguyen', 'HuMotPhan', 'SapHong'][state]}", "Models/HangHoa", p)


# ---------- Nhà ống (rộng 4 m, sâu 10 m, mặt tiền ở y = 0 quay về -Y) ----------
def chau_cay(x, y, z, s=1.0):
    return [cyl(0.15 * s, 0.3 * s, (x, y, z + 0.15 * s), "dat", v=7, r2=0.19 * s, bev=0.01),
            ball(0.25 * s, (x, y, z + 0.42 * s), "la1", jit=0.04 * s, scale=(1, 1, 0.85)),
            ball(0.16 * s, (x + 0.12 * s, y - 0.05, z + 0.55 * s), "la2", jit=0.03 * s)]


def xoay(parts, do):
    """Xoay các khối đã hoàn thiện quanh trục đứng qua gốc tọa độ."""
    for o in parts:
        o.data.transform(Matrix.Rotation(math.radians(do), 4, "Z"))
    return parts


def ma_no_canh(x, y, ao, dai=False):
    """Ma-nơ-canh trưng bày: đế tròn, hai chân, thân áo, đầu trắng; dai=True mặc áo dài tà dài."""
    p = [cyl(0.18, 0.04, (x, y, 0.02), "sat", v=10), ball(0.1, (x, y, 1.5), "trim", sub=2)]
    if dai:
        p += [cyl(0.2, 1.1, (x, y, 0.6), "trim", v=8, r2=0.13),
              cyl(0.24, 1.05, (x, y, 0.78), ao, v=8, r2=0.13),
              box((0.3, 0.18, 0.45), (x, y, 1.18), ao, taper=(0.8, 0.9), bev=0.04)]
    else:
        p += [cyl(0.05, 0.75, (x + sx * 0.08, y, 0.42), "sat", v=6) for sx in (-1, 1)]
        p += [box((0.36, 0.2, 0.6), (x, y, 1.1), ao, taper=(1.15, 1), bev=0.04)]
    return p


def bien_doc(chu, x, y, ztren, nen, col):
    """Biển dọc gắn vuông góc mặt tiền (kiểu biển chồng lớp phố Quận 1): tấm đứng trong mặt phẳng YZ chìa ra
    đường, mỗi chữ cái một hàng, chữ có ở hai mặt quay về hai đầu đường (±X)."""
    ky_tu = [c for c in chu if c != " "]
    h = 0.42 * len(ky_tu) + 0.3
    p = [box((0.12, 0.75, h), (x, y, ztren - h / 2), nen, bev=0.03),
         box((0.14, 0.62, h - 0.16), (x, y, ztren - h / 2), "trim", bev=0.01),
         box((0.06, 0.06, 0.06), (x, y + 0.42, ztren - 0.2), "sat"),
         box((0.06, 0.06, 0.06), (x, y + 0.42, ztren - h + 0.2), "sat")]
    for i, c in enumerate(ky_tu):
        z = ztren - 0.35 - i * 0.42
        for mat in (-1, 1):
            o = chu_3d(c, (0, 0, 0), 0.5, 0.32, col)
            o.data.transform(Matrix.Rotation(math.radians(-90 * mat), 4, "Z"))  # mặt chữ quay về ±X
            o.data.transform(Matrix.Translation((x + mat * 0.08, y, z)))
            p.append(o)
    return p


def mai_hien(W, kieu, awn):
    """Mái hiên tầng trệt: soc (bạt sọc), tron (bạt một màu có diềm), ton (tôn dốc có gân), None (không mái)."""
    p = []
    if kieu == "soc":
        n = 8
        for k in range(n):
            x = -W / 2 + (k + 0.5) * W / n
            c = awn[k % 2]
            p.append(box((W / n + 0.002, 1.5, 0.05), (x, -0.7, 2.62), c, rot=(22, 0, 0)))
            p.append(box((W / n + 0.002, 0.04, 0.22), (x, -1.4, 2.25), c))
    elif kieu == "tron":
        p.append(box((W - 0.2, 1.3, 0.05), (0, -0.62, 2.68), awn[0], rot=(16, 0, 0)))
        for k in range(int(W / 0.4)):  # diềm răng cưa
            p.append(box((0.3, 0.04, 0.18), (-W / 2 + 0.3 + k * 0.4, -1.26, 2.43), awn[0]))
        p.append(box((W - 0.2, 0.05, 0.05), (0, -1.27, 2.52), "trim"))
    elif kieu == "ton":
        p.append(box((W, 1.6, 0.05), (0, -0.78, 2.5), "ton", rot=(12, 0, 0)))
        for k in range(int(W / 0.25)):
            p.append(box((0.04, 1.6, 0.04), (-W / 2 + 0.12 + k * 0.25, -0.78, 2.54), "xam", rot=(12, 0, 0)))
        for x in (-W / 2 + 0.15, W / 2 - 0.15):
            p.append(cyl(0.04, 2.2, (x, -1.5, 1.1), "sat", v=6))
    return p


def tang_tret(W, kieu, awn, seed):
    """Mặt tiền tầng trệt nhà ống theo loại hình kinh doanh thường gặp ở phố Quận 1.
    quan_an (bàn inox, ghế nhựa, tủ kính xe phở), tap_hoa (kệ hàng, két nước, dây bim bim), cafe (cửa kính khung gỗ,
    bàn ghế thấp), nha_thuoc, dien_thoai, thoi_trang, ao_dai (mặt kính, ma-nơ-canh), dong_cua (cửa cuốn đóng, xe đậu)."""
    random.seed(seed)
    Wo = W - 0.64
    p = []
    mo = kieu in ("quan_an", "tap_hoa")
    if mo or kieu == "dong_cua":
        p.append(box((Wo, 0.1, 2.6), (0, -0.02, 1.3), "sat"))
    if mo:  # cửa cuốn cuộn lên gần hết
        p.append(box((Wo, 0.14, 0.45), (0, -0.05, 2.4), "xam_nhat", bev=0.02))
        for k in range(2):
            p.append(box((Wo, 0.16, 0.03), (0, -0.05, 2.25 + k * 0.18), "xam"))
    if kieu == "dong_cua":
        p.append(box((Wo, 0.12, 2.6), (0, -0.08, 1.3), "xam_nhat"))
        for k in range(16):
            p.append(box((Wo, 0.13, 0.025), (0, -0.09, 0.1 + k * 0.16), "xam"))
        p += [box((0.7, 0.14, 1.8), (Wo / 2 - 0.7, -0.1, 0.9), "xam", bev=0.01),  # cửa nhỏ trên cửa cuốn
              box((0.06, 0.16, 0.06), (Wo / 2 - 0.45, -0.12, 0.95), "sat")]
        for x, mau in ((-0.8, "nhan_do"), (0.2, "xanh_xe")):  # xe đậu sát cửa, đầu xe quay vào nhà
            p += dich(xoay(than_xe_so(mau, baga=False), 180), dx=x, dy=-1.1)
    elif kieu in ("cafe", "nha_thuoc", "dien_thoai", "thoi_trang", "ao_dai"):
        khung = {"cafe": "than_cay", "dien_thoai": "sat"}.get(kieu, "trim")
        lui = 0.0
        p.append(box((Wo, 0.08, 2.6), (0, -0.02, 1.3), "kinh", bev=0.01))
        n = max(2, round(Wo / 1.2))
        for k in range(n + 1):  # đố khung kính
            p.append(box((0.08, 0.12, 2.6), (-Wo / 2 + k * Wo / n, lui - 0.05, 1.3), khung))
        p += [box((Wo, 0.12, 0.1), (0, lui - 0.05, 2.15), khung),
              box((Wo, 0.12, 0.1), (0, lui - 0.05, 0.05), khung)]
        if kieu == "cafe":
            for x in (-W / 2 + 0.9, W / 2 - 0.9):  # bàn thấp và ghế đẩu trên vỉa hè
                p += [box((0.5, 0.5, 0.04), (x, -1.2, 0.42), "than_cay"), cyl(0.03, 0.42, (x, -1.2, 0.21), "sat", v=6)]
                for dx in (-0.4, 0.4):
                    p.append(cyl(0.13, 0.25, (x + dx, -1.2, 0.125), random.choice(["nhan_do", "nhan_xanh", "vang"]), v=8, r2=0.11))
            p += chau_cay(-0.3, -0.35, 0.0, 1.1) + chau_cay(0.4, -0.35, 0.0, 0.9)
        elif kieu == "nha_thuoc":
            p += [box((Wo - 0.2, 0.06, 0.5), (0, -0.09, 1.75), "trim", bev=0.01)]
            for k in range(int(Wo / 0.35)):  # hộp thuốc trưng ở ô kính trên
                p.append(box((0.22, 0.05, 0.3), (-Wo / 2 + 0.3 + k * 0.35, -0.13, 1.75),
                             random.choice(["la_dam", "nhan_xanh", "trim", "vang"])))
            p += [box((0.5, 0.4, 1.0), (W / 2 - 0.7, -0.35, 0.5), "trim", bev=0.03),  # máy đo huyết áp/kệ
                  box((0.52, 0.42, 0.12), (W / 2 - 0.7, -0.35, 1.0), "la_dam")]
        elif kieu == "dien_thoai":
            for k, mau in enumerate(("vang", "nhan_xanh", "nhan_do", "vang")):  # áp phích dán trên kính
                if -Wo / 2 + 0.6 + k * 0.9 < Wo / 2 - 0.3:
                    p.append(box((0.6, 0.02, 0.85), (-Wo / 2 + 0.6 + k * 0.9, -0.09, 1.3), mau))
                    p.append(box((0.3, 0.025, 0.5), (-Wo / 2 + 0.6 + k * 0.9, -0.1, 1.38), "vien"))
            p += [box((0.6, 0.4, 0.9), (0, -0.5, 0.45), "trim", bev=0.02),
                  box((0.6, 0.4, 0.06), (0, -0.5, 0.92), "vang")]
        else:  # thoi_trang, ao_dai: ma-nơ-canh đứng trước mặt kính
            mau_ao = ["hong", "vang", "trim", "nhan_xanh", "nhan_do", "tim"]
            random.shuffle(mau_ao)
            so = max(2, int(Wo / 1.1))
            p.append(box((Wo - 0.2, 0.7, 0.12), (0, -0.45, 0.06), "trim", bev=0.02))  # bục trưng bày trước mặt kính
            for k in range(so):
                p += dich(ma_no_canh(-Wo / 2 + (k + 0.5) * Wo / so, -0.45, mau_ao[k], dai=(kieu == "ao_dai")), dz=0.12)
    if kieu == "quan_an":
        p += [box((1.2, 0.6, 0.85), (-W / 2 + 1.0, -0.45, 0.43), "trim", bev=0.02),  # tủ kính xe phở
              box((1.1, 0.55, 0.5), (-W / 2 + 1.0, -0.45, 1.1), "kinh_sang", bev=0.02),
              box((1.22, 0.62, 0.05), (-W / 2 + 1.0, -0.45, 1.37), "nhan_do"),
              cyl(0.28, 0.5, (-W / 2 + 1.0, 0.1, 1.1), "xam_nhat", v=12)]  # nồi nước dùng
        for x in ([0.6] if W < 5 else [0.2, 1.8]):
            p += [box((0.75, 0.75, 0.04), (x, -1.1, 0.72), "xam_nhat", bev=0.01),
                  cyl(0.03, 0.7, (x, -1.1, 0.36), "xam_nhat", v=6),
                  cyl(0.05, 0.22, (x + 0.2, -1.1, 0.85), "nhan_do", v=6)]  # ống đũa
            for dx in (-0.55, 0.55):
                p.append(cyl(0.15, 0.3, (x + dx, -1.1, 0.15), random.choice(["nhan_do", "nhan_xanh"]), v=8, r2=0.13))
    elif kieu == "tap_hoa":
        for z in (0.5, 1.1, 1.7):
            p.append(box((Wo - 0.6, 0.4, 0.05), (0, -0.2, z), "than_cay"))
            for i in range(int((Wo - 0.8) / 0.3)):
                p.append(box((0.22, 0.25, random.uniform(0.2, 0.4)), (-Wo / 2 + 0.55 + i * 0.3, -0.2, z + 0.15),
                             random.choice(["nhan_do", "vang", "nhan_xanh", "la1", "cam", "tim"]), bev=0.01))
        for k in range(3):  # két nước suối chồng trước cửa
            p.append(box((0.5, 0.35, 0.3), (W / 2 - 0.7, -0.9, 0.15 + k * 0.31), "nhan_xanh" if k % 2 else "trim", bev=0.02))
        for i in range(int(W / 0.45)):  # dây bim bim treo dưới mái hiên
            p.append(box((0.12, 0.03, 0.45), (-W / 2 + 0.3 + i * 0.45, -1.2, 1.95), random.choice(["vang", "nhan_do", "la1", "cam"])))
    p += mai_hien(W, {"quan_an": "soc", "tap_hoa": "ton", "cafe": "tron", "dong_cua": None,
                      "nha_thuoc": None, "dien_thoai": None, "thoi_trang": None, "ao_dai": "tron"}[kieu], awn)
    return p


def nha(idx, floors, wall, awn, shutter, roof, W=4.0, tiem="quan_an", ten=None, bien="lan_can"):
    """Nhà ống mặt phố. W: bề ngang lô đất (4 m một lô, 8 m hai lô). tiem: loại hình ở tầng trệt (xem tang_tret).
    ten: chữ trên biển hiệu. bien: lan_can (biển trên lan can tầng 2), to (biển lớn che gần hết tầng 2),
    mat (dải biển ngay trên cửa tầng trệt, tầng 2 để ban công), doc (biển dọc chìa ra đường), None (không biển)."""
    reset()
    random.seed(40 + idx)
    D, F = 10.0, 3.2
    cac_cua = [-W / 2 + (i + 0.5) * W / max(2, round(W / 2)) for i in range(max(2, round(W / 2)))]
    H = floors * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04)]
    # Tầng trệt: hai cột, mặt tiền theo loại hình kinh doanh
    for s in (-1, 1):
        p.append(box((0.32, 0.22, F), (s * (W / 2 - 0.16), -0.1, F / 2), "trim", bev=0.03))
    p += tang_tret(W, tiem, awn, 400 + idx)
    random.seed(40 + idx)
    if bien == "mat" and ten:  # dải biển ngay trên cửa
        p += [box((W - 0.5, 0.14, 0.42), (0, -0.1, 2.93), awn[0], bev=0.03),
              box((W - 0.8, 0.04, 0.3), (0, -0.19, 2.93), "trim", bev=0.01),
              chu_3d(ten, (0, -0.215, 2.93), W - 1.2, 0.28, awn[0])]
    if bien == "doc" and ten:
        p += bien_doc(ten, W / 2 - 0.25, -1.45, 2 * F - 0.1, awn[0], awn[0])
    # Các tầng trên
    for f in range(1, floors):
        z = f * F
        p.append(box((W + 0.04, 0.08, 0.14), (0, -0.02, z - 0.1), "trim"))
        p.append(box((W, 1.0, 0.16), (0, -0.5, z), "trim", bev=0.03))
        if f == 1 and bien == "lan_can" and ten:  # biển hiệu trên lan can tầng 2
            p.append(box((W - 0.1, 0.14, 0.9), (0, -1.02, z + 0.55), awn[0], bev=0.04))
            p.append(box((W - 0.4, 0.04, 0.6), (0, -1.1, z + 0.55), "trim", bev=0.01))
            p.append(chu_3d(ten, (0, -1.125, z + 0.55), W - 0.9, 0.38, awn[0]))
        elif f == 1 and bien == "to" and ten:  # biển lớn che gần hết tầng 2
            p.append(box((W - 0.1, 0.16, 1.9), (0, -1.03, z + 1.1), awn[0], bev=0.04))
            p.append(box((W - 0.4, 0.04, 1.55), (0, -1.12, z + 1.1), "trim", bev=0.01))
            p.append(chu_3d(ten, (0, -1.145, z + 1.3), W - 0.9, 0.6, awn[0]))
            p.append(box((W - 1.2, 0.03, 0.08), (0, -1.15, z + 0.55), awn[1] if awn[1] != "trim" else "vien"))
        else:
            p.append(box((W, 0.07, 0.07), (0, -0.97, z + 0.95), "sat", bev=0.01))
            for k in range(int(W / 0.2) - 1):
                p.append(box((0.03, 0.03, 0.85), (-W / 2 + 0.1 + k * 0.2, -0.97, z + 0.5), "sat"))
        for x in cac_cua:  # cửa sổ: khung, kính, chớp hai bên
            p.append(box((1.2, 0.06, 2.1), (x, -0.02, z + 1.2), "trim", bev=0.02))
            p.append(box((0.95, 0.1, 1.85), (x, -0.03, z + 1.15), "kinh"))
            p.append(box((0.04, 0.12, 1.85), (x, -0.04, z + 1.15), "trim"))
            for sx in (-1, 1):
                p.append(box((0.22, 0.06, 1.85), (x + sx * 0.73, -0.06, z + 1.15), shutter, bev=0.01))
        if (f + idx) % 2 == 0:  # cục nóng máy lạnh
            xm = W / 2 - 0.65
            p.append(box((0.8, 0.32, 0.55), (xm, -0.18, z + 2.7), "trim", bev=0.03))
            p.append(cyl(0.18, 0.04, (xm + 0.12, -0.35, z + 2.7), "xam", v=10, rot=(90, 0, 0)))
            p.append(cyl(0.05, 0.05, (xm + 0.12, -0.37, z + 2.7), "sat", v=6, rot=(90, 0, 0)))
        if f > 1 or floors == 2:
            p += chau_cay(-W / 2 + 0.5 + random.uniform(0, 0.3), -0.75, z + 0.08, 1.0)
            if random.random() < 0.6:
                p += chau_cay(W / 2 - 0.6, -0.7, z + 0.08, 0.8)
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
        p += tum_thang(W, 3.0, H + 0.2, wall, mai="xam_nhat" if roof == "ton" else "ngoi")
        p += chau_cay(1.2, 1.2, H + 0.2, 1.0)
    done(f"NhaOng_{idx}", "Models/Pho", p)


# ---------- Xe máy tay ga và người lái (đầu xe hướng -Y) ----------
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


def nha_hem(idx, floors, wall, roof, W=4.0):
    """Nhà trong hẻm (4 m một lô, 6–8 m nhà rộng): cửa sắt xếp, mái tôn che cửa, cửa sổ có song sắt,
    ban công phơi đồ, đồng hồ điện."""
    reset()
    random.seed(140 + idx)
    D, F = 8.0, 3.0
    cac_cua = [0.0] if W < 5 else [-W / 4, W / 4]
    H = floors * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((3.0, 0.08, 2.4), (-0.3, -0.02, 1.2), "vien"),
         box((W, 1.0, 0.05), (0, -0.48, 2.75), "ton", rot=(15, 0, 0)),
         box((0.3, 0.12, 0.4), (W / 2 - 0.4, -0.06, 1.6), "xam", bev=0.02),
         box((0.35, 0.04, 0.22), (W / 2 - 0.4, -0.04, 2.25), "nhan_xanh")]
    if W >= 5:
        p += cua_so_song(W / 2 - 1.4, 1.5, w=1.2)
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
                  limb((-W / 2 + 0.1, -0.6, z + 1.9), (W / 2 - 0.1, -0.6, z + 1.9), 0.02, "sat", bev=0)]
            for k in range(int(W / 0.8)):
                x = -W / 2 + 0.5 + k * 0.8
                p.append(box((0.4, 0.04, 0.55), (x, -0.6, z + 1.6),
                             random.choice(["nhan_do", "vang", "nhan_xanh", "trim", "tim", "hong"])))
            p += chau_cay(W / 2 - 0.6, -0.5, z + 0.11, 0.6)
        else:  # cửa sổ song sắt
            for xc in cac_cua:
                p.append(box((1.6, 0.08, 1.4), (xc, -0.03, z + 1.4), "kinh"))
                for k in range(7):
                    p.append(box((0.03, 0.06, 1.4), (xc - 0.7 + k * 0.233, -0.08, z + 1.4), "sat"))
            p.append(box((0.7, 0.3, 0.45), (W / 2 - 0.7, -0.17, z + 2.4), "trim", bev=0.03))
    p.append(box((W, 0.15, 0.6), (0, 0.05, H + 0.3), wall))
    if roof == "bon":
        p.append(cyl(0.45, 1.0, (0.8, 2.0, H + 0.75), "xam_nhat", v=10, rot=(0, 90, 0)))
        p.append(box((1.0, 0.6, 0.25), (0.8, 2.0, H + 0.12), "sat"))
    else:
        p += tum_thang(W, 2.5, H, wall)
    p.append(cyl(0.03, 2.5, (W / 2 - 0.5, 6.5, H + 1.25), "sat", v=4))
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
    diem = {"DiemNoi": (0, -L, 0, 0)}
    if loi_hem == "trai":
        diem["DiemVaoHem"] = (x_le + le / 2, -50, 0, 90)
    elif loi_hem == "phai":
        diem["DiemVaoHem"] = (-(x_le + le / 2), -50, 0, -90)
    done(ten, "Models/Duong", p, diem)


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
    done("Hem_50m", "Models/Duong", p, {"DiemNoi": (0, -L, 0, 0)})


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
def nguoi(name, ao, quan, kieu="thuong", k=1.0, toc="toc", phu="nhan_do"):
    """Người đi bộ dáng chibi cùng phong cách với shipper. kieu: thuong (tóc ngắn), toc_dai,
    ganh (nón lá, đòn gánh hai thúng trái cây), hoc_sinh (nhỏ hơn, cặp sau lưng, khăn quàng đỏ),
    ong_cu (tóc bạc, chống gậy), ve_so (mũ lưỡi trai, cầm bảng vé số), van_phong (cà vạt, túi đeo chéo),
    ao_dai (tà áo dài trước sau, tóc dài), the_duc (quần đùi, giày thể thao), tre_em (mũ lưỡi trai).
    phu: màu mũ lưỡi trai (ve_so, tre_em)."""
    reset()
    v = lambda x, y, z: (x * k, y * k, z * k)
    p = []
    giay = "trim" if kieu in ("hoc_sinh", "the_duc", "ao_dai", "tre_em") else "vien"
    for s_, dy in ((-1, -0.16), (1, 0.14)):  # chân: một chân bước tới, một chân sau
        if kieu == "the_duc":
            goi = v(s_ * 0.1, dy * 0.5, 0.36)
            p.append(limb(v(s_ * 0.1, 0, 0.62), goi, 0.17 * k, quan, bev=0.05 * k))
            p.append(limb(goi, v(s_ * 0.1, dy, 0.1), 0.13 * k, "da_nguoi", bev=0.04 * k))
        else:
            p.append(limb(v(s_ * 0.1, 0, 0.62), v(s_ * 0.1, dy, 0.1), 0.16 * k, quan, bev=0.05 * k))
        p.append(bo_tron(1, v(s_ * 0.1, dy - 0.04, 0.06), giay, (0.07 * k, 0.13 * k, 0.055 * k)))
    p += [box((0.42 * k, 0.26 * k, 0.5 * k), v(0, 0, 0.85), ao, taper=(1.08, 1.0), bev=0.1 * k),
          cyl(0.06 * k, 0.08 * k, v(0, 0, 1.12), "da_nguoi", v=8),
          ball(0.2 * k, v(0, 0, 1.3), "da_nguoi", sub=2)]

    def tay_dua(trai=True, phai=True):
        for s_, dy, co in ((1, -0.14, phai), (-1, 0.14, trai)):  # tay đánh ngược chân
            if co:
                p.append(limb(v(s_ * 0.23, 0, 1.04), v(s_ * 0.27, dy, 0.7), 0.11 * k, ao, bev=0.035 * k))
                p.append(ball(0.06 * k, v(s_ * 0.28, dy * 1.05, 0.66), "da_nguoi", sub=2))

    def mu_luoi_trai(col):
        p.extend([bo_tron(0.212 * k, v(0, 0.02, 1.37), col, (1, 1, 0.7)),
                  box((0.24 * k, 0.16 * k, 0.025 * k), v(0, -0.2, 1.35), col, bev=0.01 * k)])

    if kieu == "ganh":
        p += [limb(v(0.23, 0, 1.04), v(0.2, -0.28, 1.16), 0.11 * k, ao, bev=0.035 * k),
              ball(0.06 * k, v(0.2, -0.3, 1.16), "da_nguoi", sub=2),
              limb(v(-0.23, 0, 1.04), v(-0.27, 0.14, 0.7), 0.11 * k, ao, bev=0.035 * k),
              ball(0.06 * k, v(-0.28, 0.15, 0.66), "da_nguoi", sub=2),
              cyl(0.42 * k, 0.22 * k, v(0, 0, 1.55), "giay", v=14, r2=0.0),
              limb(v(0.2, -0.9, 1.16), v(0.2, 0.9, 1.16), 0.045 * k, "than_cay", bev=0)]
        for y in (-0.85, 0.85):
            for dx in (-0.12, 0.12):
                p.append(limb(v(0.2, y, 1.16), v(0.2 + dx, y, 0.5), 0.012 * k, "than_cay", bev=0))
            p.append(cyl(0.27 * k, 0.22 * k, v(0.2, y, 0.39), "giay", v=10, r2=0.2 * k))
            for j in range(4):
                p.append(ball(0.07 * k, v(0.2 + (j % 2 - 0.5) * 0.15, y + (j // 2 - 0.5) * 0.15, 0.52),
                              ["vang", "nhan_do", "la1", "cam"][j]))
        done(name, "Models/Nguoi", p)
        return
    if kieu == "ve_so":  # hai tay cầm bảng vé số trước ngực
        for s_ in (-1, 1):
            p += [limb(v(s_ * 0.23, 0, 1.04), v(s_ * 0.15, -0.3, 0.88), 0.11 * k, ao, bev=0.035 * k),
                  ball(0.06 * k, v(s_ * 0.14, -0.33, 0.88), "da_nguoi", sub=2)]
        p.append(box((0.44 * k, 0.03 * k, 0.32 * k), v(0, -0.36, 0.92), "trim", bev=0.01 * k))
        for j, col in enumerate(("vang", "nhan_xanh", "hong", "la3")):
            p.append(box((0.38 * k, 0.035 * k, 0.05 * k), v(0, -0.37, 1.03 - j * 0.07), col))
    elif kieu == "ong_cu":  # tay phải chống gậy
        tay_dua(trai=True, phai=False)
        p += [limb(v(0.23, 0, 1.04), v(0.3, -0.2, 0.72), 0.11 * k, ao, bev=0.035 * k),
              ball(0.06 * k, v(0.3, -0.22, 0.7), "da_nguoi", sub=2),
              limb(v(0.3, -0.22, 0.72), v(0.33, -0.32, 0.0), 0.04 * k, "than_cay", bev=0),
              limb(v(0.28, -0.22, 0.74), v(0.33, -0.22, 0.74), 0.04 * k, "than_cay", bev=0)]
    else:
        tay_dua()
    p.append(bo_tron(0.208 * k, v(0, 0.03, 1.35), toc, (1, 1, 0.85)))
    if kieu in ("toc_dai", "ao_dai"):
        p.append(box((0.3 * k, 0.1 * k, 0.4 * k), v(0, 0.14, 1.14), toc, bev=0.05 * k))
    if kieu == "ao_dai":  # hai tà áo dài trước sau buông tới bắp chân
        p += [box((0.32 * k, 0.03 * k, 0.5 * k), v(0, -0.14, 0.4), ao, taper=(1.15, 1), bev=0.01 * k),
              box((0.32 * k, 0.03 * k, 0.5 * k), v(0, 0.14, 0.4), ao, taper=(1.15, 1), bev=0.01 * k)]
    if kieu == "van_phong":  # cà vạt, cổ áo, túi đeo chéo
        p += [box((0.16 * k, 0.1 * k, 0.06 * k), v(0, -0.08, 1.08), "trim", bev=0.01 * k),
              box((0.06 * k, 0.02 * k, 0.26 * k), v(0, -0.14, 0.93), "nhan_do"),
              box((0.08 * k, 0.3 * k, 0.24 * k), v(-0.3, 0.06, 0.62), "vien", bev=0.02 * k),
              limb(v(0.18, 0.0, 1.08), v(-0.3, 0.06, 0.75), 0.025 * k, "vien", bev=0)]
    if kieu in ("ve_so", "tre_em"):
        mu_luoi_trai(phu)
    if kieu == "hoc_sinh":
        p += [box((0.32 * k, 0.16 * k, 0.34 * k), v(0, 0.21, 0.86), "nhan_xanh", bev=0.05 * k),
              limb(v(-0.13, 0.1, 1.06), v(-0.13, 0.2, 1.02), 0.03 * k, "vien", bev=0),
              limb(v(0.13, 0.1, 1.06), v(0.13, 0.2, 1.02), 0.03 * k, "vien", bev=0),
              cyl(0.09 * k, 0.03 * k, v(0, -0.14, 1.05), "nhan_do", v=3, rot=(90, 0, 180))]
    done(name, "Models/Nguoi", p)


def nguoi_ngoi_ghe(name, ao, quan, toc_dai=False, ghe="nhan_do"):
    """Người ngồi ghế nhựa thấp ở quán vỉa hè, một tay cầm ly cà phê."""
    reset()
    p = [cyl(0.17, 0.3, (0, 0.05, 0.15), ghe, v=8, r2=0.14), cyl(0.18, 0.03, (0, 0.05, 0.31), ghe, v=8)]
    for s_ in (-1, 1):
        p += [limb((s_ * 0.1, 0.05, 0.4), (s_ * 0.12, -0.32, 0.5), 0.16, quan, bev=0.05),
              limb((s_ * 0.12, -0.32, 0.5), (s_ * 0.12, -0.38, 0.1), 0.13, quan, bev=0.04),
              bo_tron(1, (s_ * 0.12, -0.42, 0.06), "vien", (0.07, 0.13, 0.055))]
    p += [box((0.42, 0.26, 0.5), (0, 0.04, 0.65), ao, taper=(1.08, 1.0), bev=0.1),
          cyl(0.06, 0.08, (0, 0.03, 0.92), "da_nguoi", v=8),
          ball(0.2, (0, 0.02, 1.1), "da_nguoi", sub=2),
          bo_tron(0.208, (0, 0.05, 1.15), "toc", (1, 1, 0.85)),
          limb((0.23, 0.04, 0.84), (0.18, -0.22, 0.72), 0.11, ao, bev=0.035),
          ball(0.06, (0.16, -0.25, 0.75), "da_nguoi", sub=2),
          cyl(0.035, 0.1, (0.16, -0.27, 0.82), "ly", v=8),
          cyl(0.036, 0.01, (0.16, -0.27, 0.865), "caphe", v=8),
          limb((-0.23, 0.04, 0.84), (-0.16, -0.3, 0.55), 0.11, ao, bev=0.035),
          ball(0.06, (-0.15, -0.32, 0.53), "da_nguoi", sub=2)]
    if toc_dai:
        p.append(box((0.3, 0.1, 0.4), (0, 0.16, 0.94), "toc", bev=0.05))
    done(name, "Models/Nguoi", p)


# ---------- Vật cản (đặt được trên đường lớn lẫn trong hẻm; mặt hướng về người chơi là +Y Blender = -Z Unity) ----------
def dia(rx, ry, z, col, v=12, meo=0.0, loc=(0, 0), day=0.008):
    """Đĩa dẹt hình elip, mép méo ngẫu nhiên (lòng ổ gà, mặt nước)."""
    o = cyl(1, day, (0, 0, z), col, v=v)
    he_so = {}
    for vt in o.data.vertices:
        k = round(math.atan2(vt.co.y, vt.co.x), 3)
        f = he_so.setdefault(k, random.uniform(1 - meo, 1 + meo))
        vt.co.x = vt.co.x * rx * f + loc[0]
        vt.co.y = vt.co.y * ry * f + loc[1]
    return o


def o_ga(kieu):
    """Ổ gà: lòng tối, mép nhựa vỡ nhô lên, vết nứt tỏa ra để nhìn rõ từ xa. kieu: 1 tròn, 2 vệt dài, cum (3 hố nhỏ)."""
    reset()
    random.seed({"1": 200, "2": 210, "cum": 220}[kieu])
    p = []
    ho = {"1": [(0, 0, 0.65, 0.5)], "2": [(-0.45, 0.05, 0.5, 0.36), (0.45, -0.05, 0.6, 0.38)],
          "cum": [(-0.5, 0.2, 0.36, 0.28), (0.35, -0.2, 0.42, 0.32), (0.05, 0.5, 0.28, 0.22)]}[kieu]
    for x, y, rx, ry in ho:
        p.append(dia(rx + 0.14, ry + 0.12, 0.003, "xam", v=12, meo=0.18, loc=(x, y), day=0.006))  # mép nhựa vỡ sáng
        p.append(dia(rx, ry, 0.006, "vien", v=11, meo=0.15, loc=(x, y), day=0.01))                # lòng hố tối
        p.append(dia(rx * 0.55, ry * 0.55, 0.012, "dat", v=9, meo=0.2, loc=(x + 0.04, y - 0.03)))  # đất đáy hố
        n = 9
        for k in range(n):  # mảnh nhựa vỡ quanh mép
            a = k / n * math.tau + random.uniform(-0.2, 0.2)
            p.append(box((random.uniform(0.14, 0.24), random.uniform(0.09, 0.15), 0.04),
                         (x + (rx + 0.08) * math.cos(a), y + (ry + 0.08) * math.sin(a), 0.02), "xam",
                         rot=(random.uniform(-8, 8), random.uniform(-8, 8), math.degrees(a)), jit=0.008))
        for k in range(4):  # vết nứt
            a = random.uniform(0, math.tau)
            r0, r1 = max(rx, ry) + 0.05, max(rx, ry) + random.uniform(0.25, 0.45)
            p.append(limb((x + r0 * math.cos(a), y + r0 * math.sin(a), 0.006),
                          (x + r1 * math.cos(a + 0.2), y + r1 * math.sin(a + 0.2), 0.006), 0.022, "vien", bev=0))
        for k in range(3):  # sỏi văng ra
            a = random.uniform(0, math.tau)
            p.append(ball(0.03, (x + (rx + 0.2) * math.cos(a), y + (ry + 0.2) * math.sin(a), 0.012), "xam",
                          scale=(1, 1, 0.5)))
    done({"1": "OGa_1", "2": "OGa_2", "cum": "OGa_Cum"}[kieu], "Models/VatCan", p)


def lo_cot(so_lan):
    """Rào chắn lô cốt công trình: khung tôn quây quanh hố đào, sọc cảnh báo, biển báo và đèn nháy ở mặt
    hướng về người chơi, nón giao thông phía trước. Rộng 2,6 m (1 làn) hoặc 5,6 m (2 làn), dài 4 m."""
    reset()
    random.seed(230 + so_lan)
    W, L, H = (2.6, 4.0, 1.9) if so_lan == 1 else (5.6, 4.0, 1.9)
    p = [box((W - 0.2, L - 0.2, 0.06), (0, 0, 0.03), "dat")]
    for s in (-1, 1):  # vách tôn hai bên
        p.append(box((0.05, L, H), (s * W / 2, 0, H / 2), "nhan_xanh", bev=0.01))
        for k in range(int(L / 0.25)):
            p.append(box((0.07, 0.06, H - 0.1), (s * W / 2, -L / 2 + 0.125 + k * 0.25, H / 2), "nhan_xanh"))
        p.append(box((0.08, L + 0.02, 0.18), (s * W / 2, 0, H - 0.09), "trim"))
    for s in (-1, 1):  # vách đầu và cuối, sọc cảnh báo
        p.append(box((W, 0.05, H), (0, s * L / 2, H / 2), "nhan_xanh", bev=0.01))
        n = int(W / 0.4)
        for k in range(n):
            x = -W / 2 + (k + 0.5) * W / n
            p.append(box((W / n + 0.002, 0.07, 0.35), (x, s * (L / 2 + 0.01), 0.35), "vang" if k % 2 else "vien"))
        p.append(box((W + 0.02, 0.08, 0.18), (0, s * L / 2, H - 0.09), "trim"))
    for x in (-W / 2, W / 2):  # cột góc và đèn nháy
        for y in (-L / 2, L / 2):
            p.append(box((0.1, 0.1, H + 0.1), (x, y, (H + 0.1) / 2), "sat"))
            p.append(ball(0.07, (x, y, H + 0.17), "den_sau"))
    # biển báo công trường tam giác vàng trên mặt +Y (mặt người chơi nhìn thấy khi chạy tới)
    p += [cyl(0.45, 0.04, (0, L / 2 + 0.06, H * 0.62), "vang", v=3, rot=(90, 0, 0)),
          cyl(0.32, 0.045, (0, L / 2 + 0.07, H * 0.62), "trim", v=3, rot=(90, 0, 0)),
          box((0.06, 0.03, 0.22), (0, L / 2 + 0.1, H * 0.64), "vien"),
          ball(0.03, (0, L / 2 + 0.1, H * 0.54), "vien")]
    for x in [(-W / 2 + 0.4) + k * (W - 0.8) / max(1, so_lan) for k in range(so_lan + 1)]:  # nón trước lô cốt
        p += [box((0.38, 0.38, 0.04), (x, L / 2 + 0.9, 0.02), "vien"),
              cyl(0.16, 0.6, (x, L / 2 + 0.9, 0.34), "cam", v=10, r2=0.03),
              cyl(0.115, 0.1, (x, L / 2 + 0.9, 0.42), "trim", v=10, r2=0.09)]
    done(f"LoCot_{so_lan}Lan", "Models/VatCan", p)


def rao_chan():
    """Rào chắn chữ A sọc đỏ trắng, ngang 1 làn (2,6 m)."""
    reset()
    p = []
    for s in (-1, 1):
        for d in (-1, 1):
            p.append(limb((s * 1.15, 0, 1.0), (s * 1.15, d * 0.35, 0.0), 0.07, "trim", bev=0))
        p.append(box((0.12, 0.8, 0.06), (s * 1.15, 0, 0.03), "vien"))
    for z in (0.55, 0.85):
        n = 8
        for k in range(n):
            x = -1.3 + (k + 0.5) * 2.6 / n
            p.append(box((2.6 / n + 0.002, 0.06, 0.2), (x, 0.0, z), "nhan_do" if (k + (z > 0.7)) % 2 else "trim"))
    p.append(ball(0.07, (-1.15, 0, 1.08), "den_sau"))
    p.append(ball(0.07, (1.15, 0, 1.08), "den_sau"))
    done("RaoChan_SocDo", "Models/VatCan", p)


def non_giao_thong():
    reset()
    p = [box((0.38, 0.38, 0.04), (0, 0, 0.02), "vien", bev=0.01),
         cyl(0.16, 0.6, (0, 0, 0.34), "cam", v=10, r2=0.03),
         cyl(0.115, 0.1, (0, 0, 0.42), "trim", v=10, r2=0.09)]
    done("NonGiaoThong", "Models/VatCan", p)


def vung_nuoc(lon):
    """Vũng nước: mặt nước xanh có vệt sáng phản chiếu, viền mặt đường ướt sẫm. Nhỏ 1,4 m, lớn 2,6 m (gần trọn làn)."""
    reset()
    random.seed(240 + lon)
    rx, ry = (1.3, 0.85) if lon else (0.7, 0.5)
    p = []
    for r, z, col in ((1.18, 0.003, "uot"), (1.0, 0.006, "nuoc")):
        p.append(dia(rx * r, ry * r, z, col, v=16, meo=0.13, day=0.006))
    for k in range(3):  # vệt sáng phản chiếu trời
        p.append(box((rx * random.uniform(0.25, 0.5), 0.05, 0.004),
                     (random.uniform(-rx, rx) * 0.4, random.uniform(-ry, ry) * 0.4, 0.011), "kinh_sang",
                     rot=(0, 0, random.uniform(-25, 25))))
    for k in range(4):  # giọt bắn quanh vũng
        a = random.uniform(0, math.tau)
        p.append(cyl(random.uniform(0.05, 0.1), 0.004, (rx * 1.3 * math.cos(a), ry * 1.35 * math.sin(a), 0.004), "uot", v=8))
    done("VungNuoc_Lon" if lon else "VungNuoc_Nho", "Models/VatCan", p)


# ---------- Shipper Út trên xe tay ga (dáng chibi theo ảnh tham khảo; đầu xe hướng -Y) ----------
def bo_tron(r, loc, col, scale, sub=2, rot=None):
    """Khối bo tròn (icosphere bị kéo dãn) cho thân xe, mũ, giày."""
    return ball(r, loc, col, sub=sub, scale=scale, rot=rot)


def than_xe_tay_ga(than, baga=False):
    """Thân xe tay ga bo tròn (đầu xe -Y). baga=True thêm giá sắt sau yên, mặt baga ở (0, 0,66, 0,855)."""
    p = []
    for y in (-0.64, 0.6):
        p.append(cyl(0.27, 0.14, (0, y, 0.27), "banh", v=14, rot=(0, 90, 0), bev=0.03))
        p.append(cyl(0.15, 0.15, (0, y, 0.27), "xam_nhat", v=10, rot=(0, 90, 0)))
        p.append(cyl(0.06, 0.16, (0, y, 0.27), "sat", v=8, rot=(0, 90, 0)))
    p.append(limb((0, -0.64, 0.27), (0, -0.52, 0.85), 0.07, "xam_nhat", bev=0))
    p += [bo_tron(1, (0, 0.3, 0.56), than, (0.25, 0.5, 0.22)),
          bo_tron(1, (0, -0.66, 0.55), than, (0.11, 0.27, 0.09)),
          box((0.44, 0.14, 0.62), (0, -0.44, 0.66), than, rot=(-14, 0, 0), taper=(0.72, 1), bev=0.09),
          box((0.36, 0.46, 0.08), (0, -0.12, 0.33), "sat", bev=0.035),
          bo_tron(1, (0, 0.2, 0.79), "vien", (0.18, 0.36, 0.07)),
          bo_tron(1, (0, -0.52, 1.02), than, (0.17, 0.14, 0.12)),
          cyl(0.065, 0.05, (0, -0.65, 1.02), "den_truoc", v=12, rot=(90, 0, 0)),
          cyl(0.02, 0.66, (0, -0.47, 1.1), "sat", v=6, rot=(0, 90, 0)),
          box((0.22, 0.05, 0.08), (0, 0.79, 0.62), "den_sau", bev=0.02),
          cyl(0.045, 0.38, (0.21, 0.42, 0.32), "xam_nhat", v=8, rot=(90, 0, 0)),
          box((0.42, 0.04, 0.05), (0, 0.18, 0.56), "trim")]
    for s in (-1, 1):
        p.append(cyl(0.028, 0.11, (s * 0.3, -0.47, 1.1), "vien", v=8, rot=(0, 90, 0)))
        p.append(limb((s * 0.2, -0.47, 1.1), (s * 0.25, -0.5, 1.3), 0.018, "sat", bev=0))
        p.append(cyl(0.055, 0.02, (s * 0.25, -0.51, 1.32), "kinh_sang", v=10, rot=(90, 0, 0)))
    if baga:
        yc, zb = 0.66, 0.855
        p.append(box((0.38, 0.32, 0.03), (0, yc, zb - 0.015), "sat"))
        for s in (-1, 1):
            p.append(limb((s * 0.17, yc - 0.16, zb - 0.01), (s * 0.17, yc + 0.17, zb - 0.01), 0.025, "sat", bev=0))
            p.append(limb((s * 0.17, yc + 0.12, zb - 0.02), (s * 0.12, yc - 0.05, 0.62), 0.022, "sat", bev=0))
    return p


def mu_nua_dau(mu, loc=(0, 0.16, 1.63), k=1.0):
    """Mũ bảo hiểm nửa đầu kiểu Việt Nam: chỏm tròn và lưỡi trai ngắn."""
    x, y, z = loc
    return [bo_tron(0.178 * k, (x, y, z), mu, (1, 1.06, 0.72)),
            box((0.2 * k, 0.09 * k, 0.02 * k), (x, y - 0.17 * k, z - 0.02 * k), mu, rot=(-12, 0, 0), bev=0.006),
            torus(0.176 * k, 0.012 * k, (x, y, z - 0.03 * k), "vien")]


def nguoi_ngoi(kieu, ao, quan, mu, chan="xe_may"):
    """Người ngồi lái xe tay ga, dáng chibi. kieu: shipper (mũ trùm, áo khoác sọc phản quang, logo lưng, găng tay),
    nam (mũ nửa đầu, áo sơ mi có cổ, thắt lưng), nu (áo chống nắng trùm tay, váy chống nắng, khẩu trang, tóc đuôi ngựa)."""
    p = []
    giay = {"shipper": "trim", "nam": "than_cay", "nu": "trim", "ba": "than_cay", "thun": "than_cay", "vest": "vien"}[kieu]
    tay = {"shipper": "vien", "nam": "da_nguoi", "nu": ao, "ba": "da_nguoi", "thun": "da_nguoi", "vest": "da_nguoi"}[kieu]
    cang_tay = "da_nguoi" if kieu == "thun" else ao
    for sx in (-1, 1):
        if chan == "xe_dap":  # đùi chéo xuống, cẳng chân tới bàn đạp, hai bàn đạp lệch nhau
            ped = (sx * 0.14, 0.02 + sx * 0.12, 0.3 + sx * 0.07)
            p.append(limb((sx * 0.1, 0.24, 0.9), (sx * 0.13, -0.06, 0.66), 0.15, quan, bev=0.05))
            p.append(limb((sx * 0.13, -0.06, 0.66), ped, 0.12, quan, bev=0.04))
            p.append(bo_tron(1, (ped[0], ped[1] - 0.05, ped[2] - 0.02), giay, (0.07, 0.13, 0.05)))
        elif chan == "xe_so":  # đầu gối kẹp bình xăng, bàn chân trên gác chân hai bên
            p.append(limb((sx * 0.1, 0.24, 0.9), (sx * 0.16, -0.12, 0.84), 0.16, quan, bev=0.05))
            p.append(limb((sx * 0.16, -0.12, 0.84), (sx * 0.2, 0.02, 0.4), 0.13, quan, bev=0.04))
            p.append(bo_tron(1, (sx * 0.2, -0.04, 0.38), giay, (0.075, 0.14, 0.06)))
        else:
            p.append(limb((sx * 0.1, 0.24, 0.88), (sx * 0.12, -0.12, 0.88), 0.16, quan, bev=0.05))
            p.append(limb((sx * 0.12, -0.12, 0.88), (sx * 0.13, -0.18, 0.44), 0.13, quan, bev=0.04))
            p.append(bo_tron(1, (sx * 0.13, -0.26, 0.42), giay, (0.075, 0.14, 0.06)))
            p.append(box((0.15, 0.28, 0.025), (sx * 0.13, -0.26, 0.37), "vien"))
        p.append(limb((sx * 0.22, 0.19, 1.34), (sx * 0.28, -0.1, 1.14), 0.12, ao, bev=0.04))
        p.append(limb((sx * 0.28, -0.1, 1.14), (sx * 0.3, -0.44, 1.1), 0.11, cang_tay, bev=0.04))
        p.append(ball(0.06, (sx * 0.3, -0.47, 1.1), tay, sub=2))
    p += [box((0.42, 0.27, 0.52), (0, 0.22, 1.13), ao, rot=(12, 0, 0), taper=(1.1, 1.0), bev=0.09),
          cyl(0.07, 0.1, (0, 0.17, 1.44), "da_nguoi", v=8),
          ball(0.155, (0, 0.15, 1.58), "da_nguoi", sub=2)]
    if kieu == "shipper":
        p += [box((0.44, 0.29, 0.05), (0, 0.23, 1.04), "vang", rot=(12, 0, 0)),
              box((0.44, 0.29, 0.03), (0, 0.24, 1.2), "trim", rot=(12, 0, 0)),
              cyl(0.085, 0.012, (0, 0.375, 1.24), "trim", v=12, rot=(78, 0, 0)),
              cyl(0.05, 0.014, (0, 0.38, 1.243), ao, v=8, rot=(78, 0, 0)),
              box((0.22, 0.14, 0.08), (0, 0.16, 1.4), ao, bev=0.03),
              bo_tron(0.2, (0, 0.17, 1.63), mu, (1, 1.08, 0.95)),
              bo_tron(0.17, (0, 0.02, 1.64), "kinh", (0.95, 0.45, 0.4)),
              torus(0.197, 0.022, (0, 0.17, 1.6), ao)]
    elif kieu == "nam":
        p += [box((0.24, 0.16, 0.06), (0, 0.15, 1.4), "trim", bev=0.02),          # cổ áo
              box((0.43, 0.28, 0.05), (0, 0.27, 0.9), "vien", rot=(12, 0, 0)),    # thắt lưng
              bo_tron(0.158, (0, 0.18, 1.57), "toc", (1, 1, 0.88))] + mu_nua_dau(mu)
    elif kieu == "thun":
        p += [box((0.2, 0.14, 0.04), (0, 0.15, 1.39), ao, bev=0.015),
              bo_tron(0.158, (0, 0.18, 1.57), "toc", (1, 1, 0.88))] + mu_nua_dau(mu)
    elif kieu == "vest":
        p += [box((0.16, 0.12, 0.08), (0, 0.13, 1.39), "trim", bev=0.02),
              box((0.06, 0.03, 0.24), (0, 0.075, 1.26), "nhan_do", rot=(12, 0, 0)),
              box((0.43, 0.28, 0.05), (0, 0.27, 0.9), "vien", rot=(12, 0, 0)),
              bo_tron(0.158, (0, 0.18, 1.57), "toc", (1, 1, 0.88))] + mu_nua_dau(mu)
    elif kieu == "ba":
        p += [box((0.24, 0.16, 0.06), (0, 0.15, 1.4), ao, bev=0.02),
              bo_tron(0.158, (0, 0.18, 1.57), "toc", (1, 1, 0.88)),
              bo_tron(0.07, (0, 0.31, 1.6), "toc", (1, 0.9, 0.9)),                # búi tóc
              cyl(0.36, 0.2, (0, 0.15, 1.8), "giay", v=14, r2=0.0),               # nón lá
              torus(0.2, 0.01, (0, 0.15, 1.7), "vien")]
    else:
        p += [bo_tron(0.13, (0, 0.3, 1.42), ao, (1.1, 0.7, 0.55)),               # mũ áo chống nắng gấp sau gáy
              box((0.46, 0.5, 0.05), (0, 0.04, 0.95), "tim", bev=0.02),           # váy chống nắng phủ đùi
              box((0.46, 0.05, 0.46), (0, -0.21, 0.72), "tim", bev=0.02),         # vạt váy phủ ống chân
              box((0.17, 0.05, 0.1), (0, 0.0, 1.54), "nhan_xanh", bev=0.02),      # khẩu trang
              bo_tron(0.158, (0, 0.18, 1.57), "toc", (1, 1, 0.88)),
              bo_tron(0.06, (0, 0.34, 1.48), "toc", (0.8, 1, 1.7))] + mu_nua_dau(mu)
    return p


def shipper():
    """Út trên xe tay ga xanh có baga trống sau yên. Đồ chở (ThungHang, GioSau, KhayLy) là model riêng,
    gắn vào điểm DiemGanThung trên mặt baga."""
    reset()
    p = than_xe_tay_ga("nhan_xanh", baga=True) + nguoi_ngoi("shipper", "cam", "quan", "vang")
    done("XeShipper", "Models/XeShipper", p, {"DiemGanThung": (0, 0.66, 0.855)})


def xe_may_ai(name, than, kieu, ao, quan, mu):
    """Xe máy AI: cùng thân xe tay ga với shipper nhưng không có baga, người lái mặc thường phục."""
    reset()
    done(name, "Models/XeAI", than_xe_tay_ga(than) + nguoi_ngoi(kieu, ao, quan, mu))


def xe_dau(name, than, mu):
    """Xe tay ga đậu trong hẻm: chân chống nghiêng, mũ nửa đầu móc trên gương."""
    reset()
    p = than_xe_tay_ga(than)
    p.append(limb((-0.12, 0.15, 0.25), (-0.3, 0.2, 0.0), 0.03, "sat", bev=0))
    p += mu_nua_dau(mu, loc=(0.25, -0.5, 1.2), k=0.85)
    done(name, "Models/Hem", p)


# Đồ chở: gốc model ở giữa đáy, đặt trùng DiemGanThung của xe; DiemGanHang là chỗ đặt món hàng
def thung_hang():
    """Thùng giao hàng vàng viền cam, nắp lật ra sau rủ xuống có logo, sàn trong nâng cao. Dùng cho đồ gốm."""
    reset()
    W, D, H = 0.5, 0.46, 0.42
    ao, mu = "cam", "vang"
    p = [box((W, D, 0.03), (0, 0, 0.015), mu, bev=0.01)]
    for s in (-1, 1):
        p.append(box((0.035, D, H), (s * (W / 2 - 0.0175), 0, H / 2), mu, bev=0.01))
        p.append(box((W, 0.035, H), (0, s * (D / 2 - 0.0175), H / 2), mu, bev=0.01))
        p.append(box((0.04, D + 0.01, 0.07), (s * (W / 2 - 0.0175), 0, H * 0.45), ao))
        p.append(box((W + 0.01, 0.04, 0.07), (0, s * (D / 2 - 0.0175), H * 0.45), ao))
    san = H - 0.08
    p.append(box((W - 0.07, D - 0.07, 0.03), (0, 0, san - 0.015), "vien"))
    nap = Vector((0, D / 2 + 0.07, H - D / 2 + 0.02))
    phap = Vector((0, math.cos(math.radians(12)), math.sin(math.radians(12))))
    p += [box((W + 0.02, 0.035, D), tuple(nap), ao, rot=(12, 0, 0), bev=0.01),
          cyl(0.09, 0.012, tuple(nap + phap * 0.022), "trim", v=12, rot=(-78, 0, 0)),
          cyl(0.05, 0.014, tuple(nap + phap * 0.03), mu, v=8, rot=(-78, 0, 0))]
    done("ThungHang", "Models/XeShipper", p, {"DiemGanHang": (0, 0, san)})


def gio_sau():
    """Rổ nhựa đỏ thấp có khe, buộc vào baga bằng hai dây chun đen. Dùng cho bó hoa, ly cà phê."""
    reset()
    W, D, H, col = 0.46, 0.4, 0.15, "nhan_do"
    p = [box((W, D, 0.02), (0, 0, 0.01), col)]
    for s in (-1, 1):  # khung vành trên, vành dưới hai bên
        for z in (0.02, H - 0.015):
            p.append(box((W, 0.025, 0.03), (0, s * (D / 2 - 0.0125), z), col, bev=0.006))
            p.append(box((0.025, D, 0.03), (s * (W / 2 - 0.0125), 0, z), col, bev=0.006))
    for k in range(7):  # nan dọc mặt trước sau
        x = -W / 2 + 0.03 + k * (W - 0.06) / 6
        for s in (-1, 1):
            p.append(box((0.03, 0.022, H), (x, s * (D / 2 - 0.011), H / 2), col))
    for k in range(6):  # nan dọc hai bên
        y = -D / 2 + 0.03 + k * (D - 0.06) / 5
        for s in (-1, 1):
            p.append(box((0.022, 0.03, H), (s * (W / 2 - 0.011), y, H / 2), col))
    for s in (-1, 1):  # dây chun vắt chéo trên miệng rổ
        p.append(limb((s * 0.2, -D / 2 - 0.01, H + 0.005), (-s * 0.2, D / 2 + 0.01, H + 0.005), 0.012, "vien", bev=0))
    done("GioSau", "Models/XeShipper", p, {"DiemGanHang": (0, 0, 0.02)})


def khay_ly():
    """Khay giấy giữ ly 4 lỗ (2 x 2) có quai cầm, đặt trên baga. Dùng cho cà phê sữa đá."""
    reset()
    p = [box((0.3, 0.3, 0.035), (0, 0, 0.0175), "giay", bev=0.01),
         box((0.32, 0.32, 0.015), (0, 0, 0.0075), "vien")]
    diem = {}
    for i, (x, y) in enumerate(((-0.075, -0.075), (0.075, -0.075), (-0.075, 0.075), (0.075, 0.075))):
        p.append(lathe([(0.06, 0.035), (0.062, 0.075), (0.066, 0.08)], "giay", seg=12, loc=(x, y, 0), caps=(False, False)))
        diem[f"DiemGanHang_{i + 1}"] = (x, y, 0.035)
    p += [box((0.02, 0.26, 0.12), (0, 0, 0.095), "giay", bev=0.005),
          box((0.024, 0.08, 0.05), (0, 0, 0.13), "vien")]  # lỗ quai cầm
    done("KhayLy", "Models/XeShipper", p, diem)


def xe_dap(name, khung, kieu, ao, quan, gio):
    """Người đạp xe đạp mini (đầu xe -Y): khung sườn thấp, giỏ trước, baga sau. Chạy chậm, len được vào hẻm.
    gio: món trong giỏ trước ("rau" hoặc "cap")."""
    reset()
    p = []
    for y in (-0.52, 0.52):
        p += [torus(0.3, 0.035, (0, y, 0.33), "banh", rot=(0, 90, 0)),
              torus(0.26, 0.015, (0, y, 0.33), "xam_nhat", rot=(0, 90, 0)),
              cyl(0.04, 0.08, (0, y, 0.33), "sat", v=8, rot=(0, 90, 0))]
        for k in range(6):  # nan hoa
            a = k / 6 * math.tau
            p.append(limb((0, y, 0.33), (0, y + 0.26 * math.cos(a), 0.33 + 0.26 * math.sin(a)), 0.012, "xam_nhat", bev=0))
    for a, b in (((0, 0.2, 0.32), (0, 0.24, 0.86)),        # cọc yên
                 ((0, 0.02, 0.3), (0, -0.4, 0.92)),        # ống chéo (sườn thấp)
                 ((0, 0.02, 0.3), (0, 0.2, 0.34)),
                 ((0, 0.2, 0.34), (0, 0.52, 0.33)),        # gióng sau
                 ((0, 0.24, 0.78), (0, 0.52, 0.33)),
                 ((0, -0.4, 0.92), (0, -0.52, 0.33)),      # càng trước
                 ((0, -0.4, 0.92), (0, -0.44, 1.08))):
        p.append(limb(a, b, 0.045, khung, bev=0))
    p += [cyl(0.018, 0.56, (0, -0.44, 1.08), "sat", v=6, rot=(0, 90, 0)),
          bo_tron(1, (0, 0.25, 0.9), "vien", (0.08, 0.13, 0.04)),
          cyl(0.09, 0.02, (0, 0.02, 0.3), "sat", v=10, rot=(0, 90, 0)),
          box((0.3, 0.34, 0.02), (0, 0.42, 0.66), "sat"),
          box((0.12, 0.3, 0.03), (0, 0.48, 0.62), khung, bev=0.01)]
    for s in (-1, 1):
        p.append(cyl(0.025, 0.1, (s * 0.28, -0.44, 1.08), "vien", v=6, rot=(0, 90, 0)))
    # giỏ trước đan
    p += [box((0.34, 0.26, 0.02), (0, -0.66, 0.86), "than_cay")]
    for sx in (-1, 1):
        p.append(box((0.02, 0.26, 0.2), (sx * 0.16, -0.66, 0.96), "than_cay"))
        p.append(box((0.34, 0.02, 0.2), (0, -0.66 + sx * 0.12, 0.96), "than_cay"))
    if gio == "rau":
        p += [ball(0.09, (-0.06, -0.66, 1.04), "la1", jit=0.02), ball(0.08, (0.07, -0.64, 1.02), "la3", jit=0.02),
              ball(0.06, (0.02, -0.7, 1.08), "nhan_do")]
    else:
        p.append(box((0.28, 0.12, 0.22), (0, -0.66, 1.05), "nhan_xanh", bev=0.03))
    p += nguoi_ngoi(kieu, ao, quan, "trim", chan="xe_dap")
    done(name, "Models/XeAI", p)


def dich(parts, dx=0.0, dy=0.0, dz=0.0):
    """Dời các khối đã hoàn thiện (transform đã áp vào lưới) một đoạn."""
    for o in parts:
        o.data.transform(Matrix.Translation((dx, dy, dz)))
    return parts


def xe_ba_gac(name, than, ao, mu, hang):
    """Xe ba gác máy: đầu xe máy phía trước, thùng sàn phẳng rộng 1,3 m phía sau có hai bánh và lan can.
    Dài ~3 m, chạy rất chậm, chiếm gần trọn một làn. hang: "thung" (thùng giấy chồng) hoặc "bao" (bao tải, bình nước)."""
    reset()
    random.seed(260 + len(hang))
    p = dich(than_xe_tay_ga(than) + nguoi_ngoi("nam", ao, "quan", mu), dy=-0.75)
    Wb, y0, y1, zs = 1.3, 0.05, 1.75, 0.6
    yc = (y0 + y1) / 2
    p += [box((Wb, y1 - y0, 0.06), (0, yc, zs), "than_cay", bev=0.01),
          box((Wb + 0.04, 0.06, 0.08), (0, y0, zs - 0.05), "sat"),
          box((0.12, y1 - y0, 0.1), (0, yc, zs - 0.1), "sat")]
    for k in range(6):  # ván sàn
        p.append(box((0.02, y1 - y0, 0.065), (-Wb / 2 + (k + 0.5) * Wb / 6, yc, zs + 0.002), "vien"))
    for sx in (-1, 1):
        p += [cyl(0.25, 0.12, (sx * 0.6, 1.25, 0.25), "banh", v=12, rot=(0, 90, 0), bev=0.02),
              cyl(0.13, 0.13, (sx * 0.6, 1.25, 0.25), "xam_nhat", v=8, rot=(0, 90, 0)),
              bo_tron(1, (sx * 0.6, 1.25, 0.5), "sat", (0.1, 0.32, 0.06)),
              box((0.04, y1 - y0, 0.04), (sx * Wb / 2, yc, zs + 0.32), "sat")]
        for y in (y0 + 0.02, yc, y1 - 0.02):
            p.append(box((0.04, 0.04, 0.32), (sx * Wb / 2, y, zs + 0.16), "sat"))
    p += [box((Wb, 0.04, 0.04), (0, y1, zs + 0.32), "sat"), box((0.2, 0.04, 0.08), (0, y1 + 0.02, zs - 0.02), "den_sau")]
    if hang == "thung":  # thùng giấy chồng 2 tầng, buộc dây
        for i, (x, y, z) in enumerate(((-0.33, 0.45, 0), (0.33, 0.45, 0), (-0.33, 1.05, 0), (0.33, 1.05, 0),
                                        (-0.2, 0.7, 1), (0.25, 0.85, 1))):
            h = 0.4
            p.append(box((0.58, 0.55, h), (x, y, zs + 0.03 + h / 2 + z * h), "giay", bev=0.015,
                         rot=(0, 0, random.uniform(-6, 6))))
            p.append(box((0.6, 0.06, 0.012), (x, y, zs + 0.035 + h + z * h), "trim"))
        p.append(limb((-0.66, 0.6, zs + 0.85), (0.66, 0.6, zs + 0.85), 0.015, "vien", bev=0))
    else:  # bao tải và bình nước
        for x, y in ((-0.35, 0.4), (0.3, 0.45), (-0.3, 0.95), (0.32, 1.0)):
            p.append(bo_tron(1, (x, y, zs + 0.2), "trim", (0.28, 0.24, 0.18), sub=1))
        for x in (-0.4, 0.0, 0.4):
            p += [cyl(0.15, 0.38, (x, 1.5, zs + 0.22), "nhan_xanh", v=10),
                  cyl(0.05, 0.06, (x, 1.5, zs + 0.44), "nhan_xanh", v=8)]
    done(name, "Models/XeAI", p)


# ---------- Đoạn đường cong (đường lớn, hẻm) ----------
def diem_cong(d, t, z, R, trai):
    """Điểm trên cung: d là độ lệch ngang (+ là bên trái người lái = +X Blender), t là góc đã đi (rad)."""
    dd = d if trai else -d
    r = R - dd
    x = R - r * math.cos(t)
    return (x if trai else -x, -r * math.sin(t), z)


def dai_cong(d1, d2, z0, z1, goc, R, trai, col, buoc):
    """Khối hình quạt chạy theo cung: từ độ lệch d1 tới d2, cao từ z0 tới z1."""
    bm = bmesh.new()
    vong = []
    for i in range(buoc + 1):
        t = goc * i / buoc
        vong.append([bm.verts.new(diem_cong(d, t, z, R, trai)) for d, z in ((d1, z0), (d2, z0), (d2, z1), (d1, z1))])
    for a, b in zip(vong, vong[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(vong[0][::-1])
    bm.faces.new(vong[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("cong")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("cong", me)
    bpy.context.scene.collection.objects.link(o)
    return fin(o, col)


def vach_cong(d, goc, R, trai, dai=3.0, cach=6.0, col="trim", rong=0.15, cao=0.02, z=0.01):
    """Vạch đứt dọc theo cung ở độ lệch ngang d."""
    dd = d if trai else -d
    r = R - dd
    p = []
    s_ = 0.0
    while s_ + dai <= r * goc:
        t = (s_ + dai / 2) / r
        p.append(box((rong, dai, cao), diem_cong(d, t, z, R, trai), col, rot=(0, 0, math.degrees(t) * (1 if trai else -1))))
        s_ += cach
    return p


def duong_lon_cong(goc_do, R, trai):
    """Đoạn đường lớn 3 làn cong theo cung bán kính R (tim đường), quay goc_do độ sang trái hoặc phải.
    Có vỉa hè, bó vỉa, vạch làn; DiemNoi ở cuối cung với hướng đi tiếp."""
    reset()
    goc = math.radians(goc_do)
    buoc = max(6, int(goc_do / 3))
    p = [dai_cong(-4.5, 4.5, -0.2, 0.0, goc, R, trai, "duong", buoc)]
    for x in (-1.5, 1.5):
        p += vach_cong(x, goc, R, trai)
    for s_ in (-1, 1):
        p.append(dai_cong(s_ * 4.5, s_ * 4.7, -0.2, 0.27, goc, R, trai, "xam_nhat", buoc))
        p.append(dai_cong(s_ * 4.7, s_ * 6.5, -0.2, 0.25, goc, R, trai, "via_he", buoc))
        p += vach_cong(s_ * 5.6, goc, R, trai, dai=0.04, cach=2.0, col="xam_nhat", rong=1.8, cao=0.005, z=0.25)
    ten = f"DuongLon_Cong{'Trai' if trai else 'Phai'}_{goc_do}"
    done(ten, "Models/Duong", p, {"DiemNoi": (*diem_cong(0, goc, 0, R, trai), goc_do if trai else -goc_do)})


def hem_cong(goc_do, R, trai):
    """Khúc cong của hẻm 3,5 m (vào, ra hẻm hoặc đổi hướng trong hẻm), có rãnh thoát nước hai bên."""
    reset()
    goc = math.radians(goc_do)
    buoc = max(6, int(goc_do / 6))
    p = [dai_cong(-1.75, 1.75, -0.2, 0.0, goc, R, trai, "nhua_hem", buoc)]
    for s_ in (-1, 1):
        p.append(dai_cong(s_ * 1.5, s_ * 1.75, 0.0, 0.03, goc, R, trai, "xam", buoc))
    ten = f"Hem_Cong{'Trai' if trai else 'Phai'}_{goc_do}"
    done(ten, "Models/Duong", p, {"DiemNoi": (*diem_cong(0, goc, 0, R, trai), goc_do if trai else -goc_do)})


# ---------- Địa điểm: Trạm Ký Ức, 3 cửa hàng, biển số nhà và cờ đích ----------
FONT_CHU = os.path.join(os.path.dirname(bpy.app.binary_path), f"{bpy.app.version[0]}.{bpy.app.version[1]}",
                        "datafiles", "fonts", "Inter.woff2")  # Inter (OFL) đi kèm Blender, đủ dấu tiếng Việt


def chu_3d(noi_dung, loc, rong_toi_da, cao_chu, col, day=0.012):
    """Dựng chữ thành khối 3D mỏng nằm trên mặt phẳng XZ, mặt chữ quay về -Y (đọc được từ ngoài đường)."""
    bpy.ops.object.text_add()
    o = bpy.context.active_object
    o.data.body = noi_dung
    o.data.font = bpy.data.fonts.load(FONT_CHU, check_existing=True)
    o.data.size = cao_chu
    o.data.extrude = day
    o.data.offset = cao_chu * 0.045  # làm nét chữ đậm hơn
    o.data.resolution_u = 3          # ít điểm trên đường cong, hợp phong cách low-poly
    o.data.align_x, o.data.align_y = "CENTER", "CENTER"
    o.rotation_euler = (math.radians(90), 0, 0)
    activate(o)
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    rong = o.dimensions.x
    if rong > rong_toi_da:
        o.scale = (rong_toi_da / rong,) * 3
    return fin(o, col, loc)


def mat_tien_cua_hang(W, wall, bien, awn):
    """Nhà 2 tầng mặt tiền W m có gian hàng mở ở tầng trệt (lòng tiệm tối), bạt sọc, biển hiệu có chỗ gắn chữ."""
    D, F = 10.0, 3.2
    H = 2 * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((W - 0.64, 0.08, 2.7), (0, -0.02, 1.35), "sat")]
    for sx in (-1, 1):
        p.append(box((0.32, 0.22, F), (sx * (W / 2 - 0.16), -0.1, F / 2), "trim", bev=0.03))
    n = int(W * 2)
    for k in range(n):  # bạt sọc
        x = -W / 2 + (k + 0.5) * W / n
        c = awn[k % 2]
        p.append(box((W / n + 0.002, 1.4, 0.05), (x, -0.65, 2.62), c, rot=(22, 0, 0)))
        p.append(box((W / n + 0.002, 0.04, 0.2), (x, -1.3, 2.27), c))
    p += [box((W - 0.2, 0.16, 0.82), (0, -0.1, 3.42), bien, bev=0.04),
          box((W - 0.5, 0.04, 0.6), (0, -0.2, 3.42), "trim", bev=0.01)]
    # tầng 2: ban công, cửa sổ, chậu cây; mái
    z = F
    p += [box((W, 0.9, 0.16), (0, -0.45, z + 0.85), "trim", bev=0.03),
          box((W, 0.06, 0.06), (0, -0.87, z + 1.75), "sat", bev=0.01)]
    for k in range(int(W / 0.2)):  # song sắt lan can
        p.append(box((0.03, 0.03, 0.82), (-W / 2 + 0.1 + k * 0.2, -0.87, z + 1.33), "sat"))
    for x in (-W / 4, W / 4):
        p += [box((1.2, 0.06, 1.8), (x, -0.02, z + 1.45), "trim", bev=0.02),
              box((0.95, 0.1, 1.55), (x, -0.03, z + 1.4), "kinh")]
    p += chau_cay(-W / 2 + 0.5, -0.6, z + 0.93, 0.8) + chau_cay(W / 2 - 0.5, -0.6, z + 0.93, 0.7)
    p += [box((W + 0.1, D + 0.1, 0.2), (0, D / 2, H + 0.1), "trim", bev=0.04),
          box((W + 0.1, 0.18, 0.7), (0, 0.04, H + 0.55), wall, bev=0.04)]
    return p


def ly_da(x, y, z, col="caphe"):
    return [cyl(0.045, 0.14, (x, y, z + 0.07), "ly", v=8, r2=0.055),
            cyl(0.05, 0.01, (x, y, z + 0.135), col, v=8),
            box((0.03, 0.03, 0.03), (x, y, z + 0.15), "da", rot=(20, 10, 30))]


def cua_hang(loai):
    """loai: nuoc (Quán nước Ngon), hoa (Tiệm hoa Bốn Mùa), gom (Tiệm gốm Cô Tư), tram (Trạm Ký Ức, tạp hóa Cô Ba)."""
    reset()
    random.seed({"nuoc": 300, "hoa": 310, "gom": 320, "tram": 330}[loai])
    cau_hinh = {"nuoc": (5, "tuong_mint", "nhan_xanh", ("nhan_xanh", "trim"), "QuanNuocNgon"),
                "hoa": (5, "tuong_dao", "hong", ("hong", "trim"), "TiemHoaBonMua"),
                "gom": (5, "tuong_kem", "men_nau", ("men_nau", "tuong_kem"), "TiemGomCoTu"),
                "tram": (6, "tuong_vang", "cam", ("cam", "trim"), "TramKyUc")}[loai]
    W, wall, bien, awn, ten = cau_hinh
    p = mat_tien_cua_hang(W, wall, bien, awn)
    ten_bien = {"nuoc": "QUÁN NƯỚC NGON", "hoa": "TIỆM HOA BỐN MÙA", "gom": "TIỆM GỐM CÔ TƯ", "tram": "TRẠM KÝ ỨC"}[loai]
    p.append(chu_3d(ten_bien, (0, -0.225, 3.42), W - 0.8, 0.42, bien))
    if loai == "nuoc":  # quầy nước, ly đá trên quầy, thùng đá xốp, bảng menu
        p += [box((2.6, 0.7, 0.95), (0.6, -0.55, 0.475), "nhan_xanh", bev=0.03),
              box((2.7, 0.8, 0.06), (0.6, -0.55, 0.98), "trim", bev=0.02),
              box((0.7, 0.5, 0.6), (-1.7, -0.5, 0.3), "trim", bev=0.04),
              box((0.72, 0.52, 0.05), (-1.7, -0.5, 0.62), "nhan_xanh")]
        for i in range(6):
            p += ly_da(-0.4 + i * 0.4, -0.55, 1.01, "caphe" if i % 2 else "caphe_nhat")
        p += [limb((-1.2, -1.6, 0.0), (-1.2, -1.4, 1.0), 0.04, "than_cay", bev=0),
              limb((-1.2, -1.2, 0.0), (-1.2, -1.4, 1.0), 0.04, "than_cay", bev=0),
              box((0.6, 0.04, 0.75), (-1.2, -1.52, 0.6), "vien", rot=(-12, 0, 0)),
              box((0.45, 0.02, 0.08), (-1.2, -1.56, 0.75), "trim", rot=(-12, 0, 0)),
              box((0.35, 0.02, 0.06), (-1.2, -1.55, 0.6), "vang", rot=(-12, 0, 0))]
    elif loai == "hoa":  # xô hoa trước cửa, kệ bậc thang có chậu hoa
        for i in range(7):
            x = -2.0 + i * 0.66
            y = -0.9 if i % 2 else -0.55
            p.append(cyl(0.2, 0.42, (x, y, 0.21), random.choice(["xam_nhat", "nhan_xanh", "trim"]), v=10, r2=0.24))
            c = random.choice(["hong", "vang", "trim", "nhan_do", "tim", "cam"])
            for j in range(5):
                p.append(ball(0.09, (x + random.uniform(-0.12, 0.12), y + random.uniform(-0.12, 0.12),
                                     0.5 + random.uniform(0, 0.25)), c, jit=0.015))
            p.append(cyl(0.06, 0.3, (x, y, 0.55), "la1", v=4, r2=0.0, rot=(18, 0, random.uniform(0, 360))))
        for k in range(3):
            p.append(box((1.0, 0.35, 0.05), (1.6, -0.2 - k * 0.3, 0.35 + k * 0.4), "than_cay"))
            for j in range(3):
                p += chau_cay(1.3 + j * 0.3, -0.2 - k * 0.3, 0.38 + k * 0.4, 0.35)
    elif loai == "gom":  # kệ gỗ hai tầng bày gốm men nâu và men xanh trắng, chum lớn dưới đất
        for z in (0.45, 1.05, 1.65):
            p.append(box((3.0, 0.45, 0.05), (-0.6, -0.4, z), "than_cay"))
        for x in (-2.05, 0.85):
            p.append(box((0.06, 0.45, 1.7), (x, -0.4, 0.85), "than_cay"))
        prof = [(0.07, 0), (0.11, 0.06), (0.12, 0.14), (0.07, 0.24), (0.05, 0.28), (0.06, 0.3)]
        for z in (0.475, 1.075, 1.675):
            for i in range(5):
                x = -1.8 + i * 0.6
                k = random.uniform(0.7, 1.2)
                col = "men_nau" if (i + int(z * 10)) % 3 else "gom_trang"
                p.append(lathe([(r * k, h * k) for r, h in prof], col, seg=10, loc=(x, -0.4, z)))
        for x in (1.6, 2.1):
            p.append(lathe([(0.18, 0), (0.3, 0.2), (0.32, 0.4), (0.18, 0.62), (0.2, 0.66)], "men_nau", seg=12,
                           loc=(x, -0.6, 0)))
    else:  # tram: kệ tạp hóa nhiều màu, két nước, xe đẩy hàng, chồng thùng giao hàng vàng, bàn sổ của Cô Ba
        for z in (0.5, 1.1, 1.7):
            p.append(box((2.4, 0.4, 0.05), (-1.4, -0.3, z), "than_cay"))
            for i in range(8):
                p.append(box((0.22, 0.25, random.uniform(0.2, 0.4)), (-2.45 + i * 0.3, -0.3, z + 0.15),
                             random.choice(["nhan_do", "vang", "nhan_xanh", "la1", "cam", "trim", "tim"]), bev=0.01))
        for x in (0.6, 1.1):
            p.append(box((0.45, 0.35, 0.3), (x, -0.7, 0.15), "nhan_do", bev=0.02))
            for j in range(6):
                p.append(cyl(0.04, 0.22, (x - 0.15 + (j % 3) * 0.15, -0.76 + (j // 3) * 0.12, 0.38), "la_dam", v=6))
        for k in range(3):
            p.append(box((0.5, 0.46, 0.42), (2.2, -0.6, 0.21 + k * 0.43), "vang" if k != 1 else "cam", bev=0.02))
        p += [box((1.2, 0.6, 0.8), (0.2, -0.2, 0.4), "than_cay", bev=0.02),
              box((0.4, 0.3, 0.05), (0.2, -0.25, 0.83), "nhan_do", rot=(0, 0, 8))]  # Sổ Ký Ức trên bàn
    done(ten, "Models/DiaDiem", p)


def bien_so_nha():
    """Biển số nhà xanh viền trắng gắn tường cạnh cửa nhà khách; số nhà và tên đường là chữ đặt ở DiemChu."""
    reset()
    p = [box((0.5, 0.04, 0.34), (0, -0.02, 0), "trim", bev=0.01),
         box((0.44, 0.05, 0.28), (0, -0.03, 0), "nhan_xanh", bev=0.01)]
    done("BienSoNha", "Models/DiaDiem", p, {"DiemChu": (0, -0.06, 0, 180)})


def co_dich():
    """Cờ đích cắm trước cửa nhà khách: cột trắng, chân đế, cờ đuôi nheo hai lớp màu xanh chanh."""
    reset()
    p = [cyl(0.2, 0.06, (0, 0, 0.03), "vien", v=10),
         cyl(0.03, 2.4, (0, 0, 1.2), "trim", v=8),
         ball(0.05, (0, 0, 2.42), "vang")]
    for i, (z, col) in enumerate(((2.15, "la3"), (1.85, "trim"))):
        bm = bmesh.new()
        v = [bm.verts.new(c) for c in ((0.02, 0, z + 0.25), (0.02, 0, z - 0.05), (0.75, 0.08 * (i + 1), z + 0.1))]
        bm.faces.new(v)
        me = bpy.data.meshes.new("co")
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new("co", me)
        bpy.context.scene.collection.objects.link(o)
        p.append(fin(o, col))
    done("CoDich", "Models/DiaDiem", p)


def cay_me():
    """Cây me Quận 1: thân to sần, ba nhánh chính, tán xòe rộng gồm nhiều chùm lá nhỏ xanh nhạt, cao ~9 m."""
    reset()
    random.seed(140)
    p = [cyl(0.42, 3.8, (0, 0, 1.9), "than_cay", v=7, r2=0.3, jit=0.05),
         cyl(0.7, 0.6, (0, 0, 0.3), "than_cay", v=7, r2=0.42)]
    for a in (0, 2.1, 4.2):
        p.append(limb((0, 0, 3.4), (2.4 * math.cos(a), 2.4 * math.sin(a), 5.6), 0.22, "than_cay", bev=0))
    for i in range(16):
        a = random.uniform(0, math.tau)
        r = random.uniform(0.5, 3.6)
        p.append(ball(random.uniform(0.9, 1.3), (r * math.cos(a), r * math.sin(a), 6.0 + random.uniform(0, 2.2) - r * 0.25),
                      random.choice(["la3", "la1", "la3"]), sub=1, jit=0.12, scale=(1, 1, 0.6)))
    for x, y, sx, sy in ((0, -0.8, 1.7, 0.12), (0, 0.8, 1.7, 0.12), (-0.8, 0, 0.12, 1.5), (0.8, 0, 0.12, 1.5)):
        p.append(box((sx, sy, 0.12), (x, y, 0.06), "xam", bev=0.02))
    done("CayMe", "Models/Pho", p)


# ---------- Xe máy cho đoạn đông xe: xe số, chở 2 người, chở hàng, shipper khác, tay ga lớn ----------
def than_xe_so(than, baga=True):
    """Xe số (đầu xe -Y): thân mảnh, yếm nhỏ, ống sườn lộ, khối máy ở giữa, yên dài, baga sau."""
    p = []
    for y in (-0.66, 0.62):
        p.append(cyl(0.29, 0.1, (0, y, 0.29), "banh", v=14, rot=(0, 90, 0), bev=0.025))
        p.append(cyl(0.17, 0.11, (0, y, 0.29), "xam_nhat", v=10, rot=(0, 90, 0)))
    p += [limb((0, -0.66, 0.29), (0, -0.52, 0.95), 0.06, "xam_nhat", bev=0),
          bo_tron(1, (0, -0.66, 0.6), than, (0.08, 0.26, 0.06)),
          box((0.3, 0.1, 0.38), (0, -0.45, 0.78), than, rot=(-18, 0, 0), taper=(0.8, 1), bev=0.05),
          limb((0, -0.42, 0.9), (0, -0.05, 0.42), 0.09, than, bev=0.02),
          box((0.24, 0.32, 0.24), (0, 0.0, 0.36), "xam", bev=0.03),
          cyl(0.07, 0.26, (0, -0.02, 0.36), "sat", v=10, rot=(0, 90, 0)),
          bo_tron(1, (0, 0.38, 0.63), than, (0.17, 0.4, 0.14)),
          bo_tron(1, (0, 0.18, 0.79), "vien", (0.15, 0.4, 0.06)),
          bo_tron(1, (0, -0.5, 1.02), than, (0.14, 0.12, 0.1)),
          cyl(0.06, 0.05, (0, -0.62, 1.0), "den_truoc", v=10, rot=(90, 0, 0)),
          cyl(0.018, 0.62, (0, -0.47, 1.1), "sat", v=6, rot=(0, 90, 0)),
          box((0.16, 0.05, 0.07), (0, 0.8, 0.66), "den_sau", bev=0.015),
          cyl(0.04, 0.6, (0.17, 0.3, 0.3), "xam_nhat", v=8, rot=(80, 0, 0))]
    for sx in (-1, 1):
        p.append(cyl(0.026, 0.1, (sx * 0.28, -0.47, 1.1), "vien", v=8, rot=(0, 90, 0)))
        p.append(limb((sx * 0.19, -0.47, 1.1), (sx * 0.23, -0.5, 1.28), 0.016, "sat", bev=0))
        p.append(cyl(0.05, 0.02, (sx * 0.23, -0.51, 1.3), "kinh_sang", v=10, rot=(90, 0, 0)))
        p.append(limb((sx * 0.08, -0.05, 0.36), (sx * 0.2, -0.05, 0.36), 0.03, "sat", bev=0))   # gác chân
    if baga:
        p.append(box((0.3, 0.36, 0.03), (0, 0.66, 0.8), "sat"))
    return p


def nguoi_sau(kieu, ao, quan, mu, k=1.0):
    """Người ngồi sau (chở 2): tay ôm eo người lái, chân trên gác chân sau. k < 1 cho trẻ em."""
    S = Vector((0, 0.56, 0.86))
    v = lambda x, y, z: tuple(S + (Vector((x, y, z)) - S) * k)
    p = []
    for sx in (-1, 1):
        p += [limb(v(sx * 0.1, 0.62, 0.9), v(sx * 0.16, 0.34, 0.86), 0.15 * k, quan, bev=0.05 * k),
              limb(v(sx * 0.16, 0.34, 0.86), v(sx * 0.2, 0.44, 0.46), 0.12 * k, quan, bev=0.04 * k),
              bo_tron(1, v(sx * 0.2, 0.4, 0.44), "trim" if kieu == "hoc_sinh" else "than_cay",
                      (0.07 * k, 0.13 * k, 0.055 * k)),
              limb(v(sx * 0.21, 0.55, 1.32), v(sx * 0.2, 0.36, 1.1), 0.11 * k, ao, bev=0.04 * k),
              ball(0.055 * k, v(sx * 0.16, 0.33, 1.08), "da_nguoi", sub=2)]
    p += [box((0.4 * k, 0.26 * k, 0.5 * k), v(0, 0.6, 1.13), ao, rot=(6, 0, 0), taper=(1.08, 1.0), bev=0.09 * k),
          cyl(0.065 * k, 0.1 * k, v(0, 0.57, 1.43), "da_nguoi", v=8),
          ball(0.15 * k, v(0, 0.55, 1.57), "da_nguoi", sub=2),
          bo_tron(0.155 * k, v(0, 0.58, 1.56), "toc", (1, 1, 0.88))]
    if kieu == "nu":
        p += [bo_tron(0.06 * k, v(0, 0.74, 1.47), "toc", (0.8, 1, 1.7)),
              box((0.17 * k, 0.05 * k, 0.1 * k), v(0, 0.4, 1.53), "nhan_xanh", bev=0.02)]
    if kieu == "hoc_sinh":
        p += [box((0.32 * k, 0.17 * k, 0.36 * k), v(0, 0.8, 1.16), "nhan_xanh", bev=0.05 * k),
              cyl(0.09 * k, 0.03 * k, v(0, 0.46, 1.38), "nhan_do", v=3, rot=(90, 0, 180))]
    x, y, z = v(0, 0.57, 1.62)
    p += mu_nua_dau(mu, loc=(x, y, z), k=k)
    return p


def hop_giao_hang(mau, vien):
    """Thùng giao hàng đóng nắp đặt trên baga (cho shipper đối thủ)."""
    return [box((0.46, 0.42, 0.42), (0, 0.66, 1.03), mau, bev=0.03),
            box((0.47, 0.43, 0.07), (0, 0.66, 0.98), vien, bev=0.01),
            box((0.48, 0.44, 0.04), (0, 0.66, 1.25), vien, bev=0.01),
            cyl(0.08, 0.01, (0, 0.875, 1.1), "trim", v=10, rot=(90, 0, 0))]


def xe_dong(name, mau, than, ao, mu, ao2=None, quan="quan"):
    """Một mẫu xe máy cho đoạn đông xe. mau: so_a, so_b, hai_nguoi_a, hai_nguoi_b, cho_hang, shipper_khac, tay_ga_lon."""
    reset()
    random.seed(sum(map(ord, name)))
    if mau == "so_a":
        p = than_xe_so(than) + nguoi_ngoi("thun", ao, quan, mu, chan="xe_so")
    elif mau == "so_b":
        p = than_xe_so(than) + nguoi_ngoi("nam", ao, quan, mu, chan="xe_so")
        p += [bo_tron(1, (0, 0.68, 0.95), "trim", (0.2, 0.2, 0.15), sub=1)]          # bao hàng nhỏ trên baga
    elif mau == "hai_nguoi_a":
        p = than_xe_tay_ga(than) + nguoi_ngoi("nam", ao, quan, mu) + nguoi_sau("nu", ao2, "vien", "trim")
    elif mau == "hai_nguoi_b":
        p = than_xe_so(than, baga=False) + nguoi_ngoi("nu", ao, quan, mu, chan="xe_so") \
            + nguoi_sau("hoc_sinh", "trim", "quan", "nhan_do", k=0.75)
    elif mau == "cho_hang":  # chồng thùng xốp cao quá đầu, rộng hơn thân xe, buộc dây
        p = than_xe_so(than) + nguoi_ngoi("thun", ao, quan, mu, chan="xe_so")
        for i in range(4):
            p.append(box((0.62, 0.5, 0.3), (random.uniform(-0.02, 0.02), 0.72, 0.97 + i * 0.31), "trim", bev=0.02,
                         rot=(0, 0, random.uniform(-4, 4))))
        for z in (1.1, 1.7):
            p.append(limb((-0.33, 0.72, z), (0.33, 0.72, z), 0.015, "vien", bev=0))
    elif mau == "shipper_khac":
        p = than_xe_tay_ga(than, baga=True) + nguoi_ngoi("shipper", ao, quan, mu) + hop_giao_hang(mu, ao)
    else:  # tay_ga_lon: thân dài, đầu xe to, kính chắn gió, yên hai tầng
        p = than_xe_tay_ga(than) + nguoi_ngoi("vest", ao, quan, mu)
        p += [bo_tron(1, (0, 0.36, 0.6), than, (0.28, 0.58, 0.24)),
              bo_tron(1, (0, -0.5, 1.04), than, (0.21, 0.16, 0.14)),
              box((0.36, 0.03, 0.28), (0, -0.58, 1.2), "kinh_sang", rot=(-20, 0, 0), bev=0.02),
              bo_tron(1, (0, 0.5, 0.86), "vien", (0.16, 0.18, 0.07)),
              box((0.5, 0.05, 0.04), (0, 0.2, 0.62), "xam_nhat")]
    done(name, "Models/XeAI", p)


# ---------- Nhà trệt, nhà ở (không kinh doanh), nhà có gara ----------
def cua_so_song(x, z, w=1.2, h=1.3, y=-0.03):
    """Cửa sổ kính có khung và song sắt."""
    p = [box((w + 0.2, 0.06, h + 0.2), (x, y + 0.01, z), "trim", bev=0.02), box((w, 0.08, h), (x, y, z), "kinh")]
    for k in range(int(w / 0.18)):
        p.append(box((0.025, 0.05, h), (x - w / 2 + 0.09 + k * 0.18, y - 0.05, z), "sat"))
    return p


def nha_tret(idx):
    """Nhà trệt một tầng rộng 4 m: 1 mái ngói dốc ra đường, cửa gỗ hai cánh; 2 mái bằng có lan can, hiên tôn, cửa sắt xếp."""
    reset()
    random.seed(400 + idx)
    W, D, H = 4.0, 10.0, 3.6
    wall = ("tuong_dao", "tuong_mint")[idx - 1]
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((W + 0.1, 0.25, 0.3), (0, 0.0, 0.15), "xam"),
         box((0.3, 0.12, 0.4), (1.6, -0.06, 1.6), "xam", bev=0.02),
         box((0.35, 0.04, 0.22), (-0.9, -0.03, 2.55), "nhan_xanh")]
    p += cua_so_song(1.0, 1.6, w=1.1)
    p += chau_cay(1.5, -0.45, 0.0, 0.8)
    if idx == 1:
        p += [box((1.4, 0.08, 2.3), (-0.9, -0.02, 1.15), "than_cay", bev=0.02),
              box((0.04, 0.1, 2.3), (-0.9, -0.03, 1.15), "vien"),
              ]
        p += mai_hai_mai(W, 0.0, D, H, 2.0, wall)
    else:
        p += [box((1.8, 0.08, 2.4), (-0.8, -0.02, 1.2), "vien")]
        for k in range(15):
            p.append(box((0.03, 0.06, 2.4), (-1.65 + k * 0.12, -0.07, 1.2), "sat"))
        p += [box((W, 1.2, 0.05), (0, -0.55, 2.75), "ton", rot=(12, 0, 0)),
              box((W + 0.1, D + 0.1, 0.18), (0, D / 2, H + 0.09), "trim", bev=0.03),
              box((W, 0.06, 0.06), (0, 0.03, H + 1.0), "sat")]
        for k in range(20):
            p.append(box((0.03, 0.03, 0.8), (-W / 2 + 0.1 + k * 0.2, 0.03, H + 0.6), "sat"))
        p += chau_cay(-1.3, 0.6, H + 0.18, 0.9)
    done(f"NhaTret_{idx}", "Models/Pho", p)


def nha_o(idx):
    """Nhà ở 2–3 tầng rộng 5 m, không kinh doanh: sân trước 2 m có tường rào thấp và cổng sắt,
    cửa chính gỗ, cửa sổ chớp, ban công trồng cây, mái tôn hoặc mái ngói."""
    reset()
    random.seed(410 + idx)
    W, D, F = 5.0, 10.0, 3.2
    floors, wall, roof = ((2, "tuong_xanh", "ngoi"), (3, "tuong_kem", "ton"))[idx - 1]
    H = floors * F
    y0 = 2.0  # mặt tiền lùi vào sau sân
    p = [box((W, D - y0, H), (0, y0 + (D - y0) / 2, H / 2), wall, bev=0.04),
         box((W, y0, 0.08), (0, y0 / 2, 0.04), "gach")]
    for sx in (-1, 1):  # tường rào thấp hai bên cổng, hai trụ cổng
        p += [box((1.1, 0.2, 1.1), (sx * (W / 2 - 0.55), 0.1, 0.55), wall, bev=0.03),
              box((0.3, 0.3, 1.6), (sx * 1.35, 0.1, 0.8), "trim", bev=0.03),
              box((0.2, y0, 1.1), (sx * (W / 2 - 0.1), y0 / 2, 0.55), wall, bev=0.03)]
    for k in range(12):  # cổng sắt hai cánh
        p.append(box((0.03, 0.04, 1.4), (-1.15 + k * 0.21, 0.1, 0.75), "la_dam"))
    p += [box((2.4, 0.05, 0.06), (0, 0.1, 1.42), "la_dam"), box((2.4, 0.05, 0.06), (0, 0.1, 0.1), "la_dam"),
          box((1.4, 0.08, 2.3), (0.6, y0 - 0.02, 1.15), "than_cay", bev=0.02),
          box((0.04, 0.1, 2.3), (0.6, y0 - 0.03, 1.15), "vien")]
    p += cua_so_song(-1.4, 1.6, w=1.1, y=y0 - 0.03)
    p += chau_cay(-1.6, 0.8, 0.08, 0.9) + chau_cay(1.7, 0.6, 0.08, 0.7)
    for f in range(1, floors):
        z = f * F
        p += [box((W, 1.0, 0.16), (0, y0 - 0.5, z), "trim", bev=0.03),
              box((W, 0.06, 0.06), (0, y0 - 0.97, z + 0.95), "sat")]
        for k in range(24):
            p.append(box((0.03, 0.03, 0.85), (-W / 2 + 0.1 + k * 0.2, y0 - 0.97, z + 0.5), "sat"))
        for x in (-1.2, 1.2):
            p += [box((1.2, 0.06, 2.0), (x, y0 - 0.02, z + 1.2), "trim", bev=0.02),
                  box((0.95, 0.1, 1.75), (x, y0 - 0.03, z + 1.15), "kinh")]
            for sx in (-1, 1):
                p.append(box((0.24, 0.06, 1.75), (x + sx * 0.72, y0 - 0.06, z + 1.15), "la_dam", bev=0.01))
        p += chau_cay(-2.0, y0 - 0.6, z + 0.08, 0.8) + chau_cay(0, y0 - 0.6, z + 0.08, 0.6)
    p.append(box((W + 0.1, D - y0 + 0.1, 0.2), (0, y0 + (D - y0) / 2, H + 0.1), "trim", bev=0.04))
    if roof == "ngoi":
        p += mai_hai_mai(W, y0, D, H + 0.2, 2.2, wall)
    else:
        p += tum_thang(W, y0 + 2.0, H + 0.2, wall, x=1.2)
        p.append(box((W, 0.15, 0.8), (0, y0 + 0.05, H + 0.6), wall, bev=0.03))
    done(f"NhaO_{idx}", "Models/Pho", p)


def nha_gara(idx):
    """Nhà 2–3 tầng rộng 5 m có gara ở tầng trệt: 1 cửa cuốn đóng; 2 cửa xếp mở, trong có xe máy đậu."""
    reset()
    random.seed(420 + idx)
    W, D, F = 5.0, 10.0, 3.2
    floors, wall = ((2, "tuong_vang"), (3, "tuong_cu"))[idx - 1]
    H = floors * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((3.2, 0.1, 2.6), (-0.7, -0.02, 1.3), "sat"),
         box((0.9, 0.08, 2.3), (1.85, -0.02, 1.15), "than_cay", bev=0.02),
         box((0.35, 0.04, 0.22), (1.85, -0.04, 2.5), "nhan_xanh"),
         box((3.4, 1.2, 0.08), (-0.7, -0.6, 2.9), "trim", rot=(8, 0, 0), bev=0.02)]
    if idx == 1:  # cửa cuốn đóng: các nan ngang
        p.append(box((3.1, 0.12, 2.5), (-0.7, -0.05, 1.25), "xam_nhat", bev=0.01))
        for k in range(12):
            p.append(box((3.12, 0.14, 0.03), (-0.7, -0.06, 0.15 + k * 0.2), "xam"))
        p.append(box((3.2, 0.2, 0.25), (-0.7, -0.1, 2.62), "xam", bev=0.02))
    else:  # cửa sắt xếp kéo gọn hai bên, trong gara có 2 xe máy
        for sx in (-1, 1):
            for k in range(5):
                p.append(box((0.03, 0.08, 2.5), (-0.7 + sx * (1.45 - k * 0.06), -0.06, 1.25), "sat"))
        for x in (-1.4, -0.1):
            p += dich(than_xe_tay_ga(random.choice(["nhan_do", "trim", "xanh_xe", "vien"])), dx=x, dy=1.2)
    for f in range(1, floors):
        z = f * F
        p.append(box((W + 0.04, 0.1, 0.15), (0, -0.03, z - 0.05), "trim"))
        p += cua_so_song(-1.2, z + 1.5, w=1.3) + cua_so_song(1.3, z + 1.5, w=1.3)
        p.append(box((0.8, 0.3, 0.5), (0, -0.16, z + 2.6), "trim", bev=0.03))
    p += [box((W + 0.1, D + 0.1, 0.2), (0, D / 2, H + 0.1), "trim", bev=0.04),
          box((W + 0.1, 0.18, 0.7), (0, 0.04, H + 0.55), wall, bev=0.04),
          cyl(0.45, 1.0, (1.2, 3.0, H + 0.75), "xam_nhat", v=10, rot=(0, 90, 0))]
    done(f"NhaGara_{idx}", "Models/Pho", p)


# ---------- Công trình công cộng và nhà ở cao cấp (gốc ở giữa mép giáp vỉa hè, mặt tiền quay -Y) ----------
def lang_tru_tam_giac(rong, cao, sau, loc, col):
    """Khối lăng trụ tam giác (trán tường, đầu hồi mái): đáy rộng `rong`, cao `cao`, dày `sau` theo trục Y."""
    x, y, z = loc
    bm = bmesh.new()
    mat = [[bm.verts.new((x + a, y + b, z + c)) for a, c in ((-rong / 2, 0), (rong / 2, 0), (0, cao))] for b in (0, sau)]
    bm.faces.new(mat[0][::-1])
    bm.faces.new(mat[1])
    for k in range(3):
        bm.faces.new((mat[0][k], mat[0][(k + 1) % 3], mat[1][(k + 1) % 3], mat[1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("tru")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("tru", me)
    bpy.context.scene.collection.objects.link(o)
    return fin(o, col)


def cay_nho(x, y, s=1.0, col="la1"):
    """Cây tán tròn nhỏ trong sân vườn."""
    return [cyl(0.15 * s, 2.2 * s, (x, y, 1.1 * s), "than_cay", v=6, r2=0.1 * s),
            ball(1.2 * s, (x, y, 2.9 * s), col, jit=0.12 * s, scale=(1, 1, 0.85)),
            ball(0.8 * s, (x + 0.6 * s, y + 0.2 * s, 2.4 * s), "la3", jit=0.08 * s)]


def hang_rao_sat(x0, x1, y, h, col="la_dam", tru="trim"):
    """Hàng rào tường thấp + song sắt dọc theo trục X từ x0 tới x1."""
    p = [box((x1 - x0, 0.25, 0.5), ((x0 + x1) / 2, y, 0.25), tru, bev=0.02),
         box((x1 - x0, 0.05, 0.05), ((x0 + x1) / 2, y, h), col)]
    for k in range(int((x1 - x0) / 0.15)):
        p.append(box((0.03, 0.03, h - 0.5), (x0 + 0.075 + k * 0.15, y, 0.5 + (h - 0.5) / 2), col))
    return p


def bao_tang():
    """Bảo tàng kiểu cổ điển: bệ cao, hàng cột trán tam giác, cửa sổ vòm hai tầng, mái vòm giữa, băng rôn đỏ."""
    reset()
    W, D, H, b = 30.0, 18.0, 10.0, 0.9
    p = [box((W + 1, D + 1, b), (0, D / 2, b / 2), "xam_nhat", bev=0.04),
         box((W, D, H), (0, D / 2, b + H / 2), "tuong_kem", bev=0.05),
         box((W + 0.3, D + 0.3, 0.35), (0, D / 2, b + H / 2), "trim"),
         box((W + 0.5, D + 0.5, 0.5), (0, D / 2, b + H + 0.25), "trim", bev=0.04)]
    for x in [s_ * (6.5 + k * 2.9) for s_ in (-1, 1) for k in range(3)]:
        for z in (b + 0.6, b + 5.6):
            p += [box((1.3, 0.12, 2.8), (x, -0.06, z + 1.4), "kinh"),
                  cyl(0.65, 0.12, (x, -0.06, z + 2.8), "kinh", v=10, rot=(90, 0, 0)),
                  box((1.7, 0.16, 0.2), (x, -0.08, z), "trim")]
    for s_ in (-1, 1):  # băng rôn
        p += [box((1.3, 0.08, 4.2), (s_ * 13.6, -0.08, b + 6.2), "nhan_do", bev=0.02),
              box((1.3, 0.09, 0.25), (s_ * 13.6, -0.09, b + 4.4), "vang")]
    yc = -3.0
    for x in (-5, -3, -1, 1, 3, 5):  # hàng cột
        p += [cyl(0.42, 8.0, (x, yc, b + 4.15), "trim", v=12),
              box((1.1, 1.1, 0.3), (x, yc, b + 0.15), "trim", bev=0.02),
              box((1.1, 1.1, 0.35), (x, yc, b + 8.3), "trim", bev=0.02)]
    p += [box((12.6, 3.8, 1.0), (0, -1.2, b + 8.95), "trim", bev=0.03),
          lang_tru_tam_giac(13.0, 2.6, 3.8, (0, -3.1, b + 9.45), "tuong_kem"),
          box((4.0, 0.12, 4.5), (0, -0.06, b + 2.25), "than_cay", bev=0.02),
          chu_3d("BẢO TÀNG", (0, -3.13, b + 8.95), 9.0, 0.7, "vien")]
    for k in range(4):  # bậc thềm
        p.append(box((13.0, 1.0, b - k * 0.22), (0, -3.6 - k * 1.0, (b - k * 0.22) / 2), "xam_nhat", bev=0.02))
    p += [lathe([(4.2, 0), (4.0, 1.3), (3.2, 2.7), (1.7, 3.7), (0.3, 4.1)], "ton", seg=16, loc=(0, D / 2, b + H + 0.5)),
          cyl(0.35, 1.0, (0, D / 2, b + H + 5.0), "trim", v=8),
          cyl(0.05, 1.6, (0, D / 2, b + H + 6.3), "sat", v=5)]
    done("BaoTang", "Models/Pho", p)


def truong_hoc():
    """Trường tiểu học: cổng có biển tên, hàng rào, sân trường có cây bàng, dãy lớp 3 tầng màu vàng
    có hành lang lan can phía trước, mái ngói. Lô 34 x 20 m, dãy lớp lùi vào 10 m."""
    reset()
    random.seed(500)
    W, y0, D, F, n = 34.0, 10.0, 8.0, 3.4, 3
    H = n * F
    p = [box((W, y0, 0.06), (0, y0 / 2, 0.03), "be_tong"),
         box((W, D, H), (0, y0 + 2 + D / 2, H / 2), "tuong_vang", bev=0.05)]
    for f in range(n):  # hành lang trước lớp
        z = f * F
        p += [box((W, 2.0, 0.2), (0, y0 + 1.0, z + F - 0.1), "trim", bev=0.03),
              box((W, 0.15, 1.0), (0, y0 + 0.08, z + F + 0.5), "tuong_vang", bev=0.02) if f < n - 1 else
              box((W + 0.4, 2.6, 0.15), (0, y0 + 1.0, H + 0.08), "trim"),
              box((W, 0.17, 0.12), (0, y0 + 0.07, z + F + 1.0), "trim")]
        for k in range(4):  # mỗi phòng học: một cửa gỗ, hai cửa sổ có chớp
            xc = -W / 2 + 4.25 + k * 8.5
            p += [box((1.0, 0.08, 2.2), (xc - 2.6, y0 + 2 - 0.02, z + 1.1), "than_cay", bev=0.01)]
            for dx in (-0.6, 1.9):
                p += [box((1.6, 0.08, 1.3), (xc + dx, y0 + 2 - 0.02, z + 1.6), "kinh"),
                      box((0.4, 0.06, 1.3), (xc + dx - 1.0, y0 + 2 - 0.05, z + 1.6), "la_dam"),
                      box((0.4, 0.06, 1.3), (xc + dx + 1.0, y0 + 2 - 0.05, z + 1.6), "la_dam")]
        for k in range(9):
            p.append(box((0.35, 0.35, F), (-W / 2 + 0.2 + k * (W - 0.4) / 8, y0 + 0.2, z + F / 2), "trim"))
    p.append(box((W + 1.0, D + 3.0, 2.4), (0, y0 + 1.5 + D / 2, H + 1.3), "ngoi", taper=(0.94, 0.4)))
    p += hang_rao_sat(-W / 2, -2.4, 0, 1.8, col="la_dam") + hang_rao_sat(2.4, W / 2, 0, 1.8, col="la_dam")
    for s_ in (-1, 1):  # trụ cổng
        p.append(box((0.6, 0.6, 3.6), (s_ * 2.7, 0, 1.8), "trim", bev=0.03))
    p += [box((6.0, 0.5, 0.9), (0, 0, 3.9), "nhan_xanh", bev=0.04),
          chu_3d("TRƯỜNG TIỂU HỌC", (0, -0.26, 3.9), 5.4, 0.45, "trim")]
    for k in range(14):  # cổng sắt kéo
        p.append(box((0.04, 0.05, 1.6), (-2.3 + k * 0.35, 0.05, 0.85), "la_dam"))
    for x in (-9.0, 9.0):  # cây bàng giữa sân
        p.append(cyl(0.3, 3.6, (x, 5.0, 1.8), "than_cay", v=6, r2=0.2))
        for z, r, c in ((3.6, 3.2, "la2"), (4.8, 2.4, "la1"), (5.8, 1.5, "la3")):
            p.append(ball(r, (x, 5.0, z), c, sub=2, scale=(1, 1, 0.28), jit=r * 0.06))
        p.append(box((2.2, 2.2, 0.4), (x, 5.0, 0.2), "xam_nhat", bev=0.03))
    done("TruongHoc", "Models/Pho", p)


def benh_vien():
    """Bệnh viện 5 tầng trắng, dải cửa sổ ngang có viền xanh, sảnh vào có mái che và đường dốc,
    chữ BỆNH VIỆN trên mái và biển chữ thập xanh lá."""
    reset()
    W, D, F, n = 28.0, 16.0, 3.4, 5
    H = n * F
    p = [box((W, D, H), (0, D / 2, H / 2), "trim", bev=0.05)]
    for f in range(1, n):
        z = f * F
        p += [box((W - 1.0, 0.12, 1.5), (0, -0.04, z + 1.6), "kinh"),
              box((W + 0.1, 0.2, 0.3), (0, -0.05, z + 0.5), "nhan_xanh")]
        for k in range(1, 9):
            p.append(box((0.2, 0.18, 1.5), (-W / 2 + 0.5 + k * (W - 1.0) / 9, -0.08, z + 1.6), "trim"))
    p += [box((W - 6, 0.12, 2.6), (3, -0.04, 1.4), "kinh_sang"),
          box((10.0, 5.0, 0.4), (3, -2.5, 3.3), "trim", bev=0.05),
          box((10.2, 0.3, 0.6), (3, -5.0, 3.3), "nhan_xanh", bev=0.03),
          box((6.0, 3.5, 0.3), (3, -2.5, 0.15), "xam_nhat"),
          box((4.0, 2.5, 0.15), (-6.5, -1.4, 0.08), "xam_nhat", rot=(-3, 0, 0))]
    for x in (-1.6, 7.6):
        p.append(cyl(0.25, 3.1, (x, -4.7, 1.55), "trim", v=10))
    p += [box((16.0, 0.6, 1.8), (0, 1.0, H + 0.9), "trim", bev=0.04),
          chu_3d("BỆNH VIỆN", (0, 0.68, H + 0.9), 15.0, 1.3, "nhan_xanh", day=0.05)]
    p += [box((2.4, 0.3, 2.4), (-W / 2 + 2.0, -0.2, H - 2.0), "trim", bev=0.05),  # biển chữ thập xanh lá
          box((1.8, 0.35, 0.6), (-W / 2 + 2.0, -0.22, H - 2.0), "la1"),
          box((0.6, 0.35, 1.8), (-W / 2 + 2.0, -0.22, H - 2.0), "la1")]
    for x, y in ((6, 10), (-8, 9), (10, 4)):
        p.append(box((3, 2.5, 1.6), (x, y, H + 0.8), "xam_nhat", bev=0.05))
    p += chau_cay(-12.0, -1.0, 0.0, 1.0) + chau_cay(-9.5, -1.0, 0.0, 1.0)
    done("BenhVien", "Models/Pho", p)


def mai_hien_cot(x, y, rong, cao, col_mai):
    """Hiên trước cửa: hai cột và mái ngói nhỏ."""
    return [cyl(0.15, cao, (x - rong / 2 + 0.2, y, cao / 2), "trim", v=8),
            cyl(0.15, cao, (x + rong / 2 - 0.2, y, cao / 2), "trim", v=8),
            box((rong + 0.4, 2.0, 0.12), (x, y + 0.8, cao + 0.15), col_mai, rot=(14, 0, 0), bev=0.02)]


def nha_san_vuon():
    """Nhà 2 tầng mái ngói lùi sau khu vườn trước 6 m: cỏ, lối đá, bồn hoa, cây, hàng rào và cổng."""
    reset()
    random.seed(510)
    W, y0, Dn, F = 10.0, 6.0, 9.0, 3.2
    p = [box((W, y0, 0.1), (0, y0 / 2, 0.05), "co"),
         box((1.2, y0, 0.12), (0, y0 / 2, 0.06), "gach"),
         box(((W - 2), Dn, 2 * F), (0, y0 + Dn / 2, F), "tuong_mint", bev=0.04),
         box((W - 1.4, Dn + 0.6, 2.2), (0, y0 + Dn / 2, 2 * F + 1.1), "ngoi", taper=(0.75, 0.55)),
         box((W - 1.8, Dn + 0.2, 0.25), (0, y0 + Dn / 2, 2 * F + 0.1), "trim"),
         box((1.4, 0.08, 2.3), (0, y0 - 0.02, 1.15), "than_cay", bev=0.02)]
    p += mai_hien_cot(0, y0 - 1.6, 3.0, 2.8, "ngoi")
    for x in (-2.5, 2.5):
        for z in (1.6, F + 1.5):
            p += [box((1.2, 0.08, 1.4), (x, y0 - 0.02, z), "kinh"),
                  box((0.35, 0.06, 1.4), (x - 0.8, y0 - 0.05, z), "la_dam"),
                  box((0.35, 0.06, 1.4), (x + 0.8, y0 - 0.05, z), "la_dam")]
    p += hang_rao_sat(-W / 2, -1.0, 0, 1.4) + hang_rao_sat(1.0, W / 2, 0, 1.4)
    for s_ in (-1, 1):
        p.append(box((0.35, 0.35, 1.8), (s_ * 1.0, 0, 0.9), "trim", bev=0.02))
    p += cay_nho(-3.3, 2.5, 1.0) + cay_nho(3.6, 3.6, 0.8, "la2")
    for k in range(10):  # bồn hoa dọc lối đi
        x = random.choice((-1, 1)) * random.uniform(0.9, 1.6)
        p.append(ball(0.18, (x, 0.8 + k * 0.5, 0.25), random.choice(["hong", "vang", "nhan_do", "tim", "trim"]), jit=0.02))
    done("NhaSanVuon", "Models/Pho", p)


def biet_thu_phap():
    """Biệt thự kiểu Pháp 2 tầng: tường vàng, gờ trắng, cửa chớp xanh, mái ngói dốc, hiên cột có ban công,
    ống khói, vườn trước 6 m, hàng rào sắt trụ trắng."""
    reset()
    W, y0, Dn, F = 16.0, 6.0, 10.0, 3.6
    Wn = 12.0
    p = [box((W, y0, 0.1), (0, y0 / 2, 0.05), "co"),
         box((3.0, y0, 0.12), (0, y0 / 2, 0.06), "xam_nhat"),
         box((Wn, Dn, 2 * F), (0, y0 + Dn / 2, F), "vang_phap", bev=0.05),
         box((Wn + 0.3, Dn + 0.3, 0.3), (0, y0 + Dn / 2, F), "trim"),
         box((Wn + 0.5, Dn + 0.5, 0.35), (0, y0 + Dn / 2, 2 * F), "trim"),
         box((Wn + 0.6, Dn + 0.6, 2.8), (0, y0 + Dn / 2, 2 * F + 1.55), "ngoi", taper=(0.7, 0.5)),
         box((0.8, 0.8, 2.4), (3.5, y0 + 6.5, 2 * F + 2.4), "trim", bev=0.03)]
    for x in (-4.5, -2.4, 2.4, 4.5):
        for z in (0.5, F + 0.5):
            p += [box((1.1, 0.1, 2.3), (x, y0 - 0.03, z + 1.15), "kinh"),
                  cyl(0.55, 0.1, (x, y0 - 0.03, z + 2.3), "kinh", v=10, rot=(90, 0, 0)),
                  box((0.35, 0.08, 2.3), (x - 0.75, y0 - 0.06, z + 1.15), "la_dam"),
                  box((0.35, 0.08, 2.3), (x + 0.75, y0 - 0.06, z + 1.15), "la_dam")]
    p += [box((4.0, 2.4, 0.3), (0, y0 - 1.2, F), "trim", bev=0.03),
          box((1.6, 0.1, 2.6), (0, y0 - 0.03, 1.3), "than_cay", bev=0.02)]
    for x in (-1.7, 1.7):
        p.append(cyl(0.22, F, (x, y0 - 2.2, F / 2), "trim", v=10))
    for k in range(13):  # lan can con tiện ban công
        p.append(cyl(0.06, 0.8, (-1.8 + k * 0.3, y0 - 2.3, F + 0.55), "trim", v=6))
    p.append(box((4.0, 0.15, 0.1), (0, y0 - 2.3, F + 0.98), "trim"))
    p += hang_rao_sat(-W / 2, -1.8, 0, 1.8, col="sat") + hang_rao_sat(1.8, W / 2, 0, 1.8, col="sat")
    for s_ in (-1, 1):
        p += [box((0.6, 0.6, 2.4), (s_ * 1.9, 0, 1.2), "trim", bev=0.03), ball(0.3, (s_ * 1.9, 0, 2.6), "trim")]
    p += cay_nho(-5.5, 2.8, 1.3) + cay_nho(5.5, 3.2, 1.1, "la2")
    done("BietThu_Phap", "Models/Pho", p)


def biet_thu_hien_dai():
    """Biệt thự hiện đại: các khối hộp trắng xếp lệch, tầng trên đua ra, kính lớn, ốp gỗ dọc,
    mái bằng có cây, cổng trượt nan sắt, sân cỏ."""
    reset()
    W, y0 = 14.0, 6.0
    p = [box((W, y0, 0.1), (0, y0 / 2, 0.05), "co"),
         box((3.4, y0, 0.12), (-3.5, y0 / 2, 0.06), "be_tong"),
         box((10.0, 8.0, 3.4), (-1.0, y0 + 4.0, 1.7), "trim", bev=0.03),
         box((7.0, 0.1, 2.6), (-0.5, y0 - 0.03, 1.4), "kinh_sang"),
         box((9.0, 8.0, 3.2), (1.5, y0 + 3.0, 5.0), "trim", bev=0.03),
         box((5.0, 0.1, 2.2), (2.5, y0 - 1.03, 5.0), "kinh"),
         box((9.2, 8.2, 0.25), (1.5, y0 + 3.0, 6.7), "xam_nhat"),
         box((10.2, 8.2, 0.25), (-1.0, y0 + 4.0, 3.5), "xam_nhat")]
    for k in range(12):  # ốp gỗ dọc tầng trên
        p.append(box((0.12, 0.12, 3.1), (-2.7 + k * 0.17, y0 - 1.05, 5.0), "than_cay"))
    p += chau_cay(-4.5, y0 + 1.0, 3.6, 0.9) + chau_cay(-3.2, y0 + 1.2, 3.6, 0.7) + chau_cay(4.5, y0 + 2, 6.8, 0.8)
    p += [box((W, 0.3, 0.6), (0, 0, 0.3), "be_tong")]
    for k in range(20):  # cổng trượt nan ngang
        p.append(box((4.0, 0.06, 0.06), (-3.5, 0.0, 0.7 + k * 0.08), "sat"))
    p += cay_nho(4.5, 2.5, 0.9) + cay_nho(1.5, 1.5, 0.7, "la2")
    done("BietThu_HienDai", "Models/Pho", p)


def tram_xe_buyt():
    """Trạm chờ xe buýt dài 4 m trên vỉa hè: khung sắt, mái nghiêng, vách kính sau, ghế băng,
    bảng quảng cáo một bên, cột biển XE BUÝT. Mặt mở quay -Y (ra lòng đường)."""
    reset()
    L = 4.0
    p = [box((L + 0.4, 1.6, 0.08), (0, 0.6, 2.6), "nhan_xanh", rot=(-6, 0, 0), bev=0.02),
         box((L + 0.45, 0.1, 0.12), (0, -0.2, 2.55), "trim"),
         box((L, 0.06, 1.9), (0, 1.3, 1.25), "kinh_sang"),
         box((2.6, 0.4, 0.06), (-0.4, 1.0, 0.48), "than_cay", bev=0.01)]
    for x in (-L / 2, L / 2):
        p += [box((0.1, 0.1, 2.55), (x, 1.3, 1.28), "sat"), box((0.1, 0.1, 2.5), (x, -0.1, 1.25), "sat")]
    for x in (-1.5, 0.7):
        p.append(box((0.06, 0.35, 0.45), (x, 1.0, 0.23), "sat"))
    p += [box((1.3, 0.12, 2.0), (L / 2 - 0.3, 1.35, 1.25), "sat", bev=0.02),
          box((1.15, 0.13, 1.8), (L / 2 - 0.3, 1.33, 1.25), "vang"),
          box((0.9, 0.14, 0.5), (L / 2 - 0.3, 1.32, 1.6), "nhan_do")]
    p += [cyl(0.05, 3.0, (-L / 2 - 0.8, 0.0, 1.5), "xam_nhat", v=8),
          box((0.9, 0.06, 0.6), (-L / 2 - 0.8, -0.04, 2.7), "nhan_xanh", bev=0.02),
          chu_3d("XE BUÝT", (-L / 2 - 0.8, -0.08, 2.7), 0.8, 0.22, "trim", day=0.01)]
    done("TramXeBuyt", "Models/Pho", p)


# ---------- Hẻm: nhà trệt, nhà cổ, tiệm và quán nhỏ, xe bán hàng rong ----------
def nha_hem_tret(idx):
    """Nhà trệt trong hẻm rộng 4 m: 1 mái tôn, cửa sắt xếp, hiên tôn; 2 mái ngói, cửa gỗ."""
    reset()
    random.seed(600 + idx)
    W, D, H = 4.0, 8.0, 3.2
    wall = ("tuong_xanh", "tuong_dao")[idx - 1]
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((0.3, 0.12, 0.4), (1.6, -0.06, 1.5), "xam", bev=0.02),
         box((0.35, 0.04, 0.22), (1.6, -0.04, 2.2), "nhan_xanh")]
    p += cua_so_song(1.0, 1.6, w=1.0)
    p += chau_cay(1.5, -0.45, 0.0, 0.7)
    if idx == 1:
        p.append(box((2.0, 0.08, 2.3), (-0.8, -0.02, 1.15), "vien"))
        for k in range(16):
            p.append(box((0.03, 0.06, 2.3), (-1.75 + k * 0.125, -0.07, 1.15), "sat"))
        p.append(box((W, 1.0, 0.05), (0, -0.48, 2.65), "ton", rot=(15, 0, 0)))  # hiên tôn nhỏ trên cửa
        p += mai_mot_mai(W, 0.0, D, H, 1.0, wall, cao_truoc=True)
    else:
        p.append(box((1.3, 0.08, 2.2), (-0.9, -0.02, 1.1), "than_cay", bev=0.02))
        p += mai_hai_mai(W, 0.0, D, H, 1.8, wall)
    done(f"NhaHem_Tret_{idx}", "Models/Hem", p)


def nha_hem_co():
    """Nhà cổ trong hẻm: tường vàng cũ có vệt ố và vết nứt, cửa gỗ xếp nhiều cánh, cửa sổ chớp gỗ, ban công lan can
    hoa văn, mái ngói âm dương, đèn lồng đỏ, bàn thờ thổ địa ở chân tường."""
    reset()
    random.seed(620)
    W, D, F = 4.5, 9.0, 3.2
    H = 2 * F
    p = [box((W, D, H), (0, D / 2, H / 2), "tuong_cu", bev=0.04)]
    for k in range(6):  # vệt ố
        p.append(box((random.uniform(0.4, 1.0), 0.02, random.uniform(0.3, 0.9)),
                     (random.uniform(-1.8, 1.8), -0.01, random.uniform(0.3, H - 0.4)), "giay"))
    for k in range(3):
        x, z = random.uniform(-1.8, 1.8), random.uniform(2.4, 5.6)
        p.append(limb((x, -0.015, z), (x + random.uniform(-0.3, 0.3), -0.015, z - random.uniform(0.3, 0.6)), 0.02, "vien", bev=0))
    for k in range(6):  # cửa gỗ xếp
        p.append(box((0.5, 0.08, 2.5), (-1.25 + k * 0.5, -0.02, 1.25), "than_cay", bev=0.01))
        p.append(box((0.3, 0.09, 0.6), (-1.25 + k * 0.5, -0.03, 1.7), "men_nau"))
    p += [box((3.2, 0.12, 0.25), (0, -0.04, 2.62), "do_dam"),
          ball(0.18, (-1.6, -0.35, 2.4), "nhan_do", scale=(1, 1, 1.2)), cyl(0.02, 0.3, (-1.6, -0.35, 2.75), "vang", v=4),
          box((0.35, 0.25, 0.3), (1.9, -0.15, 0.15), "do_dam", bev=0.01)]
    z = F
    p += [box((W, 0.8, 0.15), (0, -0.4, z), "trim", bev=0.02), box((W, 0.05, 0.08), (0, -0.78, z + 0.95), "trim")]
    for k in range(15):  # lan can con tiện
        p.append(cyl(0.04, 0.85, (-W / 2 + 0.15 + k * 0.3, -0.78, z + 0.5), "trim", v=6))
    for x in (-1.2, 1.2):
        p += [box((1.0, 0.08, 1.9), (x, -0.02, z + 1.2), "kinh"),
              box((0.5, 0.06, 1.9), (x - 0.75, -0.05, z + 1.2), "than_cay"),
              box((0.5, 0.06, 1.9), (x + 0.75, -0.05, z + 1.2), "than_cay")]
    p += mai_hai_mai(W, 0.0, D, H, 2.4, "tuong_cu", gan="do_dam", ong=True)
    for s_ in (-1, 1):  # đầu đao cong lên ở hai đầu đỉnh mái
        p.append(box((0.3, 0.4, 0.45), (s_ * (W / 2 + 0.45), D / 2, H + 2.65), "do_dam", rot=(0, s_ * 25, 0)))
    done("NhaHem_Co", "Models/Hem", p)


def hem_tiem(loai, tang=2, mai="tum", W=4.0, hau_to=""):
    """Tiệm, quán nhỏ trong hẻm: tầng trệt mở, mái hiên tôn, bảng hiệu có chữ.
    loai: tap_hoa, sua_xe, cat_toc, com_tam, ca_phe. tang: 1 (nhà trệt) tới 3.
    mai: tum (sân thượng có tum cầu thang), bang (sân thượng phẳng, bồn nước, không tum), ton (nhà trệt mái tôn một dốc).
    W: bề ngang (4 m một lô, 8 m hai lô). hau_to: thêm vào tên file cho các biến thể."""
    reset()
    random.seed(sum(map(ord, loai)) + tang * 7 + int(W))
    D, F = 8.0, 3.0
    ten, wall, bien, chu = {"tap_hoa": ("HemTiem_TapHoa", "tuong_vang", "nhan_do", "TẠP HÓA"),
                            "sua_xe": ("HemTiem_SuaXe", "tuong_cu", "nhan_xanh", "SỬA XE"),
                            "cat_toc": ("HemTiem_CatToc", "tuong_mint", "tim", "CẮT TÓC"),
                            "com_tam": ("HemQuan_ComTam", "tuong_kem", "cam", "CƠM TẤM"),
                            "ca_phe": ("HemQuan_CaPhe", "tuong_dao", "men_nau", "CÀ PHÊ")}[loai]
    ten += hau_to
    H = tang * F
    p = [box((W, D, H), (0, D / 2, H / 2), wall, bev=0.04),
         box((W - 0.5, 0.08, 2.4), (0, -0.02, 1.2), "sat"),
         box((W, 1.3, 0.05), (0, -0.62, 2.55), "ton", rot=(14, 0, 0)),
         box((W - 0.3, 0.12, 0.55), (0, -0.08, 2.85), bien, bev=0.03),
         box((W - 0.6, 0.04, 0.4), (0, -0.15, 2.85), "trim", bev=0.01),
         chu_3d(chu, (0, -0.18, 2.85), W - 1.0, 0.28, bien)]
    for f in range(1, tang):  # các tầng lầu: cửa sổ, dây phơi đồ, cục máy lạnh
        z = f * F
        p += [box((W + 0.04, 0.1, 0.15), (0, -0.04, z + 0.05), "trim"),
              box((0.7, 0.3, 0.45), (W / 2 - 0.8, -0.17, z + 2.3), "trim", bev=0.03),
              limb((-W / 2 + 0.1, -0.45, z + 2.0), (W / 2 - 0.1, -0.45, z + 2.0), 0.02, "sat", bev=0)]
        for xc in ([-0.8] if W < 5 else [-W / 4, W / 4]):
            p.append(box((1.4, 0.08, 1.4), (xc, -0.03, z + 1.4), "kinh"))
        for k in range(int(W / 0.8)):
            p.append(box((0.4, 0.04, 0.5), (-W / 2 + 0.6 + k * 0.8, -0.45, z + 1.7),
                         random.choice(["nhan_do", "vang", "nhan_xanh", "trim", "hong"])))
    if mai == "ton":
        p += mai_mot_mai(W, 0.0, D, H, 1.0, wall, cao_truoc=True)
    else:
        p.append(box((W, 0.15, 0.7), (0, 0.05, H + 0.35), wall, bev=0.03))
        if mai == "tum":
            p += tum_thang(W, 3.0, H, wall)
        else:  # sân thượng phẳng: bồn nước, chậu cây, ăng-ten
            p += [cyl(0.45, 1.0, (W / 2 - 1.0, 3.0, H + 0.75), "xam_nhat", v=10, rot=(0, 90, 0)),
                  box((1.0, 0.6, 0.25), (W / 2 - 1.0, 3.0, H + 0.12), "sat"),
                  cyl(0.03, 2.2, (-W / 2 + 0.5, 6.0, H + 1.1), "sat", v=4)]
            p += chau_cay(-W / 2 + 0.8, 1.0, H, 0.9)
    if loai == "tap_hoa":
        for z in (0.5, 1.1):
            p.append(box((2.2, 0.4, 0.05), (-0.6, -0.4, z), "than_cay"))
            for i in range(7):
                p.append(box((0.24, 0.26, random.uniform(0.2, 0.4)), (-1.55 + i * 0.32, -0.4, z + 0.15),
                             random.choice(["nhan_do", "vang", "nhan_xanh", "la1", "cam", "tim"]), bev=0.01))
        for i in range(8):  # dây bim bim treo dưới mái hiên
            p.append(box((0.12, 0.03, 0.5), (-1.6 + i * 0.45, -1.1, 2.05), random.choice(["vang", "nhan_do", "la1", "cam"])))
        p += [cyl(0.15, 0.55, (1.5, -0.45, 0.28), "cam", v=10), cyl(0.06, 0.1, (1.5, -0.45, 0.6), "sat", v=6),
              box((0.45, 0.35, 0.3), (1.0, -0.5, 0.15), "nhan_do", bev=0.02)]
    elif loai == "sua_xe":
        for k in range(4):
            p.append(torus(0.28, 0.08, (-1.5, -0.5, 0.08 + k * 0.16), "banh"))
        p += [cyl(0.18, 0.6, (1.4, -0.5, 0.3), "nhan_do", v=10, rot=(0, 90, 0)),
              box((0.4, 0.3, 0.2), (1.4, -0.5, 0.6), "sat", bev=0.02),
              box((1.6, 0.05, 0.9), (0, -0.06, 1.6), "sat", bev=0.01),
              cyl(0.07, 0.18, (0.9, -0.7, 0.09), "vang", v=8), cyl(0.07, 0.18, (1.05, -0.75, 0.09), "nhan_xanh", v=8),
              cyl(0.5, 0.004, (0, -1.0, 0.003), "uot", v=10)]
        for k in range(5):
            p.append(box((0.04, 0.06, 0.3), (-0.6 + k * 0.3, -0.1, 1.6), "xam_nhat"))
        p += dich(than_xe_so("nhan_do", baga=False), dx=0.1, dy=-1.2)
    elif loai == "cat_toc":
        p += [box((1.0, 0.05, 1.2), (0.6, -0.06, 1.5), "kinh_sang", bev=0.01),
              box((1.1, 0.04, 1.3), (0.6, -0.04, 1.5), "trim"),
              cyl(0.2, 0.4, (0.6, -0.6, 0.2), "sat", v=8), box((0.55, 0.5, 0.15), (0.6, -0.6, 0.48), "vien", bev=0.04),
              box((0.55, 0.12, 0.6), (0.6, -0.35, 0.82), "vien", bev=0.04),
              box((0.65, 0.12, 0.08), (0.6, -0.6, 0.62), "sat")]
        for k in range(6):  # cột sọc tiệm hớt tóc
            p.append(cyl(0.08, 0.15, (-1.7, -0.3, 1.4 + k * 0.15), ("nhan_do", "trim", "nhan_xanh")[k % 3], v=8))
        p += [ball(0.09, (-1.7, -0.3, 2.35), "trim"), ball(0.09, (-1.7, -0.3, 1.25), "trim")]
    elif loai == "com_tam":
        p += [box((1.2, 0.6, 0.85), (-1.1, -0.5, 0.43), "trim", bev=0.02),
              box((1.1, 0.55, 0.45), (-1.1, -0.5, 1.08), "kinh_sang", bev=0.02),
              box((1.2, 0.6, 0.04), (-1.1, -0.5, 1.32), "cam")]
        for j, col in enumerate(("nhan_do", "vang", "la1", "cam", "trim")):
            p.append(box((0.18, 0.18, 0.06), (-1.5 + j * 0.2, -0.5, 0.9), col, bev=0.01))
        for x in (0.5, 1.6):
            p += [box((0.7, 0.7, 0.04), (x, -1.0, 0.7), "xam_nhat", bev=0.01),
                  cyl(0.03, 0.7, (x, -1.0, 0.35), "xam_nhat", v=6)]
            for dy in (-0.5, 0.5):
                p.append(cyl(0.15, 0.3, (x + dy * 0.6, -1.0, 0.15), random.choice(["nhan_do", "nhan_xanh"]), v=8, r2=0.13))
    else:  # ca_phe: bàn thấp, ghế nhựa, quầy pha phin
        p += [box((1.0, 0.5, 0.9), (-1.3, -0.4, 0.45), "than_cay", bev=0.02),
              box((1.05, 0.55, 0.04), (-1.3, -0.4, 0.92), "trim")]
        for i in range(4):
            p += [cyl(0.035, 0.1, (-1.65 + i * 0.22, -0.4, 0.99), "ly", v=8),
                  cyl(0.04, 0.05, (-1.65 + i * 0.22, -0.4, 1.06), "xam_nhat", v=8)]
        for x in (0.3, 1.4):
            p += [box((0.55, 0.55, 0.04), (x, -1.0, 0.45), "nhan_xanh", bev=0.01),
                  cyl(0.03, 0.45, (x, -1.0, 0.22), "sat", v=6)]
            for dx in (-0.45, 0.45):
                p.append(cyl(0.14, 0.28, (x + dx, -1.0, 0.14), random.choice(["nhan_do", "nhan_xanh"]), v=8, r2=0.12))
        p += chau_cay(1.85, -0.4, 0.0, 0.8)
    done(ten, "Models/Hem", p)


def xe_hang_rong(loai):
    """Xe bán hàng rong (đầu xe -Y): nuoc_mia (máy ép, bó mía, ly), hu_tieu (xe gỗ, nồi nước lèo, tủ kính, đèn lồng),
    trai_cay (xe đẩy chất trái cây, dù che)."""
    reset()
    random.seed(sum(map(ord, loai)))
    p = []
    for sx in (-1, 1):
        p.append(cyl(0.25, 0.06, (sx * 0.62, 0.2, 0.25), "banh", v=10, rot=(0, 90, 0)))
    p.append(limb((0, 0.6, 0.85), (0, 0.95, 0.95), 0.04, "sat", bev=0))
    if loai == "nuoc_mia":
        p += [box((1.2, 0.8, 0.75), (0, 0.15, 0.62), "trim", bev=0.03),
              box((1.22, 0.82, 0.2), (0, 0.15, 0.55), "la1"),
              chu_3d("NƯỚC MÍA", (0, -0.26, 0.82), 1.0, 0.16, "la1", day=0.008),
              box((0.5, 0.4, 0.4), (-0.25, 0.15, 1.2), "xam_nhat", bev=0.03),
              cyl(0.08, 0.42, (-0.25, 0.0, 1.32), "sat", v=8, rot=(0, 90, 0)),
              cyl(0.08, 0.42, (-0.25, 0.3, 1.32), "sat", v=8, rot=(0, 90, 0)),
              torus(0.18, 0.025, (0.0, 0.15, 1.3), "sat", rot=(0, 90, 0))]
        for i in range(8):  # bó mía dựng nghiêng
            p.append(limb((0.45 + random.uniform(-0.08, 0.08), 0.05 + i * 0.03, 0.95),
                          (0.55 + random.uniform(-0.1, 0.1), 0.05 + i * 0.03, 2.4), 0.05, "la3" if i % 3 else "tim", bev=0))
        for i in range(3):
            p += ly_da(0.15 + i * 0.13, -0.1, 1.0, "caphe_nhat")
    elif loai == "hu_tieu":
        p += [box((1.3, 0.75, 0.8), (0, 0.15, 0.62), "than_cay", bev=0.02),
              box((1.0, 0.04, 0.3), (0, -0.24, 0.75), "nhan_do", bev=0.01),
              chu_3d("HỦ TIẾU", (0, -0.27, 0.75), 0.9, 0.17, "vang", day=0.008),
              box((0.6, 0.6, 0.45), (-0.3, 0.15, 1.25), "kinh_sang", bev=0.02),
              box((0.62, 0.62, 0.04), (-0.3, 0.15, 1.49), "than_cay"),
              cyl(0.24, 0.35, (0.35, 0.15, 1.2), "xam_nhat", v=12), cyl(0.25, 0.04, (0.35, 0.15, 1.39), "xam", v=12),
              limb((-0.6, 0.5, 1.0), (-0.6, 0.5, 1.9), 0.04, "than_cay", bev=0),
              ball(0.14, (-0.6, 0.3, 1.75), "nhan_do", scale=(1, 1, 1.25))]
        for i in range(4):
            p.append(cyl(0.1, 0.05, (-0.3, 0.15, 1.08 + i * 0.05), "trim", v=10, r2=0.07))
    else:
        p += [box((1.4, 0.9, 0.06), (0, 0.15, 0.75), "than_cay"),
              box((1.4, 0.06, 0.2), (0, -0.3, 0.85), "than_cay"), box((1.4, 0.06, 0.2), (0, 0.6, 0.85), "than_cay")]
        for i in range(40):  # trái cây chất thành đống
            p.append(ball(0.08, (random.uniform(-0.6, 0.6), random.uniform(-0.25, 0.55), 0.85 + random.uniform(0, 0.12)),
                          random.choice(["vang", "cam", "nhan_do", "la1", "hong"])))
        p += [cyl(0.03, 1.8, (0.55, 0.5, 1.6), "sat", v=5), cyl(1.0, 0.35, (0.55, 0.5, 2.6), "nhan_xanh", v=8, r2=0.05)]
    ten = {"nuoc_mia": "XeNuocMia", "hu_tieu": "XeHuTieu", "trai_cay": "XeTraiCay"}[loai]
    done(ten, "Models/Hem", p)


# ---------- Ngã rẽ đường lớn, đoạn cuối nhánh có nhà giao, tiệm sửa xe Chú Bảy ----------
def khoi_phang(diem, z0, z1, col):
    """Lăng trụ đứng có đáy là đa giác `diem` [(x, y), ...], từ z0 lên z1 (dùng cho mũi tên sơn trên mặt đường)."""
    bm = bmesh.new()
    duoi = [bm.verts.new((x, y, z0)) for x, y in diem]
    tren = [bm.verts.new((x, y, z1)) for x, y in diem]
    n = len(diem)
    bm.faces.new(duoi[::-1])
    bm.faces.new(tren)
    for k in range(n):
        bm.faces.new((duoi[k], duoi[(k + 1) % n], tren[(k + 1) % n], tren[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("phang")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("phang", me)
    bpy.context.scene.collection.objects.link(o)
    return fin(o, col)


def mui_ten(x, y, re=None, col="trim", z=0.015):
    """Mũi tên sơn trên làn, chỉ hướng đi tới (-Y). re = 1 (rẽ trái, +X) / -1 (rẽ phải): thêm nhánh rẽ ngang.
    Mũi tên rẽ dời thân về phía đối diện để cả mũi tên nằm gọn trong làn rộng 3 m (cách tim làn tối đa 1,2 m)."""
    if re:
        x -= re * 0.5
    p = [box((0.3, 3.0, z), (x, y, z / 2), col),
         khoi_phang([(x - 0.55, y - 1.5), (x + 0.55, y - 1.5), (x, y - 2.6)], 0, z, col)]
    if re:
        p += [box((0.8, 0.3, z), (x + re * 0.4, y - 0.4, z / 2), col),
              khoi_phang([(x + re * 0.8, y - 0.9), (x + re * 0.8, y + 0.1), (x + re * 1.7, y - 0.4)], 0, z, col)]
    return p


def via_he_doan(x0, x1, y0, y1, bo):
    """Một khối vỉa hè chữ nhật (x0..x1, y0..y1) cao 0,25 m, bó vỉa ở các cạnh trong `bo` ("x0", "x1", "y0", "y1")."""
    p = [box((x1 - x0, y1 - y0, 0.45), ((x0 + x1) / 2, (y0 + y1) / 2, 0.025), "via_he")]
    for c in bo:
        if c in ("x0", "x1"):
            x = x0 + 0.1 if c == "x0" else x1 - 0.1
            p.append(box((0.2, y1 - y0, 0.47), (x, (y0 + y1) / 2, 0.035), "xam_nhat"))
        else:
            y = y0 + 0.1 if c == "y0" else y1 - 0.1
            p.append(box((x1 - x0, 0.2, 0.47), ((x0 + x1) / 2, y, 0.035), "xam_nhat"))
    return p


def nga_re(ben):
    """Đoạn đường lớn 40 m có ngã rẽ vuông góc ở giữa (z = 20 trong Unity), để người chơi chọn đi thẳng hay rẽ.
    ben: trai (nhánh bên trái người lái, +X Blender), phai, tu (cả hai bên). Nhánh là đoạn đường 3 làn dài 12 m tính
    từ mép đường chính; nối tiếp bằng DuongLon_100m đặt tại DiemNhanhTrai/DiemNhanhPhai.
    Có vạch người đi bộ ở miệng nhánh và mũi tên sơn trên làn trước giao lộ."""
    reset()
    L, lane, le, Lb = 40.0, 3.0, 2.0, 12.0
    W2, yc = 1.5 * lane, -L / 2
    phia = {"trai": [1], "phai": [-1], "tu": [1, -1]}[ben]
    p = [box((3 * lane, L, 0.2), (0, -L / 2, -0.1), "duong")]
    for x in (-lane / 2, lane / 2):  # vạch làn, bỏ trong lòng giao lộ
        for i in range(0, int(L), 6):
            if abs(-(i + 1.5) - yc) > W2 + le + 2:
                p.append(box((0.15, 3.0, 0.02), (x, -(i + 1.5), 0.01), "trim"))
    for sgn in (-1, 1):
        xa, xb = sorted((sgn * W2, sgn * (W2 + le)))
        bo = ["x0"] if sgn > 0 else ["x1"]
        if sgn in phia:  # vỉa hè đường chính bị cắt ở miệng nhánh; vỉa hè nhánh chạy ra ngoài
            p += via_he_doan(xa, xb, yc + W2, 0, bo + ["y0"])
            p += via_he_doan(xa, xb, -L, yc - W2, bo + ["y1"])
            xn0, xn1 = sorted((sgn * (W2 + le), sgn * (W2 + Lb)))
            p += via_he_doan(xn0, xn1, yc + W2, yc + W2 + le, ["y0"])
            p += via_he_doan(xn0, xn1, yc - W2 - le, yc - W2, ["y1"])
            p.append(box((Lb, 3 * lane, 0.2), (sgn * (W2 + Lb / 2), yc, -0.1), "duong"))
            for y in (yc - lane / 2, yc + lane / 2):  # vạch làn của nhánh
                for xm in (W2 + 4.5, W2 + 10.5):
                    p.append(box((3.0, 0.15, 0.02), (sgn * xm, y, 0.01), "trim"))
            for k in range(8):  # vạch người đi bộ băng qua miệng nhánh
                p.append(box((2.6, 0.45, 0.02), (sgn * (W2 + 3.6), yc - 3.5 + k, 0.012), "trim"))
        else:
            p += via_he_doan(xa, xb, -L, 0, bo)
    for k, x in enumerate((-lane, 0, lane)):  # mũi tên trước giao lộ: làn sát nhánh có thêm hướng rẽ
        re = None
        if x > 0 and 1 in phia:
            re = 1
        elif x < 0 and -1 in phia:
            re = -1
        p += mui_ten(x, -7.0, re)
    ten = {"trai": "DuongLon_NgaBaTrai", "phai": "DuongLon_NgaBaPhai", "tu": "DuongLon_NgaTu"}[ben]
    diem = {"DiemNoi": (0, -L, 0, 0), "DiemGiaoLo": (0, yc, 0, 0)}
    for sgn in phia:
        diem["DiemNhanhTrai" if sgn > 0 else "DiemNhanhPhai"] = (sgn * (W2 + Lb), yc, 0, 90 * sgn)
    done(ten, "Models/Duong", p, diem)


def cuoi_nhanh():
    """Đoạn cuối nhánh dài 30 m, đường cụt có vỉa hè chắn ngang và bồn cây. Ô dừng giao hàng sơn vàng ở làn phải
    (-X Blender = bên phải người lái) trước nhà khách. DiemGiao: chỗ xe dừng; DiemNhaKhach: chỗ đặt nhà khách
    (mặt tiền quay ra đường); DiemCoDich: chỗ cắm cờ đích."""
    reset()
    random.seed(350)
    L, lane, le = 30.0, 3.0, 2.0
    W2 = 1.5 * lane
    p = [box((3 * lane, L, 0.2), (0, -L / 2, -0.1), "duong")]
    for x in (-lane / 2, lane / 2):
        for i in range(0, 12, 6):
            p.append(box((0.15, 3.0, 0.02), (x, -(i + 1.5), 0.01), "trim"))
    p += via_he_doan(W2, W2 + le, -L, 0, ["x0"])
    p += via_he_doan(-W2 - le, -W2, -L, 0, ["x1"])
    p += via_he_doan(-W2 - le, W2 + le, -L - le, -L, ["y1"])
    for x in (-3.6, 0, 3.6):  # bồn cây chắn cuối đường, có sọc phản quang
        p += [box((2.6, 0.9, 0.5), (x, -L - 1.1, 0.5), "be_tong", bev=0.04),
              box((2.62, 0.92, 0.12), (x, -L - 1.1, 0.55), "vang"),
              box((0.5, 0.94, 0.13), (x, -L - 1.1, 0.55), "vien")]
        for j in range(3):
            p.append(ball(0.42, (x - 0.8 + j * 0.8, -L - 1.1, 0.95), random.choice(["la1", "la2", "la_dam"]), jit=0.05))
    yg = -20.0  # ô dừng giao hàng
    p += [box((0.15, 8.0, 0.02), (-lane - 1.3, yg, 0.012), "vang"),
          box((0.15, 8.0, 0.02), (-lane + 1.3, yg, 0.012), "vang"),
          box((2.75, 0.15, 0.02), (-lane, yg + 4.0, 0.012), "vang"),
          box((2.75, 0.15, 0.02), (-lane, yg - 4.0, 0.012), "vang")]
    for k in range(5):
        p.append(box((0.25, 2.5, 0.015), (-lane, yg + 2.8 - k * 1.4, 0.01), "vang", rot=(0, 0, 45)))
    p += mui_ten(-lane, -6.0, None, col="vang")
    done("DuongLon_CuoiNhanh_30m", "Models/Duong", p,
         {"DiemGiao": (-lane, yg, 0, 0), "DiemNhaKhach": (-W2 - le, yg, 0.25, 90), "DiemCoDich": (-W2 - 0.6, yg + 2.5, 0.25, 0)})


def cuoi_hem():
    """Đoạn cuối hẻm cụt 20 m: mặt hẻm có rãnh thoát nước, cuối hẻm là bức tường cũ có cửa sắt, chậu cây, bóng đèn.
    Nhà khách đặt bên phải hẻm tại DiemNhaKhach."""
    reset()
    random.seed(360)
    L, W = 20.0, 3.5
    p = [box((W, L, 0.2), (0, -L / 2, -0.1), "nhua_hem")]
    for sgn in (-1, 1):
        p.append(box((0.25, L, 0.03), (sgn * (W / 2 - 0.125), -L / 2, 0.005), "xam"))
    p += [box((W + 0.6, 0.3, 3.2), (0, -L - 0.15, 1.6), "tuong_cu", bev=0.03, jit=0.01),
          box((W + 0.7, 0.4, 0.15), (0, -L - 0.15, 3.25), "trim", bev=0.02),
          box((1.6, 0.06, 2.3), (0.5, -L + 0.02, 1.15), "sat", bev=0.01),
          box((0.12, 0.08, 0.18), (-0.8, -L + 0.01, 2.8), "vang"),
          box((0.08, 0.2, 0.05), (-0.8, -L + 0.08, 2.9), "sat")]
    for k in range(7):
        p.append(box((0.05, 0.05, 2.2), (-0.2 + k * 0.233, -L - 0.02, 1.15), "xam"))
    p += chau_cay(-1.3, -L + 0.4, 0.0, 1.0) + chau_cay(1.45, -L + 0.4, 0.0, 0.8)
    p.append(cyl(0.35, 0.02, (0.4, -8, 0.005), "sat", v=10))
    done("Hem_CuoiHem_20m", "Models/Duong", p,
         {"DiemGiao": (0, -14.0, 0, 0), "DiemNhaKhach": (-W / 2, -14.0, 0, 90), "DiemCoDich": (-W / 2 + 0.4, -12.0, 0, 0)})


def tiem_sua_xe_chu_bay():
    """Tiệm sửa xe của Chú Bảy (nâng cấp xe giữa các màn): nhà 2 tầng mặt tiền 6 m như các cửa hàng ở mục địa điểm.
    Trong tiệm có xe đang sửa, chồng lốp, lốp treo tường, bảng đồ nghề, máy bơm hơi; ngoài vỉa hè có bảng "VÁ XE"."""
    reset()
    random.seed(340)
    W = 6
    p = mat_tien_cua_hang(W, "tuong_xanh", "xanh_xe", ("xanh_xe", "trim"))
    p.append(chu_3d("SỬA XE CHÚ BẢY", (0, -0.225, 3.42), W - 0.8, 0.42, "xanh_xe"))
    for x in (-2.35, -1.75):  # chồng lốp
        for k in range(5 if x < -2 else 3):
            p.append(torus(0.28, 0.08, (x, -0.55, 0.08 + k * 0.16), "banh"))
    for x in (-0.9, -0.2, 0.5):  # lốp treo trên tường trong tiệm
        p.append(torus(0.3, 0.07, (x, -0.1, 2.05), "banh", rot=(90, 0, 0)))
    p.append(box((1.3, 0.05, 0.8), (1.75, -0.1, 1.5), "sat", bev=0.01))  # bảng đồ nghề
    for k in range(5):
        p.append(box((0.05, 0.06, 0.35), (1.25 + k * 0.25, -0.14, 1.55), random.choice(["xam_nhat", "nhan_do", "vang"])))
    p += [cyl(0.18, 0.6, (2.2, -0.6, 0.3), "nhan_do", v=10, rot=(0, 90, 0)),  # máy bơm hơi
          box((0.4, 0.3, 0.2), (2.2, -0.6, 0.6), "sat", bev=0.02),
          limb((2.0, -0.6, 0.62), (1.6, -1.1, 0.05), 0.02, "vien", bev=0),
          box((0.5, 0.3, 0.25), (1.2, -0.8, 0.13), "nhan_do", bev=0.02),  # thùng đồ nghề
          cyl(0.07, 0.2, (0.85, -0.85, 0.1), "vang", v=8), cyl(0.07, 0.2, (0.7, -0.8, 0.1), "nhan_xanh", v=8),
          cyl(0.55, 0.004, (0.0, -1.2, 0.003), "uot", v=10)]  # vệt nhớt
    p += dich(than_xe_so("nhan_do", baga=False), dx=0.0, dy=-1.3)
    xb = -2.4  # bảng chữ A "VÁ XE" trên vỉa hè
    p += [box((0.75, 0.05, 0.85), (xb, -1.75, 0.75), "trim", bev=0.02),
          box((0.75, 0.05, 0.85), (xb, -1.45, 0.75), "trim", bev=0.02),
          limb((xb - 0.35, -1.75, 0.0), (xb - 0.35, -1.75, 0.35), 0.03, "sat", bev=0),
          limb((xb + 0.35, -1.75, 0.0), (xb + 0.35, -1.75, 0.35), 0.03, "sat", bev=0),
          chu_3d("VÁ XE", (xb, -1.785, 0.82), 0.6, 0.22, "nhan_do")]
    done("TiemSuaXeChuBay", "Models/DiaDiem", p)


# ---------- Biển hiệu đặt trên vỉa hè: hộp đèn, bảng chữ A, biển đứng hai cột ----------
def chu_hai_mat(noi_dung, z, nua_day, rong, cao, col, nghieng=0.0):
    """Chữ trên cả hai mặt của một bảng đứng ở x = 0: mặt trước quay -Y, mặt sau quay +Y, cách tâm nua_day.
    nghieng: góc ngả đầu bảng vào trong (độ), dùng cho bảng chữ A."""
    p = []
    for mat in (-1, 1):
        o = chu_3d(noi_dung, (0, 0, 0), rong, cao, col)
        if mat > 0:
            o.data.transform(Matrix.Rotation(math.pi, 4, "Z"))
        o.data.transform(Matrix.Rotation(math.radians(nghieng) * mat, 4, "X"))
        o.data.transform(Matrix.Translation((0, mat * nua_day, z)))
        p.append(o)
    return p


def hop_den(ten, chu, mau):
    """Hộp đèn đứng trên vỉa hè (kiểu quán ăn, tiệm gội đầu): thân hộp 0,9 x 0,35 x 1,3 m trên đế, hai mặt chữ.
    Đặt vuông góc với lề đường để xe chạy tới đọc được."""
    reset()
    p = [box((0.6, 0.45, 0.12), (0, 0, 0.06), "vien", bev=0.02),
         box((0.12, 0.12, 0.2), (0, 0, 0.2), "sat"),
         box((0.92, 0.36, 1.3), (0, 0, 0.95), mau, bev=0.03)]
    for mat in (-1, 1):
        p += [box((0.8, 0.02, 1.0), (0, mat * 0.18, 0.95), "trim", bev=0.005),
              box((0.8, 0.025, 0.1), (0, mat * 0.185, 0.55), mau),
              box((0.5, 0.025, 0.05), (0, mat * 0.185, 1.32), mau)]
    p += chu_hai_mat(chu, 1.0, 0.205, 0.7, 0.24, mau)
    done(ten, "Models/Pho", p)


def bang_chu_a(ten, chu, nen, mau):
    """Bảng chữ A gấp đặt trước cửa tiệm: hai tấm ngả 12 độ, khung gỗ, chữ hai mặt."""
    reset()
    g = 12
    p = []
    for mat in (-1, 1):  # hai tấm chụm đầu ở trên, xòe chân ở dưới
        p.append(box((0.7, 0.04, 1.0), (0, mat * 0.11, 0.5), "than_cay", rot=(g * mat, 0, 0), bev=0.01))
        p.append(box((0.6, 0.045, 0.85), (0, mat * 0.115, 0.52), nen, rot=(g * mat, 0, 0)))
    p += chu_hai_mat(chu, 0.65, 0.11 - 0.15 * math.sin(math.radians(g)) + 0.04, 0.52, 0.17, mau, nghieng=g)
    p.append(box((0.06, 0.3, 0.03), (0, 0, 0.35), "sat"))
    done(ten, "Models/Pho", p)


def bien_dung(ten, chu, mau):
    """Biển đứng hai cột cao 2,3 m có chân đế bê tông, bảng ngang 1,4 x 0,6 m chữ hai mặt (tiệm sim thẻ, photo)."""
    reset()
    p = []
    for x in (-0.65, 0.65):
        p += [box((0.3, 0.3, 0.2), (x, 0, 0.1), "be_tong", bev=0.03),
              cyl(0.03, 2.3, (x, 0, 1.15), "sat", v=8)]
    p += [box((1.45, 0.08, 0.65), (0, 0, 1.95), mau, bev=0.02),
          box((1.3, 0.1, 0.5), (0, 0, 1.95), "trim")]
    p += chu_hai_mat(chu, 1.95, 0.055, 1.15, 0.26, mau)
    done(ten, "Models/Pho", p)


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
    o = [x for x in bpy.context.selected_objects if x.parent is None][0]  # bỏ qua Empty con (điểm gắn)
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


def preview_vatcan(png):
    """Góc camera trong game: xe shipper chạy giữa làn, phía trước là ổ gà, vũng nước, rào chắn, lô cốt."""
    reset()
    place("Models/Duong/DuongLon_100m.fbx", (0, 10, 0))
    for k in range(10):
        place(f"Models/Pho/NhaOng_{k % 4 + 1}.fbx", (-6.5, 6 - k * 4, 0), 90)
        place(f"Models/Pho/NhaOng_{(k + 2) % 4 + 1}.fbx", (6.5, 4 - k * 4, 0), -90)
    place("Models/VatCan/OGa_1.fbx", (0.2, -6, 0))
    place("Models/VatCan/VungNuoc_Lon.fbx", (-3.0, -11, 0))
    place("Models/VatCan/OGa_Cum.fbx", (3.0, -14, 0))
    place("Models/VatCan/RaoChan_SocDo.fbx", (3.0, -20, 0))
    place("Models/VatCan/LoCot_1Lan.fbx", (-3.0, -26, 0))
    place("Models/VatCan/OGa_2.fbx", (0.0, -30, 0))
    place("Models/VatCan/VungNuoc_Nho.fbx", (0.6, -36, 0))
    place("Models/VatCan/LoCot_2Lan.fbx", (1.5, -44, 0))
    place("Models/XeShipper/XeShipper.fbx", (0, 0, 0))
    place("Models/XeShipper/GioSau.fbx", (0, 0.66, 0.855))
    place("Models/HangHoa/BoHoa_Nguyen.fbx", (0, 0.66, 0.875))
    setup_render(png, (1080, 1920), HEX["bau_troi"], (0, 6.5, 4.2), (0, -14, 0.4), None)


def preview_shipper(png):
    """Ba bộ ghép thử nhìn từ sau lưng: thùng + đồ gốm, rổ + bó hoa, khay + 2 ly cà phê; và xe trống nhìn chéo trước."""
    reset()
    ground((10, 7, 0.1), (0, 0, -0.05), "duong")

    def ghep(x, rz, do_cho, mon):
        a = math.radians(rz)
        quay = lambda px, py: (x + px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a))
        place("Models/XeShipper/XeShipper.fbx", (x, 0, 0), rz)
        if do_cho:
            place(f"Models/XeShipper/{do_cho}.fbx", (*quay(0, 0.66), 0.855), rz)
        for (px, py, pz), m in mon:
            place(f"Models/HangHoa/{m}.fbx", (*quay(px, 0.66 + py), 0.855 + pz), rz)
    ghep(-2.4, -35, None, [])
    ghep(-0.8, 180, "ThungHang", [((0, 0, 0.34), "BinhGom_Nguyen")])
    ghep(0.8, 180, "GioSau", [((0, 0, 0.02), "BoHoa_Nguyen")])
    ghep(2.4, 180, "KhayLy", [((-0.075, -0.075, 0.035), "CaPhe_Nguyen"), ((0.075, 0.075, 0.035), "CaPhe_HuMotPhan")])
    setup_render(png, (1920, 1000), HEX["bau_troi"], (-1.5, -7.5, 3.6), (0, 0, 0.95), 6.4)


def preview_nguoi(png):
    """Xe máy AI, xe đậu, shipper và người đi bộ đứng cạnh nhau để so phong cách."""
    reset()
    ground((14, 6, 0.1), (0, 0, -0.05), "duong")
    for x, f, rz in ((-4.6, "XeAI/XeMayAI_1", -30), (-3.0, "XeAI/XeMayAI_2", -30), (-1.4, "XeShipper/XeShipper", -30),
                     (0.2, "Hem/XeMayDau_1", -30)):
        place(f"Models/{f}.fbx", (x, 0, 0), rz)
    for x, f in ((1.5, "NguoiDiBo_1"), (2.4, "NguoiDiBo_2"), (3.5, "NguoiGanhHang"), (4.6, "HocSinh")):
        place(f"Models/Nguoi/{f}.fbx", (x, 0, 0), -20)
    setup_render(png, (1920, 900), HEX["bau_troi"], (-2.0, -9.5, 3.4), (0, 0, 0.85), 10.5)


def preview_xecham(png):
    """Xe chậm trên đường: người đạp xe và xe ba gác, cạnh xe máy AI để so cỡ."""
    reset()
    ground((14, 8, 0.1), (0, 0, -0.05), "duong")
    for x, f in ((-4.2, "XeDap_1"), (-2.8, "XeDap_2"), (-0.6, "XeBaGac_1"), (2.4, "XeBaGac_2"), (4.6, "XeMayAI_1")):
        place(f"Models/XeAI/{f}.fbx", (x, 0, 0), -30)
    setup_render(png, (1920, 900), HEX["bau_troi"], (-2.5, -11, 4.5), (0, 0.3, 0.85), 11.5)


def preview_duong_cong(png):
    """Nhìn từ trên: các đoạn cong nối nhau, khúc rẽ 90 độ, các khúc cong của hẻm."""
    reset()
    ground((260, 200, 0.1), (0, -60, -0.3), "co")
    x, y = 0, 0
    place("Models/Duong/DuongLon_100m_HemPhai.fbx", (0, 0, 0))
    place("Models/Duong/DuongLon_CongTrai_30.fbx", (0, -100, 0))
    a = math.radians(30)
    R = 60
    ex, ey = R - R * math.cos(a), -R * math.sin(a)
    place("Models/Duong/DuongLon_CongPhai_30.fbx", (ex, -100 + ey, 0), 30)
    place("Models/Duong/DuongLon_CongPhai_90.fbx", (-30, 0, 0))
    place("Models/Duong/Hem_CongPhai_90.fbx", (-6.5, -50, 0), -90)
    place("Models/Duong/Hem_CongTrai_45.fbx", (-30, -60, 0))
    place("Models/Duong/Hem_CongPhai_45.fbx", (-40, -60, 0))
    place("Models/Duong/Hem_CongTrai_90.fbx", (-50, -60, 0))
    setup_render(png, (1400, 1400), HEX["bau_troi"], (-15, -75, 160), (-15, -74, 0), 170)


def preview_dia_diem(png):
    """Trạm Ký Ức và 3 cửa hàng đứng cạnh nhau; nhà khách có biển số và cờ đích; cây me."""
    reset()
    ground((50, 10, 0.2), (0, -6, -0.1), "duong")
    ground((50, 3, 0.15), (0, -1.5, 0.075), "via_he")
    for x, f in ((-12.5, "TramKyUc"), (-6.5, "QuanNuocNgon"), (-1, "TiemHoaBonMua"), (4.5, "TiemGomCoTu")):
        place(f"Models/DiaDiem/{f}.fbx", (x, 0, 0))
    place("Models/Pho/NhaOng_3.fbx", (10, 0, 0))
    place("Models/DiaDiem/BienSoNha.fbx", (8.95, -0.12, 1.9))
    place("Models/DiaDiem/CoDich.fbx", (9.2, -1.2, 0.15))
    place("Models/Pho/CayMe.fbx", (15.5, -1.8, 0.15))
    place("Models/XeShipper/XeShipper.fbx", (7.5, -4.2, 0), 90)
    setup_render(png, (1920, 1000), HEX["bau_troi"], (-8, -32, 15), (0, -1, 3.2), 34)


def preview_xe_dong(png):
    """Đoạn đông xe nhìn từ góc camera trong game: ba làn kín xe máy các kiểu, xen xe đạp và ba gác."""
    reset()
    place("Models/Duong/DuongLon_100m.fbx", (0, 10, 0))
    for k in range(8):
        place(f"Models/Pho/{['NhaOng_1', 'NhaTret_1', 'NhaO_1', 'NhaGara_1', 'NhaOng_3', 'NhaTret_2', 'NhaO_2', 'NhaGara_2'][k]}.fbx",
              (-6.5, 4 - k * 5, 0), 90)
        place(f"Models/Pho/{['NhaO_2', 'NhaOng_2', 'NhaGara_2', 'NhaTret_1', 'NhaOng_4', 'NhaO_1', 'NhaTret_2', 'NhaGara_1'][k]}.fbx",
              (6.5, 2 - k * 5, 0), -90)
    ds = ["XeSo_A1", "XeSo_A2", "XeSo_B1", "XeSo_B2", "XeHaiNguoi_A1", "XeHaiNguoi_A2", "XeHaiNguoi_B1",
          "XeHaiNguoi_B2", "XeChoHang_1", "XeChoHang_2", "XeShipperKhac_1", "XeShipperKhac_2", "XeTayGaLon_1",
          "XeTayGaLon_2", "XeMayAI_1", "XeMayAI_2", "XeDap_1", "XeBaGac_1"]
    random.seed(5)
    i = 0
    for row in range(7):
        for lane in (-3.0, 0.0, 3.0):
            for sub in (-0.7, 0.7):
                if random.random() < 0.25:
                    continue
                f = ds[i % len(ds)]
                i += 1
                if f == "XeBaGac_1" and sub > 0:
                    continue
                place(f"Models/XeAI/{f}.fbx", (lane + sub + random.uniform(-0.2, 0.2), -6 - row * 3.2 + random.uniform(-0.5, 0.5), 0),
                      random.uniform(-6, 6))
    place("Models/XeShipper/XeShipper.fbx", (0, 0, 0))
    place("Models/XeShipper/GioSau.fbx", (0, 0.66, 0.855))
    place("Models/HangHoa/BoHoa_Nguyen.fbx", (0, 0.66, 0.875))
    setup_render(png, (1080, 1920), HEX["bau_troi"], (0, 6.5, 4.6), (0, -14, 0.6), None)


def preview_nha_moi(png):
    """Nhà trệt, nhà ở, nhà có gara xếp cạnh nhà ống để so tỉ lệ."""
    reset()
    ground((44, 10, 0.2), (0, -6, -0.1), "duong")
    ground((44, 3, 0.15), (0, -1.5, 0.075), "via_he")
    x = -28.0
    for f, w in (("NhaOng_1", 4), ("NhaOng_6", 6), ("NhaOng_5", 8), ("NhaTret_1", 4), ("NhaTret_2", 4), ("NhaO_1", 5),
                 ("NhaO_2", 5), ("NhaGara_1", 5), ("NhaGara_2", 5)):
        place(f"Models/Pho/{f}.fbx", (x + w / 2, 0, 0))
        x += w + 0.3
    setup_render(png, (1920, 1000), HEX["bau_troi"], (-10, -42, 18), (-2, -1, 4.5), 50)


def preview_cong_trinh2(png):
    """Bảo tàng, trường học, bệnh viện, nhà sân vườn, biệt thự xếp dọc một dãy phố, trạm xe buýt trên vỉa hè."""
    reset()
    ground((175, 14, 0.2), (0, -8, -0.1), "duong")
    ground((175, 3, 0.15), (0, -1.5, 0.075), "via_he")
    for x, f in ((-70, "BaoTang"), (-35, "TruongHoc"), (-1, "BenhVien"), (21, "NhaSanVuon"), (35, "BietThu_Phap"),
                 (52, "BietThu_HienDai"), (66, "NhaOng_2"), (70.5, "NhaO_1")):
        place(f"Models/Pho/{f}.fbx", (x, 0, 0))
    place("Models/Pho/TramXeBuyt.fbx", (-17, -2.6, 0.15))
    place("Models/XeShipper/XeShipper.fbx", (-12, -6, 0), 90)
    setup_render(png, (1920, 1000), HEX["bau_troi"], (-70, -150, 75), (-6, 0, 6), 162)


def preview_hem2(png):
    """Hẻm có nhà trệt, nhà cổ, tiệm và quán, xe bán hàng rong, nhiều kiểu người, nhìn từ góc camera trong game."""
    reset()
    ground((80, 120, 0.1), (0, -30, -0.08), "duong")
    place("Models/Duong/Hem_50m.fbx", (0, 0, 0))
    trai = ["HemTiem_TapHoa", "NhaHem_Tret_1", "NhaHem_Co", "HemQuan_CaPhe", "NhaHem_2", "HemTiem_CatToc", "NhaHem_Tret_2", "NhaHem_1"]
    phai = ["NhaHem_Tret_2", "HemQuan_ComTam", "NhaHem_1", "HemTiem_SuaXe", "NhaHem_Tret_1", "NhaHem_3", "NhaHem_Co", "NhaHem_2"]
    for k in range(8):
        place(f"Models/Hem/{trai[k]}.fbx", (-1.75, -2 - k * 4.6, 0), 90)
        place(f"Models/Hem/{phai[k]}.fbx", (1.75, -4 - k * 4.6, 0), -90)
    place("Models/Hem/CongHem.fbx", (0, 0, 0))
    place("Models/Hem/XeNuocMia.fbx", (1.2, -9.5, 0), 180)
    place("Models/Hem/XeTraiCay.fbx", (-1.1, -24, 0), 90)
    place("Models/Hem/XeHuTieu.fbx", (1.1, -30, 0), -90)
    for x, y, f, rz in ((-0.9, -16.5, "NguoiNgoiGhe_1", 90), (-1.2, -17.8, "NguoiNgoiGhe_2", 60), (0.4, -12, "OngCu", 0),
                        (-0.3, -20, "NguoiBanVeSo", 180), (0.6, -27, "NuSinhAoDai", 0), (-0.5, -34, "TreEm", 180),
                        (0.2, -6, "NhanVienVanPhong", 0), (0.7, -38, "NguoiTapTheDuc", 180)):
        place(f"Models/Nguoi/{f}.fbx", (x, y, 0), rz)
    place("Models/XeShipper/XeShipper.fbx", (0, 2.5, 0))
    setup_render(png, (1080, 1920), HEX["bau_troi"], (0, 7.5, 4.2), (0, -14, 1.2), None, 1.1, (18, 0, -25))


def preview_hem2_tiem(png):
    """Nhà trệt, nhà cổ, 5 tiệm và quán trong hẻm, 3 xe bán hàng rong, nhìn chính diện."""
    reset()
    ground((44, 8, 0.1), (0, -2.5, -0.05), "nhua_hem")
    ds = [("NhaHem_Tret_1", 4), ("NhaHem_Co", 4.5), ("HemTiem_TapHoa", 4), ("HemTiem_TapHoa_Tret", 4),
          ("HemTiem_SuaXe_Tret", 4), ("HemQuan_ComTam_Rong", 8), ("HemTiem_CatToc_MaiBang", 4),
          ("HemQuan_CaPhe_MaiBang", 6), ("NhaHem_4", 6), ("NhaHem_5", 8)]
    x = -27.0
    for f, w in ds:
        place(f"Models/Hem/{f}.fbx", (x + w / 2, 0, 0))
        x += w + 0.4
    for x, f in ((-17, "XeNuocMia"), (1, "XeHuTieu"), (14, "XeTraiCay")):
        place(f"Models/Hem/{f}.fbx", (x, -3.2, 0), 180)
    for x, f, rz in ((-4, "NguoiNgoiGhe_1", 0), (15.4, "NguoiNgoiGhe_2", 20), (-13, "OngCu", -30), (7, "NguoiBanVeSo", 10)):
        place(f"Models/Nguoi/{f}.fbx", (x, -2.2, 0), rz)
    setup_render(png, (1920, 900), HEX["bau_troi"], (-8, -40, 15), (0, 0, 3.2), 58)


def preview_nguoi2(png):
    """Mọi kiểu người đi bộ và người ngồi ghế đứng cạnh nhau."""
    reset()
    ground((16, 5, 0.1), (0, 0, -0.05), "via_he")
    ds = ["NguoiDiBo_1", "NguoiDiBo_2", "NguoiGanhHang", "HocSinh", "OngCu", "NguoiBanVeSo", "NhanVienVanPhong",
          "NuSinhAoDai", "NguoiTapTheDuc", "TreEm", "NguoiNgoiGhe_1", "NguoiNgoiGhe_2"]
    for i, f in enumerate(ds):
        place(f"Models/Nguoi/{f}.fbx", (-6.6 + i * 1.2, 0, 0), -20)
    setup_render(png, (1920, 700), HEX["bau_troi"], (-2, -10, 3.2), (0, 0, 0.75), 14.5)


def preview_hanghoa(png):
    """6 món hàng x 3 trạng thái (cột: nguyên, hư một phần, sập hỏng)."""
    reset()
    ground((1.6, 2.4, 0.04), (0, 0.1, -0.02), "tuong_kem")
    hang = [("BoHoa", "Nguyen", "HuMotPhan", "SapHong"), ("BanhKem", "Nguyen", "HuMotPhan", "SapHong"),
            ("BinhGom", "Nguyen", "Nut", "Vo"), ("TraSua", "Nguyen", "HuMotPhan", "SapHong"),
            ("CaPhe", "Nguyen", "HuMotPhan", "SapHong"), ("ViTrung", "Nguyen", "HuMotPhan", "SapHong")]
    for r, (mon, *tt) in enumerate(hang):
        for c, st in enumerate(tt):
            place(f"Models/HangHoa/{mon}_{st}.fbx", (-0.42 + c * 0.42, 0.95 - r * 0.36, 0))
    setup_render(png, (1400, 1800), "FBE3C8", (-1.5, -2.6, 2.6), (0, 0.1, 0.05), 2.35)


# Tham số sau thư mục Art chọn nhóm cần dựng: cu, cong_trinh, cong_vien, hem (bỏ trống là dựng tất cả)
NHOM = set(sys.argv[sys.argv.index("--") + 2:]) if "--" in sys.argv else set()
def preview_nga_re(png):
    """Nhìn từ trên cao: đi thẳng qua ngã ba, nhánh trái nối đường 100 m; đi tiếp tới đoạn cuối nhánh có nhà khách;
    tiệm sửa xe Chú Bảy bên đường."""
    reset()
    ground((200, 200, 0.1), (0, -60, -0.3), "co")
    place("Models/Duong/DuongLon_NgaBaTrai.fbx", (0, 0, 0))
    place("Models/Duong/DuongLon_100m.fbx", (16.5, -20, 0), 90)
    place("Models/Duong/DuongLon_CuoiNhanh_30m.fbx", (0, -40, 0))
    place("Models/Pho/NhaOng_3.fbx", (-6.5, -60, 0.25), 90)
    place("Models/DiaDiem/CoDich.fbx", (-5.1, -57.5, 0.25))
    place("Models/XeShipper/XeShipper.fbx", (-3, -60, 0))
    place("Models/XeShipper/XeShipper.fbx", (3, -2, 0))
    place("Models/DiaDiem/TiemSuaXeChuBay.fbx", (6.5, -4, 0.25), -90)
    for i, n in enumerate((1, 2)):
        place(f"Models/Pho/NhaOng_{n}.fbx", (-6.5, -4 - i * 4.5, 0.25), 90)
    place("Models/XeAI/XeMayAI_1.fbx", (0, -12, 0))
    place("Models/XeAI/XeSo_A1.fbx", (3, -30, 0))
    setup_render(png, (1400, 1400), HEX["bau_troi"], (0, 16, 20), (0, -32, 0), 0)


def preview_chu_bay(png):
    """Tiệm sửa xe Chú Bảy nhìn chính diện, cạnh là đoạn cuối hẻm cụt có nhà khách."""
    reset()
    ground((30, 8, 0.2), (0, -5, -0.1), "duong")
    ground((30, 3, 0.15), (0, -1.5, 0.075), "via_he")
    place("Models/DiaDiem/TiemSuaXeChuBay.fbx", (-6, 0, 0.15))
    place("Models/Pho/NhaOng_1.fbx", (-11, 0, 0.15))
    place("Models/XeShipper/XeShipper.fbx", (-3.5, -4.5, 0), 90)
    place("Models/Duong/Hem_CuoiHem_20m.fbx", (8, 0, 0), 180)
    place("Models/Hem/NhaHem_2.fbx", (9.75, 14, 0), -90)
    place("Models/DiaDiem/CoDich.fbx", (9.35, 12, 0))
    setup_render(png, (1920, 1000), HEX["bau_troi"], (-6, -30, 13), (1, 4, 2.5), 0)


def preview_mat_tien(png):
    """Tám mặt tiền nhà ống với các loại hình kinh doanh khác nhau, nhìn chính diện hơi chếch."""
    reset()
    ground((50, 8, 0.2), (0, -5, -0.1), "duong")
    ground((50, 3, 0.15), (0, -1.5, 0.075), "via_he")
    x = -22.0
    for n in (1, 2, 3, 4, 5, 6, 7, 8):
        w = {5: 8, 6: 6}.get(n, 4)
        place(f"Models/Pho/NhaOng_{n}.fbx", (x + w / 2, 0, 0.15))
        x += w + 0.3
    setup_render(png, (1920, 900), HEX["bau_troi"], (-6, -34, 9), (0, 0, 4.5), 0)


def preview_bien_via_he(png):
    """Biển hiệu đứng trên vỉa hè trước dãy nhà ống, xoay vuông góc với lề như ngoài phố."""
    reset()
    ground((34, 10, 0.2), (0, -8, -0.1), "duong")
    ground((34, 3, 0.15), (0, -1.5, 0.075), "via_he")
    x = -16.0
    for n in (1, 2, 3, 4, 7, 8, 6):
        w = {5: 8, 6: 6}.get(n, 4)
        place(f"Models/Pho/NhaOng_{n}.fbx", (x + w / 2, 0, 0.15))
        x += w
    ds = ["BienHopDen_Pho", "BienChuA_BanhMi", "BienHopDen_CaPhe", "BienDung_SimThe", "BienHopDen_ComTam",
          "BienChuA_TraSua", "BienHopDen_GoiDau", "BienDung_Photo"]
    for i, f in enumerate(ds):
        place(f"Models/Pho/{f}.fbx", (-14.6 + i * 4, -2.6, 0.15), 70)
    place("Models/XeShipper/XeShipper.fbx", (-4, -5.5, 0), 90)
    setup_render(png, (1920, 1080), HEX["bau_troi"], (-12, -12, 3.2), (-3, -2, 1.2), 0)


lam = lambda g: not NHOM or g in NHOM

make_palette()
make_palette(os.path.join(ROOT, "Textures", "BangMau_Quan3.png"), QUAN3)
if lam("cu"):
    for s in range(3):
        caphe(s); bohoa(s); gom(s); tra_sua(s); banh_kem(s); vi_trung(s)
    nha(1, 3, "tuong_kem", ("nhan_do", "trim"), "la_dam", "bon", tiem="quan_an", ten="PHỞ BÒ")
    nha(2, 4, "tuong_dao", ("men_nau", "trim"), "trim", "ton", tiem="cafe", ten="CÀ PHÊ", bien="doc")
    nha(3, 2, "tuong_mint", ("nhan_do", "vang"), "nhan_xanh", "ngoi", tiem="tap_hoa", ten="TẠP HÓA", bien="mat")
    nha(4, 5, "tuong_vang", ("la_dam", "trim"), "ton", "bon", tiem="nha_thuoc", ten="NHÀ THUỐC", bien="mat")
    nha(5, 3, "tuong_xanh", ("tim", "trim"), "trim", "bon", W=8.0, tiem="thoi_trang", ten="THỜI TRANG", bien="to")  # 2 lô
    nha(6, 4, "tuong_mint", ("vang", "vien"), "la_dam", "ton", W=6.0, tiem="dien_thoai", ten="ĐIỆN THOẠI", bien="to")  # 1,5 lô
    nha(7, 3, "tuong_kem", ("xam", "trim"), "nhan_xanh", "ton", tiem="dong_cua", bien=None)
    nha(8, 4, "tuong_dao", ("hong", "trim"), "trim", "bon", tiem="ao_dai", ten="ÁO DÀI", bien="lan_can")
    shipper(); thung_hang(); gio_sau(); khay_ly()
    xe_may_ai("XeMayAI_1", "nhan_do", "nam", "trim", "quan", "nhan_xanh")
    xe_may_ai("XeMayAI_2", "trim", "nu", "hong", "quan", "trim")
    cay(1); cay(2); cot_dien()
    preview_pho(os.path.join(HERE, "xem_truoc_asset.png"))
    preview_hanghoa(os.path.join(HERE, "xem_truoc_hanghoa.png"))
    preview_mat_tien(os.path.join(HERE, "xem_truoc_mat_tien.png"))
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
    nha_hem(4, 3, "tuong_kem", "bon", W=6.0)
    nha_hem(5, 2, "tuong_vang", "tum", W=8.0)
    day_dien_hem(); mieu_nho(); guong_cau_loi(); xe_banh_mi()
    xe_dau("XeMayDau_1", "nhan_do", "vang")
    xe_dau("XeMayDau_2", "xanh_xe", "trim")
    nguoi("NguoiDiBo_1", "nhan_xanh", "quan")
    nguoi("NguoiDiBo_2", "hong", "vien", "toc_dai")
    nguoi("NguoiGanhHang", "nhan_do", "vien", "ganh")
    nguoi("HocSinh", "trim", "quan", "hoc_sinh", k=0.72)
    preview_nguoi(os.path.join(HERE, "xem_truoc_nguoi.png"))
if lam("vat_can"):
    o_ga("1"); o_ga("2"); o_ga("cum")
    lo_cot(1); lo_cot(2); rao_chan(); non_giao_thong()
    vung_nuoc(False); vung_nuoc(True)
    shipper(); thung_hang(); gio_sau(); khay_ly()
    preview_vatcan(os.path.join(HERE, "xem_truoc_vatcan.png"))
    preview_shipper(os.path.join(HERE, "xem_truoc_shipper.png"))
if lam("xe_ai"):
    xe_dap("XeDap_1", "nhan_xanh", "ba", "nhan_do", "vien", "rau")
    xe_dap("XeDap_2", "vang", "nam", "trim", "quan", "cap")
    xe_ba_gac("XeBaGac_1", "la_dam", "nhan_xanh", "trim", "thung")
    xe_ba_gac("XeBaGac_2", "xanh_xe", "vang", "nhan_do", "bao")
    preview_xecham(os.path.join(HERE, "xem_truoc_xecham.png"))
if lam("dia_diem"):
    for loai in ("tram", "nuoc", "hoa", "gom"):
        cua_hang(loai)
    bien_so_nha(); co_dich(); cay_me()
    preview_dia_diem(os.path.join(HERE, "xem_truoc_dia_diem.png"))
if lam("nha_o"):
    nha_tret(1); nha_tret(2); nha_o(1); nha_o(2); nha_gara(1); nha_gara(2)
    preview_nha_moi(os.path.join(HERE, "xem_truoc_nha_moi.png"))
if lam("xe_dong"):
    for ten, mau, than, ao, mu, ao2 in (
            ("XeSo_A1", "so_a", "xanh_xe", "nhan_do", "trim", None), ("XeSo_A2", "so_a", "vien", "la1", "vang", None),
            ("XeSo_B1", "so_b", "nhan_do", "tuong_xanh", "xanh_xe", None), ("XeSo_B2", "so_b", "trim", "vang", "nhan_do", None),
            ("XeHaiNguoi_A1", "hai_nguoi_a", "hong", "trim", "nhan_xanh", "tim"),
            ("XeHaiNguoi_A2", "hai_nguoi_a", "la_dam", "nhan_xanh", "trim", "vang"),
            ("XeHaiNguoi_B1", "hai_nguoi_b", "xanh_xe", "hong", "trim", None),
            ("XeHaiNguoi_B2", "hai_nguoi_b", "nhan_do", "tuong_mint", "vang", None),
            ("XeChoHang_1", "cho_hang", "xanh_xe", "xam", "trim", None), ("XeChoHang_2", "cho_hang", "nhan_do", "nhan_xanh", "vang", None),
            ("XeShipperKhac_1", "shipper_khac", "trim", "la_dam", "la1", None),
            ("XeShipperKhac_2", "shipper_khac", "vien", "nhan_do", "do_dam", None),
            ("XeTayGaLon_1", "tay_ga_lon", "trim", "vien", "vien", None), ("XeTayGaLon_2", "tay_ga_lon", "vien", "quan", "trim", None)):
        xe_dong(ten, mau, than, ao, mu, ao2)
    preview_xe_dong(os.path.join(HERE, "xem_truoc_xe_dong.png"))
if lam("cong_trinh2"):
    bao_tang(); truong_hoc(); benh_vien(); nha_san_vuon(); biet_thu_phap(); biet_thu_hien_dai(); tram_xe_buyt()
    preview_cong_trinh2(os.path.join(HERE, "xem_truoc_cong_trinh2.png"))
if lam("hem2"):
    nha_hem_tret(1); nha_hem_tret(2); nha_hem_co()
    for loai in ("tap_hoa", "sua_xe", "cat_toc", "com_tam", "ca_phe"):
        hem_tiem(loai)
    for loai in ("tap_hoa", "sua_xe", "com_tam"):  # tiệm chỉ có tầng trệt, mái tôn
        hem_tiem(loai, tang=1, mai="ton", hau_to="_Tret")
    hem_tiem("ca_phe", tang=2, mai="bang", W=6.0, hau_to="_MaiBang")     # có lầu, sân thượng không tum
    hem_tiem("cat_toc", tang=3, mai="bang", hau_to="_MaiBang")
    hem_tiem("com_tam", tang=2, mai="bang", W=8.0, hau_to="_Rong")      # quán rộng 2 lô
    for loai in ("nuoc_mia", "hu_tieu", "trai_cay"):
        xe_hang_rong(loai)
    nguoi("OngCu", "trim", "quan", "ong_cu", toc="xam_nhat")
    nguoi("NguoiBanVeSo", "nhan_xanh", "vien", "ve_so", phu="nhan_do")
    nguoi("NhanVienVanPhong", "tuong_xanh", "vien", "van_phong")
    nguoi("NuSinhAoDai", "trim", "trim", "ao_dai")
    nguoi("NguoiTapTheDuc", "la1", "vien", "the_duc")
    nguoi("TreEm", "vang", "nhan_xanh", "tre_em", k=0.62, phu="nhan_do")
    nguoi_ngoi_ghe("NguoiNgoiGhe_1", "trim", "quan")
    nguoi_ngoi_ghe("NguoiNgoiGhe_2", "hong", "vien", toc_dai=True, ghe="nhan_xanh")
    preview_nguoi2(os.path.join(HERE, "xem_truoc_nguoi2.png"))
    preview_hem2(os.path.join(HERE, "xem_truoc_hem2.png"))
    preview_hem2_tiem(os.path.join(HERE, "xem_truoc_hem2_tiem.png"))
if lam("duong"):
    duong_lon(); duong_lon("trai"); duong_lon("phai"); hem_duong()
    for tr in (True, False):
        duong_lon_cong(30, 60, tr); duong_lon_cong(90, 15, tr)
        hem_cong(45, 6, tr); hem_cong(90, 5, tr)
    preview_duong_cong(os.path.join(HERE, "xem_truoc_duong_cong.png"))
    dai_cay_le(); khuon_vien(20); khuon_vien(32)
    preview_duong(os.path.join(HERE, "xem_truoc_duong.png"))
if lam("hem"):
    preview_hem(os.path.join(HERE, "xem_truoc_hem.png"))
if lam("nga_re"):
    nga_re("trai"); nga_re("phai"); nga_re("tu")
    cuoi_nhanh(); cuoi_hem(); tiem_sua_xe_chu_bay()
    for ten, chu, mau in (("BienHopDen_Pho", "PHỞ", "do_dam"), ("BienHopDen_CaPhe", "CÀ PHÊ", "men_nau"),
                          ("BienHopDen_ComTam", "CƠM TẤM", "cam"), ("BienHopDen_GoiDau", "GỘI ĐẦU", "tim")):
        hop_den(ten, chu, mau)
    bang_chu_a("BienChuA_BanhMi", "BÁNH MÌ", "vang", "nhan_do")
    bang_chu_a("BienChuA_TraSua", "TRÀ SỮA", "trim", "hong")
    bien_dung("BienDung_SimThe", "SIM THẺ", "nhan_xanh")
    bien_dung("BienDung_Photo", "PHOTO", "la_dam")
    preview_nga_re(os.path.join(HERE, "xem_truoc_nga_re.png"))
    preview_bien_via_he(os.path.join(HERE, "xem_truoc_bien_via_he.png"))
    preview_chu_bay(os.path.join(HERE, "xem_truoc_chu_bay.png"))
