#!/usr/bin/python

'Reset (clear all entry) & set initial status for entry count database'

__author__ ='Rosberg Liu'

import aws
import sys,time
import platform

# Dining hall code define:
# 
# ID		Dining Hall		Node / Hostname				Database Name
# 
# 1			John Jay		Rosberg_RaspberryPi_3BP		EntryCount_JohnJay
# 2			JJ's place		RaspberryPi_lanlan			EntryCount_JJPlace
# 3			Ferris Booth	Rosberg_RaspberryPi_3B		EntryCount_FerrisBooth

#------------------------------------------------------------
# DynamoDB table config

node_ec_db_pair = {
	'Rosberg_RaspberryPi_3BP':'EntryCount_JohnJay',
	'RaspberryPi_lanlan':'EntryCount_JJPlace',
	'Rosberg_RaspberryPi_3B':'EntryCount_FerrisBooth'
	}

# set table name for different node individually
DYNAMO_TABLE_NAME_ToF = node_ec_db_pair[platform.node()]
dynamodb = aws.getResource('dynamodb', 'us-east-1')
table_ToF = dynamodb.Table(DYNAMO_TABLE_NAME_ToF)

#------------------------------------------------------------
# Dining hall identification

node_name_pair = {
	'Rosberg_RaspberryPi_3BP':'John Jay',
	'RaspberryPi_lanlan':"JJ's Place",
	'Rosberg_RaspberryPi_3B':'Ferris Booth'
	}

# set dining hall name for different node individually
DINING_HALL = node_name_pair[platform.node()]

#------------------------------------------------------------

try:
	scan = table_ToF.scan(
		ProjectionExpression='#k',
		ExpressionAttributeNames={
			'#k': 'time'
		}
	)

	with table_ToF.batch_writer() as batch:
		for each in scan['Items']:
			batch.delete_item(Key=each)
	
	print('Table status: {}'.format(table_ToF.table_status))

	if len(sys.argv) == 2 and sys.argv[1].isdigit():
		initial_headcount = int(sys.argv[1])
		if initial_headcount >= 0:
			t = int(time.time())
			print('Time: {}, {} set initial headcount as {}'.format(t,DINING_HALL,initial_headcount))
			table_ToF.put_item(Item = {'time':t,'headcount':initial_headcount})
	else:
		t = int(time.time())
		print('Time: {}, {} set initial headcount as 0'.format(t,DINING_HALL))
		table_ToF.put_item(Item = {'time':t,'headcount':0})


except KeyboardInterrupt:
    exit
