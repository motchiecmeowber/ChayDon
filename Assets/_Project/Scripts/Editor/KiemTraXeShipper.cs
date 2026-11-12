using UnityEditor;
using UnityEngine;

// Kiểm tra model XeShipper sau khi import: đầu xe có hướng +Z không, vật liệu có nhận ảnh bảng màu không.
// Đèn trước và đèn sau dùng hai ô màu riêng trong BangMau_LowPoly, nên tìm theo UV là biết vị trí của chúng.
public static class KiemTraXeShipper
{
    const string DuongDan = "Assets/_Project/Art/Models/XeShipper/XeShipper.fbx";
    static readonly Vector2 UvDenTruoc = new Vector2(0.4375f, 0.5625f);
    static readonly Vector2 UvDenSau = new Vector2(0.5625f, 0.5625f);

    [MenuItem("Chạy Đơn/Kiểm tra hướng và màu XeShipper")]
    static void KiemTra()
    {
        GameObject goc = AssetDatabase.LoadAssetAtPath<GameObject>(DuongDan);
        MeshFilter mf = goc.GetComponentInChildren<MeshFilter>();
        Mesh mesh = mf.sharedMesh;
        Vector3[] dinh = mesh.vertices;
        Vector2[] uv = mesh.uv;

        float tongTruoc = 0f, tongSau = 0f;
        int soTruoc = 0, soSau = 0;
        for (int i = 0; i < dinh.Length; i++)
        {
            Vector3 p = goc.transform.InverseTransformPoint(mf.transform.TransformPoint(dinh[i]));
            if ((uv[i] - UvDenTruoc).sqrMagnitude < 1e-4f) { tongTruoc += p.z; soTruoc++; }
            else if ((uv[i] - UvDenSau).sqrMagnitude < 1e-4f) { tongSau += p.z; soSau++; }
        }
        float zTruoc = soTruoc > 0 ? tongTruoc / soTruoc : float.NaN;
        float zSau = soSau > 0 ? tongSau / soSau : float.NaN;
        string huong = zTruoc > zSau ? "+Z (đúng)" : "-Z (ngược, cần xoay 180°)";

        Material vl = goc.GetComponentInChildren<MeshRenderer>().sharedMaterial;
        string anh = vl.mainTexture != null ? vl.mainTexture.name : "KHÔNG CÓ";
        Bounds b = mesh.bounds;
        Debug.Log($"[KiemTraXeShipper] đèn trước z={zTruoc:F2}, đèn sau z={zSau:F2} → đầu xe hướng {huong}; " +
                  $"shader={vl.shader.name}, ảnh màu={anh}; kích thước={b.size.x:F2} x {b.size.y:F2} x {b.size.z:F2} m");
    }
}
