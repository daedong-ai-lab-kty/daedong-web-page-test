# -*- coding: utf-8 -*-
import os
import json
import hashlib
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from tqdm import tqdm
import time

# Embedding backend
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

# Optional OpenAI embeddings
try:
    import openai
except Exception:
    openai = None

# Optional FAISS
try:
    import faiss
    _FAISS_AVAILABLE = True
except Exception:
    _FAISS_AVAILABLE = False

# Optional YAML support for per-person user_config.yaml
try:
    import yaml
except Exception:
    yaml = None  # fall back to JSON if yaml not available


def _sanitize_person(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("_", "-")).strip() or "person"

def _make_id(date: str, time_str: str, content: str) -> str:
    h = hashlib.sha1()
    h.update(f"{date}||{time_str}||{content}".encode("utf-8"))
    return h.hexdigest()

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

class FarmingLanceDBManager:
    def __init__(self, root_dir: str = "lancedb_data",
                 sqlite_db_path: Optional[str] = None,
                 embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 use_openai: bool = False):
        self.root = Path(root_dir)
        _ensure_dir(self.root)
        self.use_openai = use_openai
        self.embedding_model_name = embedding_model_name

        if use_openai and openai is None:
            raise RuntimeError("openai package not available but use_openai=True")

        # Threading lock for sqlite usage
        self._sqlite_lock = threading.RLock()

        print('Farming DB root:', self.root)

        # sqlite metadata DB
        if sqlite_db_path:
            self.sqlite_path = Path(sqlite_db_path)
        else:
            self.sqlite_path = self.root / "metadata.db"
        self._init_sqlite()
        # Ensure required columns (pid, person_name) exist
        self._ensure_table_columns()

    # -----------------------
    # SQLite init & schema utilities
    # -----------------------
    def _init_sqlite(self):
        # allow usage from multiple threads (we'll serialize access with a lock)
        self.conn = sqlite3.connect(str(self.sqlite_path), check_same_thread=False)
        try:
            cur = self.conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass

        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS processed_files (
            filepath TEXT PRIMARY KEY,
            mtime REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY,
            person TEXT,
            date TEXT,
            time TEXT,
            content TEXT,
            filepath TEXT,
            mtime REAL
        )""")
        self.conn.commit()

    def _get_existing_columns(self, table_name: str) -> List[str]:
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute(f"PRAGMA table_info('{table_name}')")
            rows = cur.fetchall()
        return [row[1] for row in rows]  # name is at index 1

    def _ensure_table_columns(self):
        """
        Ensure 'records' table has pid and person_name columns.
        If they are missing, ALTER TABLE to add them.
        """
        desired_cols = {
            "pid": "TEXT",
            "person_name": "TEXT"
        }
        existing = self._get_existing_columns("records")
        with self._sqlite_lock:
            cur = self.conn.cursor()
            for col, col_type in desired_cols.items():
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE records ADD COLUMN {col} {col_type};")
                        print(f"Added column '{col}' to records table.")
                    except Exception as e:
                        print(f"Warning: failed to add column {col}: {e}")
            self.conn.commit()

    # -----------------------
    # Person folder parsing
    # -----------------------
    def _split_person_folder(self, folder_name: str) -> Tuple[str, str]:
        """
        Parse folder names of the form "id_name" into (pid, person_name).
        If folder_name doesn't contain an underscore, pid='' and person_name is folder_name.
        """
        if not folder_name:
            return ("", "")
        folder_name = folder_name.strip()
        if "_" in folder_name:
            pid, name = folder_name.split("_", 1)
            return (pid.strip(), name.strip())
        else:
            return ("", folder_name)

    # -----------------------
    # File path helpers (per-person storage)
    # -----------------------
    def _person_dir(self, person: str) -> Path:
        name = _sanitize_person(person)
        return self.root / name

    def _meta_path(self, person: str) -> Path:
        return self._person_dir(person) / "meta.json"

    def _records_path(self, person: str) -> Path:
        return self._person_dir(person) / "records.jsonl"

    def _embeddings_path(self, person: str) -> Path:
        return self._person_dir(person) / "embeddings.npy"

    def _ids_path(self, person: str) -> Path:
        return self._person_dir(person) / "ids.json"

    def _faiss_path(self, person: str) -> Path:
        return self._person_dir(person) / "faiss.index"

    # -----------------------
    # Per-person user_config.yaml helpers
    # -----------------------
    def _user_config_path(self, person: str) -> Path:
        """
        Return the path for per-person user_config.yaml inside the person's folder.
        """
        return self._person_dir(person) / "user_config.yaml"

    def load_user_config(self, person: str) -> Optional[Dict[str, Any]]:
        """
        Load per-person user_config.yaml (or fall back to meta.json's 'user' key).
        Returns dict with user fields or None if not found/parse error.
        """
        u_path = self._user_config_path(person)
        if u_path.exists():
            try:
                raw = u_path.read_text(encoding="utf-8")
                if yaml:
                    data = yaml.safe_load(raw) or {}
                else:
                    # fallback to JSON parsing
                    data = json.loads(raw) if raw.strip() else {}
                # Accept either top-level 'user' or flat fields
                if isinstance(data, dict):
                    if "user" in data and isinstance(data["user"], dict):
                        return data["user"]
                    # if file itself is flat user dict
                    # normalize to expected keys
                    user_keys = {k: data.get(k) for k in ("id", "name", "email", "farm_id", "location", "location_name") if k in data}
                    if user_keys:
                        return user_keys
                return None
            except Exception as e:
                print(f"[load_user_config] failed to parse {u_path}: {e}")
                return None
        # fallback: try reading meta.json 'user' key
        mpath = self._meta_path(person)
        if mpath.exists():
            try:
                raw = mpath.read_text(encoding="utf-8")
                meta = json.loads(raw) if raw.strip() else {}
                if isinstance(meta, dict) and "user" in meta and isinstance(meta["user"], dict):
                    return meta["user"]
            except Exception:
                pass
        return None

    def save_user_config(self, person: str, user_dict: Dict[str, Any]) -> bool:
        """
        Save provided user_dict into person's user_config.yaml.
        If yaml module available, write YAML; else write JSON.
        Returns True on success.
        """
        u_path = self._user_config_path(person)
        _ensure_dir(u_path.parent)
        # Normalize simple types (avoid non-serializable objects)
        to_write = {"user": {
            "id": user_dict.get("id"),
            "name": user_dict.get("name"),
            "email": user_dict.get("email"),
            "farm_id": user_dict.get("farm_id"),
            "location": user_dict.get("location"),
            "location_name": user_dict.get("location_name"),
        }}
        try:
            if yaml:
                # allow_unicode to keep non-ascii names
                u_path.write_text(yaml.safe_dump(to_write, sort_keys=False, allow_unicode=True), encoding="utf-8")
            else:
                u_path.write_text(json.dumps(to_write, ensure_ascii=False, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            print(f"[save_user_config] failed to write {u_path}: {e}")
            return False

    def get_person_user_info(self, person: str) -> Dict[str, Any]:
        """
        Higher-level accessor that returns a normalized user dict for a person.
        It prefers per-person user_config.yaml, then meta.json, then returns an empty dict.
        """
        u = self.load_user_config(person)
        if u:
            # ensure keys exist
            return {
                "id": u.get("id"),
                "name": u.get("name"),
                "email": u.get("email"),
                "farm_id": u.get("farm_id"),
                "location": u.get("location"),
                "location_name": u.get("location_name"),
            }
        # fallback: return minimal skeleton
        return {"id": None, "name": None, "email": None, "farm_id": None, "location": None, "location_name": None}

    # -----------------------
    # Meta / embeddings
    # -----------------------
    def _load_meta(self, person: str) -> Dict[str, Any]:
        p = self._meta_path(person)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                return {"count": 0}
        return {"count": 0}

    def _save_meta(self, person: str, meta: Dict[str, Any]):
        p = self._meta_path(person)
        p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _compute_embeddings(self, texts: List[str]) -> np.ndarray:
        if self.use_openai:
            resp = openai.Embedding.create(input=texts, model="text-embedding-3-small")
            embs = [r["embedding"] for r in resp["data"]]
            arr = np.array(embs, dtype=np.float32)
            norm = np.linalg.norm(arr, axis=1, keepdims=True)
            norm[norm == 0] = 1.0
            return arr / norm
        else:
            if not hasattr(self, "embed_model") or self.embed_model is None:
                return np.zeros((len(texts), 1), dtype=np.float32)
            arr = self.embed_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            norm = np.linalg.norm(arr, axis=1, keepdims=True)
            norm[norm == 0] = 1.0
            return (arr / norm).astype(np.float32)

    # -----------------------
    # Upsert / storage
    # -----------------------
    def upsert(self, person: str, records: List[Dict[str, Any]]):
        pdir = self._person_dir(person)
        _ensure_dir(pdir)
        records_path = self._records_path(person)
        ids_path = self._ids_path(person)
        emb_path = self._embeddings_path(person)

        existing = {}
        if records_path.exists():
            with records_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    existing[obj["id"]] = obj

        for r in records:
            rid = r.get("id") or _make_id(r.get("date", ""), r.get("time", ""), r.get("content", ""))
            r["id"] = rid
            existing[rid] = r

        all_ids = list(existing.keys())
        all_texts = [existing[_id].get("content", "") for _id in all_ids]
        if all_texts:
            all_embs = self._compute_embeddings(all_texts)
        else:
            all_embs = np.zeros((0, 1), dtype=np.float32)

        with records_path.open("w", encoding="utf-8") as f:
            for _id in all_ids:
                f.write(json.dumps(existing[_id], ensure_ascii=False) + "\n")

        ids_path.write_text(json.dumps(all_ids, ensure_ascii=False), encoding="utf-8")
        np.save(str(emb_path), all_embs)

        if _FAISS_AVAILABLE and all_embs.shape[0] > 0:
            dim = all_embs.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(all_embs)
            faiss.write_index(index, str(self._faiss_path(person)))
        else:
            fpath = self._faiss_path(person)
            if fpath.exists():
                try:
                    fpath.unlink()
                except Exception:
                    pass

        meta = {"count": len(all_ids)}
        self._save_meta(person, meta)

    def list_persons(self) -> List[str]:
        return [p.name for p in self.root.iterdir() if p.is_dir()]

    def get_by_person(self, person: str) -> List[Dict[str, Any]]:
        records_path = self._records_path(person)
        out = []
        if records_path.exists():
            with records_path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        out.append(json.loads(line))
        return out

    def query_by_text(self, person: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        ids_path = self._ids_path(person)
        emb_path = self._embeddings_path(person)
        if not ids_path.exists() or not emb_path.exists():
            return []

        ids = json.loads(ids_path.read_text(encoding="utf-8"))
        embs = np.load(str(emb_path))
        q_emb = self._compute_embeddings([text])[0:1]

        if _FAISS_AVAILABLE and self._faiss_path(person).exists():
            index = faiss.read_index(str(self._faiss_path(person)))
            D, I = index.search(q_emb, min(top_k, embs.shape[0]))
            hits = []
            for idx in I[0]:
                if idx < 0 or idx >= len(ids):
                    continue
                rid = ids[idx]
                hits.append((rid, float(D[0][idx])))
        else:
            sims = (embs @ q_emb.T).reshape(-1)
            top_idx = np.argsort(-sims)[:top_k]
            hits = [(ids[int(i)], float(sims[int(i)])) for i in top_idx]

        all_records = {r["id"]: r for r in self.get_by_person(person)}
        out = []
        for rid, score in hits:
            rec = all_records.get(rid)
            if rec:
                rec_copy = dict(rec)
                rec_copy["_score"] = score
                out.append(rec_copy)
        return out

    # -----------------------
    # SQLite helper methods
    # -----------------------
    def _get_file_mtime(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except Exception:
            return 0.0

    def _is_file_processed(self, filepath: str, mtime: float) -> bool:
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute("SELECT mtime FROM processed_files WHERE filepath = ?", (filepath,))
            row = cur.fetchone()
            if not row:
                return False
            return float(row[0]) >= float(mtime)

    def _mark_file_processed(self, filepath: str, mtime: float):
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute("REPLACE INTO processed_files(filepath, mtime) VALUES (?, ?)", (filepath, float(mtime)))
            self.conn.commit()

    def _upsert_record_sqlite(self, rec: Dict[str, Any], filepath: str, mtime: float):
        """
        Upsert record into sqlite 'records' table. This will include pid and person_name
        if those columns exist in the table.
        """
        with self._sqlite_lock:
            existing_cols = self._get_existing_columns("records")
            cols = ["id", "person", "date", "time", "content", "filepath", "mtime"]
            vals = [
                rec["id"],
                rec.get("person", ""),
                rec.get("date", ""),
                rec.get("time", ""),
                rec.get("content", ""),
                filepath,
                float(mtime)
            ]
            if "pid" in existing_cols:
                cols.append("pid")
                vals.append(rec.get("pid", ""))
            if "person_name" in existing_cols:
                cols.append("person_name")
                vals.append(rec.get("person_name", ""))

            placeholders = ",".join("?" for _ in cols)
            cols_sql = ",".join(cols)
            sql = f"REPLACE INTO records({cols_sql}) VALUES ({placeholders})"
            cur = self.conn.cursor()
            cur.execute(sql, tuple(vals))
            self.conn.commit()

    def sql_query(self, sql: str, params: tuple = ()):
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchall()
        out = [dict(zip(cols, r)) for r in rows]
        return out

    def list_tables(self) -> List[str]:
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            rows = cur.fetchall()
        return [r[0] for r in rows]

    def dump_all_tables(self) -> Dict[str, List[Dict[str, Any]]]:
        out: Dict[str, List[Dict[str, Any]]] = {}
        tables = self.list_tables()
        with self._sqlite_lock:
            cur = self.conn.cursor()
            for table in tables:
                cur.execute(f"PRAGMA table_info('{table}')")
                cols_info = cur.fetchall()
                cols = [c[1] for c in cols_info] if cols_info else []
                cur.execute(f"SELECT * FROM '{table}'")
                rows = cur.fetchall()
                out[table] = [dict(zip(cols, r)) for r in rows]
        return out

    def print_all_tables(self):
        data = self.dump_all_tables()
        for table, rows in data.items():
            print("=" * 40)
            print(f"TABLE: {table} (rows: {len(rows)})")
            if rows:
                cols = list(rows[0].keys())
                print(" | ".join(cols))
                for r in rows:
                    vals = [str(r.get(c, "")) for c in cols]
                    print(" | ".join(vals))
            else:
                print("(empty)")
        print("=" * 40)

    # -----------------------
    # JSON normalization helper (moved inside class to avoid NameError)
    # -----------------------
    def _extract_entries_from_json(self, data) -> List[Dict[str, Any]]:
        """
        Normalize multiple possible JSON layouts into a list of entry dicts
        where each entry is expected to have keys like 'date','time','content'.
        """
        out: List[Dict[str, Any]] = []
        if isinstance(data, dict):
            val = data.get("farming_work_log")
            if isinstance(val, list):
                out.extend([v for v in val if isinstance(v, dict)])
            elif isinstance(val, dict):
                out.append(val)
            else:
                if "content" in data or "date" in data:
                    out.append(data)
            if not out:
                for k, v in data.items():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        candidate = [item for item in v if isinstance(item, dict)]
                        if candidate:
                            out.extend(candidate)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if "farming_work_log" in item:
                        fw = item.get("farming_work_log")
                        if isinstance(fw, list):
                            out.extend([v for v in fw if isinstance(v, dict)])
                        elif isinstance(fw, dict):
                            out.append(fw)
                    else:
                        if "content" in item or "date" in item or "time" in item:
                            out.append(item)
        return out

    # -----------------------
    # Ingest from server (robust JSON shapes)
    # -----------------------
    def ingest_from_server(self, server_root: str, person_dir_pattern: Optional[str] = None):
        sroot = Path(server_root)
        if not sroot.exists():
            raise FileNotFoundError(f"{server_root} not found")

        for p in sroot.iterdir():
            if not p.is_dir():
                continue
            pname = p.name
            if person_dir_pattern and person_dir_pattern not in pname:
                continue

            pid, person_name = self._split_person_folder(pname)
            person_folder_identifier = pname
            collected_records = []
            for jf in p.rglob("*.json"):
                jpath = str(jf.resolve())
                mtime = self._get_file_mtime(jf)
                try:
                    if self._is_file_processed(jpath, mtime):
                        continue
                except Exception as e:
                    print("Warning: _is_file_processed error:", e)

                try:
                    raw = jf.read_text(encoding="utf-8")
                    data = json.loads(raw)
                except Exception as e:
                    print(f"Warning: failed to parse JSON file {jpath}: {e}")
                    continue

                try:
                    entries = self._extract_entries_from_json(data)
                except Exception as e:
                    print(f"Warning: error while extracting entries from {jpath}: {e}")
                    entries = []

                if not isinstance(entries, list):
                    if isinstance(entries, dict):
                        entries = [entries]
                    else:
                        entries = []

                if not entries:
                    try:
                        self._mark_file_processed(jpath, mtime)
                    except Exception as e:
                        print("Warning: _mark_file_processed error on empty file:", e)
                    continue

                for e in entries:
                    if not isinstance(e, dict):
                        continue
                    date = e.get("date", "")
                    time_str = e.get("time", "")
                    content = e.get("content", "")
                    if not content and not date:
                        continue
                    rid = _make_id(date, time_str, content)
                    rec = {
                        "id": rid,
                        "date": date,
                        "time": time_str,
                        "content": content,
                        "person": person_folder_identifier,
                        "pid": pid,
                        "person_name": person_name
                    }
                    collected_records.append((rec, jpath, mtime))

                try:
                    self._mark_file_processed(jpath, mtime)
                except Exception as e:
                    print("Warning: _mark_file_processed error:", e)

            if collected_records:
                recs_only = [r for (r, _, _) in collected_records]
                self.upsert(person_folder_identifier, recs_only)
                for rec, filepath, mtime in collected_records:
                    try:
                        self._upsert_record_sqlite(rec, filepath, mtime)
                    except Exception as e:
                        print("Warning: _upsert_record_sqlite error:", e)

    def delete_person(self, person: str):
        pdir = self._person_dir(person)
        if pdir.exists() and pdir.is_dir():
            for f in pdir.iterdir():
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                pdir.rmdir()
            except Exception:
                pass
        with self._sqlite_lock:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM records WHERE person = ?", (person,))
            self.conn.commit()
            
    def add_entry_and_persist(self, person_folder_identifier: str, entry: Dict[str, Any], target_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Append `entry` to a JSON file under the person's folder and persist.
        Returns a dict: {"rec": rec, "file": str(path), "ok": True/False, "error": str or None}
        Behavior change: if log_{date}.json doesn't exist, DO NOT pick arbitrary existing json (like ids.json).
        Instead create log_{date}.json (or pick an existing log_{date}* file).
        """
        person_folder = self.root / person_folder_identifier
        _ensure_dir(person_folder)
        print(f"[add_entry_and_persist] person_folder: {person_folder}")

        date_str = entry.get("date") or time.strftime("%Y-%m-%d")
        # if explicit target_filename given, use it
        if target_filename:
            jf = person_folder / target_filename
        else:
            # prefer exact date-named log file
            cand = person_folder / f"log_{date_str}.json"
            if cand.exists():
                jf = cand
            else:
                # look for any other files that are clearly log files for that date (e.g. log_2023-09-25_v1.json)
                pattern = f"log_{date_str}*.json"
                log_candidates = sorted(person_folder.glob(pattern))
                if log_candidates:
                    jf = log_candidates[0]
                else:
                    # No existing log file for that date -> create new log_{date}.json
                    jf = cand

        print(f"[add_entry_and_persist] target file chosen: {jf}")

        # load existing JSON robustly
        data = None
        if jf.exists():
            try:
                raw = jf.read_text(encoding="utf-8")
                data = json.loads(raw)
            except Exception as e:
                err = f"Failed to parse existing JSON {jf}: {e}"
                print(f"[add_entry_and_persist] {err}")
                data = None

        # normalize and append
        if isinstance(data, dict):
            if "farming_work_log" in data and isinstance(data["farming_work_log"], list):
                data["farming_work_log"].append(entry)
            else:
                data["farming_work_log"] = data.get("farming_work_log", [])
                if not isinstance(data["farming_work_log"], list):
                    data["farming_work_log"] = []
                data["farming_work_log"].append(entry)
        elif isinstance(data, list):
            data.append(entry)
        else:
            data = {"farming_work_log": [entry]}

        # atomic write: write to tmp then replace
        try:
            tmp = jf.with_suffix(jf.suffix + ".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(jf)
        except Exception as e:
            try:
                jf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e2:
                err_msg = f"Failed to write JSON file {jf}: {e2}"
                print(f"[add_entry_and_persist] {err_msg}")
                return {"rec": None, "file": str(jf), "ok": False, "error": err_msg}

        # refresh mtime
        mtime = self._get_file_mtime(jf)

        # build record
        pid, person_name = self._split_person_folder(person_folder_identifier)
        rid = entry.get("id") or _make_id(entry.get("date", ""), entry.get("time", ""), entry.get("content", ""))
        rec = {
            "id": rid,
            "date": entry.get("date", ""),
            "time": entry.get("time", ""),
            "content": entry.get("content", ""),
            "person": person_folder_identifier,
            "pid": pid,
            "person_name": person_name
        }

        # persist: upsert per-person storage and sqlite index
        try:
            self.upsert(person_folder_identifier, [rec])
        except Exception as e:
            print(f"[add_entry_and_persist] Warning: upsert failed: {e}")

        try:
            self._upsert_record_sqlite(rec, str(jf), mtime)
        except Exception as e:
            print(f"[add_entry_and_persist] Warning: _upsert_record_sqlite failed: {e}")

        try:
            self._mark_file_processed(str(jf), mtime)
        except Exception as e:
            print(f"[add_entry_and_persist] Warning: _mark_file_processed failed: {e}")

        print(f"[add_entry_and_persist] success: wrote to {jf}")
        return {"rec": rec, "file": str(jf), "ok": True, "error": None}