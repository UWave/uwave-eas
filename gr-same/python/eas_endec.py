#!/usr/bin/env python

import collections
import datetime
import socket
import array

class src_state:
    idle, same_recvd, eas_wat_detect, nws_wat_detect, alert_sent = range(5)

class eas_source:

    def __init__(self, endec, mon_id):
        self.state = src_state.idle
        self.last_state_change = datetime.datetime.utcnow();
        self.msg = None
        self.endec = endec;
        self.mon_id = mon_id
        # A deque of the last three (timestamp, SAME message) tuples received
        self.same_msgs = collections.deque(maxlen=3)
        # Timestamps of when the 853 Hz, 960 Hz, and 1050 Hz tones were received, or 0 if not active
        self.tones_received = [0, 0, 0]

    def same_msg_received(self, same_msg):
        print '%s SAME message received from %s: %s' % \
            (datetime.datetime.now().isoformat(' '), self.mon_id, same_msg)
        self.same_msgs.appendleft((datetime.datetime.utcnow(), same_msg))

        if self.state != src_state.idle and same_msg == 'NNNN':
            print '    Handling EOM'
            self.state = src_state.idle
            self.last_state_change = datetime.datetime.utcnow()
            self.endec.eom(self)

        recent_msgs = [self.same_msgs[0][1]]
        if len(self.same_msgs) >= 2 and (self.same_msgs[1][0] - self.same_msgs[0][0]).total_seconds() < 3:
            recent_msgs.append(self.same_msgs[1])
            if len(self.same_msgs) == 3 and (self.same_msgs[2][0] - self.same_msgs[1][0]).total_seconds() < 3:
                recent_msgs.append(self.same_msgs[2])

        if len(recent_msgs) >= 2 and recent_msgs[0][1] == recent_msgs[1][1]:
            print '    SAME integrity verified'
            self.state = src_state.same_recvd
            self.last_state_change = datetime.datetime.utcnow()
            self.msg = recent_msgs[0]
        elif len(recent_msgs) == 3: # Process the messages byte-wise
            msg_len = min(len(recent_msgs[0]), len(recent_msgs[1]), len(recent_msgs[2]))
            msg = []
            for i in range(msg_len):
                if recent_msgs[0][i] == recent_msgs[1][i]:
                    msg.append(recent_msgs[0][i])
                elif recent_msgs[0][i] == recent_msgs[2][i]:
                    msg.append(recent_msgs[0][i])
                elif recent_msgs[1][i] == recent_msgs[2][i]:
                    msg.append(recent_msgs[1][i])
                else:
                    msg.append('?')
            msg = ''.join(msg)
            if '?' in msg:
                print '    SAME message corrupt... Trying to handle anyway'
            else:
                print '    SAME integrity verified'
            self.state = src_state.same_recvd
            self.last_state_change = datetime.datetime.utcnow()
            self.msg = msg

    def wat_event_received(self, tone, active):
        if active:
            self.tones_received[tone] = datetime.datetime.utcnow()
        else:
            self.tones_received[tone] = 0
            if self.state == src_state.eas_wat_detect and tone != 2:
                self.state = src_state.alert_sent
                self.last_state_change = datetime.datetime.utcnow()
                self.endec.wat_ended(self)
            elif self.state == src_state.nws_wat_detect and tone == 2:
                self.state = src_state.alert_sent
                self.last_state_change = datetime.datetime.utcnow()
                self.endec.wat_ended(self)

    def check_events(self):
        if self.state == src_state.same_recvd:
            now = datetime.datetime.utcnow()
            if (now - self.tones_received[0]).total_seconds() > 2 and (now - self.tones_received[1]).total_seconds() > 2:
                self.state = src_state.eas_wat_detect
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC w/ WAT' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert(self, 1)

            if (now - self.tones_received[2]).total_seconds() > 2:
                self.state = src_state.eas_wat_detect
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC w/ WAT' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert(self, 1)

            if (now - self.last_state_change).total_seconds() > 3:
                self.state = src_state.alert_sent
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert(self, 0)

class eas_endec:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0xEA51))
        self.sock.settimeout(0.1)
        self.sources = dict()

    def get_source(self, mon_id):
        if mon_id in self.sources:
            return self.sources[mon_id]
        else:
            source = eas_source(self, mon_id)
            self.sources[mon_id] = source
            return source

    def alert(self, source, with_wat):
        print 'Source %s received alert, wat: %d' % (source.mon_id, with_wat)
        pass

    def run(self):
        should_run = True
        while should_run:
            try:
                msg = self.sock.recv(512)

                if msg[0] == 'S': # SAME message received
                    (type, mon_id, same_msg) = msg.split(' ', 2)
                    self.get_source(mon_id).same_msg_received(same_msg)
                elif msg[0] == 'T': # Warning alert tone event received
                    (type, mon_id, tone, active) = msg.split(' ', 3)
                    self.get_source(mon_id).wat_event_received(int(tone), int(active))

            except socket.timeout:
                pass

            for s in self.sources.values():
                s.check_events()

if __name__ == '__main__':
    endec = eas_endec()
    endec.run()     
