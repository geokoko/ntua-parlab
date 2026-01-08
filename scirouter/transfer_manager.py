import pexpect
import sys
import os
import subprocess
import getpass

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

def handle_scp_interaction(child, timeout_initial=30, timeout_copy=600):
    """
    Handles the interaction for SCP.
    Expects: Password prompt, Host confirmation, or Completion/Prompt.
    """
    while True:
        # Expect either a password prompt, a confirmation, or the shell prompt (meaning done)
        index = child.expect(['password:', 'continue connecting', '[$#]', pexpect.EOF, pexpect.TIMEOUT], timeout=timeout_initial)
        
        if index == 0: # password:
            child.sendline(PASSWORD)
            # After sending password, we wait for completion (prompt)
            # We increase timeout for large file copy
            child.expect(['[$#]', pexpect.EOF], timeout=timeout_copy)
            return True
            
        elif index == 1: # continue connecting (yes/no)
            child.sendline('yes')
            # Loop back to check for password or prompt
            continue
            
        elif index == 2: # [$#] - Prompt returned, meaning command finished immediately or fast
            return True
            
        elif index == 3: # EOF
            return True
            
        elif index == 4: # TIMEOUT
            # If we timed out waiting for a password, it's possible that:
            # 1. SCP is working (copying files) and didn't ask for a password (SSH keys).
            # 2. SCP is stuck silently.
            # We check the buffer to see if there is activity.
            output = child.before
            if "100%" in output or "KB/s" in output or "shared" in output:
                print("  -> SCP seems to be running (no password needed). Waiting for completion...")
                # Wait for the prompt (completion)
                child.expect(['[$#]', pexpect.EOF], timeout=timeout_copy)
                return True
            else:
                print("Timeout waiting for interaction. Output so far:")
                print(output)
                return False

def run_step_1_pull_remote_scp():
    """
    On Orion: scp -r scirouter:.../shared /home/parallel/parlab16
    """
    print("Step 1: Orion pulling from Scirouter...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {ORION}",
        encoding='utf-8'
    )
    
    # Handle Orion Login
    i = child.expect(['password:', '[$#]'], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(['[$#]', 'parlab16@orion'], timeout=10)
    
    # Run SCP on Orion
    # Using -o StrictHostKeyChecking=no for inner SSH too
    scp_cmd = (
        f"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-r {SCIROUTER}:{SCIROUTER_SHARED} {ORION_HOME}"
    )
    child.sendline(scp_cmd)
    
    if handle_scp_interaction(child):
        print("  -> Remote copy finished.")
        child.sendline('exit')
        child.close()
        return True
    else:
        child.close()
        return False

def run_step_2_push_remote_scp():
    """
    On Orion: scp -r .../shared/* scirouter:.../shared
    """
    print("Step 2: Orion pushing to Scirouter...")
    child = pexpect.spawn(
        f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {ORION}",
        encoding='utf-8'
    )
    
    i = child.expect(['password:', '[$#]'], timeout=10)
    if i == 0:
        child.sendline(PASSWORD)
        child.expect(['[$#]', 'parlab16@orion'], timeout=10)
        
    scp_cmd = (
        f"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
        f"-r {ORION_HOME}/shared/* {SCIROUTER}:{SCIROUTER_SHARED}"
    )
    child.sendline(scp_cmd)
    
    if handle_scp_interaction(child):
        print("  -> Remote copy finished.")
        child.sendline('exit')
        child.close()
        return True
    else:
        child.close()
        return False

def pull():
    require_password()
    # 1. Remote SCP (Orion pulls from Scirouter)
    if not run_step_1_pull_remote_scp():
        print("Failed Step 1")
        sys.exit(1)
        
    # 2. Local SCP (Local pulls from Orion)
    print("Step 2: Pulling from Orion to Local...")
    require_exercise_dirs()
    remote_sources = [
        f"{ORION}:{ORION_HOME}/shared/{name}"
        for name in EXERCISE_DIRS
    ]
    cmd = [
        "sshpass", "-p", PASSWORD,
        "scp", *SSH_OPTIONS, "-r",
        *remote_sources,
        LOCAL_PARALLEL
    ]
    if not run_cmd(cmd, "Step 2"):
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

    # 2. Local SCP (Local pushes to Orion)
    print("Step 2: Pushing from Local to Orion...")
    local_sources = local_exercise_paths()
    cmd = [
        "sshpass", "-p", PASSWORD,
        "scp", *SSH_OPTIONS, "-r",
        *local_sources,
        f"{ORION}:{ORION_HOME}/shared"
    ]
    if not run_cmd(cmd, "Step 2"):
        print("Failed Step 2")
        sys.exit(1)
        
    # 3. Remote SCP (Orion pushes to Scirouter)
    if not run_step_2_push_remote_scp():
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
