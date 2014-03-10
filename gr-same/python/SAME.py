#!/usr/bin/python

import calendar
import re
import time

same_re = re.compile('ZCZC-(...)-(...)((?:-\d{6})+)\+(\d\d)(\d\d)-(\d{7})-(........)-')

event_types = {
	'EAN': { 'description': 'Emergency Action Notification', 'forward': True, 'max_delay': 0 },
	'EAT': { 'description': 'Emergency Action Termination', 'forward': True, 'max_delay': 0 },
	'NIC': { 'description': 'National Information Center Statement', 'forward': True, 'max_delay': 0 },
	'RMT': { 'description': 'Required Monthly Test', 'forward': True, 'max_delay': 900 },
	'RWT': { 'description': 'Required Weekly Test', 'forward': False }
}

org_types = {
	'PEP': { 'description': 'Primary Entry Point Station' },
	'CIV': { 'description': 'Civil authorities' },
	'WXR': { 'description': 'National Weather Service' },
	'EAS': { 'description': 'EAS Participant' }
}


class SAME(object):
	"""A class for Specific Area Messaging Protocol messages"""

	def __init__(self, org, event, areas, purgetime, timestamp, callsign):
		self._org = org
		self._event = event
		self._areas = areas
		self._purgetime = purgetime
		self._time = timestamp
		self._callsign = callsign

	def __str__(self): 
		return 'ZCZC-%3s-%3s-%s+%4s-%7s-%-8s-' % (
			self._org, self._event,
			'-'.join(self._areas),
			'%02d%02d' % (self._purgetime / 60, self._purgetime % 60),
			time.strftime('%j%H%M', time.gmtime(self._time)),
			self._callsign)

	def set_callsign(self, callsign):
		# In case we get a callsign with a dash in it, convert it to the SAME-compatible format
		self._callsign = callsign.replace('-', '/')

	def has_expired(self):
		return time.time() > self._time + self._purgetime

def from_str(msg):
	
	m = same_re.search(msg)
	if m is None:
		raise ValueError('Not a valid SAME message')

	org = m.group(1)
	event = m.group(2)
	areas = m.group(3)[1:].split('-')
	purgetime = int(m.group(4)) * 60 + int(m.group(5))
	# Lots of shenanigans to make sure we get the year right
	julian_day = int(m.group(6)[0:3])
	gmt = time.gmtime()
	year = gmt.tm_year
	if gmt.tm_mon == 12 and julian_day <= 31:
		year += 1
	if gmt.tm_mon == 1 and julian_day >= 334:
		year -= 1
	timestamp = calendar.timegm(time.strptime('%d%s' % (year, m.group(6)), '%Y%j%H%M'))
	callsign = m.group(7)
	return SAME(org, event, areas, purgetime, timestamp, callsign)
