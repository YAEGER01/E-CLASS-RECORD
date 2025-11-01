import logging
import hashlib
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, SocketIO
from utils.db_conn import get_db_connection


_socketio: SocketIO | None = None
_logger = logging.getLogger(__name__)


def initialize_live(socketio: SocketIO, logger: logging.Logger | None = None):
    """Provide socketio and optional logger to this module."""
    global _socketio, _logger
    _socketio = socketio
    if logger is not None:
        _logger = logger


def register_socketio_handlers(socketio: SocketIO):
    """Register Socket.IO event handlers. Call this after SocketIO(app) in app.py."""

    @socketio.on("connect")
    def _on_connect():
        emit("connected", {"message": "connected"})

    @socketio.on("disconnect")
    def _on_disconnect():
        # No-op; could add logging if needed
        pass

    @socketio.on("subscribe_live_version")
    def _on_subscribe_live_version(data):
        try:
            class_id = int((data or {}).get("class_id"))
        except Exception:
            emit("error", {"message": "invalid class_id"})
            return
        join_room(f"class-{class_id}")
        version = get_cached_class_live_version(class_id)
        emit("live_version", {"class_id": class_id, "version": version})

    @socketio.on("unsubscribe_live_version")
    def _on_unsubscribe_live_version(data):
        try:
            class_id = int((data or {}).get("class_id"))
        except Exception:
            return
        leave_room(f"class-{class_id}")


def emit_live_version_update(class_id: int):
    """Emit the latest live version for a class to its room."""
    try:
        version = get_cached_class_live_version(class_id)
        if _socketio is not None:
            _socketio.emit(
                "live_version",
                {"class_id": class_id, "version": version},
                room=f"class-{class_id}",
            )
    except Exception as e:
        _logger.error(f"Failed to emit live version for class {class_id}: {str(e)}")


# Simple in-memory cache for normalized structures, keyed by class_id + live version
_NORMALIZED_CACHE = {}
_NORMALIZED_CACHE_MAX = 200  # basic cap to prevent unbounded growth


def _cache_put(key: str, value):
    # Evict oldest if at capacity
    if len(_NORMALIZED_CACHE) >= _NORMALIZED_CACHE_MAX:
        oldest_key = None
        oldest_ts = None
        for k, v in _NORMALIZED_CACHE.items():
            ts = v.get("ts")
            if oldest_ts is None or (ts and ts < oldest_ts):
                oldest_key = k
                oldest_ts = ts
        if oldest_key:
            _NORMALIZED_CACHE.pop(oldest_key, None)

    _NORMALIZED_CACHE[key] = {"data": value, "ts": datetime.now()}


def _cache_get(key: str):
    item = _NORMALIZED_CACHE.get(key)
    return item.get("data") if item else None


# Grouped cache
_GROUPED_CACHE = {}
_GROUPED_CACHE_MAX = 200


def _grouped_cache_put(key: str, value):
    if len(_GROUPED_CACHE) >= _GROUPED_CACHE_MAX:
        oldest_key = None
        oldest_ts = None
        for k, v in _GROUPED_CACHE.items():
            ts = v.get("ts")
            if oldest_ts is None or (ts and ts < oldest_ts):
                oldest_key = k
                oldest_ts = ts
        if oldest_key:
            _GROUPED_CACHE.pop(oldest_key, None)

    _GROUPED_CACHE[key] = {"data": value, "ts": datetime.now()}


def _grouped_cache_get(key: str):
    item = _GROUPED_CACHE.get(key)
    return item.get("data") if item else None


def compute_class_live_version(class_id: int) -> str:
    """Compute the live version hash for a class, matching the API endpoint logic."""
    try:
        with get_db_connection().cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(MAX(updated_at), '1970-01-01 00:00:00') AS max_updated,
                       COALESCE(MAX(version), 0) AS max_version
                FROM grade_structures
                WHERE class_id = %s AND is_active = 1
                """,
                (class_id,),
            )
            gs = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COALESCE(MAX(updated_at), '1970-01-01 00:00:00') AS class_updated
                FROM classes
                WHERE id = %s
                """,
                (class_id,),
            )
            cls = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt, COALESCE(MAX(joined_at), '1970-01-01 00:00:00') AS max_joined
                FROM student_classes
                WHERE class_id = %s
                """,
                (class_id,),
            )
            sc = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COUNT(*) AS cnt, COALESCE(MAX(ss.updated_at), '1970-01-01 00:00:00') AS max_score_updated
                FROM student_scores ss
                WHERE ss.student_id IN (
                    SELECT sc2.student_id FROM student_classes sc2 WHERE sc2.class_id = %s
                )
                """,
                (class_id,),
            )
            ss = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT COALESCE(MAX(pi.updated_at), '1970-01-01 00:00:00') AS max_pi_updated
                FROM personal_info pi
                JOIN students s ON s.personal_info_id = pi.id
                JOIN student_classes sc3 ON sc3.student_id = s.id
                WHERE sc3.class_id = %s
                """,
                (class_id,),
            )
            pi = cursor.fetchone() or {}

        parts = [
            str(gs.get("max_updated")),
            str(gs.get("max_version")),
            str(cls.get("class_updated")),
            str(sc.get("cnt")),
            str(sc.get("max_joined")),
            str(ss.get("cnt")),
            str(ss.get("max_score_updated")),
            str(pi.get("max_pi_updated")),
        ]
        payload = "|".join(parts)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    except Exception as e:
        _logger.error(f"Failed to compute class live version for {class_id}: {str(e)}")
        return ""


# Micro-cache for live-version to reduce DB queries during frequent polling
_LIVE_VERSION_CACHE = {}
_LIVE_VERSION_TTL_SECONDS = 2.0


def get_cached_class_live_version(class_id: int) -> str:
    try:
        now_ts = datetime.now().timestamp()
        entry = _LIVE_VERSION_CACHE.get(class_id)
        if entry and (now_ts - entry.get("ts", 0)) < _LIVE_VERSION_TTL_SECONDS:
            return entry.get("version", "")

        version = compute_class_live_version(class_id)
        _LIVE_VERSION_CACHE[class_id] = {"version": version, "ts": now_ts}
        return version
    except Exception as e:
        _logger.error(f"Live-version micro-cache error for class {class_id}: {str(e)}")
        return compute_class_live_version(class_id)
