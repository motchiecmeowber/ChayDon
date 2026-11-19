using System;
using UnityEngine;
using UnityEngine.Rendering;

// Lighting for one time of day. No skybox: solid sky color plus matching fog (cheap on mobile).
[CreateAssetMenu(menuName = "Chạy Đơn/Lighting Preset", fileName = "Lighting_")]
public class LightingPreset : ScriptableObject
{
    public static event Action<LightingPreset> Changed;

    [Header("Sky (camera background)")]
    public Color skyColor = new Color32(0xBF, 0xE3, 0xF2, 0xFF);

    [Header("Sun")]
    public Color sunColor = new Color32(0xFF, 0xE7, 0xA8, 0xFF);
    [Range(0f, 3f)] public float sunIntensity = 1.3f;
    [Tooltip("Sun light rotation in degrees: X is elevation, Y is heading.")]
    public Vector3 sunRotation = new Vector3(50f, -30f, 0f);
    [Range(0f, 1f)] public float shadowStrength = 0.75f;

    [Header("Trilight ambient")]
    public Color ambientSky = new Color32(0xBF, 0xE3, 0xF2, 0xFF);
    public Color ambientEquator = new Color32(0xF2, 0xD7, 0xB6, 0xFF);
    public Color ambientGround = new Color32(0x8E, 0x8A, 0x85, 0xFF);

    [Header("Linear fog")]
    public bool fog = true;
    public Color fogColor = new Color32(0xBF, 0xE3, 0xF2, 0xFF);
    public float fogStart = 60f;
    public float fogEnd = 170f;

    [Header("Post-processing (optional)")]
    public VolumeProfile postProcess;

    void OnValidate() => Changed?.Invoke(this);
}
