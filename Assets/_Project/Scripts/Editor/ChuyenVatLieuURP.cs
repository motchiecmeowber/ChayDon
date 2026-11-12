using UnityEditor;
using UnityEngine;

// Gói Low Poly Cars (Broken Vector) dùng shader Built-in nên bị hồng trong URP.
// Công cụ này đổi mọi vật liệu của gói sang URP/Lit (hoặc URP/Unlit), giữ nguyên ảnh bảng màu và màu tint.
public static class ChuyenVatLieuURP
{
    const string ThuMuc = "Assets/BrokenVector";

    [MenuItem("Chạy Đơn/Chuyển vật liệu Low Poly Cars sang URP")]
    static void ChuyenDoi()
    {
        Shader lit = Shader.Find("Universal Render Pipeline/Lit");
        Shader unlit = Shader.Find("Universal Render Pipeline/Unlit");
        int dem = 0;
        foreach (string guid in AssetDatabase.FindAssets("t:Material", new[] { ThuMuc }))
        {
            Material m = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
            if (m == null || m.shader.name.StartsWith("Universal Render Pipeline"))
                continue;

            Texture bangMau = m.HasProperty("_MainTex") ? m.GetTexture("_MainTex") : null;
            Color mau = m.HasProperty("_Color") ? m.GetColor("_Color") : Color.white;
            float doMin = m.HasProperty("_Glossiness") ? m.GetFloat("_Glossiness") : 0.5f;
            float kimLoai = m.HasProperty("_Metallic") ? m.GetFloat("_Metallic") : 0f;
            bool khongChieuSang = m.shader.name.Contains("Unlit");

            Undo.RecordObject(m, "Chuyển vật liệu sang URP");
            m.shader = khongChieuSang ? unlit : lit;
            m.SetTexture("_BaseMap", bangMau);
            m.SetColor("_BaseColor", mau);
            if (!khongChieuSang)
            {
                m.SetFloat("_Smoothness", doMin);
                m.SetFloat("_Metallic", kimLoai);
            }
            EditorUtility.SetDirty(m);
            dem++;
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"Đã chuyển {dem} vật liệu trong {ThuMuc} sang URP.");
    }
}
