using System.Collections.Generic;
using UnityEngine;

// Route map in the HUD, Google-Maps-like: heading-up, grey streets, the chosen route in blue with a white casing,
// traffic overlays (orange busy, red jam), player puck, destination pin or an edge arrow toward it.
// Near view follows the player; when SetFocus gets points (e.g. junction branches) it zooms out to frame them.
public class RouteMapView : MonoBehaviour
{
    public class Edge
    {
        public readonly List<Vector3> points = new List<Vector3>();
        public int traffic;  // 0 free, 1 busy, 2 jam
    }

    public RectTransform viewport;
    public RouteMapGraphic graphic;
    public RectTransform puck;
    public RectTransform pin;
    public RectTransform edgeArrow;
    [Tooltip("Zoom of the near view, metres per dp.")]
    public float nearScale = 1f;
    [Tooltip("Player position below the map center, as a fraction of the map height (near view).")]
    public float playerOffset = 0.3f;
    public float smoothTime = 0.45f;
    public float padding = 14f;

    static readonly Color Street = new Color(0.79f, 0.8f, 0.82f, 0.55f);
    static readonly Color Casing = new Color(0.98f, 0.96f, 0.9f, 0.95f);
    static readonly Color RouteBlue = new Color32(0x3F, 0xA7, 0xD6, 0xFF);
    static readonly Color Busy = new Color32(0xFF, 0x8A, 0x3D, 0xFF);
    static readonly Color Jam = new Color32(0xE5, 0x39, 0x35, 0xFF);

    IList<Edge> edges = new List<Edge>();
    readonly List<Vector3> route = new List<Vector3>();
    readonly List<Vector3> focus = new List<Vector3>();
    readonly List<Vector2> scratch = new List<Vector2>();
    Vector3 player, destination;
    float playerYaw;
    bool hasDestination, initialized;
    Vector3 center, centerVel;
    float scale, scaleVel, yaw, yawVel, flash;

    public void SetEdges(IList<Edge> mapEdges) => edges = mapEdges;
    public void SetDestination(Vector3 p) { destination = p; hasDestination = true; }
    public void SetPlayer(Vector3 position, float headingDeg) { player = position; playerYaw = headingDeg; }
    public void Flash() => flash = 1f;

    public void SetRoute(IList<Vector3> points)
    {
        route.Clear();
        route.AddRange(points);
    }

    // Empty list: near view around the player.
    public void SetFocus(IList<Vector3> points)
    {
        focus.Clear();
        if (points != null)
            focus.AddRange(points);
    }

    void LateUpdate()
    {
        Rect r = viewport.rect;
        TargetView(r, out Vector3 targetCenter, out float targetScale);
        float dt = Time.deltaTime;
        if (!initialized)
        {
            center = targetCenter;
            scale = targetScale;
            yaw = playerYaw;
            initialized = true;
        }
        yaw = Mathf.SmoothDampAngle(yaw, playerYaw, ref yawVel, smoothTime * 0.6f, Mathf.Infinity, dt);
        center = Vector3.SmoothDamp(center, targetCenter, ref centerVel, smoothTime, Mathf.Infinity, dt);
        scale = Mathf.SmoothDamp(scale, targetScale, ref scaleVel, smoothTime, Mathf.Infinity, dt);
        flash = Mathf.Max(0f, flash - dt / 0.45f);
        Draw(r);
    }

    void TargetView(Rect r, out Vector3 targetCenter, out float targetScale)
    {
        Vector3 fwd = Quaternion.Euler(0f, playerYaw, 0f) * Vector3.forward;
        Vector3 right = Quaternion.Euler(0f, playerYaw, 0f) * Vector3.right;
        if (focus.Count == 0)
        {
            targetScale = nearScale;
            targetCenter = player + fwd * (playerOffset * r.height * nearScale);
            return;
        }
        float minX = 0f, maxX = 0f, minY = 0f, maxY = 0f;
        foreach (Vector3 p in focus)
        {
            Vector3 d = p - player;
            float x = Vector3.Dot(d, right), y = Vector3.Dot(d, fwd);
            minX = Mathf.Min(minX, x); maxX = Mathf.Max(maxX, x);
            minY = Mathf.Min(minY, y); maxY = Mathf.Max(maxY, y);
        }
        targetScale = Mathf.Max(nearScale, (maxX - minX) / (r.width - 2f * padding), (maxY - minY) / (r.height - 2f * padding));
        targetCenter = player + right * ((minX + maxX) * 0.5f) + fwd * ((minY + maxY) * 0.5f);
    }

    Vector2 Map(Vector3 p)
    {
        Vector3 d = p - center;
        Quaternion q = Quaternion.Euler(0f, yaw, 0f);
        return new Vector2(Vector3.Dot(d, q * Vector3.right), Vector3.Dot(d, q * Vector3.forward)) / scale;
    }

    void Stroke(IList<Vector3> points, float width, Color color)
    {
        scratch.Clear();
        foreach (Vector3 p in points)
            scratch.Add(Map(p));
        graphic.AddStroke(scratch, width, color);
    }

    void Draw(Rect r)
    {
        graphic.Clear();
        foreach (Edge e in edges)
            Stroke(e.points, 5f, Street);
        if (route.Count > 1)
        {
            Stroke(route, 9f, Casing);
            Stroke(route, 6f, Color.Lerp(RouteBlue, Color.white, flash));
        }
        foreach (Edge e in edges)
            if (e.traffic > 0)
                Stroke(e.points, 4.5f, e.traffic > 1 ? Jam : Busy);

        Vector2 p = Map(player);
        puck.anchoredPosition = p;
        puck.localRotation = Quaternion.Euler(0f, 0f, yaw - playerYaw);

        if (!hasDestination)
        {
            pin.gameObject.SetActive(false);
            edgeArrow.gameObject.SetActive(false);
            return;
        }
        Vector2 d = Map(destination);
        Rect inner = new Rect(r.xMin + 10f, r.yMin + 10f, r.width - 20f, r.height - 34f);  // room for the pin height
        bool inside = inner.Contains(d);
        pin.gameObject.SetActive(inside);
        edgeArrow.gameObject.SetActive(!inside);
        if (inside)
            pin.anchoredPosition = d;
        else
        {
            Vector2 half = new Vector2(r.width * 0.5f - 14f, r.height * 0.5f - 14f);
            float k = Mathf.Min(half.x / Mathf.Max(Mathf.Abs(d.x), 1e-3f), half.y / Mathf.Max(Mathf.Abs(d.y), 1e-3f));
            edgeArrow.anchoredPosition = d * Mathf.Min(1f, k);
            edgeArrow.localRotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg - 90f);
        }
    }
}
