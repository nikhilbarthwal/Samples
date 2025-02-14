# """
# Instructions
# Your task is to implement a simplified version of a banking system. All operations that should be supported are listed below.
# 
# Solving this task consists of several levels. Subsequent levels are opened when the current level is correctly solved. You always have access to the data for the current and all previous levels.
# 
# Requirements
# Your task is to implement a simplified version of a banking system. Plan your design according to the level specifications below:
# 
# Level 1: The banking system should support creating new accounts and depositing money into and withdrawing/paying money from accounts.
# 
# Expand to see level 1 details.
# The banking system should support creating new accounts and depositing money into and withdrawing/paying money from accounts.
# 
# CREATE_ACCOUNT <timestamp> <accountId> — should create a new account with the given accountId if it doesn't already exist. Returns "true" if the account was successfully created or "false" if an account with accountId already exists.
# 
# DEPOSIT <timestamp> <accountId> <amount> — should deposit the given amount of money to the specified account accountId. Returns a string representing the total amount of money in the account (balance) after processing the query. If the specified account does not exist, should return an empty string.
# 
# PAY <timestamp> <accountId> <amount> — should withdraw the given amount of money from the specified account. Returns a string representing the amount of money in the account (balance) after processing the query. If the specified account does not exist, or if the account has insufficient funds to perform the withdrawal, should return an empty string.
# 
# Level 2: The banking system should support ranking accounts based on the total value of transactions.
# 
# Expand to see level 2 details.
# The banking system should support ranking accounts based on the total value of transactions.
# 
# TOP_ACTIVITY <timestamp> <n> — should return the top n accounts with the highest total value of transactions sorted in descending order (in case of ties, sorted alphabetically by accountId in ascending order). The returned value should be a string representing an array of accounts and transaction values in this format "<accountId1>(<transactionsValue1>), <accountId2>(<transactionsValue2>), ..., <accountIdN>(<transactionsValueN>)".
# Total value of transactions is defined as the sum of all transactions for an account (regardless of how the transaction affects account balance), including the amount of money deposited, withdrawn, and/or successfully transferred (transfers will be introduced on level 3, so you can ignore them for now).
# If less than n accounts exist in the system, return all active accounts (in the described format).
# Level 3: The banking system should support scheduling transfers and checking the scheduled transfer status.
# 
# Level 4: The banking system should support merging two accounts while retaining the balances and transaction histories of the original accounts.
# 
# To move to the next level, you should pass all the tests at the current level.
# 
# Note
# 
# You will receive a list of queries to the system, and the final output should be an array of strings representing the returned values of all queries. Each query will only call one operation.
# 
# All queries will have a timestamp parameter — a stringified timestamp in milliseconds. It is guaranteed that all timestamps are unique and are in a range from 1 to 109. Queries will be given in the order of strictly increasing timestamps.
# 
# Level 3
# The banking system should allow scheduling payments and checking the status of scheduled payments.
# 
# TRANSFER <timestamp> <sourceAccountId> <targetAccountId> <amount> — should initiate a transfer between accounts. The given amount of money should be withdrawn from the source account sourceAccountId and held until the transfer is accepted by the target account targetAccountId, or until the transfer expires. The withheld money is added back to the source account's balance if the transfer expires. After the query is processed:
# 
# Returns an empty string if sourceAccountId is equal to targetAccountId.
# Returns an empty string if sourceAccountId or targetAccountId doesn't exist.
# Returns an empty string if the source account sourceAccountId has insufficient funds to perform the transfer.
# The expiration period is 24 hours, which is equal to 24 · 60 · 60 · 1000 = 86400000 milliseconds. A transfer expires at the beginning of the next millisecond after the expiration period ends.
# A valid TRANSFER should return a string containing a unique transfer ID in the following format "transfer[ordinal number of the transfer]", e.g., "transfer1", "transfer2", etc.
# For transfers, transaction history for source and target accounts is only updated when the transfer is accepted.
# Transfers count toward the total value of transactions of both source and target accounts.
# ACCEPT_TRANSFER <timestamp> <accountId> <transferId> — should accept the transfer with the given transferId.
# 
# Returns "true" if the transfer was successfully accepted or "false" otherwise.
# Returns "false" if a transfer with transferId does not exist, was already accepted, or has expired.
# Returns "false" if the given accountId was not the target account for the transfer.
# Examples
# The examples below show how these operations should work (the section is scrollable to the right):
# 
# Queries	Explanations
# queries = [
#   ["CREATE_ACCOUNT", "1", "account1"],
#   ["CREATE_ACCOUNT", "2", "account2"],
#   ["DEPOSIT", "3", "account1", "2000"],
#   ["DEPOSIT", "4", "account2", "3000"],
#   ["TRANSFER", "5", "account1", "account2", "5000"],
#   ["TRANSFER", "16", "account1", "account2", "1000"],
#   ["ACCEPT_TRANSFER", "20", "account1", "transfer1"],
#   ["ACCEPT_TRANSFER", "21", "non-existing", "transfer1"],
#   ["ACCEPT_TRANSFER", "22", "account1", "transfer2"],
#   ["ACCEPT_TRANSFER", "25", "account2", "transfer1"],
#   ["ACCEPT_TRANSFER", "30", "account2", "transfer1"],
#   ["TRANSFER", "40", "account1", "account2", "1000"],
#   ["ACCEPT_TRANSFER", str(45 + MILLISECONDS_IN_1_DAY), "account2", "transfer2"],
#   ["TRANSFER", str(50 + MILLISECONDS_IN_1_DAY), "account1", "account1", "1000"]
# ]
# 
# returns "true"
# returns "true"
# returns "2000"
# returns "3000"
# returns ""; "account1" has insufficient funds
# returns "transfer1"
# returns "false"; "account1" is not the target account for this transfer
# returns "false"; this account does not exist
# returns "false"; this transfer does not exist
# returns "true"
# returns "false"; the transfer was already accepted
# returns "transfer2"
# returns "false"; the transfer has expired
# returns ""; the source account is equal to the target account
# 
# the output should be ["true", "true", "2000", "3000", "", "transfer1", "false", "false", "false", "true", "false", "transfer2", "false", ""].
# 
# Another example:
# 
# Queries	Explanations
# queries = [
#   ["CREATE_ACCOUNT", "1", "account1"],
#   ["CREATE_ACCOUNT", "2", "account2"],
#   ["CREATE_ACCOUNT", "3", "account3"],
#   ["DEPOSIT", "4", "account1", "1000"],
#   ["DEPOSIT", "5", "account2", "1100"],
#   ["DEPOSIT", "6", "account3", "1200"],
#   ["TRANSFER", "7", "account2", "account1", "300"],
#   ["TOP_ACTIVITY", "8", "3"],
#   ["ACCEPT_TRANSFER", "9", "account1", "transfer1"],
#   ["TOP_ACTIVITY", "10", "3"]
# ]
# 
# returns "true"
# returns "true"
# returns "true"
# returns "1000"
# returns "1100"
# returns "1200"
# returns "transfer1"
# returns "account3(1200), account2(1100), account1(1000)"
# returns "true"
# returns "account2(1400), account1(1300), account3(1200)"
# 
# the output should be ["true", "true", "true", "1000", "1100", "1200", "transfer1", "account3(1200), account2(1100), account1(1000)", "true", "account2(1400), account1(1300), account3(1200)"].
# 
# Input/Output
# 
# [execution time limit] 4 seconds (py3)
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
# [Python 3] Syntax Tips
# 
# # Prints help message to the console
# # Returns a string
# def helloWorld(name):
#     print("This prints to the console when you Run Tests")
#     return "Hello, " + name
# """
# 
