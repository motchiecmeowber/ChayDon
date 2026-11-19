using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

// Builds one prefab per model in Art/Models, with the FBX nested so model updates carry over.
// Root colliders and Rigidbody are regenerated on every run; don't add them by hand.
public static class PrefabBuilder
{
    const string ModelsFolder = "Assets/_Project/Art/Models";
    const string PrefabsFolder = "Assets/_Project/Prefabs";
    const string MaterialsFolder = "Assets/_Project/Art/Materials";
    const string BlenderMaterialName = "BangMau_LowPoly";  // material name in the FBX

    enum ColliderKind { None, Obstacle, Vehicle, Pedestrian }

    // Obstacles: trigger. Vehicles: trigger + kinematic Rigidbody. Pedestrians: capsule trigger. Others: none.
    static ColliderKind KindFor(string folder, string modelName)
    {
        switch (folder)
        {
            case "VatCan": return ColliderKind.Obstacle;
            case "XeAI": return ColliderKind.Vehicle;
            case "Nguoi": return modelName.StartsWith("NguoiNgoiGhe") ? ColliderKind.None : ColliderKind.Pedestrian;
            case "XeShipper": return modelName == "XeShipper" ? ColliderKind.Vehicle : ColliderKind.None;
            default: return ColliderKind.None;
        }
    }

    [MenuItem("Chạy Đơn/Build Prefabs From Models")]
    static void BuildAll()
    {
        Material palette = CreatePaletteMaterial("M_Palette_LowPoly", "Assets/_Project/Art/Textures/BangMau_LowPoly.png");
        CreatePaletteMaterial("M_Palette_District3", "Assets/_Project/Art/Textures/BangMau_Quan3.png");

        var models = new List<string>();
        foreach (string guid in AssetDatabase.FindAssets("t:Model", new[] { ModelsFolder }))
            models.Add(AssetDatabase.GUIDToAssetPath(guid));

        int reimported = 0;
        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (string path in models)
                if (ConfigureImport(path, palette))
                    reimported++;
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }

        int created = 0, updated = 0;
        try
        {
            for (int i = 0; i < models.Count; i++)
            {
                EditorUtility.DisplayProgressBar("Building prefabs", models[i], (float)i / models.Count);
                if (BuildOne(models[i]))
                    created++;
                else
                    updated++;
            }
        }
        finally
        {
            EditorUtility.ClearProgressBar();
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"[PrefabBuilder] {models.Count} models: {created} prefabs created, {updated} updated; " +
                  $"{reimported} models had their material remap or import settings changed.");
    }

    // Shared URP/Lit palette material, no reflections or specular.
    static Material CreatePaletteMaterial(string materialName, string texturePath)
    {
        ConfigurePaletteTexture(texturePath);
        string path = $"{MaterialsFolder}/{materialName}.mat";
        Material m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null)
        {
            EnsureFolder(MaterialsFolder);
            m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            AssetDatabase.CreateAsset(m, path);
        }
        m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath));
        m.SetColor("_BaseColor", Color.white);
        m.SetFloat("_Metallic", 0f);
        m.SetFloat("_Smoothness", 0.1f);
        m.SetFloat("_SpecularHighlights", 0f);
        m.EnableKeyword("_SPECULARHIGHLIGHTS_OFF");
        m.SetFloat("_EnvironmentReflections", 0f);
        m.EnableKeyword("_ENVIRONMENTREFLECTIONS_OFF");
        EditorUtility.SetDirty(m);
        return m;
    }

    // Point filter, no mipmaps, no compression so palette cells don't bleed.
    static void ConfigurePaletteTexture(string texturePath)
    {
        var ti = AssetImporter.GetAtPath(texturePath) as TextureImporter;
        if (ti == null)
            return;
        if (ti.filterMode == FilterMode.Point && !ti.mipmapEnabled &&
            ti.textureCompression == TextureImporterCompression.Uncompressed)
            return;
        ti.filterMode = FilterMode.Point;
        ti.mipmapEnabled = false;
        ti.textureCompression = TextureImporterCompression.Uncompressed;
        ti.SaveAndReimport();
    }

    static bool ConfigureImport(string path, Material palette)
    {
        var importer = AssetImporter.GetAtPath(path) as ModelImporter;
        if (importer == null)
            return false;
        bool changed = false;
        var id = new AssetImporter.SourceAssetIdentifier(typeof(Material), BlenderMaterialName);
        if (!importer.GetExternalObjectMap().TryGetValue(id, out Object current) || current != palette)
        {
            importer.AddRemap(id, palette);
            changed = true;
        }
        if (importer.importCameras || importer.importLights || importer.importAnimation)
        {
            importer.importCameras = false;
            importer.importLights = false;
            importer.importAnimation = false;
            changed = true;
        }
        if (changed)
            importer.SaveAndReimport();
        return changed;
    }

    // Returns true if created, false if updated.
    static bool BuildOne(string modelPath)
    {
        GameObject model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
        string folder = Path.GetFileName(Path.GetDirectoryName(modelPath));
        string modelName = model.name;
        string outFolder = $"{PrefabsFolder}/{folder}";
        EnsureFolder(outFolder);
        string prefabPath = $"{outFolder}/{modelName}.prefab";
        bool exists = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath) != null;

        GameObject root = exists ? PrefabUtility.LoadPrefabContents(prefabPath) : new GameObject(modelName);
        try
        {
            Transform child = root.transform.Find(modelName);
            if (child == null || PrefabUtility.GetCorrespondingObjectFromSource(child.gameObject) != model)
            {
                if (child != null)
                    Object.DestroyImmediate(child.gameObject);
                var instance = (GameObject)PrefabUtility.InstantiatePrefab(model);
                instance.name = modelName;
                instance.transform.SetParent(root.transform, false);
                child = instance.transform;
            }

            var points = new List<Transform>();
            foreach (Transform t in child.GetComponentsInChildren<Transform>(true))
                if (t != child && t.name.StartsWith("Diem"))
                    points.Add(t);
            var attach = root.GetComponent<AttachPoints>();
            if (points.Count > 0)
            {
                if (attach == null)
                    attach = root.AddComponent<AttachPoints>();
                attach.SetPoints(points.ToArray());
            }
            else if (attach != null)
                Object.DestroyImmediate(attach);

            foreach (Collider c in root.GetComponents<Collider>())
                Object.DestroyImmediate(c);
            var body = root.GetComponent<Rigidbody>();
            if (body != null)
                Object.DestroyImmediate(body);
            Bounds bounds = ComputeBounds(root.transform, child);
            AddColliders(root, bounds, KindFor(folder, modelName));
            UpdateFrontage(root, child, bounds, IsStreetBuilding(folder, modelName));

            PrefabUtility.SaveAsPrefabAsset(root, prefabPath);
        }
        finally
        {
            if (exists)
                PrefabUtility.UnloadPrefabContents(root);
            else
                Object.DestroyImmediate(root);
        }
        return !exists;
    }

    // Buildings that line the street; sidewalk props (trees, poles, signs) are excluded.
    static bool IsStreetBuilding(string folder, string modelName)
    {
        if (folder != "Pho" && folder != "DiaDiem")
            return false;
        return !(modelName.StartsWith("Cay") || modelName.StartsWith("Bien") || modelName.StartsWith("Cot") ||
                 modelName == "CoDich");
    }

    static void UpdateFrontage(GameObject root, Transform model, Bounds bounds, bool isBuilding)
    {
        var frontage = root.GetComponent<StreetFrontage>();
        if (!isBuilding)
        {
            if (frontage != null)
                Object.DestroyImmediate(frontage);
            return;
        }
        if (frontage == null)
            frontage = root.AddComponent<StreetFrontage>();
        frontage.width = bounds.size.x;
        frontage.groundDepth = GroundDepth(root.transform, model);
    }

    // Furthest point in front of the facade (z > 0) between 0.3 m and 3 m above ground.
    static float GroundDepth(Transform root, Transform model)
    {
        float depth = 0f;
        foreach (MeshFilter mf in model.GetComponentsInChildren<MeshFilter>(true))
        {
            if (mf.sharedMesh == null)
                continue;
            Matrix4x4 toRoot = root.worldToLocalMatrix * mf.transform.localToWorldMatrix;
            foreach (Vector3 v in mf.sharedMesh.vertices)
            {
                Vector3 p = toRoot.MultiplyPoint3x4(v);
                if (p.y > 0.3f && p.y < 3f && p.z > depth)
                    depth = p.z;
            }
        }
        return depth;
    }

    static void AddColliders(GameObject root, Bounds bounds, ColliderKind kind)
    {
        switch (kind)
        {
            case ColliderKind.Obstacle:
            {
                var box = root.AddComponent<BoxCollider>();
                box.isTrigger = true;
                Vector3 center = bounds.center, size = bounds.size;
                if (size.y < 0.5f)  // flat obstacles get a 0.5 m tall trigger
                {
                    size.y = 0.5f;
                    center.y = 0.25f;
                }
                box.center = center;
                box.size = size;
                break;
            }
            case ColliderKind.Vehicle:
            {
                var box = root.AddComponent<BoxCollider>();
                box.isTrigger = true;
                box.center = bounds.center;
                box.size = bounds.size;
                var body = root.AddComponent<Rigidbody>();
                body.isKinematic = true;
                body.useGravity = false;
                break;
            }
            case ColliderKind.Pedestrian:
            {
                var capsule = root.AddComponent<CapsuleCollider>();
                capsule.isTrigger = true;
                capsule.direction = 1;
                capsule.center = bounds.center;
                capsule.height = bounds.size.y;
                capsule.radius = Mathf.Clamp(Mathf.Max(bounds.size.x, bounds.size.z) * 0.5f, 0.15f, 0.5f);
                break;
            }
        }
    }

    // Mesh bounds in root space.
    static Bounds ComputeBounds(Transform root, Transform model)
    {
        bool hasPoint = false;
        Bounds b = default;
        foreach (MeshFilter mf in model.GetComponentsInChildren<MeshFilter>(true))
        {
            if (mf.sharedMesh == null)
                continue;
            Bounds m = mf.sharedMesh.bounds;
            Matrix4x4 toRoot = root.worldToLocalMatrix * mf.transform.localToWorldMatrix;
            for (int i = 0; i < 8; i++)
            {
                var corner = new Vector3((i & 1) == 0 ? -1 : 1, (i & 2) == 0 ? -1 : 1, (i & 4) == 0 ? -1 : 1);
                Vector3 p = toRoot.MultiplyPoint3x4(m.center + Vector3.Scale(m.extents, corner));
                if (!hasPoint)
                {
                    b = new Bounds(p, Vector3.zero);
                    hasPoint = true;
                }
                else
                    b.Encapsulate(p);
            }
        }
        return b;
    }

    public static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path))
            return;
        string parent = Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }
}
