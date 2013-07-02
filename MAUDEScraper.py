from bs4 import BeautifulSoup
import urllib
import os

desired_fields = ['Model Number', 'Event Date', 'Event Type',
'Patient Outcome', 'Event Description', 'Manufacturer Narrative',
'Brand Name', 'Type of Device', 'Device Event Key', 'MDR Report Key',
'Event Key', 'Report Number', 'Device Sequence Number', 'Product Code',
'Report Source', 'Source Type', 'Reporter Occupation', 'Type of Report',
'Report Date', 'Date FDA Received', 'Is This An Adverse Event Report?',
'Is This A Product Problem Report?', 'Device Operator', 'Device MODEL Number',
'Was Device Available For Evaluation?',
'Is The Reporter A Health Professional?', 'Date Manufacturer Received',
'Was Device Evaluated By Manufacturer?',
'Is The Device Single Use?', 'Type of Device Usage']

"""Takes a local text document of HTML, returns the master beautifulSoup object containing all HTML."""
"""Files will be in a folder, one for each year."""
def loadMasterHTML(filename):
	file = open(filename)
	string = file.read()
	soup = BeautifulSoup(string)
	return soup

"""Takes a string URL for page of a specific record, returns BeautifulSoup object of page."""
"""Each soup object returned from the loadMasterHTML contains URL suffixes for individual records, which are input here."""
def getRecordPage(url):
	thisURL = urllib.urlopen(url)
	toString = thisURL.read()
	toSoup = BeautifulSoup(toString)
	return toSoup

"""Input file name of query results return table of URLs from the page."""
def getURLTable(filename):
	soup = loadMasterHTML(filename)
	table = soup.find_all('table')[7]
	isolated_URLs = table.find_all('a')
	URL_list = []
	for link in isolated_URLs:
		url = link.get('href')
		url = "http://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/" + url[0:len(url)]
		URL_list.append(url)
	URL_list = URL_list[4:len(URL_list)]
	return URL_list

"""Input: a beautifulsoup object of an individual record.
Output: list of all the tags containing all fields, divided into 2 sections."""
def getTagList(record):
	first_table = record.find_all('strong')

	first_table_strings = [tag.string for tag in first_table]
	for i in range(0, len(first_table_strings)):
		if first_table_strings[i] == None:
			first_table_strings[i] = str(first_table_strings[i])
	first_table_strings = [string.strip() for string in first_table_strings]

	second_table = record.find_all('th')

	second_table_strings = [tag.string for tag in second_table]
	for i in range(0, len(second_table_strings)):
		if second_table_strings[i] == None:
			second_table_strings[i] = str(second_table_strings[i])
	second_table_strings = [string.strip() for string in second_table_strings]
	
	"""Here is the part where we pick the ones we want by comparing
	these tables to the desired_fields list."""
	first_table_indices = []
	second_table_indices = []
	for element in first_table_strings:
		if element in desired_fields:
			current_index = first_table_strings.index(element)
			"""Handles duplicates."""
			if current_index in first_table_indices:
				augmented = first_table_strings
				augmented[current_index] = 'jesus'
				current_index = augmented.index(element)
			first_table_indices.append(current_index)
	for element in second_table_strings:
		if element in desired_fields:
			second_table_indices.append(second_table_strings.index(element))
	final_field_list = []
	for index in first_table_indices:
		final_field_list.append(first_table[index])
	for index in second_table_indices:
		final_field_list.append(second_table[index])
	return final_field_list

"""Input: list of tags from function above.
Output:list of associated datapoints."""
special_cases = ['Event Description', 'Manufacturer Narrative']

def getDataPoints(tag_list):
	datapoints = []
	for tag in tag_list:
		if tag.string.strip() in special_cases:
			correct_tag = tag.parent.parent.next_sibling.next_sibling.p
			try:
				datapoint = " ".join(correct_tag.string.split())
			except:
				datapoint = correct_tag.string
			"""Piece for concatenating duplicate records. Logic for making fields match this is not implemented yet so taking it out for now."""
			#if tag_list.index(tag) > 5:
			#	insert_index = desired_fields.index(tag.string.strip())
			#	datapoints[insert_index] = datapoints[insert_index] + datapoint
			#	continue
			try:
				datapoints.append(str(datapoint))
			except:
				datapoints.append(str(''.join(e for e in datapoint if e.isalnum() or e == ' ')))
				
		elif tag.string.strip() not in special_cases and tag.next_sibling.string == '\n':
			datapoint = tag.next_sibling.next_sibling.string.strip()
			try:
				datapoints.append(str(''.join(e for e in datapoint if e.isalnum() or e == ' ')))
			except:
				print ["ERROR:", datapoint]
				return
		else:
			datapoint = tag.next_sibling.string.strip()
			try:
				datapoints.append(str(''.join(e for e in datapoint if e.isalnum() or e == ' ')))
			except:
				print ["ERROR:", datapoint]
				return
	return datapoints

"""Input: filename of html. Output: list of datapoints."""
def extractData(filename):
	URL_table = getURLTable(filename)
	master_list = []
	for url in URL_table:
		record = getRecordPage(url)
		tag_list = getTagList(record)
		datapoints = getDataPoints(tag_list)
		master_list.append(datapoints)
		print datapoints
	return master_list
"""Input: filename of html. Output: list of field names, corresponding exactly to the datapoints above by index."""
def extractFields(filename):
	URL_table = getURLTable(filename)

	field_list = []
	for url in URL_table:
		record = getRecordPage(url)
		tag_list = getTagList(record)
		strings = [str(tag.string) for tag in tag_list]
		for i in range(0, len(strings)):
			if strings[i] == None:
				strings[i] = str(strings[i])
		strings = [string.strip() for string in strings]
		print strings

		field_list.append(strings)
	return field_list

"""Input: a row of fields. Output: indexes from desired_fields of fields that are missing from the row."""
def missing_fields(field_row):
	missing = []
	for field in desired_fields:
		if field not in field_row:
			missing.append(desired_fields.index(field))
	return missing
"""Returns True if row has duplicate fields in it. False if not."""
def has_duplicates(field_row):
	return len(field_row) != len(set(field_row))

"""Incomplete function, do not use."""
"""def fix_duplicates(datapoints, fields):
	no_dup_data = datapoints
	no_dup_fields = fields
	for i in range(0, len(datapoints)):
		field_row = no_dup_fields[i]
		data_row = no_dup_data[i]
		if has_duplicates(field_row):
			for j in range(0, len(field_row)):
				for k in range(0, j):
					if field_row[k] == field_row[j]:
						data_row[k] = data_row[k] + data_row[j]
						del data_row[j]
						del field_row[j]

				if has_duplicates(field_row[j:len(field_row)]) == False:
					break
						
	return [no_dup_data, no_dup_fields]
"""

"""Input: structure containing datapoints, and structure containing corresponding fields.
Output: A list containing both of them, with spaces in the datapoint structure where empty/missing fields were,
and those field names inserted into the field structure."""
def correct(datapoints, fields):
	if len(datapoints) != len(fields):
		print "WTF IS DIS"
		return
	corrected_data = datapoints
	corrected_fields = fields
	for i in range(0, len(datapoints)):
		missing = missing_fields(fields[i])
		for field_number in missing:
			corrected_data[i].insert(field_number, ' ')
			corrected_fields[i].insert(field_number, desired_fields[field_number])
	return [corrected_data, corrected_fields]

"""Input: datapoint structure of field structure. Creates file named 'filename' and writes the junk to it in csv separated by quotes."""
def writeFile(filename, datapoints_or_fields):
	f = open(filename, 'w')
	for line in datapoints_or_fields:
		for point in line:
			f.write("\"%s\"," % point)
		f.write('\n')
		print line
	f.close()

"""Input: string containing file name for html. Output: list with 2 elements, 1st being the datapoints, second containing fields."""
def pullDown(file_in):
	data = extractData(file_in)
	fields = extractFields(file_in)
	corrected = correct(data, fields)
	return corrected

"""Input: a directory. Goes through EVERY file, scrapes the data, and writes the output to files,
one each for fields and datapoints. The do-it-all function."""
def makeThemAll(dir):
	file_list = os.listdir(dir)
	for file in file_list:
		data = extractData(file)
		fields = extractFields(file)
		corrected = correct(data, fields)
		"""Change the index from 7 to 4 when dealing with non-sectioned data."""
		name_this_data = file[0][0:7] + 'Data' + '.csv'
		name_this_fields = file[0][0:7] + 'Fields' + '.csv'
		writeFile(name_this_data, corrected[0])
		writeFile(name_this_fields, corrected[1])
