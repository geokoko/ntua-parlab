# Scirouter Synchronization Scripts

This directory contains scripts to synchronize your local work with the remote `scirouter` and `orion` machines.

## Scripts

- `pull.sh`: Pulls changes from the remote server to your local machine.
- `push.sh`: Pushes your local changes to the remote server.

## Setup

To use these scripts, you must configure the environment variables by creating a `.env` file in this directory (`scirouter/`).

1.  Create a file named `.env` inside `scirouter/`.
2.  Add the following variables to the `.env` file, adjusting the values to match your configuration.

### Required Environment Variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `ORION` | SSH connection string for the Orion cluster. | `s0123456@orion.cslab.ece.ntua.gr` |
| `SCIROUTER` | SSH connection string for the SciRouter machine. | `s0123456@scirouter.cslab.ece.ntua.gr` |
| `ORION_HOME` | Your absolute home directory path on Orion (orion.cslab.ece.ntua.gr). | `/home/parallel/parlabXX` |
| `SCIROUTER_SHARED` | The absolute path to the **`/shared`** directory on SciRouter. | `/home/parallel/parlabXX/shared` |
| `LOCAL_PARALLEL` | The absolute path to the root of your local repository. | `./ntua-parlab` |
| `EXERCISE_DIRS` | Space-separated list of directories to sync (relative to repo root). | `a1 a2 a3 a4 (pick the directories you want to sync, regardless of how you named them)` |
| `SSH_OPTIONS` | Additional SSH options (leave empty if none). | `""` |

### Example `.env` File

```bash
# SSH Connection details
ORION=parlabXX@orion.cslab.ece.ntua.gr
SCIROUTER=parlabXX@scirouter.cslab.ece.ntua.gr

# Remote paths
ORION_HOME=/home/parallel/parlabXX
SCIROUTER_SHARED=/home/parallel/parlabXX/shared

# Local configuration
LOCAL_PARALLEL=<YOUR_LOCAL_REPO_PATH>
EXERCISE_DIRS="a1 a2 a3 a4 (pick the directories you want to sync, regardless of how you named them)"

# SSH configuration
SSH_OPTIONS=""
```

## Usage

Once the `.env` file is set up:

To push content to the remote server:
```bash
./scirouter/push.sh
```

To pull content from the remote server:
```bash
./scirouter/pull.sh
```
