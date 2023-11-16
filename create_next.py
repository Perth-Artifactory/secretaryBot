#!/usr/bin/python3

import re
import json
import os

from datetime import datetime

with open("config.json", "r") as f:
    config = json.load(f)

minute_filenames = [fn for fn in os.listdir(config["minute_directory"]) if fn.endswith(".md")]

# Make sure that every minute filename is (probably) an ISO date.
for filename in minute_filenames:
    assert re.match(r"\d{4}-\d{2}-\d{2}\.md", filename)

# Once we are sure that all the minute filenames are ISO dates, the latest minute file is simply the last one in the
# list.
assert len(minute_filenames) >= 1
newest_file = sorted(minute_filenames)[-1]
newest = datetime.strptime(newest_file, "%Y-%m-%d.md")
print(f"Newest file: {newest_file}")

# Check if the newest minutes file contains the date of the next meeting
newest_file_path = os.path.join(config["minute_directory"], newest_file)
with open(newest_file_path, "r") as f:
    old_minutes = f.read()

next_meeting_pattern = re.compile(pattern=r"""
Next\ meeting:\s
(?P<date>\d{4}-\d{2}-\d{2})
,?
\s+
(?P<hours>(2[0-3]|[01]?[0-9]))
:?
(?P<minutes>[0-5][0-9])
\s?
(h|hrs)?
""", flags=re.VERBOSE)

next_meeting_date = re.search(next_meeting_pattern, old_minutes)

# If the next meeting date hasn't been set, do nothing.
if not next_meeting_date:
    print("No next meeting found")

# If the next meeting date has been set -
# * Replace placeholder links to the next meeting minutes with a link to the new minutes
# * Create the new minutes
else:
    next_meeting_date_and_time = f"{next_meeting_date.group('date')} {next_meeting_date.group('hours')}:{next_meeting_date.group('minutes')}"
    next_meeting = datetime.strptime(next_meeting_date_and_time, "%Y-%m-%d %H:%M")

    # Clean up any stray template links to the next meeting that haven't been filled in
    next_meeting_date = re.sub("NNNN-NN-NN", next_meeting.strftime("%Y-%m-%d"), old_minutes)
    if next_meeting_date != old_minutes:
        with open(newest_file_path, "w") as f:
            f.write(next_meeting_date)
            old_minutes = next_meeting_date

    with open(config["minute_template"], "r") as f:
        template = f.read()

    # Add scheduled start date/time
    template = template.replace("Scheduled start: \n", f'Scheduled start: {next_meeting.strftime("%Y-%m-%d, %H:%M")}\n')

    # Add links to previous minutes
    template = template.replace("PPPP-PP-PP", newest.strftime("%Y-%m-%d"))

    # Add name of current meeting
    template = template.replace("yyyy-mm-dd", next_meeting.strftime("%Y-%m-%d"))

    # Change page creation time
    d = datetime.utcnow()
    s = f'{d.isoformat().split(".")[0]}.{round(d.microsecond / 1000)}Z'

    template = re.sub("dateCreated: .{24}", "dateCreated: " + s, template)
    template = re.sub("date: .{24}", "date: " + s, template)

    if len(old_minutes.split("## Action Summary\n\n")) < 2:
        action_items = "No action items from previous meeting"
    else:
        action_items = old_minutes.split("## Action Summary\n\n")[1]
        action_items = action_items.replace("|\n", "| Status | \n", 1)
        action_items = action_items.replace("|\n", "| ------ | \n", 1)
        action_items = action_items.replace("|\n", "| STATUS | \n")
        action_items = action_items.replace("| \n", "|\n")
    sect = "## Review Previous Meeting's Action Items\n"
    template = template.replace(sect, f'{sect}\n{action_items}')

    # Add to minute directory
    new_minutes_path = os.path.join(config["minute_directory"],
                                    next_meeting.strftime("%Y-%m-%d") + ".md")
    with open(new_minutes_path, "w") as f:
        f.write(template)
