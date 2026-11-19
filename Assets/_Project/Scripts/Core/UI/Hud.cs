using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

// In-run HUD (GDD 6.2.3, style A): timer, coins, delivery address, cargo integrity (Q%), route map, horn, pause.
// Display only: gameplay code pushes values in; the HUD raises Pressed events for pause and horn.
public class Hud : MonoBehaviour
{
    public TMP_Text timerText;
    public TMP_Text coinsText;
    public TMP_Text addressText;
    public TMP_Text qText;
    public RectTransform qFill;
    public Image qFillImage;
    public Image cargoRing;
    public Button pauseButton;
    public HornButton horn;
    public RouteMapView map;

    public event Action PausePressed;

    static readonly Color Good = new Color32(0x63, 0xBF, 0x5E, 0xFF);
    static readonly Color Fair = new Color32(0xFF, 0xD5, 0x4F, 0xFF);
    static readonly Color Bad = new Color32(0xE7, 0x6F, 0x51, 0xFF);
    static readonly Color TimeLow = new Color32(0xFF, 0x8A, 0x3D, 0xFF);
    const float LowTime = 15f;

    void Awake()
    {
        if (pauseButton != null)
            pauseButton.onClick.AddListener(() => PausePressed?.Invoke());
    }

    public void SetTimer(float seconds)
    {
        seconds = Mathf.Max(0f, seconds);
        int s = Mathf.CeilToInt(seconds);
        timerText.text = $"{s / 60:00}:{s % 60:00}";
        bool low = seconds < LowTime;
        timerText.color = low && Mathf.Repeat(Time.unscaledTime, 0.8f) < 0.4f ? TimeLow : Color.white;  // blink when low
    }

    public void SetCoins(int coins) => coinsText.text = coins.ToString("N0", System.Globalization.CultureInfo.GetCultureInfo("vi-VN"));

    public void SetAddress(string address) => addressText.text = address;

    public void SetQ(float percent)
    {
        float q = Mathf.Clamp01(percent / 100f);
        qFill.anchorMax = new Vector2(q, 1f);
        Color c = q >= 0.6f ? Good : q >= 0.3f ? Fair : Bad;
        qFillImage.color = c;
        cargoRing.color = c;
        qText.text = $"{Mathf.RoundToInt(percent)}%";
    }
}
