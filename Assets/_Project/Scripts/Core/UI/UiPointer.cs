using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

// Touch helpers for gameplay input: skip touches that start on a HUD button or at the screen edges (Android back gesture).
public static class UiPointer
{
    public const float EdgeDp = 24f;

    static readonly List<RaycastResult> hits = new List<RaycastResult>();
    static PointerEventData data;

    // True if a raycast-target UI element is under the screen position.
    public static bool IsOverUi(Vector2 screenPos)
    {
        EventSystem es = EventSystem.current;
        if (es == null)
            return false;
        data ??= new PointerEventData(es);
        data.position = screenPos;
        hits.Clear();
        es.RaycastAll(data, hits);
        return hits.Count > 0;
    }

    public static float DpToPx(float dp) => dp * (Screen.dpi > 0f ? Screen.dpi / 160f : Screen.width / 360f);

    public static bool IsAtEdge(Vector2 screenPos)
    {
        float edge = DpToPx(EdgeDp);
        return screenPos.x < edge || screenPos.x > Screen.width - edge;
    }
}
