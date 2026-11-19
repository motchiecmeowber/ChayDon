using System.Collections.Generic;
using UnityEngine;

// Attach points exported from Blender (DiemNoi, DiemGiao...), filled by PrefabBuilder. +Z is the direction of travel.
public class AttachPoints : MonoBehaviour
{
    [SerializeField] Transform[] points = new Transform[0];

    public IReadOnlyList<Transform> All => points;

    public Transform Get(string pointName)
    {
        foreach (Transform t in points)
            if (t != null && t.name == pointName)
                return t;
        return null;
    }

#if UNITY_EDITOR
    public void SetPoints(Transform[] list) => points = list;
#endif
}
