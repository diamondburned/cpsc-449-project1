#!/usr/bin/env python3
import argparse
import sqlite3
import os

parser = argparse.ArgumentParser(
    prog="schema_init.py",
    description="Initialize the SQLite database schema",
)
parser.add_argument("-i", "--input", help="Input schema file", default="schema.sql")
parser.add_argument("-f", "--file", help="SQLite database file", default="database.db")

args = parser.parse_args()

schema_sql_file = open(args.input, "r")
schema_sql = schema_sql_file.read()

schema_testdata_sql_file = open(args.input.replace(".sql", "_testdata.sql"), "r")
schema_testdata_sql = schema_testdata_sql_file.read()

if os.path.isfile(args.file):
    answer = input("Database file already exists. Overwrite? (y/n) ")
    if answer.lower() == "y":
        os.remove(args.file)
    else:
        print("Aborting...")
        exit(1)

conn = sqlite3.connect(args.file)

c = conn.cursor()
c.executescript(schema_sql)

insertTestData = input("Insert test data? (y/n) ")
if insertTestData.lower() == "y":
    c.executescript(schema_testdata_sql)

conn.commit()
conn.close()
