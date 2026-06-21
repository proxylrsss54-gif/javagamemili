import time

running_task = None      # "check", "kill", "gen", etc.
cancel_flag = False
cooldown_until = 0

def set_cooldown(seconds=15):
    global cooldown_until
    cooldown_until = time.time() + seconds

def is_cooldown():
    return time.time() < cooldown_until

def reset_state():
    global running_task, cancel_flag
    running_task = None
    cancel_flag = False