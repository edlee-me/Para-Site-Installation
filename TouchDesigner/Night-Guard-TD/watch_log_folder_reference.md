# TouchDesigner: Grab and Store New Logs from Night-Guard-TD/logs

TouchDesigner **watches** the logs folder, detects **new** `entry_*.txt` files, and **stores** the latest log text in a Text DAT for display or scripting.

## 1. Create DATs

| DAT | Type | Name | Purpose |
|-----|------|------|---------|
| A | **Text DAT** | `latest_log` | Holds the current log text (script writes here). |
| B | **Table DAT** | `log_watch_state` | Optional. Tracks last-seen file so we only update when a **new** log appears. After the script runs, you’ll see 2 rows: row 0 = `last_file` / filename (e.g. `entry_1772813814265.txt`), row 1 = `last_mtime` / timestamp. The script uses `setSize(2, 2)` to create these rows. |

Create both in the same network as the script (e.g. same component). The script expects `op('latest_log')` and `op('log_watch_state')`; rename or change the `op(...)` paths in the script if yours differ.

## 2. When to run the script

Run the watch script on a **timer** or **periodically**:

- **Option A – Timer CHOP**  
  - Add a **Timer CHOP** (e.g. length **5** seconds, repeat).  
  - Add a **CHOP Execute DAT**, set **CHOP** to that Timer.  
  - In **onTimerPulse** (or **onDone**), paste the contents of `watch_log_folder_script.py`.

- **Option B – Execute DAT**  
  - Add an **Execute DAT**.  
  - Set **Run** to **On Frame** (or **On Pulse**).  
  - In **onFrameStart** (or the pulse callback), paste the script.  
  - To run every N frames instead of every frame, use a **Count CHOP** or a variable and call the script only when `frame % 60 == 0` (e.g. once per second at 60 fps).

## 3. Script and paths

The script is in **`watch_log_folder_script.py`** in this folder. It:

- Scans **`LOGS_FOLDER`** for `entry_*.txt`.
- Picks the **newest by modification time**.
- If that file is newer than the one stored in `log_watch_state`, reads it and sets **`latest_log.text`** to the file content, then updates `log_watch_state`.

Set **`LOGS_FOLDER`** in the script to your logs directory. The default is:

`PROJECT_ROOT/TouchDesigner/Night-Guard-TD/logs`

If your `.toe` is inside the project and `project.folder` is correct, you can use:

`LOGS_FOLDER = os.path.join(project.folder, 'Night-Guard-TD', 'logs')`

(or `project.folder + '/../Night-Guard-TD/logs'` if the .toe is in a subfolder).

## 4. Using the stored log

- **Display:** Point a **Text TOP** or **Text COMP** at the Text DAT `latest_log` (or use a **Panel** that shows the DAT).
- **Scripting:** In other operators, read `op('latest_log').text` to get the latest log string.
