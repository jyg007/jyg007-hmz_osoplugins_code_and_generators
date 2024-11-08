#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#


def parse_wait_time(wait_time: str):
    hours, minutes, seconds = 0, 0, 0
    wait_time = wait_time.lower()
    if "h" in wait_time:
        hours = int(wait_time.split("h")[0])
        wait_time = wait_time.split("h")[1]
    if "m" in wait_time:
        minutes = int(wait_time.split("m")[0])
        wait_time = wait_time.split("m")[1]
    if "s" in wait_time:
        seconds = int(wait_time.split("s")[0])
    # Convert the hours, minutes, and seconds to total seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds
