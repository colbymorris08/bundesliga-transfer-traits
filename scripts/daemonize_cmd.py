#!/usr/bin/env python3
"""Fully detach a long-running command from the Cursor/parent process tree."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def daemonize(workdir: Path, log_path: Path, argv: list[str]) -> int:
    # first fork
    if os.fork() > 0:
        return 0
    os.setsid()
    # second fork
    if os.fork() > 0:
        os._exit(0)

    os.chdir(workdir)
    os.umask(0)

    # redirect stdio
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    if fd > 2:
        os.close(fd)

    os.execvp(argv[0], argv)
    os._exit(127)


def main() -> None:
    if len(sys.argv) < 4:
        print("usage: daemonize_cmd.py WORKDIR LOGPATH CMD [ARGS...]", file=sys.stderr)
        sys.exit(2)
    workdir = Path(sys.argv[1]).resolve()
    log_path = Path(sys.argv[2]).resolve()
    argv = sys.argv[3:]
    code = daemonize(workdir, log_path, argv)
    if code == 0:
        print(f"daemonized: {' '.join(argv)} -> {log_path}", flush=True)


if __name__ == "__main__":
    main()
