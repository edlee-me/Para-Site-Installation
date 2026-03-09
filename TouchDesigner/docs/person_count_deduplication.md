# Counting "person" from MediaPipe Object Tracking with Deduplication

You are using the [MediaPipe TouchDesigner](https://github.com/torinmb/mediapipe-touchdesigner) plugin and tracking objects. The object-tracking DAT lists all detected objects (one row per object). To count **only "person"** and **deduplicate** (so one person entering doesn’t get counted many times as the row count flickers), use the approach below.

## Idea: row count change with persistence

- **Current person count:** number of rows in the object DAT where the label is `"person"`.
- **Deduplicated “entries” count:** only add to a running total when the **person count increases** and the increase is **sustained** for a few frames. That avoids counting the same person multiple times when detection flickers (e.g. 1 → 0 → 1).

So we:
1. Count rows where label == `"person"` (not total DAT rows).
2. Track **previous** person count.
3. When **current > previous**, treat that as a potential “new person(s)”.
4. Optionally require the **new count to persist** for 2–3 frames before adding `(current - previous)` to the cumulative count (deduplication).

## 1. DAT layout (object tracking)

The object DAT from MediaPipe usually has a header row and columns such as:

- A column for the class **label** (e.g. `label` or `name`) — we filter on `"person"`.
- Other columns (e.g. score, bbox) — we only need the label.

If your DAT uses a different column name for the class, set `LABEL_COL` in the script to that name (e.g. `'name'` or `'class'`).

## 2. DATs to add

| DAT | Type | Purpose |
|-----|------|--------|
| `objects_dat` | (your existing object-tracking DAT) | Input: all tracked objects. |
| `person_count_state` | Table DAT | Stores: `prev_person_count`, `cumulative_entries`, optional `stable_count`, `pending_increase`. Script creates 2×2 or 4×2. |
| `person_count_output` | Table DAT (optional) | Output: e.g. current count, cumulative entries for display or CHOP. |

Create `person_count_state` and (if you want) `person_count_output` in the same component as the script.

## 3. Script (Execute DAT or CHOP Execute, every frame)

Run this **onFrameEnd** (or every frame after the object DAT has cooked). Adjust paths to match your network.

```python
# Person count from MediaPipe object DAT with deduplication
# Run each frame (e.g. Execute DAT onFrameEnd).

OBJECTS_DAT = op('objects_dat')           # Your object-tracking DAT
STATE_DAT = op('person_count_state')     # Table DAT to store state
OUTPUT_DAT = op('person_count_output')    # Optional: current count, cumulative
LABEL_COL = 'label'                       # or 'name' / 'class' if your DAT differs
LABEL_PERSON = 'person'
STABLE_FRAMES = 2                         # Frames the new count must hold before we add to cumulative

def count_person_rows(dat, label_col, person_label):
    if dat is None or dat.numRows == 0:
        return 0
    # Find column index (header in row 0)
    h = dat.row(0)
    try:
        col_idx = list(h).index(label_col)
    except ValueError:
        return 0
    n = 0
    for i in range(1, dat.numRows):
        if dat[i, col_idx].val == person_label:
            n += 1
    return n

def get_state(state_dat):
    if state_dat is None or state_dat.numRows < 5:
        return 0, 0, 0, 0
    try:
        prev = int(state_dat[1, 1].val or 0)
        cum = int(state_dat[2, 1].val or 0)
        stable = int(state_dat[3, 1].val or 0)
        pending = int(state_dat[4, 1].val or 0)
    except (IndexError, ValueError):
        prev, cum, stable, pending = 0, 0, 0, 0
    return prev, cum, stable, pending

def set_state(state_dat, prev, cum, stable, pending, current):
    if state_dat is None:
        return
    state_dat.clear()
    state_dat.setSize(6, 2)
    state_dat[0, 0] = 'key'
    state_dat[0, 1] = 'value'
    state_dat[1, 0] = 'prev_person_count'
    state_dat[1, 1] = str(prev)
    state_dat[2, 0] = 'cumulative_entries'
    state_dat[2, 1] = str(cum)
    state_dat[3, 0] = 'stable_frames'
    state_dat[3, 1] = str(stable)
    state_dat[4, 0] = 'pending_increase'
    state_dat[4, 1] = str(pending)
    state_dat[5, 0] = 'current_person_count'
    state_dat[5, 1] = str(current)

# ---
current = count_person_rows(OBJECTS_DAT, LABEL_COL, LABEL_PERSON)
prev, cum, stable, pending = get_state(STATE_DAT)

if current > prev:
    # Count went up: might be new person(s)
    pending = current - prev
    stable = 1
elif current < prev:
    # Count went down: reset pending
    pending = 0
    stable = 0
else:
    # Same count: if we had a pending increase, see if it's sustained
    if pending > 0:
        stable += 1
        if stable >= STABLE_FRAMES:
            cum += pending
            pending = 0
            stable = 0

set_state(STATE_DAT, current, cum, stable, pending, current)

# Optional: write to output DAT for display / CHOP
if OUTPUT_DAT is not None:
    OUTPUT_DAT.clear()
    OUTPUT_DAT.setSize(3, 2)
    OUTPUT_DAT[0, 0] = 'current_person_count'
    OUTPUT_DAT[0, 1] = str(current)
    OUTPUT_DAT[1, 0] = 'cumulative_entries'
    OUTPUT_DAT[1, 1] = str(cum)
    OUTPUT_DAT[2, 0] = 'pending_increase'
    OUTPUT_DAT[2, 1] = str(pending)
```

## 4. Wiring in TouchDesigner

1. Point `OBJECTS_DAT` at your MediaPipe object-tracking DAT (the table that lists all objects).
2. Create `person_count_state` (Table DAT) and, if you want, `person_count_output` (Table DAT).
3. Put the script in an **Execute DAT** with **onFrameEnd** (or in a CHOP Execute that runs every frame).
4. If your object DAT uses a different column for the class, set `LABEL_COL` (e.g. `'name'`).
5. Tune `STABLE_FRAMES`: higher = fewer false “new person” counts from flicker; lower = quicker reaction.

## 5. Using the counts

- **Current number of persons on screen:** `person_count_state[5, 1]` or `person_count_output[0, 1]` (same as number of “person” rows in the object DAT).
- **Deduplicated “persons entered” over the run:** `person_count_state[2, 1]` or `person_count_output[1, 1]` (`cumulative_entries`).

You can export these to a CHOP (e.g. with a **Constant CHOP** or **Script CHOP**) for animation or logic.

## 6. Alternative: count only DAT row changes (no “person” filter)

If you literally only care about “number of rows in the object DAT” and not the label:

- Store `prev_num_rows = OBJECTS_DAT.numRows` in state.
- Each frame: `current_rows = OBJECTS_DAT.numRows`; if `current_rows != prev_num_rows`, you have a “change” (you could count increases only, or both up/down).
- That does **not** filter by “person”, so every object (person, chair, etc.) would drive the count. Prefer the script above if you want **person-only** count and deduplication.
