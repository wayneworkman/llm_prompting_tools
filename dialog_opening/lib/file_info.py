# lib/file_info.py (place in ./lib/file_info.py)

import pwd
import grp
import time
from stat import filemode

def human_readable_size(size):
    """Convert a size in bytes into a human-readable string."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024**2:
        return f"{size/1024:.1f}K"
    elif size < 1024**3:
        return f"{size/(1024**2):.1f}M"
    else:
        return f"{size/(1024**3):.1f}G"

def format_file_line(path, st):
    """Format a single file line similar to `ls -l` output with human-readable size."""
    perms = filemode(st.st_mode)
    nlink = st.st_nlink
    owner = pwd.getpwuid(st.st_uid).pw_name if hasattr(pwd, 'getpwuid') else st.st_uid
    group = grp.getgrgid(st.st_gid).gr_name if hasattr(grp, 'getgrgid') else st.st_gid
    size = human_readable_size(st.st_size)
    mtime = time.localtime(st.st_mtime)
    mtime_str = time.strftime("%b %d %H:%M", mtime)
    import os
    name = os.path.basename(path)
    return f"{perms} {nlink} {owner} {group} {size} {mtime_str} {name}"
