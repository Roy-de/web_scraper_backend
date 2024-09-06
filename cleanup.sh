#!/bin/bash
# Cleanup old files in /tmp directory
find /tmp -type f -mtime +1 -exec rm -f {} \;
find /tmp -type d -empty -exec rmdir {} \;
