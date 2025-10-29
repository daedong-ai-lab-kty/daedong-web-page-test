from typing import List, Dict, Tuple, Any, Optional

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
    print(f"SQL query: records for {person!r} on {date}:")
    if rows:
        for r in rows:
            print(r)
    else:
        print(" - Works: None")
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
