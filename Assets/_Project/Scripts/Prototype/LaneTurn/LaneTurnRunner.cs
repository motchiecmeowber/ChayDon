using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

// Prototype: constant-speed scooter, swipe (or A/D, arrow keys) to change lane, lane-based turning:
// left lane at the commit line = turn left, right lane = turn right, otherwise straight. No input during the turn.
// Hits (GDD 4.3): 1.5 s stagger with no further hits, camera shake, cargo integrity (Q%) loss; Q = 0 fails the order.
// Drives the Hud if one is in the scene: timer, Q%, horn (slow scooters ahead move aside), pause.
// Haptics: tick when the turn choice locks, hit on collisions, failure pulse when the order is cancelled.
// Touches that start on a HUD button or at the screen edge never become swipes.
public class LaneTurnRunner : MonoBehaviour
{
    enum Exit { Straight, Left, Right }
    enum State { Running, Turning, Stopped }

    public float speed = 12f;
    public float laneWidth = 3f;
    public float laneChangeTime = 0.18f;
    [Tooltip("Swipe length needed for a lane change, as a fraction of screen width.")]
    public float swipeThreshold = 0.06f;
    public Transform model;
    [Tooltip("Follow point for the camera: road center line, shifted half way toward the lane.")]
    public Transform cameraAnchor;
    public float staggerTime = 1.5f;
    public float orderTime = 120f;

    State state = State.Running;
    Vector3 refPos;          // point on the road center line
    float yaw;               // heading in degrees
    int lane;                // -1 left, 0 middle, 1 right
    float laneX, laneVel;

    TurnJunction junction;   // junction ahead
    bool committed;
    Exit exit;

    // Turn arc
    Vector3 arcPivot, arcFrom, arcFwd;
    float arcAngle, arcRadius, yawStart;
    int arcSign;

    Vector2 pressStart;
    bool swipeUsed;
    string status = "";     // junction status (debug text when there is no HUD)
    string banner = "";     // end-of-order message
    float q = 100f;
    float staggerLeft;
    float timeLeft;
    Hud hud;
    bool paused;

    void Start()
    {
        refPos = transform.position;
        yaw = transform.eulerAngles.y;
        if (model != null)
            model.gameObject.AddComponent<HitRelay>().runner = this;
        timeLeft = orderTime;
        hud = FindFirstObjectByType<Hud>();
        if (hud != null)
        {
            hud.SetAddress("27 Lý Tự Trọng");
            hud.SetCoins(1250);
            hud.horn.Pressed += Honk;
            hud.PausePressed += () => { paused = !paused; Time.timeScale = paused ? 0f : 1f; };
        }
    }

    // Scooters ahead in the player's lane within 20 m move to an adjacent lane.
    void Honk()
    {
        foreach (PrototypeTraffic t in PrototypeTraffic.All)
            if (IsAheadInLane(t.transform.position, 20f))
                t.Evade();
    }

    bool IsAheadInLane(Vector3 position, float range)
    {
        Vector3 v = position - transform.position;
        float d = Vector3.Dot(v, Forward);
        return d > 0f && d < range && Mathf.Abs(Vector3.Dot(v, Right)) < 1.2f;
    }

    // Q% loss per obstacle, matched by prefab name prefix.
    static float DamageFor(string name)
    {
        if (name.StartsWith("OGa")) return 8f;
        if (name.StartsWith("VungNuoc")) return 5f;
        if (name.StartsWith("RaoChan") || name.StartsWith("LoCot")) return 15f;
        if (name.StartsWith("NonGiaoThong")) return 4f;
        if (name.StartsWith("Xe")) return 12f;
        return 0f;
    }

    public void OnHit(string obstacle)
    {
        float damage = DamageFor(obstacle);
        if (damage <= 0f || staggerLeft > 0f || state != State.Running)
            return;
        q = Mathf.Max(0f, q - damage);
        staggerLeft = staggerTime;
        Haptics.Impact();
        var chase = Camera.main != null ? Camera.main.GetComponent<ChaseCamera>() : null;
        if (chase != null)
            chase.Shake(0.25f, 0.35f);
        if (q <= 0f)
        {
            Haptics.Fail();
            Stop("Hàng hỏng, đơn bị hủy!");
        }
    }

    void Stop(string message)
    {
        state = State.Stopped;
        banner = message + " Chạm màn hình hoặc bấm R để chơi lại";
    }

    void Update()
    {
        if (paused)
            return;
        if (state == State.Stopped)
        {
            if (Keyboard.current?.rKey.wasPressedThisFrame == true || Pointer.current?.press.wasPressedThisFrame == true)
                SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
            return;
        }
        timeLeft -= Time.deltaTime;
        if (timeLeft <= 0f)
        {
            Haptics.Fail();
            Stop("Hết giờ, đơn bị hủy!");
            return;
        }
        if (state == State.Running)
        {
            ReadInput();
            Run(Time.deltaTime);
        }
        else
            Turn(Time.deltaTime);

        float prevX = laneX;
        laneX = Mathf.SmoothDamp(laneX, lane * laneWidth, ref laneVel, laneChangeTime);
        ApplyPose((laneX - prevX) / Mathf.Max(Time.deltaTime, 1e-4f));
        UpdateHud();
    }

    void UpdateHud()
    {
        if (hud == null)
            return;
        hud.SetTimer(timeLeft);
        hud.SetQ(q);
        bool blocked = false;
        foreach (PrototypeTraffic t in PrototypeTraffic.All)
            blocked |= IsAheadInLane(t.transform.position, 25f);
        hud.horn.SetHint(blocked);
    }

    void ReadInput()
    {
        int dir = 0;
        var kb = Keyboard.current;
        if (kb != null && (kb.aKey.wasPressedThisFrame || kb.leftArrowKey.wasPressedThisFrame)) dir = -1;
        if (kb != null && (kb.dKey.wasPressedThisFrame || kb.rightArrowKey.wasPressedThisFrame)) dir = 1;

        var pointer = Pointer.current;
        if (pointer != null)
        {
            if (pointer.press.wasPressedThisFrame)
            {
                pressStart = pointer.position.ReadValue();
                swipeUsed = UiPointer.IsOverUi(pressStart) || UiPointer.IsAtEdge(pressStart);  // HUD buttons keep their touch
            }
            else if (pointer.press.isPressed && !swipeUsed)
            {
                float dx = pointer.position.ReadValue().x - pressStart.x;
                if (Mathf.Abs(dx) > swipeThreshold * Screen.width)
                {
                    dir = dx > 0 ? 1 : -1;
                    swipeUsed = true;
                }
            }
        }
        lane = Mathf.Clamp(lane + dir, -1, 1);
    }

    void Run(float dt)
    {
        Vector3 fwd = Forward;
        staggerLeft = Mathf.Max(0f, staggerLeft - dt);
        float slow = staggerLeft > 0f ? Mathf.Lerp(1f, 0.45f, staggerLeft / staggerTime) : 1f;  // dip, then back to full speed
        refPos += fwd * speed * slow * dt;

        if (junction == null)
            junction = FindJunctionAhead();
        if (junction != null)
        {
            float d = Vector3.Dot(junction.Center.position - refPos, fwd);
            if (!committed)
            {
                exit = ExitForLane(junction);
                if (d <= junction.commitDistance)
                {
                    committed = true;
                    Haptics.ConfirmTick();
                }
            }
            status = committed ? $"Đã chốt: {Label(exit)}" : $"Ngã rẽ còn {d:0} m · đang chọn: {Label(exit)}";
            if (d <= junction.turnRadius)
            {
                if (exit == Exit.Straight)
                    ClearJunction();
                else
                    BeginTurn(junction, exit);
            }
        }
        else
            status = "";

        RouteEnd end = FindEndAhead(out float endDistance);
        if (end != null && endDistance <= 0f)
        {
            lane = 1;
            if (end.isDestination)
                Stop("Tới nhà giao!");
            else
            {
                Haptics.Fail();
                Stop("Nhầm địa chỉ!");
            }
        }
    }

    void BeginTurn(TurnJunction j, Exit e)
    {
        state = State.Turning;
        arcSign = e == Exit.Left ? -1 : 1;
        arcRadius = j.turnRadius;
        arcFwd = Forward;
        Vector3 side = Right * arcSign;
        arcFrom = j.Center.position - arcFwd * arcRadius;
        arcFrom.y = refPos.y;
        arcPivot = arcFrom + side * arcRadius;
        arcAngle = 0f;
        yawStart = yaw;
        status = e == Exit.Left ? "Đang rẽ trái" : "Đang rẽ phải";
        ClearJunction();
    }

    // Quarter circle on the center line; the lane offset rides along the new heading.
    void Turn(float dt)
    {
        arcAngle += speed * dt / arcRadius * Mathf.Rad2Deg;
        float a = Mathf.Min(arcAngle, 90f) * Mathf.Deg2Rad;
        Vector3 side = (arcPivot - arcFrom).normalized;
        refPos = arcPivot - side * arcRadius * Mathf.Cos(a) + arcFwd * arcRadius * Mathf.Sin(a);
        yaw = yawStart + arcSign * a * Mathf.Rad2Deg;
        if (arcAngle >= 90f)
        {
            yaw = Mathf.Round(yaw / 90f) * 90f;
            state = State.Running;
            status = "";
        }
    }

    void ApplyPose(float lateralSpeed)
    {
        Quaternion rot = Quaternion.Euler(0f, yaw, 0f);
        transform.SetPositionAndRotation(refPos + rot * Vector3.right * laneX, rot);
        if (model != null)
        {
            float lean = state == State.Turning ? -arcSign * 18f : -lateralSpeed * 2.2f;
            if (staggerLeft > 0f)
                lean += Mathf.Sin(staggerLeft * 28f) * 14f * (staggerLeft / staggerTime);  // wobble
            model.localRotation = Quaternion.Slerp(model.localRotation, Quaternion.Euler(0f, 0f, Mathf.Clamp(lean, -20f, 20f)), 10f * Time.deltaTime);
        }
        if (cameraAnchor != null)
            cameraAnchor.SetPositionAndRotation(refPos + rot * Vector3.right * laneX * 0.5f, rot);
    }

    Exit ExitForLane(TurnJunction j)
    {
        if (lane < 0 && j.HasLeft) return Exit.Left;
        if (lane > 0 && j.HasRight) return Exit.Right;
        return Exit.Straight;
    }

    TurnJunction FindJunctionAhead()
    {
        TurnJunction best = null;
        float bestD = float.MaxValue;
        foreach (TurnJunction j in TurnJunction.All)
        {
            Vector3 v = j.Center.position - refPos;
            float d = Vector3.Dot(v, Forward);
            if (d > j.turnRadius && d < bestD && Mathf.Abs(Vector3.Dot(v, Right)) < 1f)
            {
                best = j;
                bestD = d;
            }
        }
        return best;
    }

    RouteEnd FindEndAhead(out float distance)
    {
        distance = float.MaxValue;
        RouteEnd best = null;
        foreach (RouteEnd e in RouteEnd.All)
        {
            Vector3 v = e.DeliveryPoint.position - refPos;
            float d = Vector3.Dot(v, Forward);
            if (d > -2f && d < distance && Mathf.Abs(Vector3.Dot(v, Right)) < 6f)
            {
                best = e;
                distance = d;
            }
        }
        return best;
    }

    void ClearJunction()
    {
        junction = null;
        committed = false;
    }

    // For the route map: junction ahead, the exit the current lane picks (-1 left, 0 straight, 1 right), lock state.
    public TurnJunction UpcomingJunction => state == State.Running ? junction : null;
    public int PlannedExit => exit == Exit.Left ? -1 : exit == Exit.Right ? 1 : 0;
    public bool Committed => committed;
    public float Heading => yaw;
    public Vector3 RoadPoint => refPos;

    Vector3 Forward => Quaternion.Euler(0f, yaw, 0f) * Vector3.forward;
    Vector3 Right => Quaternion.Euler(0f, yaw, 0f) * Vector3.right;

    static string Label(Exit e) => e == Exit.Left ? "RẼ TRÁI" : e == Exit.Right ? "RẼ PHẢI" : "ĐI THẲNG";

    // Debug text: Q% and junction status only without a HUD; the end-of-order banner always.
    void OnGUI()
    {
        var style = new GUIStyle(GUI.skin.box) { fontSize = Mathf.RoundToInt(Screen.height * 0.022f), fontStyle = FontStyle.Bold, wordWrap = true };
        float w = Screen.width * 0.9f;
        if (hud == null)
        {
            GUI.Box(new Rect(Screen.width * 0.05f, Screen.height * 0.05f, Screen.width * 0.3f, Screen.height * 0.045f), $"Q {q:0}%", style);
            if (!string.IsNullOrEmpty(status))
                GUI.Box(new Rect((Screen.width - w) / 2f, Screen.height * 0.12f, w, Screen.height * 0.05f), status, style);
        }
        if (!string.IsNullOrEmpty(banner))
            GUI.Box(new Rect((Screen.width - w) / 2f, Screen.height * 0.45f, w, Screen.height * 0.07f), banner, style);
    }
}
