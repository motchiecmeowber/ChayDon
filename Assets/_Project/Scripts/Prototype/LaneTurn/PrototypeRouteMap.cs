using System.Collections.Generic;
using UnityEngine;

// Prototype: builds the route graph from the road pieces (attach points) and feeds the HUD route map each frame.
// Blue line = what the player will do: through the upcoming junction by the current lane's exit, then the fastest way
// (length weighted by traffic) to the destination. Near a junction the map frames every branch; it flashes on commit.
public class PrototypeRouteMap : MonoBehaviour
{
    public LaneTurnRunner runner;
    public Transform roads;
    [Tooltip("Zoom out to frame the branches when the junction is closer than this (m).")]
    public float wideRange = 150f;
    [Tooltip("How far along each branch the wide view shows (m).")]
    public float branchPreview = 140f;

    class Link
    {
        public RouteMapView.Edge edge;
        public int from, to;
        public float length;
    }

    readonly List<Vector3> nodes = new List<Vector3>();
    readonly List<Link> links = new List<Link>();
    readonly List<RouteMapView.Edge> edges = new List<RouteMapView.Edge>();
    readonly Dictionary<TurnJunction, Link[]> exits = new Dictionary<TurnJunction, Link[]>();  // left, straight, right
    readonly List<Vector3> path = new List<Vector3>();
    readonly List<Vector3> focus = new List<Vector3>();
    int destinationNode = -1;
    Link current;
    bool wasCommitted;
    float trafficTimer;
    RouteMapView map;

    void Start()
    {
        var hud = FindFirstObjectByType<Hud>();
        map = hud != null ? hud.map : null;
        if (map == null)
        {
            enabled = false;
            return;
        }
        BuildGraph();
        map.gameObject.SetActive(true);
        map.SetEdges(edges);
        if (destinationNode >= 0)
            map.SetDestination(nodes[destinationNode]);
    }

    void BuildGraph()
    {
        foreach (Transform piece in roads)
        {
            var ap = piece.GetComponent<AttachPoints>();
            if (ap == null)
                continue;
            var junction = piece.GetComponent<TurnJunction>();
            var end = piece.GetComponent<RouteEnd>();
            if (junction != null)
            {
                Vector3 c = ap.Get("DiemGiaoLo").position;
                AddLink(piece.position, c);
                Link Exit(string point) => ap.Get(point) != null ? AddLink(c, ap.Get(point).position) : null;
                exits[junction] = new[] { Exit("DiemNhanhTrai"), Exit("DiemNoi"), Exit("DiemNhanhPhai") };
            }
            else if (end != null)
            {
                Link l = AddLink(piece.position, ap.Get("DiemGiao").position);
                if (end.isDestination)
                    destinationNode = l.to;
            }
            else if (ap.Get("DiemNoi") != null)
                AddLink(piece.position, ap.Get("DiemNoi").position);
        }
    }

    Link AddLink(Vector3 a, Vector3 b)
    {
        var e = new RouteMapView.Edge();
        e.points.Add(a);
        e.points.Add(b);
        var l = new Link { edge = e, from = Node(a), to = Node(b), length = Vector3.Distance(a, b) };
        links.Add(l);
        edges.Add(e);
        return l;
    }

    int Node(Vector3 p)
    {
        for (int i = 0; i < nodes.Count; i++)
            if ((nodes[i] - p).sqrMagnitude < 0.5f)
                return i;
        nodes.Add(p);
        return nodes.Count - 1;
    }

    void Update()
    {
        trafficTimer -= Time.deltaTime;
        if (trafficTimer <= 0f)
        {
            trafficTimer = 0.5f;
            UpdateTraffic();
        }

        Vector3 p = runner.RoadPoint;
        Vector3 fwd = Quaternion.Euler(0f, runner.Heading, 0f) * Vector3.forward;
        Link onLink = FindLink(p, fwd);
        if (onLink != null)  // off every edge (mid-turn): keep the last route
        {
            current = onLink;
            BuildPath(p);
        }

        focus.Clear();
        TurnJunction j = runner.UpcomingJunction;
        if (j != null && Vector3.Dot(j.Center.position - p, fwd) < wideRange && exits.TryGetValue(j, out Link[] options))
        {
            focus.Add(p);
            focus.Add(j.Center.position);
            foreach (Link option in options)
                if (option != null)
                    Preview(option, branchPreview);
        }

        if (runner.Committed && !wasCommitted)
            map.Flash();
        wasCommitted = runner.Committed;
        map.SetPlayer(runner.transform.position, runner.Heading);
        map.SetRoute(path);
        map.SetFocus(focus);
    }

    // Edge the player is driving along: projects inside it, close to it, same direction.
    Link FindLink(Vector3 p, Vector3 fwd)
    {
        foreach (Link l in links)
        {
            Vector3 a = l.edge.points[0], b = l.edge.points[1];
            Vector3 dir = (b - a) / Mathf.Max(l.length, 1e-3f);
            float t = Vector3.Dot(p - a, dir);
            if (t >= 0f && t <= l.length && Vector3.Distance(a + dir * t, p) < 2f && Vector3.Dot(dir, fwd) > 0.7f)
                return l;
        }
        return null;
    }

    void BuildPath(Vector3 p)
    {
        path.Clear();
        path.Add(p);
        int node = current.to;
        path.Add(nodes[node]);
        TurnJunction j = runner.UpcomingJunction;
        if (j != null && exits.TryGetValue(j, out Link[] options))
        {
            // Walk to the junction center, then take the exit picked by the current lane.
            int center = Node(j.Center.position);
            int guard = 0;
            while (node != center && guard++ < 20)
            {
                Link next = links.Find(l => l.from == node);
                if (next == null)
                    break;
                node = next.to;
                path.Add(nodes[node]);
            }
            Link chosen = options[runner.PlannedExit + 1] ?? options[1];
            if (node == center && chosen != null)
            {
                node = chosen.to;
                path.Add(nodes[node]);
            }
        }
        AppendBestRoute(node, path);
    }

    // Fastest way to the destination (length x traffic); if it cannot be reached, follow the road to its end.
    void AppendBestRoute(int start, List<Vector3> into)
    {
        var dist = new float[nodes.Count];
        var prev = new int[nodes.Count];
        var done = new bool[nodes.Count];
        for (int i = 0; i < dist.Length; i++) { dist[i] = float.MaxValue; prev[i] = -1; }
        dist[start] = 0f;
        for (int k = 0; k < nodes.Count; k++)
        {
            int u = -1;
            for (int i = 0; i < dist.Length; i++)
                if (!done[i] && dist[i] < float.MaxValue && (u < 0 || dist[i] < dist[u]))
                    u = i;
            if (u < 0)
                break;
            done[u] = true;
            foreach (Link l in links)
                if (l.from == u)
                {
                    float w = l.length * (1f + 0.6f * l.edge.traffic);
                    if (dist[u] + w < dist[l.to]) { dist[l.to] = dist[u] + w; prev[l.to] = u; }
                }
        }
        var chain = new List<int>();
        if (destinationNode >= 0 && dist[destinationNode] < float.MaxValue)
            for (int n = destinationNode; n != start && n >= 0; n = prev[n])
                chain.Insert(0, n);
        else
            for (int n = start, guard = 0; guard < 20; guard++)
            {
                Link next = links.Find(l => l.from == n);
                if (next == null)
                    break;
                n = next.to;
                chain.Add(n);
            }
        foreach (int n in chain)
            into.Add(nodes[n]);
    }

    // Adds points along a branch for the wide view: the branch's best continuation, up to a distance.
    void Preview(Link option, float range)
    {
        var branch = new List<Vector3> { nodes[option.from], nodes[option.to] };
        AppendBestRoute(option.to, branch);
        float left = range;
        focus.Add(branch[0]);
        for (int i = 1; i < branch.Count && left > 0f; i++)
        {
            float seg = Vector3.Distance(branch[i - 1], branch[i]);
            focus.Add(seg <= left ? branch[i] : Vector3.Lerp(branch[i - 1], branch[i], left / seg));
            left -= seg;
        }
    }

    // Traffic per edge from the AI scooters on it: vehicles per 100 m, 4+ busy, 7+ jam.
    void UpdateTraffic()
    {
        foreach (Link l in links)
        {
            Vector3 a = l.edge.points[0], b = l.edge.points[1];
            Vector3 dir = (b - a) / Mathf.Max(l.length, 1e-3f);
            int count = 0;
            foreach (PrototypeTraffic t in PrototypeTraffic.All)
            {
                float s = Vector3.Dot(t.transform.position - a, dir);
                if (s >= 0f && s <= l.length && Vector3.Distance(a + dir * s, t.transform.position) < 5f)
                    count++;
            }
            float per100 = l.length > 1f ? count * 100f / l.length : 0f;
            l.edge.traffic = l.length < 30f ? 0 : per100 >= 7f ? 2 : per100 >= 4f ? 1 : 0;
        }
    }
}
