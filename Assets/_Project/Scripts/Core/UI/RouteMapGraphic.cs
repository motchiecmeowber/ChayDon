using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

// Draws thick polylines with round joins and caps into a UI rect (route map roads, route line, traffic overlays).
// Points are in the rect's local space (dp). Clipped by a RectMask2D on a parent.
[RequireComponent(typeof(CanvasRenderer))]
public class RouteMapGraphic : MaskableGraphic
{
    struct Stroke
    {
        public List<Vector2> points;
        public float width;
        public Color color;
    }

    const int CapSegments = 8;
    readonly List<Stroke> strokes = new List<Stroke>();
    readonly Stack<List<Vector2>> pool = new Stack<List<Vector2>>();

    public void Clear()
    {
        foreach (Stroke s in strokes)
        {
            s.points.Clear();
            pool.Push(s.points);
        }
        strokes.Clear();
        SetVerticesDirty();
    }

    // Copies the points; later strokes draw on top.
    public void AddStroke(IList<Vector2> points, float width, Color color)
    {
        if (points.Count < 2)
            return;
        List<Vector2> copy = pool.Count > 0 ? pool.Pop() : new List<Vector2>();
        copy.AddRange(points);
        strokes.Add(new Stroke { points = copy, width = width, color = color });
        SetVerticesDirty();
    }

    protected override void OnPopulateMesh(VertexHelper vh)
    {
        vh.Clear();
        foreach (Stroke s in strokes)
        {
            float r = s.width * 0.5f;
            for (int i = 0; i < s.points.Count - 1; i++)
                Segment(vh, s.points[i], s.points[i + 1], r, s.color);
            foreach (Vector2 p in s.points)
                Disc(vh, p, r, s.color);
        }
    }

    static void Segment(VertexHelper vh, Vector2 a, Vector2 b, float r, Color c)
    {
        Vector2 d = b - a;
        if (d.sqrMagnitude < 1e-6f)
            return;
        Vector2 n = new Vector2(-d.y, d.x).normalized * r;
        int i = vh.currentVertCount;
        vh.AddVert(a + n, c, Vector4.zero);
        vh.AddVert(b + n, c, Vector4.zero);
        vh.AddVert(b - n, c, Vector4.zero);
        vh.AddVert(a - n, c, Vector4.zero);
        vh.AddTriangle(i, i + 1, i + 2);
        vh.AddTriangle(i, i + 2, i + 3);
    }

    // Round join / cap.
    static void Disc(VertexHelper vh, Vector2 p, float r, Color c)
    {
        int center = vh.currentVertCount;
        vh.AddVert(p, c, Vector4.zero);
        for (int k = 0; k <= CapSegments * 2; k++)
        {
            float a = k * Mathf.PI / CapSegments;
            vh.AddVert(p + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r, c, Vector4.zero);
            if (k > 0)
                vh.AddTriangle(center, center + k, center + k + 1);
        }
    }
}
