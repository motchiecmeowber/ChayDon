using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// Horn button: fires on touch-down (so a touch starting here never becomes a swipe), then cools down.
// The radial ring shows the cooldown; the glow hints that a slow vehicle blocks the lane.
public class HornButton : MonoBehaviour, IPointerDownHandler
{
    public float cooldown = 4f;
    public Image face;
    public Image icon;
    public Image cooldownRing;
    public GameObject glow;

    public event Action Pressed;
    public bool Ready => left <= 0f;

    static readonly Color ReadyFace = new Color32(0xFB, 0xF4, 0xE6, 0xFF);
    static readonly Color CoolingFace = new Color32(0xCF, 0xC6, 0xB6, 0xFF);
    float left;
    bool hint;

    void Start() => Refresh();

    public void OnPointerDown(PointerEventData eventData)
    {
        if (!Ready)
            return;
        left = cooldown;
        Pressed?.Invoke();
        Refresh();
    }

    public void SetHint(bool on)
    {
        hint = on;
        Refresh();
    }

    void Update()
    {
        if (left <= 0f)
            return;
        left -= Time.unscaledDeltaTime;
        Refresh();
    }

    void Refresh()
    {
        if (cooldownRing != null)
        {
            cooldownRing.enabled = !Ready;
            cooldownRing.fillAmount = 1f - left / cooldown;
        }
        if (face != null)
            face.color = Ready ? ReadyFace : CoolingFace;
        if (icon != null)
            icon.color = Ready ? Color.white : new Color(1f, 1f, 1f, 0.45f);
        if (glow != null)
            glow.SetActive(Ready && hint);
    }
}
