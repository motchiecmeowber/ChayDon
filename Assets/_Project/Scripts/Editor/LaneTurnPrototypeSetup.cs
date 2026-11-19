using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;

// Builds the lane-based turning prototype: a small road network with two left T-junctions and a crossroads;
// every branch ends at a customer house. Straights get slow AI scooters and obstacles, including two-lane barriers.
public static class LaneTurnPrototypeSetup
{
    const string ScenePath = "Assets/Scenes/LaneTurnPrototype.unity";

    [MenuItem("Chạy Đơn/Build Lane Turn Prototype Scene")]
    static void Build()
    {
        if (EditorApplication.isPlaying)
        {
            Debug.LogWarning("Exit Play mode before building a scene.");
            return;
        }
        if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            return;
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var preset = AssetDatabase.LoadAssetAtPath<LightingPreset>("Assets/_Project/Data/Lighting/Lighting_QuietMorning.asset");

        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.shadows = LightShadows.Soft;
        var cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
        cam.tag = "MainCamera";
        cam.farClipPlane = 250f;
        var lighting = new GameObject("Lighting").AddComponent<LightingController>();
        lighting.sun = sun;
        lighting.targetCamera = cam;
        lighting.preset = preset;

        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.name = "Ground";
        ground.transform.SetPositionAndRotation(new Vector3(0f, -0.25f, 150f), Quaternion.identity);
        ground.transform.localScale = new Vector3(60f, 1f, 60f);
        var grass = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        grass.SetColor("_BaseColor", new Color32(0x6D, 0xBA, 0x45, 0xFF));
        ground.GetComponent<Renderer>().sharedMaterial = grass;
        Object.DestroyImmediate(ground.GetComponent<Collider>());
        AssetDatabase.CreateAsset(grass, "Assets/Scenes/LaneTurnPrototype_Ground.mat");

        // Route: straight → left T-junction.
        //   left:     straight → left T-junction → left: end, straight: end
        //   straight: straight → crossroads → left / straight / right: end
        Transform roads = new GameObject("Roads").transform;
        GameObject start = LightingSetup.Place("Duong/DuongLon_100m", Vector3.zero, Quaternion.identity, roads);
        GameObject j1 = Junction("Duong/DuongLon_NgaBaTrai", start, "DiemNoi", roads);
        GameObject a = LightingSetup.PlaceAt("Duong/DuongLon_100m", j1, "DiemNhanhTrai", roads);
        GameObject j2 = Junction("Duong/DuongLon_NgaBaTrai", a, "DiemNoi", roads);
        var leads = new List<GameObject> { End(j2, "DiemNhanhTrai", roads, false), End(j2, "DiemNoi", roads, false) };
        GameObject b = LightingSetup.PlaceAt("Duong/DuongLon_100m", j1, "DiemNoi", roads);
        GameObject j3 = Junction("Duong/DuongLon_NgaTu", b, "DiemNoi", roads);
        leads.Add(End(j3, "DiemNhanhTrai", roads, false));
        leads.Add(End(j3, "DiemNoi", roads, true));  // the order's address
        leads.Add(End(j3, "DiemNhanhPhai", roads, false));

        Transform traffic = new GameObject("Traffic").transform;
        var rng = new System.Random(7);
        // Traffic varies per straight so the route map shows free, busy (orange) and jammed (red) roads.
        Populate(start, 30f, true, 3, rng, traffic);
        Populate(a, 10f, true, 3, rng, traffic);
        Populate(b, 10f, true, 8, rng, traffic);
        int[] leadTraffic = { 3, 5, 3, 3, 8 };
        for (int i = 0; i < leads.Count; i++)
            Populate(leads[i], 10f, false, leadTraffic[i % leadTraffic.Length], rng, traffic);

        var runner = new GameObject("Player").AddComponent<LaneTurnRunner>();
        runner.transform.position = new Vector3(0f, 0f, 5f);
        runner.model = LightingSetup.Place("XeShipper/XeShipper", runner.transform.position, Quaternion.identity, runner.transform).transform;
        runner.cameraAnchor = new GameObject("CameraAnchor").transform;
        runner.cameraAnchor.position = runner.transform.position;
        var chase = cam.gameObject.AddComponent<ChaseCamera>();
        chase.target = runner.cameraAnchor;

        // HUD (if built) and the event system it needs for touches
        var hudPrefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/_Project/Prefabs/UI/Hud.prefab");
        if (hudPrefab != null)
            PrefabUtility.InstantiatePrefab(hudPrefab);
        new GameObject("EventSystem", typeof(EventSystem), typeof(InputSystemUIInputModule));
        var routeMap = new GameObject("RouteMap").AddComponent<PrototypeRouteMap>();
        routeMap.runner = runner;
        routeMap.roads = roads;

        lighting.Apply();
        EditorSceneManager.SaveScene(scene, ScenePath);
        Debug.Log($"[LaneTurnPrototypeSetup] Built {ScenePath}. Press Play; swipe or use A/D / arrow keys.");
    }

    static GameObject Junction(string prefab, GameObject previous, string point, Transform parent)
    {
        GameObject j = LightingSetup.PlaceAt(prefab, previous, point, parent);
        if (j != null)
            j.AddComponent<TurnJunction>();
        return j;
    }

    // Branch end: a short straight, then the dead end with the customer house and flag. Returns the straight.
    static GameObject End(GameObject junction, string point, Transform parent, bool destination)
    {
        GameObject lead = LightingSetup.PlaceAt("Duong/DuongLon_100m", junction, point, parent);
        GameObject end = LightingSetup.PlaceAt("Duong/DuongLon_CuoiNhanh_30m", lead, "DiemNoi", parent);
        if (end == null)
            return lead;
        end.AddComponent<RouteEnd>().isDestination = destination;
        LightingSetup.PlaceAt("Pho/NhaOng_4", end, "DiemNhaKhach", parent);
        LightingSetup.PlaceAt("DiaDiem/CoDich", end, "DiemCoDich", parent);
        return lead;
    }

    static readonly string[] Vehicles = { "XeAI/XeSo_A1", "XeAI/XeMayAI_1", "XeAI/XeHaiNguoi_A1", "XeAI/XeChoHang_1",
                                          "XeAI/XeDap_1", "XeAI/XeMayAI_2", "XeAI/XeTayGaLon_1" };
    // Flat obstacles can be driven over by AI scooters; tall ones block a lane, so they stay out of the traffic lane.
    static readonly string[] FlatObstacles = { "VatCan/OGa_1", "VatCan/OGa_Cum", "VatCan/VungNuoc_Nho", "VatCan/OGa_2", "VatCan/VungNuoc_Lon" };
    static readonly string[] TallObstacles = { "VatCan/RaoChan_SocDo", "VatCan/NonGiaoThong", "VatCan/LoCot_1Lan" };
    const float TwoLaneFreeWindow = 45f;  // no two-lane obstacle within this distance before the commit line

    // One 100 m straight: a row every ~15 m blocks one or two lanes, never all three. Sometimes the row is a two-lane
    // roadworks barrier (LoCot_2Lan, centered between two lanes). AI scooters keep to one traffic lane.
    // If the straight feeds a junction (commit line at z = 95): no two-lane barrier in the last 45 m before it, so the
    // player can always reach a turn lane; one single-lane obstacle sits in an edge lane past the commit line (z = 105).
    static void Populate(GameObject segment, float from, bool feedsJunction, int vehicles, System.Random rng, Transform parent)
    {
        if (segment == null)
            return;
        Transform s = segment.transform;
        float[] lanes = { -3f, 0f, 3f };
        int trafficLane = rng.Next(3);
        float until = feedsJunction ? 72f : 85f;
        float twoLaneUntil = feedsJunction ? 95f - TwoLaneFreeWindow : until;
        for (float z = from; z < until; z += 14f + (float)rng.NextDouble() * 6f)
        {
            if (trafficLane != 1 && z < twoLaneUntil && rng.NextDouble() < 0.3)
            {
                float center = trafficLane == 0 ? 1.5f : -1.5f;  // covers the two lanes away from the traffic lane
                LightingSetup.Place("VatCan/LoCot_2Lan", s.TransformPoint(new Vector3(center, 0f, z)), s.rotation, parent);
                continue;
            }
            int free = rng.Next(3);
            for (int i = 0; i < 3; i++)
            {
                if (i == free || rng.NextDouble() >= 0.55)
                    continue;
                string[] pool = i == trafficLane ? FlatObstacles : rng.NextDouble() < 0.5 ? TallObstacles : FlatObstacles;
                LightingSetup.Place(pool[rng.Next(pool.Length)], s.TransformPoint(new Vector3(lanes[i], 0f, z)), s.rotation, parent);
            }
        }
        if (feedsJunction)
            LightingSetup.Place(FlatObstacles[rng.Next(FlatObstacles.Length)], s.TransformPoint(new Vector3(rng.Next(2) == 0 ? -3f : 3f, 0f, 105f)), s.rotation, parent);
        float gap = (85f - from) / vehicles;
        for (int k = 0; k < vehicles; k++)
        {
            GameObject v = LightingSetup.Place(Vehicles[rng.Next(Vehicles.Length)],
                s.TransformPoint(new Vector3(lanes[trafficLane], 0f, from + 5f + k * gap)), s.rotation, parent);
            if (v == null)
                continue;
            var t = v.AddComponent<PrototypeTraffic>();
            t.lane = trafficLane - 1;
            t.speed = 5.5f + (float)rng.NextDouble() * 3f;
            t.segmentLength = 95f - (from + 5f + k * gap);
        }
    }
}
