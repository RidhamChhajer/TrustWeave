"""Latest current-session metadata, with no message access."""


def raw_snapshot(connection):
    result = {}
    for record in connection.metrics.collector.measurements:
        if record.session_id != connection.info.session_id or record.raw_value is None:
            continue
        value = record.raw_value
        if record.signal_name == "handshake_latency_ms":
            result["handshake_ms"] = value
        elif record.signal_name == "rtt":
            result.update(rtt_ms=value["latest_ms"], variation_ms=value["variation_ms"])
        elif record.signal_name == "communication_timing" and value["direction"] == "sent":
            result["timing_ms"] = value["interval_ms"]
        elif record.signal_name == "session_continuity":
            result["peer_ip"] = value["peer_ip"]
        elif record.signal_name == "session_establishments":
            result["establishments"] = value["count"]
    return result
