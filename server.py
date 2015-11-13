import socket
import numpy as np
import skfuzzy as fuzz

HOST = '127.0.0.1'
PORT = 4321

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
server = s.makefile()

while True:



	"""
	Rules:
	1. IF l_dist_sensor IS small THEN l_motor_power IS small AND r_motor_power IS high
	2. IF l_dist_sensor IS medium THEN l_motor_power IS medium AND r_motor_power IS medium
	3. IF l_dist_sensor IS high THEN l_motor_power IS high AND r_motor_power IS small
	"""

	# Input
	l_dist_sensor_str = server.readline()
	r_dist_sensor_str = server.readline()

	# if l_dist_sensor_str == 'Infinity\n':
	# 	l_dist_sensor = 2.0
	if 'Infinity' in l_dist_sensor_str:
		l_dist_sensor = 0.0
	else:
		l_dist_sensor = float(l_dist_sensor_str)

	# if r_dist_sensor_str == 'Infinity\n':
	# 	r_dist_sensor = 2.0
	if 'Infinity' in r_dist_sensor_str:
		r_dist_sensor = 0.0
	else:
		r_dist_sensor = float(r_dist_sensor_str)
	

	# Generate universe variables
	l_dist = np.arange(-2, 2.01, 0.01)
	r_dist = np.arange(-2, 2.01, 0.01)
	l_power = np.arange(0, 11, 0.25)
	r_power = np.arange(0, 11, 0.25)


	# Generate fuzzy membership functions
	l_dist_lo = fuzz.trimf(l_dist, [-2, -2, 0])
	l_dist_md = fuzz.trimf(l_dist, [-2, 0, 2])
	l_dist_hi = fuzz.trimf(l_dist, [0, 2, 2])

	r_dist_lo = fuzz.trimf(r_dist, [-2, -2, 0])
	r_dist_md = fuzz.trimf(r_dist, [-2, 0, 2])
	r_dist_hi = fuzz.trimf(r_dist, [0, 2, 2])

	l_power_lo = fuzz.trimf(l_power, [0, 0, 5])
	l_power_md = fuzz.trimf(l_power, [0, 5, 10])
	l_power_hi = fuzz.trimf(l_power, [5, 10, 10])

	r_power_lo = fuzz.trimf(r_power, [0, 0, 5])
	r_power_md = fuzz.trimf(r_power, [0, 5, 10])
	r_power_hi = fuzz.trimf(r_power, [5, 10, 10])


	# We need the activation of our fuzzy membership functions at these values.
	l_dist_level_lo = fuzz.interp_membership(l_dist, l_dist_lo, l_dist_sensor)
	l_dist_level_md = fuzz.interp_membership(l_dist, l_dist_md, l_dist_sensor)
	l_dist_level_hi = fuzz.interp_membership(l_dist, l_dist_hi, l_dist_sensor)

	r_dist_level_lo = fuzz.interp_membership(r_dist, r_dist_lo, r_dist_sensor)
	r_dist_level_md = fuzz.interp_membership(r_dist, r_dist_md, r_dist_sensor)
	r_dist_level_hi = fuzz.interp_membership(r_dist, r_dist_hi, r_dist_sensor)


	# Now we take our rules and apply them.
	active_rule1 = l_dist_level_lo
	active_rule2 = l_dist_level_md
	active_rule3 = l_dist_level_hi


	l_dist_activation_lo = np.fmin(active_rule1, l_power_lo)
	l_dist_activation_md = np.fmin(active_rule2, l_power_md)
	l_dist_activation_hi = np.fmin(active_rule3, l_power_hi)

	r_dist_activation_lo = np.fmin(active_rule1, r_power_hi)
	r_dist_activation_md = np.fmin(active_rule2, r_power_md)
	r_dist_activation_hi = np.fmin(active_rule3, r_power_lo)



	# Aggregate all three output membership functions together
	aggregated_l = np.fmax(l_dist_activation_lo, np.fmax(l_dist_activation_md, l_dist_activation_hi))
	aggregated_r = np.fmax(r_dist_activation_lo, np.fmax(r_dist_activation_md, r_dist_activation_hi))


	# Calculate defuzzified result
	l_motor_power = fuzz.defuzz(l_power, aggregated_l, 'centroid')
	r_motor_power = fuzz.defuzz(r_power, aggregated_r, 'centroid')
	
	print(l_motor_power, r_motor_power)

	s.sendall((str(r_motor_power)+'\n').encode())
	s.sendall((str(l_motor_power)+'\n').encode())


s.close()