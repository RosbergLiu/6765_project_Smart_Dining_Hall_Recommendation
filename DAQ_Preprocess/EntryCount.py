#!/usr/bin/python

'Diner pass detection & entry upload'

__author__ ='Rosberg Liu'

import time
import VL53L0X
import RPi.GPIO as GPIO
import platform
import aws
import sys

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
# threshold define & count initialize

SET_TO_MAX_THRESHOLD = 1200
MAX = 8190

DIS_DIFF_THRESHOLD = 600

VIEW_AS_EMPTY_THRESHOLD = 1200

DIS_DIFF_COUNT = 5
CLEAR_COUNT = 5

LOOP_SLEEP_TIME = 0.02
GPIO_SETTLE_TIME = 1

L_count = 0
R_count = 0

clear_count = 0

# locally stored headcount
LOCAL_HEADCOUNT = 0

# set initial local headcount if provided
if len(sys.argv) == 2 and sys.argv[1].isdigit():
	initial_headcount = int(sys.argv[1])
	if initial_headcount >= 0:
		LOCAL_HEADCOUNT = initial_headcount
		print('Time: {}, {} set initial headcount as {}'.format(int(time.time()),DINING_HALL,initial_headcount))

#------------------------------------------------------------
# state define

IDLE = 0
L2R_ENTERING = 1
L2R_EXITING = 2
R2L_ENTERING = 3
R2L_EXITING = 4


# state reset

state = IDLE
state_sequence = [IDLE,IDLE,IDLE]

#------------------------------------------------------------
# entry direction define

L2R_HEADCOUNT = -1
R2L_HEADCOUNT = 1

#------------------------------------------------------------
# GPIO config

# GPIO for Sensor L shutdown pin
L_shutdown = 15
# GPIO for Sensor R shutdown pin
R_shutdown = 14


GPIO.setwarnings(False)

# Setup GPIO for shutdown pins on each VL53L0X
GPIO.setmode(GPIO.BCM)
GPIO.setup(L_shutdown, GPIO.OUT)
GPIO.setup(R_shutdown, GPIO.OUT)

# Set all shutdown pins low to turn off each VL53L0X
GPIO.output(L_shutdown, GPIO.LOW)
GPIO.output(R_shutdown, GPIO.LOW)

# Keep all low for 1s or so to make sure they reset
time.sleep(GPIO_SETTLE_TIME)

#------------------------------------------------------------
# ToF initialize

# Create one object per VL53L0X passing the address to give to each.
L_ToF = VL53L0X.VL53L0X(address=0x2D)
R_ToF = VL53L0X.VL53L0X(address=0x2B)


# Set shutdown pin high for the first VL53L0X then 
# call to start ranging 
GPIO.output(L_shutdown, GPIO.HIGH)
time.sleep(GPIO_SETTLE_TIME)
L_ToF.start_ranging(VL53L0X.VL53L0X_HIGH_SPEED_MODE)


# Set shutdown pin high for the second VL53L0X then 
# call to start ranging 
GPIO.output(R_shutdown, GPIO.HIGH)
time.sleep(GPIO_SETTLE_TIME)
R_ToF.start_ranging(VL53L0X.VL53L0X_HIGH_SPEED_MODE)

#------------------------------------------------------------
# Print start timestamp & current local headcount

print('Time: {}, local headcount {}, start detecting\n'.format(int(time.time()),LOCAL_HEADCOUNT))
#------------------------------------------------------------


def data_acquisition():
	'''
	Get raw distance measurement from both ToF sensors & pre-process it by:
		1. filtering out abnormal value
		2. set value greater than certain threshold to max value
	'''

	# get raw distance data
	L_dis = L_ToF.get_distance()
	R_dis = R_ToF.get_distance()

	if L_dis <= 0 or R_dis <= 0:
		return (0,0)
	
	# set to max if measurement result is greater than threshold
	if L_dis > SET_TO_MAX_THRESHOLD:
		L_dis = MAX
	if R_dis > SET_TO_MAX_THRESHOLD:
		R_dis = MAX
	
	return (L_dis,R_dis)

def count_clear():
	'''
	Clear L_count, R_count, clear_count
	'''

	global L_count,R_count,clear_count
	L_count = 0
	R_count = 0
	clear_count = 0


def state_sequence_update():
	'''
	Update state_sequence as a queue / sliding window:\n
	remove the oldest state, and append current state\n
	window size is fixed at 3 (one single successful passing can be identified with 3 contiguous states)
	'''

	global state_sequence
	global state
	state_sequence[0] = state_sequence[1]
	state_sequence[1] = state_sequence[2]
	state_sequence[2] = state

def state_sequence_clear():
	'''
	Clear state_sequence to all IDLE
	'''

	global state_sequence
	state_sequence = [IDLE,IDLE,IDLE]


#------------------------------------------------------------

try:
	while True:
		L_dis,R_dis = data_acquisition()

		# discard this acquisition if either value is 0
		if L_dis == 0 or R_dis == 0:
			continue
		#------------------------------------------------------------
		# measurement count handling

		# sensing obstacle on right side
		if L_dis - R_dis > DIS_DIFF_THRESHOLD:
			R_count += 1
			L_count = 0
			clear_count = 0

		# sensing obstacle on left side
		if R_dis - L_dis > DIS_DIFF_THRESHOLD:
			L_count += 1
			R_count = 0
			clear_count = 0

		# all clear (empty)
		if L_dis > VIEW_AS_EMPTY_THRESHOLD and R_dis > VIEW_AS_EMPTY_THRESHOLD:
			clear_count += 1
			L_count = 0
			R_count = 0

		#------------------------------------------------------------
		# state update

		#------------------------------
		# sensing obstacle on left side
		if L_count >= DIS_DIFF_COUNT:

			# triggered from empty state
			if state == IDLE:
				state = L2R_ENTERING
				print('L2R_ENTERING')
				state_sequence_update()

			# triggered from entry from right side
			elif state == R2L_ENTERING:
				state = R2L_EXITING
				print('R2L_EXITING')
				state_sequence_update()

			count_clear()

		#------------------------------
		# sensing obstacle on right side
		if R_count >= DIS_DIFF_COUNT:
			
			# triggered from empty state
			if state == IDLE:
				state = R2L_ENTERING
				print('R2L_ENTERING')
				state_sequence_update()
			
			# triggered from entry from left side
			elif state == L2R_ENTERING:
				state = L2R_EXITING
				print('L2R_EXITING')
				state_sequence_update()
			
			count_clear()

		#------------------------------
		# empty
		if clear_count >= CLEAR_COUNT:
			if state != IDLE:
				print('IDLE')
				state = IDLE
				state_sequence_update()
			state = IDLE
			count_clear()

		#------------------------------
		# state sequence check & entry upload

		# L2R single pass
		if state_sequence == [L2R_ENTERING,L2R_EXITING,IDLE]:
			t = int(time.time())
			LOCAL_HEADCOUNT += L2R_HEADCOUNT
			print('Time: {}, {}, L2R pass, local headcount: {}'.format(t,DINING_HALL,LOCAL_HEADCOUNT))
			table_ToF.put_item(Item = {'time':t,'headcount':L2R_HEADCOUNT})
			state_sequence_clear()

		# R2L single pass
		if state_sequence == [R2L_ENTERING,R2L_EXITING,IDLE]:
			t = int(time.time())
			LOCAL_HEADCOUNT += R2L_HEADCOUNT
			print('Time: {}, {}, R2L pass, local headcount: {}'.format(t,DINING_HALL,LOCAL_HEADCOUNT))
			table_ToF.put_item(Item = {'time':t,'headcount':R2L_HEADCOUNT})
			state_sequence_clear()

		# sleep
		time.sleep(LOOP_SLEEP_TIME)

		# state update end
		#------------------------------------------------------------

except KeyboardInterrupt:
    exit
