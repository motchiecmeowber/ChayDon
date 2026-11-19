using UnityEngine;

// Short haptic cues via Android's system haptic feedback: no VIBRATE permission, and it follows the user's
// system "touch vibration" setting. Silent in the Editor and on other platforms. Toggle with Haptics.Enabled.
public static class Haptics
{
    const string PrefKey = "haptics_enabled";

    // android.view.HapticFeedbackConstants
    const int LongPress = 0, VirtualKey = 1, Confirm = 16, Reject = 17;  // Confirm/Reject need Android 11 (API 30)

    public static bool Enabled
    {
        get => PlayerPrefs.GetInt(PrefKey, 1) == 1;
        set => PlayerPrefs.SetInt(PrefKey, value ? 1 : 0);
    }

    // Light tick: the turn choice is locked at the commit line.
    public static void ConfirmTick() => Play(SdkInt >= 30 ? Confirm : VirtualKey);

    // Stronger hit: collision.
    public static void Impact() => Play(LongPress);

    // Failure: order cancelled (time out or Q = 0).
    public static void Fail() => Play(SdkInt >= 30 ? Reject : LongPress);

#if UNITY_ANDROID && !UNITY_EDITOR
    static int sdk = -1;
    static int SdkInt
    {
        get
        {
            if (sdk < 0)
                using (var version = new AndroidJavaClass("android.os.Build$VERSION"))
                    sdk = version.GetStatic<int>("SDK_INT");
            return sdk;
        }
    }

    static void Play(int feedback)
    {
        if (!Enabled)
            return;
        using var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
        AndroidJavaObject activity = player.GetStatic<AndroidJavaObject>("currentActivity");
        activity.Call("runOnUiThread", new AndroidJavaRunnable(() =>
        {
            using AndroidJavaObject view = activity.Call<AndroidJavaObject>("getWindow").Call<AndroidJavaObject>("getDecorView");
            view.Call<bool>("performHapticFeedback", feedback);
        }));
    }
#else
    static int SdkInt => 0;
    static void Play(int feedback) { }
#endif
}
