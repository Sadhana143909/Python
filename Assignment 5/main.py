import csv
import io
import sqlite3
import time
import random

# ==============================================================================
# TASK B1: IMPLEMENT AND VALIDATE THE CLEANING PIPELINE & MIN-MAX SCALING
# ==============================================================================
RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
Guindy,2026-10-04,1050
"""

def load_clean(text):
    """Returns (station, date, pm25) tuples for valid, non-negative readings <= 999 only."""
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        val_str = (row.get("pm25") or "").strip()
        if not val_str or val_str.upper() == "NA":
            continue
        try:
            pm = float(val_str)
            if pm < 0 or pm > 999:
                continue
            rows.append((row["station"].strip(), row["date"].strip(), pm))
        except ValueError:
            continue
    return rows

def min_max(values):
    """Scale each value to 0-1 using (v - min) / (max - min), rounded to 3 decimals."""
    mn, mx = min(values), max(values)
    return [round((v - mn) / (mx - mn), 3) for v in values]

clean = load_clean(RAW)
print("=== TASK B1 OUTPUT ===")
print("Cleaned rows:", clean)
print("Min-Max scaled:", min_max([pm for _, _, pm in clean]))

# ==============================================================================
# TASK B2: ENGINEER ADVERSARIAL DATA & PARAMETERISED SQLITE QUERIES
# ==============================================================================
readings = [
    ("Adyar", "2026-10-01", 48.0),
    ("Guindy", "2026-10-01", 95.0),
    ("Guindy", "2026-10-03", 121.0),
    ("Adyar", "2026-10-04", 60.0),
]

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
con.executemany("INSERT INTO aq VALUES (?, ?, ?)", readings)
con.commit()

def station_average(name):
    cur = con.execute("SELECT AVG(pm25) FROM aq WHERE station = ?", (name,))
    row = cur.fetchone()
    return row[0] if row else None

print("\n=== TASK B2 OUTPUT ===")
print("Valid averages (Adyar, Guindy):", station_average("Adyar"), station_average("Guindy"))
print("Parameterised SQL injection test:", station_average("Adyar' OR '1'='1"))
con.close()

# ==============================================================================
# TASK B3: LOOPS vs SQLITE BENCHMARK
# ==============================================================================
def generate_rows(n_stations, hours=8760):
    rows = []
    for s in range(n_stations):
        st = f"Station_{s:02d}"
        for h in range(hours):
            day = f"2026-{(h // 730) + 1:02d}-{((h // 24) % 28) + 1:02d}"
            rows.append((st, day, round(random.uniform(20.0, 160.0), 2)))
    return rows

def daily_mean_loops(rows):
    sums, counts = {}, {}
    for st, day, pm in rows:
        key = (st, day)
        sums[key] = sums.get(key, 0.0) + pm
        counts[key] = counts.get(key, 0) + 1
    return {k: sums[k] / counts[k] for k in sums}

def daily_mean_sql(conn):
    cur = conn.execute("SELECT station, day, AVG(pm25) FROM aq GROUP BY station, day")
    return {(r[0], r[1]): r[2] for r in cur.fetchall()}

print("\n=== TASK B3 OUTPUT ===")
for n_st in [1, 12]:
    data = generate_rows(n_st, 8760)
    c_bench = sqlite3.connect(":memory:")
    c_bench.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    c_bench.executemany("INSERT INTO aq VALUES (?, ?, ?)", data)

    t0 = time.perf_counter()
    res_loop = daily_mean_loops(data)
    t_loop = time.perf_counter() - t0

    t0 = time.perf_counter()
    res_sql = daily_mean_sql(c_bench)
    t_sql = time.perf_counter() - t0

    agree = all(abs(res_loop[k] - res_sql[k]) < 1e-6 for k in res_loop)
    print(f"Stations={n_st:<2} | Rows={len(data):<6} | Match={agree} | Loop={t_loop:.4f}s | SQL={t_sql:.4f}s")
    c_bench.close()

# ==============================================================================
# TASK B4: SENTIMENT SCORER WITH NEGATION & DATABASE INDEX BENCHMARK
# ==============================================================================
POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}

def score(text):
    """+1 per positive word, -1 per negative word; a preceding negator flips it."""
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0
    for i, w in enumerate(words):
        val = 1 if w in POSITIVE else (-1 if w in NEGATIVE else 0)
        if i > 0 and words[i - 1] in NEGATORS:
            val = -val
        total += val
    return total

def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"

print("\n=== TASK B4 OUTPUT ===")
complaints = [
    "Roads are clean and the bus was fast.",
    "Smoke from the factory, air is bad.",
    "The staff were not helpful.",
    "Not bad, service improved.",
]
for c in complaints:
    print(f"{label(c):8} | {c}")

# Index timing check on 100,000 rows
c_idx = sqlite3.connect(":memory:")
c_idx.execute("CREATE TABLE readings (station TEXT, day TEXT, pm25 REAL)")
idx_rows = [(f"St_{i%50}", f"2026-10-{(i%30)+1:02d}", float(i % 180)) for i in range(100000)]
c_idx.executemany("INSERT INTO readings VALUES (?, ?, ?)", idx_rows)
c_idx.commit()

t0 = time.perf_counter()
c_idx.execute("SELECT AVG(pm25) FROM readings WHERE station='St_10' AND day='2026-10-12'").fetchone()
t_before = (time.perf_counter() - t0) * 1000

c_idx.execute("CREATE INDEX idx_st_day ON readings(station, day)")
t0 = time.perf_counter()
c_idx.execute("SELECT AVG(pm25) FROM readings WHERE station='St_10' AND day='2026-10-12'").fetchone()
t_after = (time.perf_counter() - t0) * 1000

print(f"SQL Query Time -> Without Index: {t_before:.3f} ms | With Index: {t_after:.3f} ms")
c_idx.close()
