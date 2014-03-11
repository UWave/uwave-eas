#!/usr/bin/python

import calendar
import re
import time

same_re = re.compile('ZCZC-(...)-(...)((?:-\d{6})+)\+(\d\d)(\d\d)-(\d{7})-(........)-')
area_re = re.compile('(\d+),(.+)')

event_types = {
	'EAN': { 'description': 'Emergency Action Notification', 'forward': True, 'max_delay': 0 },
	'EAT': { 'description': 'Emergency Action Termination', 'forward': True, 'max_delay': 0 },
	'NIC': { 'description': 'National Information Center Statement', 'forward': True, 'max_delay': 0 },
	'NPT': { 'description': 'National Periodic Test', 'forward': True, 'max_delay': 900 },
	'RMT': { 'description': 'Required Monthly Test', 'forward': True, 'max_delay': 900 },
	'RWT': { 'description': 'Required Weekly Test', 'forward': False },

	'ADM': { 'description': 'Administrative Message', 'forward': True, 'max_delay': 300 },
	'AVW': { 'description': 'Avalanche Warning', 'forward': True, 'max_delay': 300 },
	'AVA': { 'description': 'Avalanche Watch', 'forward': True, 'max_delay': 300 },
	'BZW': { 'description': 'Blizzard Warning', 'forward': True, 'max_delay': 300 },
	'CAE': { 'description': 'Child Abduction Emergency', 'forward': True, 'max_delay': 300 },
	'CDW': { 'description': 'Civil Danger Warning', 'forward': True, 'max_delay': 300 },
	'CEM': { 'description': 'Civil Emergency Warning', 'forward': True, 'max_delay': 300 },
	'CFW': { 'description': 'Coastal Flood Warning', 'forward': True, 'max_delay': 300 },
	'CFA': { 'description': 'Coastal Flood Watch', 'forward': True, 'max_delay': 300 },
	'DSW': { 'description': 'Dust Storm Warning', 'forward': True, 'max_delay': 300 },
	'EQW': { 'description': 'Earthquake Warning', 'forward': True, 'max_delay': 300 },
	'EVI': { 'description': 'Evacuation Immediate', 'forward': True, 'max_delay': 300 },
	'FRW': { 'description': 'Fire Warning', 'forward': True, 'max_delay': 300 },
	'FFW': { 'description': 'Flash Flood Warning', 'forward': True, 'max_delay': 300 },
	'FFA': { 'description': 'Flash Flood Watch', 'forward': True, 'max_delay': 300 },
	'FFS': { 'description': 'Flash Flood Statement', 'forward': True, 'max_delay': 300 },
	'FLW': { 'description': 'Flood Warning', 'forward': True, 'max_delay': 300 },
	'FLA': { 'description': 'Flood Watch', 'forward': True, 'max_delay': 300 },
	'FLS': { 'description': 'Flood Statement', 'forward': True, 'max_delay': 300 },
	'HMW': { 'description': 'Hazardous Materials Warning', 'forward': True, 'max_delay': 300 },
	'HWW': { 'description': 'High Wind Warning', 'forward': True, 'max_delay': 300 },
	'HWA': { 'description': 'High Wind Watch', 'forward': True, 'max_delay': 300 },
	'HUW': { 'description': 'Hurricane Warning', 'forward': True, 'max_delay': 300 },
	'HUA': { 'description': 'Hurricane Watch', 'forward': True, 'max_delay': 300 },
	'HLS': { 'description': 'Hurricane Statement', 'forward': True, 'max_delay': 300 },
	'LEW': { 'description': 'Law Enforcement Warning', 'forward': True, 'max_delay': 300 },
	'LAE': { 'description': 'Local Area Emergency', 'forward': True, 'max_delay': 300 },
	'NMN': { 'description': 'Network Message Notification', 'forward': True, 'max_delay': 300 },
	'TOE': { 'description': '911 Telephone Outage Emergency', 'forward': True, 'max_delay': 300 },
	'NUW': { 'description': 'Nuclear Power Plant Warning', 'forward': True, 'max_delay': 300 },
	'DMO': { 'description': 'Practice/Demo Warning', 'forward': False, 'max_delay': 900 },
	'RHW': { 'description': 'Radiological Hazard Warning', 'forward': True, 'max_delay': 300 },
	'SVR': { 'description': 'Severe Thunderstorm Warning', 'forward': True, 'max_delay': 300 },
	'SVA': { 'description': 'Severe Thunderstorm Watch', 'forward': True, 'max_delay': 300 },
	'SVS': { 'description': 'Severe Weather Statement', 'forward': True, 'max_delay': 300 },
	'SPW': { 'description': 'Shelter in Place Warning', 'forward': True, 'max_delay': 300 },
	'SMW': { 'description': 'Special Marine Warning', 'forward': True, 'max_delay': 300 },
	'SPS': { 'description': 'Special Weather Statement', 'forward': True, 'max_delay': 300 },
	'TOR': { 'description': 'Tornado Warning', 'forward': True, 'max_delay': 300 },
	'TOA': { 'description': 'Tornado Watch', 'forward': True, 'max_delay': 300 },
	'TSW': { 'description': 'Tsunami Warning', 'forward': True, 'max_delay': 300 },
	'TSA': { 'description': 'Tsunami Watch', 'forward': True, 'max_delay': 300 },
	'VOW': { 'description': 'Volcano Warning', 'forward': True, 'max_delay': 300 },
	'WSW': { 'description': 'Winter Storm Warning', 'forward': True, 'max_delay': 300 },
	'WSA': { 'description': 'Winter Storm Watch', 'forward': True, 'max_delay': 300 }
}

org_types = {
	'PEP': { 'description': 'Primary Entry Point Station', 'msg': 'The United States Government has' },
	'CIV': { 'description': 'Civil Authorities', 'msg': 'Civil Authorities have' },
	'WXR': { 'description': 'National Weather Service', 'msg': 'The National Weather Service has' },
	'EAS': { 'description': 'EAS Participant', 'msg': 'An EAS Participant has' }
}

area_mods = [
	'',
	'Northwest ',
	'Northern ',
	'Northeast ',
	'Western ',
	'Central ',
	'Eastern ',
	'Southwest ',
	'Southern ',
	'Southeast '
]

areas = {}

_areafile = open('areas.txt', 'r')
for line in _areafile:
	match = area_re.search(line)
	if match:
		areas[match.group(1)] = match.group(2)

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

	def description(self):
		try:
			msg = "%s issued a%s %s for the following areas: " % \
				(org_types[self._org]['msg'], \
				'n' if self._event[0] == 'E' else '', \
				event_types[self._event]['description'])
			msg_areas = []
			for area in self._areas:
				msg_areas.append(area_mods[int(area[0])]+ areas[area[1:6]])
			msg += ', '.join(msg_areas)
			msg += ' until %s.' % (time.strftime('%I:%M %p %Z', time.localtime(self._time + self._purgetime)))
			return msg
		except:
			return str(self)

	def webcolor(self):
		if self._event in ['RWT','RMT','NPT','ADM','DMO','NIC','EAT']:
			return 'eas-alert-steel'
		if self._event in ['EAN','RHW','TOR','EVI','NUW','SPW','VOW']:
			return 'eas-alert-red'
		return 'eas-alert-orange'

	def expires(self):
		return (self._time + self._purgetime) * 1000

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

