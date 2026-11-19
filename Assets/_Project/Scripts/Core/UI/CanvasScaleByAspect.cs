using UnityEngine;
using UnityEngine.UI;

// Phones narrower than the reference keep the HUD sized by width; wider screens (tablets, unfolded foldables)
// size it by height so the HUD does not grow and cover the road.
[ExecuteAlways]
[RequireComponent(typeof(CanvasScaler))]
public class CanvasScaleByAspect : MonoBehaviour
{
    CanvasScaler scaler;

    void OnEnable() => scaler = GetComponent<CanvasScaler>();

    void Update()
    {
        Vector2 reference = scaler.referenceResolution;
        float aspect = Screen.height > 0 ? (float)Screen.width / Screen.height : 0f;
        scaler.matchWidthOrHeight = aspect > reference.x / reference.y ? 1f : 0f;
    }
}
