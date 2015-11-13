import socket
import numpy as np
import skfuzzy as fuzz

HOST = '127.0.0.1'
PORT = 4321

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
server = s.makefile()


def adjust_levels(min, max, mid_offset_percent, clip_max=False):
	if clip_max:
		max = max*0.6
	mid_min = (max+min)/2 - max * mid_offset_percent
	mid_max = (max+min)/2 + max * mid_offset_percent
	lo = [min, min, mid_min]
	md = [min, mid_min, mid_max]
	hi = [mid_min, mid_max, max]

	return [lo, md, hi]

while True:

	"""
	Rules:
	1. IF l_dist_sensor IS small THEN l_motor_power IS small
	2. IF l_dist_sensor IS medium THEN l_motor_power IS medium
	3. IF l_dist_sensor IS high THEN l_motor_power IS high
	4. IF r_dist_sensor IS small THEN r_motor_power IS small
	5. IF r_dist_sensor IS medium THEN r_motor_power IS medium
	6. IF r_dist_sensor IS high THEN r_motor_power IS high
	"""

	# Input
	l_dist_sensor_str = server.readline()
	r_dist_sensor_str = server.readline()

	if l_dist_sensor_str == 'Infinity\n':
		l_dist_sensor = -1.5
	elif 'Infinity' in l_dist_sensor_str:
		l_dist_sensor = -1.5
	else:
		l_dist_sensor = float(l_dist_sensor_str)

	if r_dist_sensor_str == 'Infinity\n':
		r_dist_sensor = -1.5
	if 'Infinity' in r_dist_sensor_str:
		r_dist_sensor = -1.5
	else:
		r_dist_sensor = float(r_dist_sensor_str)

	# Generate universe variables
	l_dist = np.arange(-1.5, 1.51, 0.01)
	r_dist = np.arange(-1.5, 1.51, 0.01)
	l_power = np.arange(-1, 3.25, 0.25)
	r_power = np.arange(-1, 3.25, 0.25)

	# Generate fuzzy membership functions
	levels = adjust_levels(-2, 2, 0.5)
	l_dist_lo = fuzz.trimf(l_dist, levels[0])
	l_dist_md = fuzz.trimf(l_dist, levels[1])
	l_dist_hi = fuzz.trimf(l_dist, levels[2])

	r_dist_lo = fuzz.trimf(r_dist, levels[0])
	r_dist_md = fuzz.trimf(r_dist, levels[1])
	r_dist_hi = fuzz.trimf(r_dist, levels[2])

	levels = adjust_levels(-2, 3, 0.25, True)
	l_power_lo = fuzz.trimf(l_power, levels[0])
	l_power_md = fuzz.trimf(l_power, levels[1])
	l_power_hi = fuzz.trimf(l_power, levels[2])

	r_power_lo = fuzz.trimf(r_power, levels[0])
	r_power_md = fuzz.trimf(r_power, levels[1])
	r_power_hi = fuzz.trimf(r_power, levels[2])


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

	active_rule4 = r_dist_level_lo
	active_rule5 = r_dist_level_md
	active_rule6 = r_dist_level_hi


	l_dist_activation_lo = np.fmin(active_rule1, l_power_lo)
	l_dist_activation_md = np.fmin(active_rule2, l_power_md)
	l_dist_activation_hi = np.fmin(active_rule3, l_power_hi)

	r_dist_activation_lo = np.fmin(active_rule4, r_power_lo)
	r_dist_activation_md = np.fmin(active_rule5, r_power_md)
	r_dist_activation_hi = np.fmin(active_rule6, r_power_hi)


	# Aggregate all three output membership functions together
	aggregated_l = np.fmax(l_dist_activation_lo, np.fmax(l_dist_activation_md, l_dist_activation_hi))
	aggregated_r = np.fmax(r_dist_activation_lo, np.fmax(r_dist_activation_md, r_dist_activation_hi))


	# Calculate defuzzified result
	l_motor_power = fuzz.defuzz(l_power, aggregated_l, 'centroid')
	r_motor_power = fuzz.defuzz(r_power, aggregated_r, 'centroid')


	print('Sensor', l_dist_sensor, r_dist_sensor)
	print('Motor', l_motor_power, r_motor_power)

	s.sendall((str(r_motor_power)+'\n').encode())
	s.sendall((str(l_motor_power)+'\n').encode())

s.close()
