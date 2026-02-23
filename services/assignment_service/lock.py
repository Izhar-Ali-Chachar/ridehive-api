import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

LOCK_EXPIRY = 30

def acquire_lock(driver_id: int):
    key = f"driver:lock:{driver_id}"

    locked = r.set(
        key,
        "lock",
        nx=True,
        ex=LOCK_EXPIRY
    )

    if locked:
        print(f"🔒 Lock acquired: driver {driver_id}")
    else:
        print(f"⛔ Lock failed: driver {driver_id} already locked")

    return bool(locked)

def release_lock(driver_id: int):
    key = f"driver:lock:{driver_id}"

    r.delete(key)
    print(f"🔓 Lock released: driver {driver_id}")

def is_locked(driver_id: int) -> bool:
    key = f"driver:lock:{driver_id}"

    return r.exists(key) == 1