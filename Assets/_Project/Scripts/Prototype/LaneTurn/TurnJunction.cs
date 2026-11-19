using System.Collections.Generic;
using UnityEngine;

// Prototype: a junction on the road. Exits come from the road's attach points; the choice is locked at the commit line.
[RequireComponent(typeof(AttachPoints))]
public class TurnJunction : MonoBehaviour
{
    public static readonly List<TurnJunction> All = new List<TurnJunction>();

    [Tooltip("Distance before the junction center where the exit is locked in.")]
    public float commitDistance = 25f;
    [Tooltip("Turn arc radius on the center line; half the road width keeps the arc inside the junction.")]
    public float turnRadius = 4.5f;

    public Transform Center { get; private set; }
    public bool HasLeft { get; private set; }
    public bool HasRight { get; private set; }
    public bool HasStraight { get; private set; }

    void Awake()
    {
        var points = GetComponent<AttachPoints>();
        Center = points.Get("DiemGiaoLo");
        HasLeft = points.Get("DiemNhanhTrai") != null;
        HasRight = points.Get("DiemNhanhPhai") != null;
        HasStraight = points.Get("DiemNoi") != null;
        CreateCommitLine();
    }

    void OnEnable() => All.Add(this);
    void OnDisable() => All.Remove(this);

    // Thin yellow bar across the road at the commit line.
    void CreateCommitLine()
    {
        var bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
        Destroy(bar.GetComponent<Collider>());
        bar.name = "CommitLine";
        bar.transform.SetParent(transform, false);
        bar.transform.position = Center.position - transform.forward * commitDistance + Vector3.up * 0.02f;
        bar.transform.rotation = transform.rotation;
        bar.transform.localScale = new Vector3(9f, 0.02f, 0.4f);
        var material = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        material.SetColor("_BaseColor", new Color32(0xFF, 0xD5, 0x4F, 0xFF));
        bar.GetComponent<Renderer>().sharedMaterial = material;
    }
}
