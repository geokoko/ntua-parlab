import getpass
import itertools
import os
import re
import shlex
import subprocess
import sys
import time

import pexpect

def load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (
                len(value) >= 2
                and value[0] == value[-1]
                and value[0] in ("'", '"')
            ):
                value = value[1:-1]
            os.environ.setdefault(key, value)

def require_env(name):
    value = os.getenv(name)
    if value is None or value == "":
        print(f"Missing required env var: {name}")
        sys.exit(1)
    return value

SCRIPT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))

load_env_file(os.path.join(SCRIPT_DIR, ".env"))

def resolve_repo_path(path):
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(REPO_ROOT, path))

ORION = require_env("ORION")
SCIROUTER = require_env("SCIROUTER")
# Paths
ORION_HOME = require_env("ORION_HOME")
SCIROUTER_SHARED = require_env("SCIROUTER_SHARED")
LOCAL_PARALLEL = resolve_repo_path(require_env("LOCAL_PARALLEL"))
EXERCISE_DIRS = require_env("EXERCISE_DIRS").split()
SSH_OPTIONS = require_env("SSH_OPTIONS").split()
PASSWORD = os.getenv("PASSWORD")

def die(message):
    print(message)
    sys.exit(1)

def ensure_abs_not_root(label, path):
    if not os.path.isabs(path):
        die(f"{label} must be an absolute path: {path}")
    if os.path.normpath(path) == "/":
        die(f"{label} cannot be '/'.")

def ensure_shared_dir(label, path):
    if not os.path.isabs(path):
        die(f"{label} must be an absolute path: {path}")
    if os.path.basename(os.path.normpath(path)) != "shared":
        die(f"{label} must end with '/shared': {path}")

def path_within(base, path):
    base = os.path.abspath(base)
    path = os.path.abspath(path)
    return os.path.commonpath([base, path]) == base

def validate_exercise_dirs():
    require_exercise_dirs()
    local_base = os.path.abspath(LOCAL_PARALLEL)
    ensure_abs_not_root("LOCAL_PARALLEL", local_base)
    for raw in EXERCISE_DIRS:
        if not raw:
            die("EXERCISE_DIRS contains an empty entry.")
        if any(ch in raw for ch in "*?[]"):
            die(f"EXERCISE_DIRS contains glob characters: {raw}")
        if os.path.isabs(raw):
            abs_path = raw
        else:
            norm = os.path.normpath(raw)
            if norm in (".", "..") or norm.startswith(f"..{os.sep}"):
                die(f"EXERCISE_DIRS contains unsafe path: {raw}")
            abs_path = os.path.join(local_base, norm)
        abs_path = os.path.abspath(abs_path)
        if abs_path == local_base:
            die(f"EXERCISE_DIRS entry points at LOCAL_PARALLEL: {raw}")
        if not path_within(local_base, abs_path):
            die(f"EXERCISE_DIRS entry is outside LOCAL_PARALLEL: {raw}")

def validate_transfer_paths():
    ensure_abs_not_root("ORION_HOME", ORION_HOME)
    ensure_abs_not_root("LOCAL_PARALLEL", LOCAL_PARALLEL)
    ensure_shared_dir("SCIROUTER_SHARED", SCIROUTER_SHARED)
    ensure_shared_dir("ORION_HOME/shared", os.path.join(ORION_HOME, "shared"))
    validate_exercise_dirs()

def require_password():
    global PASSWORD
    if PASSWORD:
        return
    PASSWORD = getpass.getpass("SSH password: ")
    if not PASSWORD:
        print("Password is required.")
        sys.exit(1)

def run_cmd(cmd, step_name, timeout=600):
    try:
        subprocess.run(cmd, check=True, timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        print(f"{step_name} timed out.")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"{step_name} failed with exit code {exc.returncode}.")
        return False

def require_exercise_dirs():
    if not EXERCISE_DIRS:
        print("EXERCISE_DIRS is empty.")
        sys.exit(1)

def local_exercise_paths():
    require_exercise_dirs()
    paths = []
    missing = []
    for name in EXERCISE_DIRS:
        path = name if os.path.isabs(name) else os.path.join(LOCAL_PARALLEL, name)
        if not os.path.isdir(path):
            missing.append(path)
        paths.append(path)
    if missing:
        print("Missing local exercise directories:")
        for path in missing:
            print(f"  - {path}")
        sys.exit(1)
    return paths

RSYNC_BASE_ARGS = ["rsync", "-r", "--checksum", "--info=NAME2"]

def build_ssh_command():
    parts = ["ssh", *SSH_OPTIONS]
    return " ".join(shlex.quote(part) for part in parts)

def format_rsync_line(line):
    line = line.rstrip("\r")
    if not line:
        return None
    suffix = " is uptodate"
    if line.endswith(suffix):
        name = line[: -len(suffix)]
        return f"Skipped (unchanged): {name}"
    return line

class LineFormatter:
    def __init__(self, formatter):
        self.formatter = formatter
        self.buffer = ""

    def write(self, data):
        if not data:
            return
        self.buffer += data
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._emit(line)

    def flush(self):
        if self.buffer:
            self._emit(self.buffer)
            self.buffer = ""

    def _emit(self, line):
        formatted = self.formatter(line)
        if formatted:
            print(formatted)

def handle_transfer_interaction(child, timeout_initial=30, timeout_copy=600, status_label="transfer"):
    """
    Handles the interaction for transfer commands.
    Expects: Password prompt, Host confirmation, or Completion/Prompt.
    """
    spinner = itertools.cycle("|/-\\")
    spinner_active = False
    last_activity = time.monotonic()
    max_silence = timeout_initial

    def clear_spinner():
        nonlocal spinner_active
        if not spinner_active:
            return
        sys.stderr.write("\r")
        sys.stderr.write(" " * 80)
        sys.stderr.write("\r")
        sys.stderr.flush()
        spinner_active = False
    patterns = [
        re.compile(r"(?i)password:"),
        re.compile(r"continue connecting"),
        re.compile(r"(?i)permission denied"),
        re.compile(r"(?i)host key verification failed"),
        re.compile(r"(?i)enter passphrase"),
        r"[$#]",
        pexpect.EOF,
        pexpect.TIMEOUT,
    ]
    tick_interval = 2
    while True:
        # Expect either a password prompt, a confirmation, or the shell prompt (meaning done)
        index = child.expect(patterns, timeout=tick_interval)
        now = time.monotonic()
        
        if index == 0: # password:
            clear_spinner()
            child.sendline(PASSWORD)
            max_silence = timeout_copy
            last_activity = now
            continue
            
        elif index == 1: # continue connecting (yes/no)
            clear_spinner()
            child.sendline('yes')
            # Loop back to check for password or prompt
            max_silence = timeout_copy
            last_activity = now
            continue
            
        elif index == 2: # permission denied
            clear_spinner()
            print("Permission denied during transfer.")
            return False

        elif index == 3: # host key verification failed
            clear_spinner()
            print("Host key verification failed during transfer.")
            return False

        elif index == 4: # passphrase prompt indicates key auth
            clear_spinner()
            print("SSH key passphrase prompt detected. Disable key auth or allow password auth.")
            return False

        elif index == 5: # [$#] - Prompt returned, meaning command finished immediately or fast
            clear_spinner()
            return True
            
        elif index == 6: # EOF
            clear_spinner()
            return True
            
        elif index == 7: # TIMEOUT
            # If we timed out waiting for a password, it's possible that:
            # 1. Transfer is running (copying files) and didn't ask for a password (SSH keys).
            # 2. Transfer is stuck silently.
            # We check the buffer to see if there is activity.
            output = child.before or ""
            if output.strip():
                last_activity = now
                continue
            if now - last_activity > max_silence:
                clear_spinner()
                print("Timeout waiting for interaction. Output so far:")
                print(output)
                return False
            spinner_active = True
            elapsed = int(now - last_activity)
            sys.stderr.write(f"\r{status_label}... {next(spinner)} {elapsed}s")
            sys.stderr.flush()
            continue

def run_transfer_with_pexpect(cmd, step_name, timeout_initial=30, timeout_copy=1200):
    child = pexpect.spawn(cmd, encoding='utf-8')
    child.logfile_read = LineFormatter(format_rsync_line)
    ok = handle_transfer_interaction(
        child,
        timeout_initial=timeout_initial,
        timeout_copy=timeout_copy,
        status_label=step_name
    )
    child.close()
    if not ok:
        return False
    if child.exitstatus not in (0, None):
        print(f"{step_name} failed with exit code {child.exitstatus}.")
        return False
    if child.signalstatus is not None:
        print(f"{step_name} terminated with signal {child.signalstatus}.")
        return False
    return True

def run_step_1_pull_remote_rsync():
    """
    On Orion: rsync --checksum scirouter:.../shared/<exercise> /home/parallel/parlab16/shared
    """
    print("Step 1: Orion pulling from Scirouter...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {ORION}",
        encoding='utf-8'
    )
    child.logfile_read = LineFormatter(format_rsync_line)

    # Handle Orion Login
    i = child.expect(['password:', '[$#]'], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(['[$#]', 'parlab16@orion'], timeout=10)

    child.sendline(f"mkdir -p {ORION_HOME}/shared")
    child.expect(['[$#]'], timeout=10)

    ssh_cmd = build_ssh_command()
    remote_sources = [
        f"{SCIROUTER}:{SCIROUTER_SHARED}/{name}"
        for name in EXERCISE_DIRS
    ]
    rsync_args = [
        *RSYNC_BASE_ARGS,
        "-e", ssh_cmd,
        *remote_sources,
        f"{ORION_HOME}/shared/"
    ]
    rsync_cmd = " ".join(shlex.quote(arg) for arg in rsync_args)
    child.sendline(rsync_cmd)

    if handle_transfer_interaction(child, status_label="Remote rsync (pull)"):
        print("  -> Remote sync finished.")
        child.sendline('exit')
        child.close()
        return True
    child.close()
    return False

def run_step_2_push_remote_rsync():
    """
    On Orion: rsync --checksum /home/parallel/parlab16/shared/<exercise> scirouter:.../shared
    """
    print("Step 2: Orion pushing to Scirouter...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {ORION}",
        encoding='utf-8'
    )
    child.logfile_read = LineFormatter(format_rsync_line)

    i = child.expect(['password:', '[$#]'], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(['[$#]', 'parlab16@orion'], timeout=10)

    ssh_cmd = build_ssh_command()
    local_sources = [
        f"{ORION_HOME}/shared/{name}"
        for name in EXERCISE_DIRS
    ]
    rsync_args = [
        *RSYNC_BASE_ARGS,
        "-e", ssh_cmd,
        *local_sources,
        f"{SCIROUTER}:{SCIROUTER_SHARED}/"
    ]
    rsync_cmd = " ".join(shlex.quote(arg) for arg in rsync_args)
    child.sendline(rsync_cmd)

    if handle_transfer_interaction(child, status_label="Remote rsync (push)"):
        print("  -> Remote sync finished.")
        child.sendline('exit')
        child.close()
        return True
    child.close()
    return False

def pull():
    require_password()
    validate_transfer_paths()
    # 1. Remote rsync (Orion pulls from Scirouter)
    if not run_step_1_pull_remote_rsync():
        print("Failed Step 1")
        sys.exit(1)
        
    # 2. Local rsync (Local pulls from Orion)
    print("Step 2: Pulling from Orion to Local...")
    require_exercise_dirs()
    remote_sources = [
        f"{ORION}:{ORION_HOME}/shared/{name}"
        for name in EXERCISE_DIRS
    ]
    rsync_args = [
        *RSYNC_BASE_ARGS,
        "-e", build_ssh_command(),
        *remote_sources,
        LOCAL_PARALLEL
    ]
    rsync_cmd = " ".join(shlex.quote(arg) for arg in rsync_args)
    if not run_transfer_with_pexpect(rsync_cmd, "Step 2"):
        print("Failed Step 2")
        sys.exit(1)
    
    # 3. Cleanup Orion
    print("Step 3: Cleanup on Orion...")
    cmd = [
        "sshpass", "-p", PASSWORD,
        "ssh", *SSH_OPTIONS,
        ORION,
        f"rm -rf {ORION_HOME}/shared"
    ]
    if not run_cmd(cmd, "Step 3", timeout=120):
        print("Warning: cleanup did not finish.")
    print("Pull Complete.")

def push():
    require_password()
    validate_transfer_paths()
    # 1. Prepare Orion shared directory
    print("Step 1: Preparing Orion shared directory...")
    cmd = [
        "sshpass", "-p", PASSWORD,
        "ssh", *SSH_OPTIONS,
        ORION,
        f"mkdir -p {ORION_HOME}/shared"
    ]
    if not run_cmd(cmd, "Step 1"):
        print("Failed Step 1")
        sys.exit(1)

    # 2. Local rsync (Local pushes to Orion)
    print("Step 2: Pushing from Local to Orion...")
    local_sources = local_exercise_paths()
    rsync_args = [
        *RSYNC_BASE_ARGS,
        "-e", build_ssh_command(),
        *local_sources,
        f"{ORION}:{ORION_HOME}/shared/"
    ]
    rsync_cmd = " ".join(shlex.quote(arg) for arg in rsync_args)
    if not run_transfer_with_pexpect(rsync_cmd, "Step 2"):
        print("Failed Step 2")
        sys.exit(1)
        
    # 3. Remote rsync (Orion pushes to Scirouter)
    if not run_step_2_push_remote_rsync():
        print("Failed Step 3")
        sys.exit(1)
        
    # 4. Cleanup Orion
    print("Step 4: Cleanup on Orion...")
    cmd = [
        "sshpass", "-p", PASSWORD,
        "ssh", *SSH_OPTIONS,
        ORION,
        f"rm -rf {ORION_HOME}/shared"
    ]
    if not run_cmd(cmd, "Step 4", timeout=120):
        print("Warning: cleanup did not finish.")
    print("Push Complete.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 transfer_manager.py [pull|push]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "pull":
        pull()
    elif action == "push":
        push()
    else:
        print("Unknown command")
