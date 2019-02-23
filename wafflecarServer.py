import socket
import io
import time
import struct
import os
import onionGpio
import threading
import signal
import sys
from OmegaExpansion import onionI2C

server_address = ('192.168.3.1', 19126)
stopTimerVal= 0
i2c = onionI2C.OnionI2C()

def pwm_init():
	print('[Alert] Starting servo motor initialization..')
	os.system('omega2-ctrl gpiomux set pwm0 pwm')
	time.sleep(1)
	os.system('omega2-ctrl gpiomux set pwm1 pwm')
	time.sleep(1)
	print('[Alert] Servo motor initialization finished..')

def gpio_init():
	print('[Alert] Strat gpio pins for DC motor are initialized..')
	status11 = gpio11.setOutputDirection(0)
	status17 = gpio17.setOutputDirection(0)
	status16 = gpio16.setOutputDirection(0)
	status15 = gpio15.setOutputDirection(0)
	time.sleep(1)
	if status11 == 0 and status17 == 0 and status16 == 0 and status15 == 0:
		print('[Alert] GPIO pins are ready..')
	else:
		print('[Alert] Gpio init failed..')

def makeuint16(lsb, msb):
	return ((msb & 0xFF) << 8)  | (lsb & 0xFF)

def getDistance():
	try:
		i2c.writeByte(0x29, 0x000, 0x01)
		data = i2c.readBytes(0x29, 0x14, 12)
		distance = makeuint16(data[11], data[10])
		if distance < 20 or 2000 < distance:
			distance = 0
	except Exception as e:
		distance = 0
	return '%04d' % distance

def vehicle_backward():
	servoCmd = '''fast-gpio pwm 11 0 0;
	fast-gpio pwm 17 100 90;
	fast-gpio pwm 16 0 0;
	fast-gpio pwm 15 100 90
	'''
	os.system(servoCmd)
	# gpio11.setValue(0)
	# gpio17.setValue(1)
	# gpio16.setValue(0)
	# gpio15.setValue(1)
	
    
def vehicle_forward():
	servoCmd = '''fast-gpio pwm 11 100 90;
	fast-gpio pwm 17 0 0;
	fast-gpio pwm 16 100 90;
	fast-gpio pwm 15 0 0
	'''
	os.system(servoCmd)
	# gpio11.setValue(1)
	# gpio17.setValue(0)
	# gpio16.setValue(1)
	# gpio15.setValue(0)

def vehicle_stop():
	servoCmd = '''fast-gpio pwm 11 0 0;
	fast-gpio pwm 17 0 0;
	fast-gpio pwm 16 0 0;
	fast-gpio pwm 15 0 0
	'''
	os.system(servoCmd)
	# gpio11.setValue(0)
	# gpio17.setValue(0)
	# gpio16.setValue(0)
	# gpio15.setValue(0)
	vehicle_turn(150)

def vehicle_steeringTest():
	servoCmd = '''fast-gpio pwm 11 0 0;
	fast-gpio pwm 17 0 0;
	fast-gpio pwm 16 0 0;
	fast-gpio pwm 15 0 0
	'''
	os.system(servoCmd)
	# gpio11.setValue(0)
	# gpio17.setValue(0)
	# gpio16.setValue(0)
	# gpio15.setValue(0)

def vehicle_turn(angle):
    # 140 - 160
    # 150 is Center
    if angle < 136:
        angle = 136
    elif angle > 165:
        angle = 165
    
    # The servo motor of wafflecar supports 12.6 to 16.5, and 14.0 is center. (The range of Jajucha steering angle is 140 to 160)
    # In order to keep coincident with Jajucha protocol, 10 will be subtracted.
    servoCmd = 'onion pwm 0 %0.1f 60' % ((angle-10)/10.0)
    os.system(servoCmd)
    
def stopTimer():
	global stopTimerVal
	stopTimerVal += 1
	if stopTimerVal > 2:
		try:
			vehicle_stop()
			print('Stop timer is running during %ds..' % (stopTimerVal-2))
		except Exception as e:
			print('Error occured: ', e)
	timer = threading.Timer(1, stopTimer)
	timer.daemon = True
	timer.start()
	
def signal_handler(signal, frame):
	print('wafflecar server exit..')
	sys.exit(0)
	
	
########################
	
	
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(server_address)
print('[Alert] Server initialized...')

# gpio init
gpio11 = onionGpio.OnionGpio(11)
gpio17 = onionGpio.OnionGpio(17)
gpio16 = onionGpio.OnionGpio(16)
gpio15 = onionGpio.OnionGpio(15)

pwm_init()
gpio_init()
vehicle_stop()

# timer start
stopTimer()

# main start
signal.signal(signal.SIGINT, signal_handler)
prevCmd = '0'
while True:
	try:
		# get commands from the user
		data, addr = server_socket.recvfrom(15)
		
		# send distance data to the user
		server_socket.sendto(getDistance(), addr)
		
		# high level command protocol
		if data[0] == 'H':
			comm = data.split(',')
			# correct command input
			if comm[0] == 'H' and comm[4] == 'E':
				stopTimerVal = 0
				
				# power control
				if comm[1][0] == 'F': # forward
					# set right wheel speed
					if comm[1][1] == '1':
						servoCmd = '''fast-gpio pwm 11 100 90;
						fast-gpio pwm 17 0 0
						'''
					elif comm[1][1] == '2':
						servoCmd = '''fast-gpio pwm 11 100 50;
						fast-gpio pwm 17 0 0
						'''
					elif comm[1][1] == '3':
						servoCmd = '''fast-gpio pwm 11 100 0;
						fast-gpio pwm 17 0 0
						'''
					else:
						servoCmd = '''fast-gpio pwm 11 0 0;
						fast-gpio pwm 17 0 0
						'''
					os.system(servoCmd)

				if comm[2][0] == 'F': # forward
					# set left wheel speed
					if comm[2][1] == '1':
						servoCmd = '''fast-gpio pwm 16 100 90;
						fast-gpio pwm 15 0 0
						'''
					elif comm[2][1] == '2':
						servoCmd = '''fast-gpio pwm 16 100 50;
						fast-gpio pwm 15 0 0
						'''
					elif comm[2][1] == '3':
						servoCmd = '''fast-gpio pwm 16 100 0;
						fast-gpio pwm 15 0 0
						'''
					else:
						servoCmd = '''fast-gpio pwm 16 0 0;
						fast-gpio pwm 15 0 0
						'''
					os.system(servoCmd)
				if comm[1][0] == 'B': # backward
					# set right wheel speed
					if comm[1][1] == '1':
						servoCmd = '''fast-gpio pwm 11 0 0;
						fast-gpio pwm 17 100 90
						'''
					elif comm[1][1] == '2':
						servoCmd = '''fast-gpio pwm 11 0 0;
						fast-gpio pwm 17 100 50
						'''
					elif comm[1][1] == '3':
						servoCmd = '''fast-gpio pwm 11 0 0;
						fast-gpio pwm 17 100 0
						'''
					else:
						servoCmd = '''fast-gpio pwm 11 0 0;
						fast-gpio pwm 17 0 0
						'''
					os.system(servoCmd)
				if comm[2][0] == 'B': # backward
					# set left wheel speed
					if comm[1][1] == '1':
						servoCmd = '''fast-gpio pwm 16 0 0;
						fast-gpio pwm 15 100 90
						'''
					elif comm[1][1] == '2':
						servoCmd = '''fast-gpio pwm 16 0 0;
						fast-gpio pwm 15 100 50
						'''
					elif comm[1][1] == '3':
						servoCmd = '''fast-gpio pwm 16 0 0;
						fast-gpio pwm 15 100 0
						'''
					else:
						servoCmd = '''fast-gpio pwm 16 0 0;
						fast-gpio pwm 15 0 0
						'''
					os.system(servoCmd)
				
				# steering wheel angle
				vehicle_turn(int(comm[3]))
				
			else: # incorrect command input
				print('invalid command received', data)
				
		# low level command protocol
		elif data[0] == 'L':
			# low level command protocol does not support wheel speed control.
			if len(data) is 6 and data[5] == 'E':
				stopTimerVal = 0
				# power control
				if data[1] == '0' and prevCmd != data[1]:
					vehicle_stop()
					prevCmd = data[1]
				elif data[1] == '1' and prevCmd != data[1]:
					vehicle_forward()
					prevCmd = data[1]
				elif data[1] == '2' and prevCmd != data[1]:
					vehicle_backward()
					prevCmd = data[1]
				elif data[1] == '3' and prevCmd != data[1]:
					vehicle_steeringTest()
					prevCmd = data[1]
					
				vehicle_turn(int(data[2:5]))
			else:
				print('invalid command received: ', data)
				
	except Exception as e:
		print('Error: ', e)
