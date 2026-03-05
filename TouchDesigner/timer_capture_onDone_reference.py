# Paste this into your Timer CHOP Execute DAT, onDone callback.
# Replace PROJECT_ROOT with your actual project path if needed (see below).

import os
import subprocess

def onDone(timerOp, segment, interrupt):
    target_top = op('res1')  # or op('videodevicein1') / your TOP name
    if target_top is None:
        debug('Target TOP not found. Unable to save capture.')
        return

    folder = project.folder + '/captures/' + op('parameter1')[3, 1] + '/'
    os.makedirs(folder, exist_ok=True)
    path = folder + op('parameter1')[4, 1] + '_{}.png'.format(int(absTime.seconds))
    target_top.save(path)

    # Print captured image to thermal printer
    subprocess.Popen([
        'lp', '-d', 'Printer_POS_80',
        '-o', 'fit-to-page', '-o', 'media=Custom.80x60mm',
        path
    ])

    # --- Night Guard: run script with venv Python (absolute paths) ---
    PROJECT_ROOT = '/Users/ed/Documents/Projects/Para-Site/Para-Site-Installation'
    night_guard_script = os.path.join(PROJECT_ROOT, 'Night-Guard-TD', 'night_guard.py')
    python_exe = os.path.join(PROJECT_ROOT, '.venv', 'bin', 'python')
    log_file = os.path.join(PROJECT_ROOT, 'Night-Guard-TD', 'td_nightguard_log.txt')

    if not os.path.isfile(python_exe):
        with open(log_file, 'a') as f:
            f.write('Error: venv Python not found: %s\n' % python_exe)
        return
    if not os.path.isfile(night_guard_script):
        with open(log_file, 'a') as f:
            f.write('Error: night_guard.py not found: %s\n' % night_guard_script)
        return

    try:
        cmd = [python_exe, night_guard_script, path, '--print', 'Printer_POS_80']
        with open(log_file, 'a') as f:
            f.write('\n--- %s ---\nRunning: %s\n' % (absTime.seconds, ' '.join(cmd)))
        subprocess.Popen(cmd, cwd=PROJECT_ROOT)
    except Exception as e:
        try:
            with open(log_file, 'a') as f:
                f.write('Exception: %s\n' % str(e))
        except Exception:
            pass
