using UnityEngine;

// Frontage data of a street building, measured by PrefabBuilder. Front faces +Z; facade at z = 0.
public class StreetFrontage : MonoBehaviour
{
    // Tall sidewalk props (trees, poles, standing signs) stand 1.4 m from the facade and need this much clearance.
    public const float TallPropLimit = 0.85f;

    [Tooltip("Frontage width along X (m).")]
    public float width;
    [Tooltip("How far the ground floor reaches onto the sidewalk (awning, tables, parked bikes), 0.3–3 m above ground.")]
    public float groundDepth;

    public bool AllowsTallProps => groundDepth <= TallPropLimit;
}
