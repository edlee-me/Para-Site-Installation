"""
Execute DAT – Merged: person count (with persistent cumulative) + pick_random_rows_and_apply_noise.

Enable onFrameEnd in the Execute DAT parameters.

Order on start: load cumulative from disk → seed state DAT → time/interval setup → pick_random_rows_and_apply_noise
so the noise uses the loaded cumulative value.
"""

import os
import random

# ---- Person count (persistent cumulative) ----
# Paths relative to this Execute DAT's parent component
def getOps():
	parent = me.parent()
	return (
		op('ImageCapture/object_table'),
		op('person_count_state'),
		op('person_count_output'),
	)

OBJECTS_DAT = None
STATE_DAT = None
OUTPUT_DAT = None
LABEL_COL = 'object'
LABEL_PERSON = 'person'
STABLE_FRAMES = 18

PERSIST_FILENAME = 'save_persisted_cumulative.json'
last_saved_cum = -1

def get_persist_path():
	try:
		proj_dir = project.folder if hasattr(project, 'folder') and project.folder else os.path.dirname(project.path)
		if proj_dir:
			return os.path.join(proj_dir, PERSIST_FILENAME)
	except Exception:
		pass
	return None

def load_persisted_cumulative():
	path = get_persist_path()
	if not path or not os.path.isfile(path):
		return 0
	try:
		import json
		with open(path, 'r') as f:
			data = json.load(f)
			return int(data.get('cumulative_entries', 0))
	except Exception:
		return 0

def save_persisted_cumulative(cum):
	path = get_persist_path()
	if not path:
		return
	try:
		import json
		with open(path, 'w') as f:
			json.dump({'cumulative_entries': cum}, f)
	except Exception as e:
		print(f"save_persisted_cumulative failed: {e}")

def count_person_rows(dat, label_col, person_label):
	if dat is None or dat.numRows == 0:
		return 0
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

# ---- Pick random rows and apply noise (runs after cumulative is loaded) ----
def pick_random_rows_and_apply_noise(
	count_op,
	base_comp,
	source_dat_name="chopto2",
	copy_dat_name="copy",
	noise_dat_name="noise",
	manipulate_count=3,
	noise_min=0,
	noise_max=100,
	verbose=True,
):
	"""
	Read count from count_op, pick that many random row groups from source Table DAT,
	write random noise into those rows on a copy, then merge noise into the copy.
	"""
	try:
		ch = count_op[0]
		print(ch.vals[0], "ch.vals[0]")
		count = int((ch.vals[0] if hasattr(ch, "vals") else ch) * 0.2)
	except (AttributeError, IndexError, TypeError, ValueError):
		count = 0

	source_data = base_comp.op(source_dat_name)
	if source_data is None:
		if verbose:
			print("pick_random_rows_and_apply_noise: {} not found".format(source_dat_name))
		return False

	source_data_copy = base_comp.op(copy_dat_name)
	if source_data_copy is None:
		if verbose:
			print("pick_random_rows_and_apply_noise: {} not found".format(copy_dat_name))
		return False

	noise_data = base_comp.op(noise_dat_name)
	if noise_data is None:
		if verbose:
			print("pick_random_rows_and_apply_noise: {} not found".format(noise_dat_name))
		return False

	source_data_copy.copy(source_data)

	num_rows = source_data.numRows
	num_cols = source_data.numCols

	# print(num_rows, num_cols)

	row_indices = list(range(num_rows))[:-manipulate_count]
	# print(len(row_indices))
	if count > len(row_indices):
		print(count, len(row_indices))
		count = len(row_indices)
	print(count)
	random_numbers = random.sample(row_indices, count)
	random_numbers.sort()
	result = []
	for num in random_numbers:
		result.append([num + i + 1 for i in range(manipulate_count)])
	flat_result = [item for sublist in result for item in sublist]
	if verbose:
		print("pick_random_rows_and_apply_noise: count={}, flat_result={}".format(count, flat_result))

	for row in range(noise_data.numRows):
		for col in range(noise_data.numCols):
			noise_data[row, col] = 0

	noise_data.setSize(num_rows, num_cols)

	for row in flat_result:
		if 0 <= row < noise_data.numRows:
			for col in range(noise_data.numCols):
				noise_data[row, col] = random.randint(noise_min, noise_max)

	for row in range(source_data_copy.numRows):
		for col in range(noise_data.numCols):
			if noise_data[row, col] > 0:
				source_data_copy[row, col] = noise_data[row, col]

	return True


def onStart():
	global OBJECTS_DAT, STATE_DAT, OUTPUT_DAT, last_saved_cum

	# 1) Load cumulative from disk and seed state (must happen first)
	OBJECTS_DAT, STATE_DAT, OUTPUT_DAT = getOps()
	cum = load_persisted_cumulative()
	last_saved_cum = cum
	if STATE_DAT is not None:
		set_state(STATE_DAT, 0, cum, 0, 0, 0)

	# 2) Time and interval (from original execute1)
	root.time.frame = 1
	root.time.play = 0
	ai_print_interval = random.randint(10, 45)
	op('ai_print_interval').par.value0 = ai_print_interval * 60

	# 3) Force cumulative_person_count to cook so it reflects the state we just set
	try:
		op('cumulative_person_count').cook(force=True)
	except Exception:
		pass

	# 4) Pick random rows and apply noise (after cumulative is loaded so count_op has correct value)
	pick_random_rows_and_apply_noise(
		count_op=op("cumulative_person_count"),
		base_comp=op("record_machine"),
		source_dat_name="chopto2",
		copy_dat_name="copy",
		noise_dat_name="noise",
		manipulate_count=3,
		noise_min=0,
		noise_max=100,
		verbose=True,
	)
	pick_random_rows_and_apply_noise(
		count_op=op("cumulative_person_count"),
		base_comp=op("record_machine4"),
		source_dat_name="chopto2",
		copy_dat_name="copy",
		noise_dat_name="noise",
		manipulate_count=3,
		noise_min=0,
		noise_max=100,
		verbose=True,
	)
	pick_random_rows_and_apply_noise(
		count_op=op("cumulative_person_count"),
		base_comp=op("record_machine2"),
		source_dat_name="chopto2",
		copy_dat_name="copy",
		noise_dat_name="noise",
		manipulate_count=3,
		noise_min=0,
		noise_max=1,
		verbose=True,
	)
	pick_random_rows_and_apply_noise(
		count_op=op("cumulative_person_count"),
		base_comp=op("record_machine3"),
		source_dat_name="chopto2",
		copy_dat_name="copy",
		noise_dat_name="noise",
		manipulate_count=3,
		noise_min=0,
		noise_max=100,
		verbose=True,
	)


def onCreate():
	return


def onExit():
	# Save cumulative before exit
	if STATE_DAT is not None and STATE_DAT.numRows >= 3:
		try:
			cum = int(STATE_DAT[2, 1].val or 0)
			save_persisted_cumulative(cum)
		except Exception:
			pass
	root.time.frame = 1
	root.time.play = 0


def onFrameStart(frame: int):
	return


def onFrameEnd(frame: int):
	global OBJECTS_DAT, STATE_DAT, OUTPUT_DAT, last_saved_cum
	if OBJECTS_DAT is None or STATE_DAT is None:
		OBJECTS_DAT, STATE_DAT, OUTPUT_DAT = getOps()
	if OBJECTS_DAT is None or STATE_DAT is None:
		return

	current = count_person_rows(OBJECTS_DAT, LABEL_COL, LABEL_PERSON)
	prev, cum, stable, pending = get_state(STATE_DAT)

	if current > prev:
		pending = current - prev
		stable = 1
	elif current < prev:
		pending = 0
		stable = 0
	else:
		if pending > 0:
			stable += 1
			if stable >= STABLE_FRAMES:
				cum += pending
				pending = 0
				stable = 0

	set_state(STATE_DAT, current, cum, stable, pending, current)

	if cum != last_saved_cum:
		save_persisted_cumulative(cum)
		last_saved_cum = cum

	if OUTPUT_DAT is not None:
		OUTPUT_DAT.clear()
		OUTPUT_DAT.setSize(3, 2)
		OUTPUT_DAT[0, 0] = 'current_person_count'
		OUTPUT_DAT[0, 1] = str(current)
		OUTPUT_DAT[1, 0] = 'cumulative_entries'
		OUTPUT_DAT[1, 1] = str(cum)
		OUTPUT_DAT[2, 0] = 'pending_increase'
		OUTPUT_DAT[2, 1] = str(pending)


def onPlayStateChange(state: bool):
	return


def onDeviceChange():
	return


def onProjectPreSave():
	return


def onProjectPostSave():
	return
