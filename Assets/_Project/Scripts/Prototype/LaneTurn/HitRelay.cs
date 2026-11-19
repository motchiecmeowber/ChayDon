using UnityEngine;

// Prototype: sits on the scooter model (which owns the trigger and Rigidbody) and forwards hits to the runner.
public class HitRelay : MonoBehaviour
{
    public LaneTurnRunner runner;

    void OnTriggerEnter(Collider other)
    {
        if (runner != null)
            runner.OnHit(other.gameObject.name);
    }
}
