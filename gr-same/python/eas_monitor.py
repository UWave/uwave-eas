#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Karl Koscher <supersat@uwave.fm>.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import audio
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from argparse import ArgumentParser
import same_swig as same
import gnuradio.gr.gr_threading as _threading
import datetime
import os
import socket

def db_to_abs(db):
    return pow(10, db/10.0)


class top_block(gr.top_block):

    def __init__(self, mon_id, audio_port):
        gr.top_block.__init__(self, "EAS/SAME Monitor")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 8000

        ##################################################
        # Blocks
        ##################################################

        # Resampler from input rate (44.1k) to internal rate (8k)
        self.rational_resampler_44k = filter.rational_resampler_fff(
                interpolation=80,
                decimation=441,
        )

        # Resampler from 8000 Hz to 8333 1/3rd Hz to deal with SAME's weird parameters
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=50,
                decimation=96,
                taps=None,
                fractional_bw=None,
        )

        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_fcc(1, (firdes.low_pass(1, samp_rate, 600, 100)), 1822.916667, samp_rate)
        self.digital_gmsk_demod_0 = digital.gmsk_demod(
        	samples_per_symbol=8,
        	gain_mu=0.175,
        	mu=0.5,
        	omega_relative_limit=0.01,
        	freq_error=0.0,
        	verbose=True,
        	log=False,
        )
        self.src = audio.source(44100, "eas_mon_%s:in" % (mon_id), True)
        self.agc = analog.agc_ff(0.0001, 0.1, 1.0)
        #self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_ff(-50, 0.0001, 0)
        self.msg_queue = gr.msg_queue(10)
        self.same_dec_0 = same.same_dec(self.msg_queue)

        self.tone_det_0 = fft.goertzel_fc(samp_rate, samp_rate / 10, 853)
        self.tone_det_1 = fft.goertzel_fc(samp_rate, samp_rate / 10, 960)
        self.tone_det_2 = fft.goertzel_fc(samp_rate, samp_rate / 10, 1050)
        self.wat_thresh_msg = same.wat_thresh_msg(self.msg_queue, 1, 0.05, 0.01)

        #self.avg_audio_level = analog.probe_avg_mag_sqrd_ff(-50)
        #self.level_thresh_msg = same.level_thresh_msg(self.msg_queue, 1, 3, db_to_abs(-30), db_to_abs(-40))

        self.audio_sink = blocks.udp_sink(4, '127.0.0.1', audio_port)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.src, 0), (self.rational_resampler_44k, 0))
        self.connect((self.rational_resampler_44k, 0), (self.agc, 0))
        #self.connect((self.agc, 0), (self.analog_pwr_squelch_xx_0, 0))

        #self.connect((self.analog_pwr_squelch_xx_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.agc, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.digital_gmsk_demod_0, 0))
        self.connect((self.digital_gmsk_demod_0, 0), (self.same_dec_0, 0))

        self.connect((self.agc, 0), (self.tone_det_0, 0), (self.wat_thresh_msg, 0))
        self.connect((self.agc, 0), (self.tone_det_1, 0), (self.wat_thresh_msg, 1))
        self.connect((self.agc, 0), (self.tone_det_2, 0), (self.wat_thresh_msg, 2))
        #self.connect((self.agc, 0), (self.avg_audio_level, 0), (self.level_thresh_msg, 0))

        self.connect((self.agc, 0), (self.audio_sink, 0))

        self._watcher = _queue_watcher_thread(self.msg_queue, mon_id)

class _queue_watcher_thread(_threading.Thread):
    def __init__(self, msg_q, mon_id):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.msg_q = msg_q
        self.keep_running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mon_id = mon_id

        # FIXME: these should not be hardcoded
        self.dest = ('127.0.0.1', 0xEA51)

        self.start()

    def send_eas_packet(self, msg):
        self.socket.sendto(msg, self.dest)

    def run(self):
        while self.keep_running:
            msg = self.msg_q.delete_head()
            if msg.type() == 0: # SAME message event
                print datetime.datetime.now().isoformat(' ') + ' ' + msg.to_string()
                self.send_eas_packet('S %s %s' % (self.mon_id, msg.to_string()))
            elif msg.type() == 1: # Tone/level detection event
                self.send_eas_packet('T %s %d %d' % (self.mon_id, int(msg.arg1()), int(msg.arg2())))
            elif msg.type() == 10: # Preamble detection event
                self.send_eas_packet('P')
                 
if __name__ == '__main__':
    parser = ArgumentParser(description='A source decoder/monitor for the UWave EAS ENDEC.')
    parser.add_argument('mon_id')
    parser.add_argument('audio_port', type=int)
    args = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."

    tb = top_block(args.mon_id, args.audio_port)
    tb.start()
    tb.wait()

