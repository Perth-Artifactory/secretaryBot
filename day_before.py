#!/usr/bin/python3

# Functions in this file are intended to be triggered the day before a meeting.
# This scripts assumes that interactions with a storage provider will be handled elsewhere.

import glob
import json
import datetime
import os


with open("config.json","r") as f:
    config = json.load(f)

tomorrow = datetime.date.today() + datetime.timedelta(days=1)
meeting_tomorrow = False
for minute in glob.glob(f'{config["minute_directory"]}*.md'):
    file = minute.split("/")[-1].replace(".md","")
    filedate = datetime.datetime.strptime(file,"%Y-%m-%d")
    if (filedate.day, filedate.month, filedate.year) == (tomorrow.day, tomorrow.month, tomorrow.year):
        print(minute)
        meeting_tomorrow = minute
        break

if meeting_tomorrow:
    print(f"There's a meeting tomorrow!: {meeting_tomorrow}")

    print("Running tidyauth inplace_reports.py...")
    cwd = os.getcwd()
    os.chdir(config["tidyAuth_directory"])
    with os.popen(f'python3 ./scripts/inplace_reports.py meeting "{meeting_tomorrow}"') as f:
        print("".join(f.readlines()))