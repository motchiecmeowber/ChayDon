using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Creates the MVP lighting presets (never overwrites existing ones) and builds a test scene.
public static class LightingSetup
{
    const string PresetsFolder = "Assets/_Project/Data/Lighting";
    const string TestScenePath = "Assets/Scenes/LightingTest.unity";
    const string Prefabs = "Assets/_Project/Prefabs";

    static Color Hex(string h) => ColorUtility.TryParseHtmlString("#" + h, out Color c) ? c : Color.magenta;

    [MenuItem("Chạy Đơn/Create Lighting Presets")]
    static void CreatePresets()
    {
        PrefabBuilder.EnsureFolder(PresetsFolder);
        // Quiet morning: soft yellow sun, light blue sky, far fog.
        CreatePreset("Lighting_QuietMorning", p =>
        {
            p.skyColor = Hex("BFE3F2");
            p.sunColor = Hex("FFE7A8");
            p.sunIntensity = 1.3f;
            p.sunRotation = new Vector3(50f, -30f, 0f);
            p.shadowStrength = 0.75f;
            p.ambientSky = Hex("BFE3F2");
            p.ambientEquator = Hex("F2D7B6");
            p.ambientGround = Hex("8E8A85");
            p.fogColor = Hex("BFE3F2");
            p.fogStart = 70f;
            p.fogEnd = 180f;
        });
        // Rush hour: low orange sun, long shadows, nearer fog.
        CreatePreset("Lighting_RushHour", p =>
        {
            p.skyColor = Hex("F4A261");
            p.sunColor = Hex("FFB36B");
            p.sunIntensity = 1.1f;
            p.sunRotation = new Vector3(18f, -60f, 0f);
            p.shadowStrength = 0.65f;
            p.ambientSky = Hex("F4B183");
            p.ambientEquator = Hex("D9A27E");
            p.ambientGround = Hex("6F5E58");
            p.fogColor = Hex("F2B27E");
            p.fogStart = 45f;
            p.fogEnd = 150f;
        });
        AssetDatabase.SaveAssets();
    }

    static LightingPreset CreatePreset(string presetName, System.Action<LightingPreset> setValues)
    {
        string path = $"{PresetsFolder}/{presetName}.asset";
        var p = AssetDatabase.LoadAssetAtPath<LightingPreset>(path);
        if (p != null)
            return p;
        p = ScriptableObject.CreateInstance<LightingPreset>();
        setValues(p);
        AssetDatabase.CreateAsset(p, path);
        Debug.Log($"[LightingSetup] Created preset {path}");
        return p;
    }

    [MenuItem("Chạy Đơn/Build Lighting Test Scene")]
    static void BuildTestScene()
    {
        if (EditorApplication.isPlaying)
        {
            Debug.LogWarning("Exit Play mode before building a scene.");
            return;
        }
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            return;
        CreatePresets();
        if (AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/Duong/DuongLon_100m.prefab") == null)
        {
            Debug.LogError("[LightingSetup] No prefabs yet. Run Chạy Đơn → Build Prefabs From Models first.");
            return;
        }

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        // Load after NewScene: opening a scene unloads assets loaded before it.
        var morning = AssetDatabase.LoadAssetAtPath<LightingPreset>($"{PresetsFolder}/Lighting_QuietMorning.asset");

        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.shadows = LightShadows.Soft;

        var cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
        cam.tag = "MainCamera";
        cam.farClipPlane = 250f;
        var chase = cam.gameObject.AddComponent<ChaseCamera>();

        var lighting = new GameObject("Lighting").AddComponent<LightingController>();
        lighting.sun = sun;
        lighting.targetCamera = cam;
        lighting.preset = morning;

        // Route: 2 straights → left T-junction (+ branch) → branch end with customer house.
        Transform roads = new GameObject("Roads").transform;
        GameObject first = Place("Duong/DuongLon_100m", Vector3.zero, Quaternion.identity, roads);
        GameObject second = PlaceAt("Duong/DuongLon_100m", first, "DiemNoi", roads);
        GameObject junction = PlaceAt("Duong/DuongLon_NgaBaTrai", second, "DiemNoi", roads);
        PlaceAt("Duong/DuongLon_100m", junction, "DiemNhanhTrai", roads);
        GameObject branchEnd = PlaceAt("Duong/DuongLon_CuoiNhanh_30m", junction, "DiemNoi", roads);
        PlaceAt("Pho/NhaOng_4", branchEnd, "DiemNhaKhach", roads);
        PlaceAt("DiaDiem/CoDich", branchEnd, "DiemCoDich", roads);

        // Houses on both sides of the first 200 m, turned to face the road, each with a sidewalk prop in front.
        Transform houses = new GameObject("Houses").transform;
        Transform props = new GameObject("Props").transform;
        string[] row = { "Pho/NhaOng_1", "Pho/NhaOng_2", "Pho/NhaOng_3", "Pho/NhaOng_8", "Pho/NhaTret_1", "Pho/NhaOng_5",
                         "DiaDiem/TramKyUc", "Pho/NhaOng_7", "Pho/NhaO_1", "Pho/NhaOng_6", "DiaDiem/TiemSuaXeChuBay",
                         "Pho/NhaGara_1", "Pho/NhaOng_4", "DiaDiem/QuanNuocNgon", "Pho/NhaOng_2", "Pho/NhaTret_2" };
        PlaceRow(row, 1f, 0, houses, props);
        PlaceRow(row, -1f, 7, houses, props);

        // Traffic, obstacles, player.
        string[] traffic = { "XeAI/XeSo_A1", "XeAI/XeMayAI_1", "XeAI/XeHaiNguoi_A1", "XeAI/XeTayGaLon_1", "XeAI/XeChoHang_1",
                             "XeAI/XeDap_1", "XeAI/XeMayAI_2", "XeAI/XeShipperKhac_1", "XeAI/XeSo_B2" };
        float[] lanes = { -3f, 0f, 3f };
        for (int i = 0; i < traffic.Length; i++)
            Place(traffic[i], new Vector3(lanes[(i * 2) % 3], 0f, 32f + i * 15f), Quaternion.identity, props);
        Place("VatCan/OGa_1", new Vector3(3f, 0f, 70f), Quaternion.identity, props);
        Place("VatCan/VungNuoc_Lon", new Vector3(-3f, 0f, 110f), Quaternion.identity, props);
        Place("VatCan/LoCot_1Lan", new Vector3(3f, 0f, 150f), Quaternion.identity, props);
        chase.target = Place("XeShipper/XeShipper", new Vector3(0f, 0f, 18f), Quaternion.identity, props).transform;

        lighting.Apply();
        EditorSceneManager.SaveScene(scene, TestScenePath);
        Debug.Log($"[LightingSetup] Built {TestScenePath}. To switch time of day, select Lighting and drag another preset into Preset.");
    }

    internal static GameObject Place(string prefab, Vector3 position, Quaternion rotation, Transform parent)
    {
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/{prefab}.prefab");
        if (asset == null)
        {
            Debug.LogWarning($"[LightingSetup] Prefab not found: {prefab}");
            return null;
        }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, parent);
        go.transform.SetPositionAndRotation(position, rotation);
        return go;
    }

    // Places a prefab at another object's attach point.
    internal static GameObject PlaceAt(string prefab, GameObject previous, string pointName, Transform parent)
    {
        AttachPoints attach = previous != null ? previous.GetComponent<AttachPoints>() : null;
        Transform point = attach != null ? attach.Get(pointName) : null;
        if (point == null)
        {
            Debug.LogWarning($"[LightingSetup] Attach point not found: {pointName}");
            return null;
        }
        return Place(prefab, point.position, point.rotation, parent);
    }

    static readonly string[] TallProps = { "Pho/CayXanh_1", "Pho/CayMe", "Pho/CotDien", "Pho/CayXanh_2", "Pho/BienDung_SimThe",
                                           "Pho/CaySao_Cao", "Pho/BienDung_Photo" };
    static readonly string[] ShortProps = { "Pho/BienHopDen_Pho", "Pho/BienChuA_BanhMi", "Pho/BienHopDen_CaPhe",
                                            "Pho/BienChuA_TraSua", "Pho/BienHopDen_ComTam", "Pho/BienHopDen_GoiDau" };

    // side = 1: right of the driver (+X), -1: left. Tall props only go in front of houses without awnings (StreetFrontage).
    static void PlaceRow(string[] list, float side, int start, Transform houseParent, Transform propParent)
    {
        const float facadeX = 6.5f, propDepth = 1.4f;
        Quaternion houseRot = Quaternion.Euler(0f, side > 0 ? -90f : 90f, 0f);
        Quaternion propRot = Quaternion.Euler(0f, side > 0 ? 0f : 180f, 0f);  // tree canopies lean to local -X, over the road
        float z = 0f;
        int tall = start, small = start;
        for (int i = 0; z < 196f; i++)
        {
            string prefab = list[(start + i) % list.Length];
            float width = FrontageWidth(prefab);
            if (z + width > 200f)
                break;
            GameObject house = Place(prefab, new Vector3(side * facadeX, 0.25f, z + width / 2f), houseRot, houseParent);
            var frontage = house != null ? house.GetComponent<StreetFrontage>() : null;
            Vector3 propPos = new Vector3(side * (facadeX - propDepth), 0.25f, z + width / 2f);
            if (frontage == null || frontage.AllowsTallProps)
                Place(TallProps[tall++ % TallProps.Length], propPos, propRot, propParent);
            else if (i % 2 == 0)
                Place(ShortProps[small++ % ShortProps.Length], propPos, propRot, propParent);
            z += width;
        }
    }

    static readonly Dictionary<string, float> widthCache = new Dictionary<string, float>();

    // Frontage width rounded to 0.5 m (from StreetFrontage, else from the mesh bounds); bevels make meshes ~0.1 m wider.
    static float FrontageWidth(string prefab)
    {
        if (widthCache.TryGetValue(prefab, out float w))
            return w;
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>($"{Prefabs}/{prefab}.prefab");
        w = 4f;
        if (asset != null)
        {
            var frontage = asset.GetComponent<StreetFrontage>();
            float widest = frontage != null ? frontage.width : 0f;
            if (widest <= 0f)
                foreach (MeshFilter mf in asset.GetComponentsInChildren<MeshFilter>())
                    if (mf.sharedMesh != null)
                        widest = Mathf.Max(widest, mf.sharedMesh.bounds.size.x);
            if (widest > 0f)
                w = Mathf.Round(widest * 2f) / 2f;
        }
        widthCache[prefab] = w;
        return w;
    }
}
