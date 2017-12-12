from ICAT_Client import ICAT

# Connect to ICAT
icat = ICAT()
icat_client = icat.get_client()

query_1 = 'SELECT i FROM Instrument i'

entities = icat.execute_query(icat_client, query_1)

for entity in entities:
	print instrument.name

# 1) Print out all Instrument full names

# 2) Print all of the Grouping names

# 3) Print the 'what' column of all of the rules table




