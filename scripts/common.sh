#!/bin/sh

# common logging function
log_msg() {
    level="$1"
    name="$2"
    function="$3"
    line="$4"
    message="$5"
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    level_padded=$(printf "%-8s" "$level")
    echo "$timestamp | $level_padded | $name:$function:$line - $message"
}