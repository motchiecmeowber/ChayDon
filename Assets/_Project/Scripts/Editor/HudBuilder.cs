using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore.LowLevel;
using UnityEngine.UI;

// Builds the in-run HUD prefab (Prefabs/UI/Hud.prefab) from the generated UI sprites and the Baloo 2 font.
// Layout units are dp: the canvas reference size is 360 x 780 and scales by screen width.
public static class HudBuilder
{
    const string SpritesFolder = "Assets/_Project/Art/UI/Sprites";
    const string FontPath = "Assets/_Project/Art/Fonts/Baloo2-Variable.ttf";
    const string FontAssetPath = "Assets/_Project/Art/Fonts/Baloo2 SDF.asset";
    const string ShadowMaterialPath = "Assets/_Project/Art/Fonts/Baloo2 SDF Shadow.mat";
    const string PrefabPath = "Assets/_Project/Prefabs/UI/Hud.prefab";
    const string VietnameseChars = "0123456789:%.,- aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvxyỳýỷỹỵ" +
                                   "AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬBCDĐEÈÉẺẼẸÊỀẾỂỄỆGHIÌÍỈĨỊKLMNOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢPQRSTUÙÚỦŨỤƯỪỨỬỮỰVXYỲÝỶỸỴ";

    static readonly Color DarkGlass = new Color32(0x2B, 0x2A, 0x33, 0x8C);
    static readonly Color Cream = new Color32(0xFB, 0xF4, 0xE6, 0xFF);
    static readonly Color Blue = new Color32(0x3F, 0xA7, 0xD6, 0xFF);
    static readonly Color Green = new Color32(0x63, 0xBF, 0x5E, 0xFF);

    [MenuItem("Chạy Đơn/Build HUD Prefab")]
    static void Build()
    {
        if (AssetDatabase.FindAssets("t:TMP_Settings").Length == 0)
        {
            ImportTmpEssentials();
            Debug.LogWarning("[HudBuilder] Importing TextMeshPro Essential Resources. Run Chạy Đơn → Build HUD Prefab again when the import finishes.");
            return;
        }
        ConfigureSprites();
        TMP_FontAsset font = CreateFontAsset();
        Material shadow = CreateShadowMaterial(font);

        // Built inactive so no UI component registers with the open scene's canvas or masks while it is assembled.
        var root = new GameObject("Hud", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        root.SetActive(false);
        try
        {
            BuildLayout(root, font, shadow);
            PrefabBuilder.EnsureFolder("Assets/_Project/Prefabs/UI");
            PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(root);
        }
        // Activate the saved prefab in an isolated prefab scene.
        GameObject contents = PrefabUtility.LoadPrefabContents(PrefabPath);
        contents.SetActive(true);
        PrefabUtility.SaveAsPrefabAsset(contents, PrefabPath);
        PrefabUtility.UnloadPrefabContents(contents);
        AssetDatabase.SaveAssets();
        Debug.Log($"[HudBuilder] Built {PrefabPath}.");
    }

    // TMP Essential Resources ship inside the uGUI package (Unity 6); import the bundled .unitypackage silently.
    static void ImportTmpEssentials()
    {
        const string package = "Packages/com.unity.ugui/Package Resources/TMP Essential Resources.unitypackage";
        if (System.IO.File.Exists(System.IO.Path.GetFullPath(package)))
            AssetDatabase.ImportPackage(package, false);
        else
            Debug.LogError("[HudBuilder] TMP Essential Resources not found; import them from Window → TextMeshPro.");
    }

    // Sprites: no mipmaps, transparent edges; pill and panel are 9-sliced around their rounded corners.
    static void ConfigureSprites()
    {
        foreach (string guid in AssetDatabase.FindAssets("t:Texture2D", new[] { SpritesFolder }))
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.textureType = TextureImporterType.Sprite;
            ti.spriteImportMode = SpriteImportMode.Single;
            ti.mipmapEnabled = false;
            ti.alphaIsTransparency = true;
            ti.filterMode = FilterMode.Bilinear;
            ti.textureCompression = TextureImporterCompression.Uncompressed;
            string file = System.IO.Path.GetFileNameWithoutExtension(path);
            ti.spriteBorder = file == "ui_pill" ? new Vector4(63, 63, 63, 63) : file == "ui_panel" ? new Vector4(46, 46, 46, 46) : Vector4.zero;
            ti.SaveAndReimport();
        }
    }

    static Sprite S(string name) => AssetDatabase.LoadAssetAtPath<Sprite>($"{SpritesFolder}/ui_{name}.png");

    // Dynamic SDF font asset with the Vietnamese alphabet pre-added; other glyphs are added on demand.
    static TMP_FontAsset CreateFontAsset()
    {
        var existing = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(FontAssetPath);
        if (existing != null)
            return existing;
        var font = AssetDatabase.LoadAssetAtPath<Font>(FontPath);
        TMP_FontAsset fa = TMP_FontAsset.CreateFontAsset(font, 90, 9, GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true);
        fa.name = "Baloo2 SDF";
        AssetDatabase.CreateAsset(fa, FontAssetPath);
        fa.atlasTextures[0].name = "Baloo2 SDF Atlas";
        AssetDatabase.AddObjectToAsset(fa.atlasTextures[0], fa);
        fa.material.name = "Baloo2 SDF Material";
        AssetDatabase.AddObjectToAsset(fa.material, fa);
        fa.TryAddCharacters(VietnameseChars);
        EditorUtility.SetDirty(fa);
        AssetDatabase.SaveAssets();
        return fa;
    }

    // White text over the scene: hard dark drop shadow (underlay), as in mockup style A.
    static Material CreateShadowMaterial(TMP_FontAsset font)
    {
        var m = AssetDatabase.LoadAssetAtPath<Material>(ShadowMaterialPath);
        if (m == null)
        {
            m = new Material(font.material);
            AssetDatabase.CreateAsset(m, ShadowMaterialPath);
        }
        m.shader = font.material.shader;
        m.SetTexture("_MainTex", font.atlasTextures[0]);
        m.EnableKeyword("UNDERLAY_ON");
        m.SetColor("_UnderlayColor", new Color(0.17f, 0.16f, 0.2f, 0.85f));
        m.SetFloat("_UnderlayOffsetX", 0f);
        m.SetFloat("_UnderlayOffsetY", -0.9f);
        m.SetFloat("_UnderlayDilate", 0.3f);
        EditorUtility.SetDirty(m);
        return m;
    }

    static void BuildLayout(GameObject root, TMP_FontAsset font, Material shadow)
    {
        root.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = root.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(360f, 780f);
        scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
        scaler.matchWidthOrHeight = 0f;
        root.AddComponent<CanvasScaleByAspect>();
        var hud = root.AddComponent<Hud>();

        RectTransform safe = Rect("SafeArea", root.transform);
        Stretch(safe);
        safe.gameObject.AddComponent<SafeAreaFitter>();

        // Pause: translucent round button
        RectTransform pause = Rect("Pause", safe);
        Place(pause, new Vector2(0, 1), new Vector2(0, 1), new Vector2(12, -10), new Vector2(46, 46));
        Image pauseBg = Img(pause, S("circle"), DarkGlass, true);
        hud.pauseButton = pause.gameObject.AddComponent<Button>();
        hud.pauseButton.targetGraphic = pauseBg;
        Child(pause, "Ring", S("ring"), new Color(1f, 1f, 1f, 0.35f), new Vector2(46, 46));
        Child(pause, "Icon", S("pause"), Color.white, new Vector2(24, 24));

        // Timer, coins
        RectTransform timer = Rect("Timer", safe);
        Place(timer, new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -6), new Vector2(200, 50));
        hud.timerText = Text(timer, font, shadow, 40, Color.white, TextAlignmentOptions.Center, "01:25");

        RectTransform coins = Rect("Coins", safe);
        Place(coins, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-14, -12), new Vector2(110, 32));
        Row(coins, 6, TextAnchor.MiddleRight, new RectOffset(0, 0, 0, 0));
        Fixed(Child(coins, "Coin", S("coin"), Color.white, new Vector2(24, 24)), 24, 24);
        hud.coinsText = Text(Rect("Value", coins), font, shadow, 22, Color.white, TextAlignmentOptions.MidlineRight, "1.250");

        // Delivery address pill
        RectTransform addr = Rect("Address", safe);
        Place(addr, new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -60), new Vector2(180, 30));
        Sliced(Img(addr, S("pill"), DarkGlass, false), 63f / 15f);
        Row(addr, 6, TextAnchor.MiddleCenter, new RectOffset(4, 14, 3, 3));
        addr.gameObject.AddComponent<ContentSizeFitter>().horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
        RectTransform badge = Child(addr, "Badge", S("circle"), Cream, new Vector2(24, 24));
        Fixed(badge, 24, 24);
        Child(badge, "Home", S("home"), Color.white, new Vector2(16, 16));
        hud.addressText = Text(Rect("Text", addr), font, null, 14, Color.white, TextAlignmentOptions.MidlineLeft, "27 Lý Tự Trọng");

        // Q% row: cargo badge whose ring shows the state, bar, value
        RectTransform q = Rect("Integrity", safe);
        Place(q, new Vector2(0.5f, 1), new Vector2(0.5f, 1), new Vector2(0, -96), new Vector2(236, 38));
        RectTransform cargo = Child(q, "Cargo", S("circle"), Cream, new Vector2(38, 38));
        cargo.anchorMin = cargo.anchorMax = cargo.pivot = new Vector2(0, 0.5f);
        cargo.anchoredPosition = Vector2.zero;
        cargo.gameObject.AddComponent<Shadow>().effectDistance = new Vector2(0, -3);
        hud.cargoRing = Child(cargo, "Ring", S("ring"), Green, new Vector2(40, 40)).GetComponent<Image>();
        Child(cargo, "Icon", S("cup"), Color.white, new Vector2(24, 24));
        RectTransform track = Rect("Track", q);
        track.anchorMin = new Vector2(0, 0.5f);
        track.anchorMax = new Vector2(1, 0.5f);
        track.offsetMin = new Vector2(46, -6);
        track.offsetMax = new Vector2(-48, 6);
        Sliced(Img(track, S("pill"), new Color(0.17f, 0.16f, 0.2f, 0.5f), false), 63f / 6f);
        hud.qFill = Rect("Fill", track);
        hud.qFill.anchorMin = Vector2.zero;
        hud.qFill.anchorMax = new Vector2(0.82f, 1);
        hud.qFill.offsetMin = hud.qFill.offsetMax = Vector2.zero;
        hud.qFillImage = Img(hud.qFill, S("pill"), Green, false);
        Sliced(hud.qFillImage, 63f / 6f);
        RectTransform qVal = Rect("Value", q);
        qVal.anchorMin = qVal.anchorMax = qVal.pivot = new Vector2(1, 0.5f);
        qVal.sizeDelta = new Vector2(44, 24);
        qVal.anchoredPosition = Vector2.zero;
        hud.qText = Text(qVal, font, shadow, 16, Color.white, TextAlignmentOptions.MidlineRight, "82%");

        // Route map (style 2: translucent dark card): roads drawn by RouteMapGraphic, clipped to the card
        RectTransform map = Rect("Map", safe);
        Place(map, new Vector2(1, 1), new Vector2(1, 1), new Vector2(-12, -150), new Vector2(112, 150));
        Sliced(Img(map, S("panel"), new Color(0.17f, 0.16f, 0.2f, 0.62f), false), 46f / 18f);
        RectTransform viewport = Rect("Viewport", map);
        Stretch(viewport);
        viewport.gameObject.AddComponent<RectMask2D>().padding = new Vector4(3, 3, 3, 3);
        RectTransform lines = Rect("Roads", viewport);
        Stretch(lines);
        lines.gameObject.AddComponent<CanvasRenderer>();  // the graphic draws through it; added explicitly before the graphic
        var graphic = lines.gameObject.AddComponent<RouteMapGraphic>();
        graphic.raycastTarget = false;
        var view = map.gameObject.AddComponent<RouteMapView>();
        view.viewport = viewport;
        view.graphic = graphic;
        view.puck = Child(viewport, "Player", S("puck"), Color.white, new Vector2(24, 24));
        view.pin = Child(viewport, "Destination", S("pin"), Color.white, new Vector2(22, 22));
        view.pin.pivot = new Vector2(0.5f, 0.03f);  // tip of the pin sits on the address
        view.edgeArrow = Child(viewport, "DestinationArrow", S("edge_arrow"), Color.white, new Vector2(20, 20));
        hud.map = view;

        // Horn: 64 dp face inside an 84 dp touch area, bottom right
        RectTransform hornArea = Rect("Horn", safe);
        Place(hornArea, new Vector2(1, 0), new Vector2(0.5f, 0.5f), new Vector2(-58, 76), new Vector2(84, 84));
        Img(hornArea, S("circle"), new Color(1, 1, 1, 0), true);  // invisible touch target
        var horn = hornArea.gameObject.AddComponent<HornButton>();
        horn.glow = Child(hornArea, "Glow", S("circle"), new Color(1f, 0.84f, 0.31f, 0.6f), new Vector2(84, 84)).gameObject;
        RectTransform face = Child(hornArea, "Face", S("circle"), Cream, new Vector2(64, 64));
        var faceShadow = face.gameObject.AddComponent<Shadow>();
        faceShadow.effectColor = new Color32(0xB8, 0xAE, 0x9C, 0xFF);
        faceShadow.effectDistance = new Vector2(0, -5);
        horn.face = face.GetComponent<Image>();
        horn.icon = Child(hornArea, "Icon", S("horn"), Color.white, new Vector2(34, 34)).GetComponent<Image>();
        Image ring = Child(hornArea, "Cooldown", S("ring"), Blue, new Vector2(76, 76)).GetComponent<Image>();
        ring.type = Image.Type.Filled;
        ring.fillMethod = Image.FillMethod.Radial360;
        ring.fillOrigin = (int)Image.Origin360.Top;
        ring.fillClockwise = true;
        horn.cooldownRing = ring;
        hud.horn = horn;
    }

    // ---------- small layout helpers ----------
    static RectTransform Rect(string name, Transform parent)
    {
        var go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        return (RectTransform)go.transform;
    }

    static void Stretch(RectTransform rt)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = rt.offsetMax = Vector2.zero;
    }

    static void Place(RectTransform rt, Vector2 anchor, Vector2 pivot, Vector2 pos, Vector2 size)
    {
        rt.anchorMin = rt.anchorMax = anchor;
        rt.pivot = pivot;
        rt.anchoredPosition = pos;
        rt.sizeDelta = size;
    }

    static Image Img(RectTransform rt, Sprite sprite, Color color, bool raycast)
    {
        var img = rt.gameObject.AddComponent<Image>();
        img.sprite = sprite;
        img.color = color;
        img.raycastTarget = raycast;
        return img;
    }

    // Centered child image of a fixed size.
    static RectTransform Child(RectTransform parent, string name, Sprite sprite, Color color, Vector2 size)
    {
        RectTransform rt = Rect(name, parent);
        Place(rt, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), Vector2.zero, size);
        Img(rt, sprite, color, false);
        return rt;
    }

    static void Sliced(Image img, float pixelsPerUnit)
    {
        img.type = Image.Type.Sliced;
        img.pixelsPerUnitMultiplier = pixelsPerUnit;
    }

    static void Row(RectTransform rt, float spacing, TextAnchor align, RectOffset padding)
    {
        var row = rt.gameObject.AddComponent<HorizontalLayoutGroup>();
        row.spacing = spacing;
        row.childAlignment = align;
        row.padding = padding;
        row.childControlWidth = row.childControlHeight = true;
        row.childForceExpandWidth = row.childForceExpandHeight = false;
    }

    static void Fixed(RectTransform rt, float w, float h)
    {
        var le = rt.gameObject.AddComponent<LayoutElement>();
        le.minWidth = le.preferredWidth = w;
        le.minHeight = le.preferredHeight = h;
    }

    static TMP_Text Text(RectTransform rt, TMP_FontAsset font, Material material, float size, Color color, TextAlignmentOptions align, string sample)
    {
        var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
        t.font = font;
        if (material != null)
            t.fontSharedMaterial = material;
        t.fontSize = size;
        t.fontStyle = FontStyles.Bold;
        t.color = color;
        t.alignment = align;
        t.textWrappingMode = TextWrappingModes.NoWrap;
        t.raycastTarget = false;
        t.text = sample;
        return t;
    }
}
