using System.Collections.Generic;
using UnityEngine;

// Prototype: the end of a branch; the runner stops at the delivery point (DiemGiao).
[RequireComponent(typeof(AttachPoints))]
public class RouteEnd : MonoBehaviour
{
    public static readonly List<RouteEnd> All = new List<RouteEnd>();

    [Tooltip("The order's customer house; the other ends are wrong addresses.")]
    public bool isDestination;

    public Transform DeliveryPoint { get; private set; }

    void Awake() => DeliveryPoint = GetComponent<AttachPoints>().Get("DiemGiao");
    void OnEnable() => All.Add(this);
    void OnDisable() => All.Remove(this);
}
