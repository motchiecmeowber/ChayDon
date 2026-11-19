using UnityEngine;

// Keeps a full-screen RectTransform inside Screen.safeArea (camera hole, rounded corners, navigation bar).
[ExecuteAlways]
[RequireComponent(typeof(RectTransform))]
public class SafeAreaFitter : MonoBehaviour
{
    Rect applied;
    Vector2Int screen;

    void Update()
    {
        Rect safe = Screen.safeArea;
        if (safe == applied && screen.x == Screen.width && screen.y == Screen.height)
            return;
        applied = safe;
        screen = new Vector2Int(Screen.width, Screen.height);
        var rt = (RectTransform)transform;
        rt.anchorMin = new Vector2(safe.xMin / Screen.width, safe.yMin / Screen.height);
        rt.anchorMax = new Vector2(safe.xMax / Screen.width, safe.yMax / Screen.height);
        rt.offsetMin = rt.offsetMax = Vector2.zero;
    }
}
