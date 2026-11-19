using UnityEngine;

// Follows a target from behind in the target's heading (yaw only). Fixed horizontal FOV: same road width on every phone aspect.
[ExecuteAlways]
[RequireComponent(typeof(Camera))]
public class ChaseCamera : MonoBehaviour
{
    [Tooltip("Usually a follow anchor on the road center line, not the scooter itself.")]
    public Transform target;
    [Tooltip("Camera position relative to the target, in the target's heading (about 5 m behind).")]
    public Vector3 offset = new Vector3(0f, 3f, -4f);
    [Tooltip("Point the camera looks at, this far ahead of the target.")]
    public float lookAhead = 10f;
    public float lookHeight = 0f;
    [Range(30f, 90f)] public float horizontalFov = 60f;
    [Tooltip("Caps the vertical FOV on very tall screens so the player is not too small (120 = off).")]
    [Range(60f, 120f)] public float maxVerticalFov = 120f;

    Camera cam;
    float shakeLeft, shakeTime, shakeAmount;

    void OnEnable() => cam = GetComponent<Camera>();

    // Short decaying shake (collisions). Only the camera moves; the HUD stays still.
    public void Shake(float amount, float duration)
    {
        shakeAmount = amount;
        shakeTime = shakeLeft = duration;
    }

    void LateUpdate()
    {
        if (target == null)
            return;

        Quaternion heading = Quaternion.Euler(0f, target.eulerAngles.y, 0f);
        transform.position = target.position + heading * offset;
        transform.LookAt(target.position + heading * new Vector3(0f, lookHeight, lookAhead));
        if (Application.isPlaying && shakeLeft > 0f)
        {
            shakeLeft -= Time.deltaTime;
            transform.position += Random.insideUnitSphere * shakeAmount * (shakeLeft / shakeTime);
        }

        float verticalFov = Camera.HorizontalToVerticalFieldOfView(horizontalFov, cam.aspect);
        cam.fieldOfView = Mathf.Min(verticalFov, maxVerticalFov);
    }
}
