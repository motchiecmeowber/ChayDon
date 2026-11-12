"""Sinh greybox cho Chạy Đơn: đoạn đường 3 làn, đoạn hẻm, ổ gà, rào chắn, vũng nước.
Chạy: blender --background --python tao_greybox.py -- <thu_muc_xuat>
Đơn vị: 1 = 1 m. Trục: đường kéo dài theo -Y trong Blender, xuất FBX thành +Z trong Unity (cùng hướng đầu xe)."""
import bpy, sys, os, math

out = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else os.path.dirname(__file__)
os.makedirs(out, exist_ok=True)

PALETTE = {"duong": (0.56, 0.54, 0.52), "le": (0.85, 0.80, 0.72), "vach": (1, 1, 1),
           "hem": (0.62, 0.58, 0.54), "oga": (0.22, 0.21, 0.20), "rao_do": (0.95, 0.36, 0.33),
           "rao_trang": (1, 1, 1), "nuoc": (0.36, 0.65, 0.84)}


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    r, g, b = PALETTE[name]
    m.diffuse_color = (r, g, b, 1)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (r, g, b, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
    return m


def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat(material))
    return o


def disc(name, radius, depth, loc, material, verts=10, sx=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, 1, 1)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat(material))
    return o


def join(name, objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.name = name
    # Gốc tọa độ ở mép đầu đoạn, giữa đường, mặt đường; đoạn kéo dài về -Y
    return o


def export(name):
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, name + ".fbx"), use_selection=False,
                             apply_scale_options="FBX_SCALE_ALL", axis_forward="-Z", axis_up="Y",
                             bake_space_transform=True, object_types={"MESH"}, mesh_smooth_type="FACE")
    print("XUAT", name)


# 1. Đoạn đường lớn: 3 làn x 3,0 m, dài 100 m, vỉa hè 2 m mỗi bên
def duong_lon():
    clear()
    L, lane = 100.0, 3.0
    parts = [box("mat_duong", (3 * lane, L, 0.2), (0, -L / 2, -0.1), "duong")]
    for s in (-1, 1):
        parts.append(box("le", (2.0, L, 0.35), (s * (1.5 * lane + 1.0), -L / 2, 0.075), "le"))
    for x in (-lane / 2, lane / 2):
        for i in range(0, int(L), 6):
            parts.append(box("vach", (0.15, 3.0, 0.02), (x, -(i + 1.5), 0.01), "vach"))
    join("DuongLon_100m", parts)
    export("DuongLon_100m")


# 2. Đoạn hẻm: 2 làn x 1,75 m, dài 50 m, tường nhà hai bên
def hem():
    clear()
    L, w = 50.0, 3.5
    parts = [box("mat_hem", (w, L, 0.2), (0, -L / 2, -0.1), "hem")]
    for s in (-1, 1):
        parts.append(box("tuong", (0.6, L, 6.0), (s * (w / 2 + 0.3), -L / 2, 3.0), "le"))
    join("Hem_50m", parts)
    export("Hem_50m")


# 3. Vật cản
def vat_can():
    clear()
    disc("OGa", 0.45, 0.04, (0, 0, 0.005), "oga", verts=9, sx=1.3)
    export("OGa")
    clear()
    parts = [box("chan_trai", (0.12, 0.3, 0.9), (-1.2, 0, 0.45), "rao_trang"),
             box("chan_phai", (0.12, 0.3, 0.9), (1.2, 0, 0.45), "rao_trang")]
    for i, z in enumerate((0.55, 0.8)):
        parts.append(box("thanh", (2.6, 0.12, 0.18), (0, 0, z), "rao_do" if i == 0 else "rao_trang"))
    join("RaoChan", parts)
    export("RaoChan")
    clear()
    disc("VungNuoc", 1.0, 0.02, (0, 0, 0.005), "nuoc", verts=12, sx=1.4)
    export("VungNuoc")


# 4. Ảnh xem trước: ghép mọi thứ trong một cảnh
def preview(png):
    clear()
    for f in ("DuongLon_100m", "Hem_50m", "OGa", "RaoChan", "VungNuoc"):
        bpy.ops.import_scene.fbx(filepath=os.path.join(out, f + ".fbx"))
        o = bpy.context.selected_objects[0]
        o.location = {"DuongLon_100m": (0, 0, 0), "Hem_50m": (-12, -20, 0), "OGa": (3, -14, 0),
                      "RaoChan": (0, -22, 0), "VungNuoc": (-3, -30, 0)}[f]
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, 6, 4.5)
    cam.rotation_euler = (math.radians(72), 0, math.radians(180))
    bpy.context.scene.camera = cam
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = True
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.film_transparent = False
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.75, 0.89, 0.95)
    sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    print("ANH", png)


duong_lon()
hem()
vat_can()
preview(os.path.join(out, "xem_truoc.png"))
