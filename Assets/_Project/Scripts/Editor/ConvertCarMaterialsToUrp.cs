using UnityEditor;
using UnityEngine;

// Converts Low Poly Cars materials (Built-in, pink under URP) to URP Lit/Unlit.
public static class ConvertCarMaterialsToUrp
{
    const string PackFolder = "Assets/BrokenVector";

    [MenuItem("Chạy Đơn/Convert Low Poly Cars Materials to URP")]
    static void Convert()
    {
        Shader lit = Shader.Find("Universal Render Pipeline/Lit");
        Shader unlit = Shader.Find("Universal Render Pipeline/Unlit");
        int count = 0;
        foreach (string guid in AssetDatabase.FindAssets("t:Material", new[] { PackFolder }))
        {
            Material m = AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(guid));
            if (m == null || m.shader.name.StartsWith("Universal Render Pipeline"))
                continue;

            Texture palette = m.HasProperty("_MainTex") ? m.GetTexture("_MainTex") : null;
            Color tint = m.HasProperty("_Color") ? m.GetColor("_Color") : Color.white;
            float smoothness = m.HasProperty("_Glossiness") ? m.GetFloat("_Glossiness") : 0.5f;
            float metallic = m.HasProperty("_Metallic") ? m.GetFloat("_Metallic") : 0f;
            bool isUnlit = m.shader.name.Contains("Unlit");

            Undo.RecordObject(m, "Convert material to URP");
            m.shader = isUnlit ? unlit : lit;
            m.SetTexture("_BaseMap", palette);
            m.SetColor("_BaseColor", tint);
            if (!isUnlit)
            {
                m.SetFloat("_Smoothness", smoothness);
                m.SetFloat("_Metallic", metallic);
            }
            EditorUtility.SetDirty(m);
            count++;
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"Converted {count} materials in {PackFolder} to URP.");
    }
}
