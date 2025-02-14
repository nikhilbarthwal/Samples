# Instructions
# Your task is to implement a simplified version of an in-memory database. All operations that should be supported by this database are described below.
# Solving this task consists of several levels. Subsequent levels are opened when the current level is correctly solved. You always have access to the data for the current and all previous levels.
# 
# Requirements
# Your task is to implement a simplified version of an in-memory database. Plan your design according to the level specifications below:
# 
# Level 1: In-memory database should support basic operations to manipulate records, fields, and values within fields.
# Level 2: In-memory database should support displaying a specific record's fields based on a filter.
# Level 3: In-memory database should support TTL (Time-To-Live) configurations on database records.
# Level 4: In-memory database should support backup and restore functionality.
# 
# Instructions
# Your task is to implement a simplified version of an in-memory database. All operations that should be supported by this database are described below.
# 
# Solving this task consists of several levels. Subsequent levels are opened when the current level is correctly solved. You always have access to the data for the current and all previous levels.
# 
# Requirements
# Your task is to implement a simplified version of an in-memory database. Plan your design according to the level specifications below:
# 
# Level 1: In-memory database should support basic operations to manipulate records, fields, and values within fields.
# 
# Expand to see level 1 details.
# The basic level of the in-memory database contains records. Each record can be accessed with a unique identifier key of string type. A record may contain several field-value pairs, both of which are of string type.
# 
# SET <key> <field> <value> — should insert a field-value pair to the record associated with key. If the field in the record already exists, replace the existing value with the specified value. If the record does not exist, create a new one. This operation should return an empty string.
# 
# GET <key> <field> — should return the value contained within field of the record associated with key. If the record or the field doesn't exist, should return an empty string.
# 
# DELETE <key> <field> — should remove the field from the record associated with key. Returns "true" if the field was successfully deleted, and "false" if the key or the field do not exist in the database.
# 
# 
# 
# 
# Level 2: In-memory database should support displaying a specific record's fields based on a filter.
# 
# Expand to see level 2 details.
# The database should support displaying data based on filters. Introduce an operation to support printing some fields of a record.
# 
# SCAN <key> — should return a string representing the fields of a record associated with key. The returned string should be in the following format "<field1>(<value1>), <field2>(<value2>), ...", where fields are sorted lexicographically. If the specified record does not exist, returns an empty string.
# 
# SCAN_BY_PREFIX <key> <prefix> — should return a string representing some fields of a record associated with key. Specifically, only fields that start with prefix should be included. The returned string should be in the same format as in the SCAN operation with fields sorted in lexicographical order.
# 
# 
# 
# Level 3: In-memory database should support TTL (Time-To-Live) configurations on database records.
# 
# Expand to see level 3 details.
# Support the timeline of operations and TTL (Time-To-Live) settings for records and fields. Each operation from previous levels now has an alternative version with a timestamp parameter to represent when the operation was executed. For each field-value pair in the database, the TTL determines how long that value will persist before being removed.
# 
# Notes:
# 
# Time should always flow forward, so timestamps are guaranteed to strictly increase as operations are executed.
# 
# Each test cannot contain both versions of operations (with and without timestamp). However, you should maintain backward compatibility, so all previously defined methods should work in the same way as before.
# 
# SET_AT <key> <field> <value> <timestamp> — should insert a field-value pair or updates the value of the field in the record associated with key. This operation should return an empty string.
# 
# SET_AT_WITH_TTL <key> <field> <value> <timestamp> <ttl> — should insert a field-value pair or update the value of the field in the record associated with key. Also sets its Time-To-Live starting at timestamp to be ttl. The ttl is the amount of time that this field-value pair should exist in the database, meaning it will be available during this interval: [timestamp, timestamp + ttl). This operation should return an empty string.
# 
# DELETE_AT <key> <field> <timestamp> — the same as DELETE, but with timestamp of the operation specified. Should return "true" if the field existed and was successfully deleted and "false" if the key didn't exist.
# 
# GET_AT <key> <field> <timestamp> — the same as GET, but with timestamp of the operation specified.
# 
# SCAN_AT <key> <timestamp> — the same as SCAN, but with timestamp of the operation specified.
# 
# SCAN_BY_PREFIX_AT <key> <prefix> <timestamp> — the same as SCAN_BY_PREFIX, but with timestamp of the operation specified.
# 
# Level 4: In-memory database should support backup and restore functionality.
# 
# To move to the next level, you need to pass all the tests at this level.
# 
# Note
# 
# You will receive a list of queries to the system, and the final output should be an array of strings representing the returned values of all queries. Each query will only call one operation.
# 
# 
# 
# 
# Level 4
# The database should be backed up from time to time. Introduce operations to support backing up and restoring the database state based on timestamps. When restoring, ttl expiration times should be recalculated accordingly.
# 
# BACKUP <timestamp> — should save the database state at the specified timestamp, including the remaining ttl for all records and fields. Remaining ttl is the difference between their initial ttl and their current lifespan (the duration between the timestamp of this operation and their initial timestamp). Returns a string representing the number of non-empty non-expired records in the database.
# 
# RESTORE <timestamp> <timestampToRestore> — should restore the database from the latest backup before or at timestampToRestore. It's guaranteed that a backup before or at timestampToRestore will exist. Expiration times for restored records and fields should be recalculated according to the timestamp of this operation - since the database timeline always flows forward, restored records and fields should expire after the timestamp of this operation, depending on their remaining ttls at backup. This operation should return an empty string.
# 
# Examples
# The example below shows how these operations should work (the section is scrollable to the right):
# 
# Queries Explanations
# queries = [
#   ["SET_AT_WITH_TTL", "A", "B", "C", "1", "10"],
# 
#   ["BACKUP", "3"],
#   ["SET_AT", "A", "D", "E", "4"],
#   ["BACKUP", "5"],
#   ["DELETE_AT", "A", "B", "8"],
#   ["BACKUP", "9"],
#   ["RESTORE", "10", "7"],
# 
# 
# 
# 
#   ["BACKUP", "11"],
#   ["SCAN_AT", "A", "15"],
#   ["SCAN_AT", "A", "16"]
# ]
# 
# returns ""; database state: {"A": {"B": "C"}}
#   with lifespan `[1, 11)`, meaning that the record should be deleted at timestamp = 11.
# returns "1"; saves the database state
# returns ""; database state: {"A": {"D": "E", "B": "C"}}
# returns "1"; saves the database state
# returns "true"; database state: {"A": {"D": "E"}}
# returns "1"; saves the database state
# returns ""; restores the database to state of last backup at timestamp = 5:
#   {"A": {"D": "E", "B": "C"}}
#   with {"B": "C"} expiring at timestamp = 16: Since the initial ttl of the field is 10
#   and the database was restored to the state at timestamp = 5; this field has had
#   a lifespan of 4 and a remaining ttl of 6, so it will now expire at timestamp = 10 + 6 = 16.
# returns "1"; saves the database state
# returns "B(C), D(E)"
# returns "D(E)"
# 
# the output should be ["", "1", "", "1", "true", "1", "", "1", "B(C), D(E)", "D(E)"].
# 
# Input/Output
# 
# [execution time limit] 0.5 seconds (fs)
# 
# [memory limit] 1 GB
# 
# [input] array.array.string queries
# 
# An array of queries to the system. It is guaranteed that all the queries parameters are valid: each query calls one of the operations described in the description, all operation parameters are given in the correct format, and all conditions required for each operation are satisfied.
# 
# Guaranteed constraints:
# 1 ≤ queries.length ≤ 500.
# 
# [output] array.string
# 
# An array of strings representing the returned values of queries.
# 
