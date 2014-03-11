#!/usr/bin/env python

import array
import collections
import datetime
import jack
import socket
import subprocess
import threading
import websocket

import SAME

class src_state:
    idle, same_recvd, eas_wat_detect, nws_wat_detect, alert_sent = range(5)

class source_audio_receiver(threading.Thread):
    def __init__(self, source):
        threading.Thread.__init__(self)
        self.source = source
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 31337)) # FIXME: Remove hardcoded audio port
        self.start()

    def run(self):
        # FIXME: this is a bit off, I think (it will include the EOM received)
        while self.source.state == src_state.alert_sent:
            self.source.audio_buffer.append(self.sock.recv(1500))
        self.sock.close()

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
        self.tones_received = [None, None, None]
        self.audio_buffer = collections.deque(maxlen=960000) # 120 seconds at 8 kHz
        self.audio_thread = None

    def same_msg_received(self, same_msg):
        print '%s SAME message received from %s: %s' % \
            (datetime.datetime.now().isoformat(' '), self.mon_id, same_msg)

        if same_msg == 'NNNN':
            if self.state != src_state.idle:
	        print '    Handling EOM'
	        self.state = src_state.idle
	        self.last_state_change = datetime.datetime.utcnow()
	        self.endec.eom_received(self)
            return

        self.same_msgs.appendleft((datetime.datetime.utcnow(), same_msg))

        # The maximum SAME message burst is just over 4 seconds, plus a one second delay between bursts
        recent_msgs = [self.same_msgs[0][1]]
        if len(self.same_msgs) >= 2 and (self.same_msgs[0][0] - self.same_msgs[1][0]).total_seconds() < 5.5:
            recent_msgs.append(self.same_msgs[1][1])
            if len(self.same_msgs) == 3 and (self.same_msgs[1][0] - self.same_msgs[2][0]).total_seconds() < 5.5:
                recent_msgs.append(self.same_msgs[2][1])

        if len(recent_msgs) >= 2 and recent_msgs[0] == recent_msgs[1]:
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

    def preamble_detected(self):
        # If we detect another preamble before the WAT detection has ended, restart the WAT detection timer
        # FIXME: This should really wait until the channel becomes silent again
        # TODO: If we detect a preamble but no valid messages, log the audio for manual control
        if self.state == src_state.same_recvd:
            self.last_state_change = datetime.datetime.utcnow()

    def wat_event_received(self, tone, active):
        if active:
            self.tones_received[tone] = datetime.datetime.utcnow()
        else:
            if self.state == src_state.eas_wat_detect and tone != 2:
                self.state = src_state.alert_sent
                self.last_state_change = datetime.datetime.utcnow()
                wat_len = min((self.last_state_change - self.tones_received[0]).total_seconds(), \
                              (self.last_state_change - self.tones_received[1]).total_seconds())
                self.endec.wat_ended(self, wat_len)
                self.audio_thread = source_audio_receiver(self)
            elif self.state == src_state.nws_wat_detect and tone == 2:
                self.state = src_state.alert_sent
                self.last_state_change = datetime.datetime.utcnow()
                self.endec.wat_ended(self, (self.last_state_change - self.tones_received[2]).total_seconds())
                self.audio_thread = source_audio_receiver(self)
            self.tones_received[tone] = None


    def check_events(self):
        if self.state == src_state.same_recvd:
            now = datetime.datetime.utcnow()
            if self.tones_received[0] and (now - self.tones_received[0]).total_seconds() > 1.5 and self.tones_received[1] and (now - self.tones_received[1]).total_seconds() > 1.5:
                self.state = src_state.eas_wat_detect
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC w/ WAT' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert_received(self, 1)

            if self.tones_received[2] and (now - self.tones_received[2]).total_seconds() > 1.5:
                self.state = src_state.eas_wat_detect
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC w/ WAT' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert_received(self, 1)

            if (now - self.last_state_change).total_seconds() > 3:
                self.state = src_state.alert_sent
                self.last_state_change = now
                print '%s %s: Sending alert to the ENDEC' % (datetime.datetime.now().isoformat(' '), self.mon_id)
                self.endec.alert_received(self, 0)
                self.audio_thread = source_audio_receiver(self)

class alert_thread(threading.Thread):
    def __init__(self, endec, source, msg, with_wat):
        threading.Thread.__init__(self)
        self.endec = endec
        self.source = source
        self.msg = msg
        self.with_wat = with_wat
        self.start()

    def run(self):
        subprocess.call(['./same_encode.py', self.msg, '/tmp/alert.wav'])
        # FIXME: don't hardcode these
        # This was buggy under PyJack 0.5.1. 0.6 seems to fix it.
        self.endec.jack.disconnect('system:capture_1', 'stereo_tool:in_l')
        self.endec.jack.disconnect('system:capture_2', 'stereo_tool:in_r')
        subprocess.call(['aplay', '-D', 'endec', '/tmp/alert.wav'])
        if self.with_wat:
            subprocess.call(['aplay', '-D', 'endec', 'eas-attn-8s-n20db.wav'])

        player = subprocess.Popen(['aplay', '-D', 'endec', '-t', 'raw', '-c', '1', '-r', '8000', '-f', 'S16_LE'], stdin=subprocess.PIPE)
        while len(self.source.audio_buffer) != 0:
            player.stdin.write(self.source.audio_buffer.popleft())
        player.stdin.close()
        player.wait()

        subprocess.call(['aplay', '-D', 'endec', 'nnnn.wav'])
        self.endec.jack.connect('system:capture_1', 'stereo_tool:in_l')
        self.endec.jack.connect('system:capture_2', 'stereo_tool:in_r')

class eas_endec:
    def __init__(self, default_in_client, out_client):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('127.0.0.1', 0xEA51))
        self.sock.settimeout(0.1)
        self.sources = dict()
        self.jack = jack.Client("endec")
        self.default_in_client = default_in_client
        self.out_client = out_client

        print 'UWave EAS ENDEC'
        print 'System sample rate: %d' % (self.jack.get_sample_rate())

    def get_source(self, mon_id):
        if mon_id in self.sources:
            return self.sources[mon_id]
        else:
            source = eas_source(self, mon_id)
            self.sources[mon_id] = source
            return source

    def start_alert(self, source, msg, with_wat):
        # FIXME: Do not hardcode
        msg.set_callsign('UWAVE FM')
        alert = alert_thread(self, source, str(msg), with_wat)
        try:
            ws = websocket.create_connection('wss://127.0.0.1:4444/primus')
            websock_msg = '{"type": "alert", "title": "EAS Alert", "link": "", "color": "%s", "message": "%s", "expires": %d}' % \
                (msg.webcolor(), msg.description(), msg.expires())
            print 'Sending: ', websock_msg
            ws.send(websock_msg)
            ws.close()
        except:
            print "Unexpected error sending web alert:", sys.exc_info()[0]

    def alert_received(self, source, with_wat):
        print 'Source %s received alert, wat: %d' % (source.mon_id, with_wat)
        msg = SAME.from_str(source.msg)
        # TODO: Check for duplicate messages and do proper filtering
        if msg._event == 'RWT':
            print '    Not relaying RWT'
            return
        if not msg.has_expired():
            self.start_alert(source, msg, with_wat)

    def eom_received(self, source):
        print 'Source %s received EOM' % (source.mon_id)

    def wat_ended(self, source, wat_len):
        print 'Source %s WAT ended (%f seconds)' % (source.mon_id, wat_len)

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
                #elif msg[0] == 'P': # Preamble detected
                    #print msg
                    #(type, mon_id) = msg.split(' ')
                    #self.get_source(mon_id).preamble_detected()

            except socket.timeout:
                pass

            for s in self.sources.values():
                s.check_events()

if __name__ == '__main__':
    jack_in = 'stereotool'
    jack_out = 'darkice'
    endec = eas_endec(jack_in, jack_out)
    endec.run()     
