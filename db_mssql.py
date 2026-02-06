from __future__ import annotations

import json
from typing import Optional

import pyodbc

from schemas import CallInfo, Metrics


def connect_mssql(conn_str: str) -> pyodbc.Connection:
    return pyodbc.connect(conn_str)


def create_incident(
    conn_str: str,
    *,
    call_id: str,
    language: str,
    info: CallInfo,
    transcript_text: str,
) -> int:
    """
    Writes an incident row and returns incident_id.
    Uses parameterized queries + commit (standard pyodbc pattern). [web:35]
    """
    payload = info.model_dump()
    payload_json = json.dumps(payload, ensure_ascii=False)

    with connect_mssql(conn_str) as cnxn:
        cur = cnxn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.Incidents
                (call_id, language, call_type, incident_type, location, caller_name, confidence_overall, payload_json, transcript_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            call_id,
            language,
            info.call_type,
            info.incident_type,
            info.location,
            info.caller_name,
            float(info.confidence.overall or 0.0),
            payload_json,
            transcript_text,
        )
        cnxn.commit()  # commit required for insert persistence [web:35]
        cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
        row = cur.fetchone()
        return int(row[0])


def write_call_metrics(conn_str: str, metrics: Metrics) -> None:
    with connect_mssql(conn_str) as cnxn:
        cur = cnxn.cursor()
        cur.execute(
            """
            INSERT INTO dbo.CallMetrics
                (call_id, started_at_unix, ended_at_unix, user_turns, agent_turns, stt_final_count, stt_interim_count,
                extraction_updates, incident_created, incident_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            metrics.call_id,
            float(metrics.started_at_unix),
            float(metrics.ended_at_unix) if metrics.ended_at_unix is not None else None,
            int(metrics.user_turns),
            int(metrics.agent_turns),
            int(metrics.stt_final_count),
            int(metrics.stt_interim_count),
            int(metrics.extraction_updates),
            1 if metrics.incident_created else 0,
            int(metrics.incident_id) if metrics.incident_id is not None else None,
        )
        cnxn.commit()