from typing import List, Dict, Tuple, Any, Optional
import os

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