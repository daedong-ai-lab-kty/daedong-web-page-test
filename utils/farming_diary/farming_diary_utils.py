from typing import List, Dict, Tuple, Any, Optional
import os, glob

def _person_condition(person: Optional[str]) -> Tuple[str, Tuple[Any, ...]]:
    """
    Build a SQL condition and params to match a person value.
    We accept three possible ways to identify a person:
      - folder identifier: '1_taeyong' (matches records.person)
      - pid: '1' (matches records.pid)
      - person_name: 'taeyong' (matches records.person_name)

    If person is falsy (None or empty), returns a no-op condition ("1=1") and empty params.
    """
    if not person:
        return "1=1", tuple()

    # We'll match against person (folder), pid and person_name.
    # This is simple and flexible: the same input will be tried in all three columns.
    cond = "(person = ? OR pid = ? OR person_name = ?)"
    params = (person, person, person)
    return cond, params

def get_persons(db):
    # print("Persons:", db.list_persons())
    return db.list_persons()

# def get_all_works_date(db, person, date):
#     # SQL query: get all records for a person on a date
#     # person = "ID_kim"  # 예시: 실제 폴더명이 "ID_kim"이면 이 값을 사용
#     # date = "2023-09-22"
#     rows = db.sql_query("SELECT * FROM records WHERE person = ? AND date = ? ORDER BY mtime ASC", (person, date))
#     print(f"SQL query: records for {person} on {date}:")
#     for r in rows:
#         print(r)

def get_all_works_date(db, person: Optional[str], date: str) -> List[Dict[str, Any]]:
    """
    Return all records for a given person (folder/pid/person_name) on a given date.
    - person: can be '1_taeyong' or '1' or 'taeyong'. If None/'' then search across all persons.
    - date: exact match, e.g. '2023-09-22'

    Returns list of rows (dicts). Also prints a short debug log.
    """
    cond, params = _person_condition(person)
    sql = f"SELECT * FROM records WHERE {cond} AND date = ? ORDER BY mtime ASC"
    query_params = params + (date,)
    rows = db.sql_query(sql, query_params)
    # print(f"SQL query: records for {person!r} on {date}:")
    # if rows:
    #     for r in rows:
    #         print(r)
    # else:
    #     print(" - Works: None")
    return rows

def get_search_works(db, person, target):
    # Full-text-ish SQL query (LIKE)
    rows = db.sql_query(f"SELECT * FROM records WHERE content LIKE ? LIMIT 10", ("%{target}%",))
    print(f"SQL LIKE search for '{target}':")
    for r in rows:
        print(r)

# def get_search_works(db, person, target):
#     # Semantic search using embeddings (per-person)
#     q = "배지 소독 내역"
#     hits = db.query_by_text(person, q, top_k=5)
#     print("Semantic search results:")
#     for h in hits:
#         print(h)

# def add_work(db, folder, date, time, content):
#     new_entry = {"date": date, "time": time, "content": content}
#     rec = db.add_entry_and_persist(folder, new_entry)  
#     print("Inserted record:", rec)

def add_work(db, person_identifier: str, date: str, time_str: str, content: str, target_filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a work entry and return details including actual written file path.
    """
    persons = db.list_persons()
    resolved = None
    if person_identifier in persons:
        resolved = person_identifier
    else:
        for p in persons:
            if "_" in p:
                pid, name = p.split("_", 1)
            else:
                pid, name = "", p
            if person_identifier == pid or person_identifier == name:
                resolved = p
                break
    if resolved is None:
        resolved = person_identifier

    entry = {"date": date, "time": time_str, "content": content}
    try:
        result = db.add_entry_and_persist(resolved, entry, target_filename=target_filename)
        print(f"[add_work] add_entry_and_persist returned: {result}")
        # if result['ok']==False, bubble up or return
        return result
    except Exception as e:
        print(f"[add_work] add_entry failed: {e}")
        return {"rec": None, "file": None, "ok": False, "error": str(e)}
    
def delete_works_by_date(db, person_identifier: str, date: str) -> Dict[str, Any]:
    """
    해당 사람(person_identifier)의 특정 날짜(date)에 대한 일지를 모두 삭제.
    순서:
      1) DB(records)에서 (person, date)로 filepath들을 DISTINCT 조회
      2) 조회된 실제 파일 경로들을 우선 삭제
      3) 보조로 log_{date}*.json 패턴도 한번 더 스윕
      4) sqlite records/processed_files에서 해당 항목 삭제
      5) 남은 레코드로 per-person 저장/임베딩 재구성
    """
    # 0) 사람 식별자 정규화
    persons = db.list_persons()
    resolved = None
    if person_identifier in persons:
        resolved = person_identifier
    else:
        for p in persons:
            if "_" in p:
                pid, name = p.split("_", 1)
            else:
                pid, name = "", p
            if person_identifier == pid or person_identifier == name:
                resolved = p
                break
    if resolved is None:
        resolved = person_identifier

    deleted_files: List[str] = []
    errors: List[str] = []

    # 1) DB에서 해당 (person, date)의 파일 경로 목록 확보
    try:
        fp_rows = db.sql_query("SELECT DISTINCT filepath FROM records WHERE person = ? AND date = ?", (resolved, date))
        filepaths = []
        for r in fp_rows:
            # r은 dict로 가정
            fp = r.get("filepath")
            if fp:
                filepaths.append(fp)
        print(f"[delete_works_by_date] DB filepaths for ({resolved}, {date}): {filepaths}")
    except Exception as e:
        errors.append(f"filepath query failed: {e}")
        filepaths = []

    # 2) DB가 알려준 실제 파일들 우선 삭제
    for fp in set(filepaths):
        try:
            if os.path.exists(fp):
                os.remove(fp)
                deleted_files.append(fp)
                print(f"[delete_works_by_date] removed file: {fp}")
            else:
                print(f"[delete_works_by_date] file not found (skip): {fp}")
        except Exception as e:
            msg = f"failed to remove {fp}: {e}"
            print(f"[delete_works_by_date] {msg}")
            errors.append(msg)

    # 3) 보조: 패턴 기반 삭제(log_{date}*.json)
    try:
        # 가장 정확한 사람 폴더 경로를 사용
        if hasattr(db, "_person_dir") and callable(getattr(db, "_person_dir")):
            person_dir: Path = db._person_dir(resolved)
        else:
            from pathlib import Path as _Path
            person_dir = _Path(getattr(db, "root")) / resolved  # fallback
        pattern = str(person_dir / f"log_{date}*.json")
        extras = glob.glob(pattern)
        print(f"[delete_works_by_date] pattern scan: {pattern} -> {extras}")
        for f in extras:
            try:
                if os.path.exists(f):
                    os.remove(f)
                    deleted_files.append(f)
                    print(f"[delete_works_by_date] removed (pattern): {f}")
            except Exception as e:
                msg = f"failed to remove(pattern) {f}: {e}"
                print(f"[delete_works_by_date] {msg}")
                errors.append(msg)
    except Exception as e:
        errors.append(f"pattern cleanup error: {e}")

    # 4) sqlite 정리 (records + processed_files)
    try:
        conn = getattr(db, "conn", None)
        lock = getattr(db, "_sqlite_lock", None)
        def _do_delete_sqlite():
            cur = conn.cursor()
            # records 삭제
            cur.execute("DELETE FROM records WHERE person = ? AND date = ?", (resolved, date))
            # processed_files에서도 지운 파일 경로 제거
            for fp in set(filepaths + extras if 'extras' in locals() else filepaths):
                cur.execute("DELETE FROM processed_files WHERE filepath = ?", (fp,))
            conn.commit()
        if conn is not None and lock is not None:
            with lock:
                _do_delete_sqlite()
        elif conn is not None:
            _do_delete_sqlite()
        else:
            # fallback: DML 지원 시
            db.sql_query("DELETE FROM records WHERE person = ? AND date = ?", (resolved, date))
            for fp in set(filepaths):
                db.sql_query("DELETE FROM processed_files WHERE filepath = ?", (fp,))
    except Exception as e:
        errors.append(f"sqlite delete exception: {e}")
        return {"ok": False, "error": "; ".join(errors), "deleted_files": deleted_files}

    # 5) 남은 레코드로 per-person 저장소 재구성
    try:
        rows = db.sql_query(
            "SELECT id, date, time, content, person, pid, person_name FROM records WHERE person = ? ORDER BY date, time",
            (resolved,)
        )
        records: List[Dict[str, Any]] = []
        for r in rows:
            records.append({
                "id": r.get("id"),
                "date": r.get("date", ""),
                "time": r.get("time", ""),
                "content": r.get("content", ""),
                "person": r.get("person", resolved),
                "pid": r.get("pid", ""),
                "person_name": r.get("person_name", "")
            })
        db.upsert(resolved, records)
    except Exception as e:
        print(f"[delete_works_by_date] upsert rebuild failed: {e}")
        errors.append(f"upsert rebuild failed: {e}")

    return {"ok": len(errors) == 0, "deleted_files": deleted_files, "error": "; ".join(errors) if errors else None}