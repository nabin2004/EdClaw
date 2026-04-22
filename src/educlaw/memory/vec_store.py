"""Vector storage: sqlite-vec when available; else pure-Python cosine fallback."""

from __future__ import annotations

import math
import sqlite3
import struct
from collections.abc import Sequence
from pathlib import Path


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class VecStore:
    def __init__(self, path: Path, dim: int) -> None:
        self.path = path
        self.dim = dim
        self._db = sqlite3.connect(str(path))
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS vec_meta ("
            "rowid INTEGER PRIMARY KEY, key TEXT UNIQUE, payload TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS vec_fallback (rowid INTEGER PRIMARY KEY, embedding BLOB)"
        )
        self._has_sqlite_vec = False
        try:
            self._db.enable_load_extension(True)  # type: ignore[attr-defined]
            import sqlite_vec  # noqa: PLC0415

            sqlite_vec.load(self._db)
            self._has_sqlite_vec = True
            self._db.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS vec USING vec0(embedding float[{dim}])"
            )
        except Exception:
            self._has_sqlite_vec = False
        self._db.commit()
        self._fallback_vectors: dict[int, list[float]] = {}
        self._rowid_by_key: dict[str, int] = {}

    def upsert(self, key: str, vec: Sequence[float], payload: str) -> None:
        self._db.execute(
            "INSERT INTO vec_meta(key, payload) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET payload=excluded.payload",
            (key, payload),
        )
        row = self._db.execute("SELECT rowid FROM vec_meta WHERE key=?", (key,)).fetchone()
        if not row:
            return
        rowid = row[0]
        blob = struct.pack(f"{self.dim}f", *vec)
        if self._has_sqlite_vec:
            self._db.execute(
                "INSERT OR REPLACE INTO vec(rowid, embedding) VALUES(?, ?)",
                (rowid, blob),
            )
        else:
            self._db.execute(
                "INSERT OR REPLACE INTO vec_fallback(rowid, embedding) VALUES(?,?)", (rowid, blob)
            )
            self._fallback_vectors[rowid] = list(vec)
        self._rowid_by_key[key] = rowid
        self._db.commit()

    def top_k(self, query_vec: Sequence[float], k: int = 8) -> list[tuple[str, str, float]]:
        if self._has_sqlite_vec:
            blob = struct.pack(f"{self.dim}f", *query_vec)
            rows = self._db.execute(
                "SELECT vec_meta.key, vec_meta.payload, distance "
                "FROM vec JOIN vec_meta USING(rowid) "
                "WHERE embedding MATCH ? ORDER BY distance LIMIT ?",
                (blob, k),
            ).fetchall()
            return [(r[0], r[1], float(r[2])) for r in rows]

        scores: list[tuple[str, str, float]] = []
        q = list(query_vec)
        for rowid, key, payload in self._db.execute(
            "SELECT vm.rowid, vm.key, vm.payload FROM vec_meta vm JOIN vec_fallback vf USING(rowid)"
        ):
            emb = self._db.execute(
                "SELECT embedding FROM vec_fallback WHERE rowid=?", (rowid,)
            ).fetchone()
            if not emb:
                continue
            vec = struct.unpack(f"{self.dim}f", emb[0])
            sim = _cosine(q, vec)
            scores.append((key, payload, -sim))
        scores.sort(key=lambda x: x[2])
        return scores[:k]
