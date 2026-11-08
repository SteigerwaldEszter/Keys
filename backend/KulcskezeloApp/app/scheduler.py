import threading

_lock = threading.Lock()
_started = False


def _loop(app, interval):
    from app.blueprints.keys.deadlines import run_sweep
    from app.extensions import db

    stop = threading.Event()

    while not stop.wait(interval):
        with app.app_context():
            try:
                run_sweep()
            except Exception:
                db.session.rollback()
                app.logger.exception("Kulcs-határidők ellenőrzése sikertelen")
            finally:
                db.session.remove()

    stop.wait(interval)


def start_deadline_scheduler(app):
    global _started

    if not app.config.get("DEADLINE_SWEEP_ENABLED", True):
        return False

    with _lock:
        if _started:
            return False
        _started = True

    interval = max(int(app.config.get("DEADLINE_SWEEP_SECONDS", 60)), 5)
    threading.Thread(
        target=_loop,
        args=(app, interval),
        name="key-deadline-sweep",
        daemon=True,
    ).start()
    return True
