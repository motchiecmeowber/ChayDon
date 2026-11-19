using UnityEngine;
using UnityEngine.Rendering;

// Applies a LightingPreset to the scene; also runs in the Editor. Call SetPreset to switch at runtime.
[ExecuteAlways]
public class LightingController : MonoBehaviour
{
    public LightingPreset preset;
    public Light sun;
    [Tooltip("Leave empty to use Camera.main.")]
    public Camera targetCamera;
    [Tooltip("Optional; receives the preset's post-processing profile.")]
    public Volume postProcessVolume;

    void OnEnable()
    {
        LightingPreset.Changed += OnPresetChanged;
        Apply();
    }

    void OnDisable() => LightingPreset.Changed -= OnPresetChanged;

    void OnValidate() => Apply();

    void OnPresetChanged(LightingPreset changed)
    {
        if (changed == preset)
            Apply();
    }

    public void SetPreset(LightingPreset newPreset)
    {
        preset = newPreset;
        Apply();
    }

    public void Apply()
    {
        if (preset == null)
            return;

        if (sun != null)
        {
            sun.type = LightType.Directional;
            sun.color = preset.sunColor;
            sun.intensity = preset.sunIntensity;
            sun.transform.rotation = Quaternion.Euler(preset.sunRotation);
            sun.shadowStrength = preset.shadowStrength;
            RenderSettings.sun = sun;
        }

        RenderSettings.skybox = null;
        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = preset.ambientSky;
        RenderSettings.ambientEquatorColor = preset.ambientEquator;
        RenderSettings.ambientGroundColor = preset.ambientGround;

        RenderSettings.fog = preset.fog;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogColor = preset.fogColor;
        RenderSettings.fogStartDistance = preset.fogStart;
        RenderSettings.fogEndDistance = preset.fogEnd;

        Camera cam = targetCamera != null ? targetCamera : Camera.main;
        if (cam != null)
        {
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = preset.skyColor;
        }

        if (postProcessVolume != null)
            postProcessVolume.sharedProfile = preset.postProcess;
    }
}
