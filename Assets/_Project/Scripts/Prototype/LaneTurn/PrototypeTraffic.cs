using System.Collections.Generic;
using UnityEngine;

// Prototype: AI scooter driving straight along one road segment, slower than the player; loops back to the segment start.
// Evade() moves it to an adjacent lane (horn, GDD 4.3).
public class PrototypeTraffic : MonoBehaviour
{
    public static readonly List<PrototypeTraffic> All = new List<PrototypeTraffic>();

    public float speed = 7f;
    public float segmentLength = 100f;
    public float laneWidth = 3f;
    [Range(-1, 1)] public int lane;

    Vector3 lineStart;   // road center line at the start position
    float travelled, laneX, laneVel;

    public int Lane => lane;

    void OnEnable() => All.Add(this);
    void OnDisable() => All.Remove(this);

    void Start()
    {
        laneX = lane * laneWidth;
        lineStart = transform.position - transform.right * laneX;
    }

    public void Evade()
    {
        int target = lane == 0 ? (Random.value < 0.5f ? -1 : 1) : 0;
        lane = target;
    }

    void Update()
    {
        travelled += speed * Time.deltaTime;
        if (travelled > segmentLength)
            travelled = 0f;
        laneX = Mathf.SmoothDamp(laneX, lane * laneWidth, ref laneVel, 0.35f);
        transform.position = lineStart + transform.forward * travelled + transform.right * laneX;
    }
}
