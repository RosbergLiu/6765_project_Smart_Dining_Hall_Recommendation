#!/usr/bin/python

'Table availability detection and update'

__author__ ='Rosberg Liu'

from gpiozero import MotionSensor
import time
import platform
import aws

# Dining hall code define:
# 
# ID		Dining Hall		Node / Hostname				Database Name
# 
# 1			John Jay		Rosberg_RaspberryPi_3BP		EntryCount_JohnJay
# 2			JJ's place		RaspberryPi_lanlan			EntryCount_JJPlace
# 3			Ferris Booth	Rosberg_RaspberryPi_3B		EntryCount_FerrisBooth

#------------------------------------------------------------
# DynamoDB table config

DYNAMO_TABLE_NAME_PIR = "TableAvailability"
dynamodb = aws.getResource('dynamodb', 'us-east-1')
table_PIR = dynamodb.Table(DYNAMO_TABLE_NAME_PIR)

#------------------------------------------------------------
# Dining hall identification

node_ta_id_pair = {
	'Rosberg_RaspberryPi_3BP':1,
	'RaspberryPi_lanlan':2,
	'Rosberg_RaspberryPi_3B':3
	}

node_name_pair = {
	'Rosberg_RaspberryPi_3BP':'John Jay',
	'RaspberryPi_lanlan':"JJ's Place",
	'Rosberg_RaspberryPi_3B':'Ferris Booth'
	}

# set dining hall ID & name for different node individually
DINING_HALL_ID = node_ta_id_pair[platform.node()]
DINING_HALL = node_name_pair[platform.node()]

#------------------------------------------------------------
# threshold define & count initialize

MOVE_COUNT = 30
EMPTY_COUNT = 75
LOOP_SLEEP_TIME = 0.2

#------------------------------------------------------------
# PIR GPIO pins define

PIR_GPIO_SEQUENCE = [17,27,22]

#------------------------------------------------------------
# PIR class

class PIR(object):

	def __init__(self,GPIO_pin,table_id):
		self.pir = MotionSensor(GPIO_pin)
		self.table_id = table_id
		self.move_count = 0
		self.empty_count = 0
		self.occupied = False

	def status_update(self):
		'''
		Update PIR sensor status
		'''
		if self.pir.motion_detected:
			self.move_count += 1
			self.empty_count = 0
		else:
			self.empty_count += 1
			self.move_count = 0
		
		if self.empty_count > EMPTY_COUNT:
			if self.occupied:
				t = int(time.time())
				print('Time: {}, {} table {} empty'.format(t,DINING_HALL,self.table_id))
				self.occupied = False
				table_PIR.update_item(
					Key = {'table_id':self.table_id,'dining_hall_id':DINING_HALL_ID},
					UpdateExpression = "set occupied = :o,ts = :ti",
					ExpressionAttributeValues = {
						':o': self.occupied,
						':ti': t
					}
				)

			self.move_count = 0
			self.empty_count = 0
		

		if self.move_count > MOVE_COUNT:
			if not self.occupied:
				t = int(time.time())
				print('Time: {}, {} table {} occupied'.format(t,DINING_HALL,self.table_id))
				self.occupied = True
				table_PIR.update_item(
					Key = {'table_id':self.table_id,'dining_hall_id':DINING_HALL_ID},
					UpdateExpression = "set occupied = :o,ts = :ti",
					ExpressionAttributeValues = {
						':o': self.occupied,
						':ti': t
					}
				)
			
			self.move_count = 0
			self.empty_count = 0

#------------------------------------------------------------

try:
	pir_list = []

	for index,value in enumerate(PIR_GPIO_SEQUENCE):
		pir_list.append(PIR(value,index+1))

	while True:

		for pir in pir_list:
			pir.status_update()
		
		time.sleep(LOOP_SLEEP_TIME)


except KeyboardInterrupt:
    exit
