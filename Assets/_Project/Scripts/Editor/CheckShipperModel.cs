using UnityEditor;
using UnityEngine;

// Checks that XeShipper faces +Z (found via headlight/taillight UVs) and uses the palette texture.
public static class CheckShipperModel
{
    const string ModelPath = "Assets/_Project/Art/Models/XeShipper/XeShipper.fbx";
    static readonly Vector2 HeadlightUv = new Vector2(0.4375f, 0.5625f);
    static readonly Vector2 TaillightUv = new Vector2(0.5625f, 0.5625f);

    [MenuItem("Chạy Đơn/Check XeShipper Orientation and Colors")]
    static void Check()
    {
        GameObject root = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        MeshFilter mf = root.GetComponentInChildren<MeshFilter>();
        Mesh mesh = mf.sharedMesh;
        Vector3[] vertices = mesh.vertices;
        Vector2[] uv = mesh.uv;

        float frontSum = 0f, backSum = 0f;
        int frontCount = 0, backCount = 0;
        for (int i = 0; i < vertices.Length; i++)
        {
            Vector3 p = root.transform.InverseTransformPoint(mf.transform.TransformPoint(vertices[i]));
            if ((uv[i] - HeadlightUv).sqrMagnitude < 1e-4f) { frontSum += p.z; frontCount++; }
            else if ((uv[i] - TaillightUv).sqrMagnitude < 1e-4f) { backSum += p.z; backCount++; }
        }
        float frontZ = frontCount > 0 ? frontSum / frontCount : float.NaN;
        float backZ = backCount > 0 ? backSum / backCount : float.NaN;
        string facing = frontZ > backZ ? "+Z (correct)" : "-Z (reversed, rotate 180°)";

        Material material = root.GetComponentInChildren<MeshRenderer>().sharedMaterial;
        string texture = material.mainTexture != null ? material.mainTexture.name : "NONE";
        Bounds b = mesh.bounds;
        Debug.Log($"[CheckShipperModel] headlight z={frontZ:F2}, taillight z={backZ:F2} → front faces {facing}; " +
                  $"shader={material.shader.name}, palette={texture}; size={b.size.x:F2} x {b.size.y:F2} x {b.size.z:F2} m");
    }
}
