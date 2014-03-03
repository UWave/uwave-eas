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
from optparse import OptionParser
import same_swig as same
import gnuradio.gr.gr_threading as _threading
import datetime
import os
import socket

class top_block(gr.top_block):

    def __init__(self):
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
                interpolation=100,
                decimation=96,
                taps=None,
                fractional_bw=None,
        )

        self.freq_xlating_fir_filter_xxx_0 = filter.freq_xlating_fir_filter_fcc(1, (firdes.low_pass(1, samp_rate, 600, 100)), 1822.916667, samp_rate)
        self.digital_gmsk_demod_0 = digital.gmsk_demod(
        	samples_per_symbol=16,
        	gain_mu=0.175,
        	mu=0.5,
        	omega_relative_limit=0.1,
        	freq_error=0.0,
        	verbose=True,
        	log=False,
        )
        self.src = audio.source(44100, "eas_mon_%d:in" % (os.getpid()), True)
        self.agc = analog.agc_ff(0.001, 0.1, 1.0)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_ff(-50, 0.0001, 0)
        self.msg_queue = gr.msg_queue(10)
        self.same_dec_0 = same.same_dec(self.msg_queue)

        self.tone_det_0 = fft.goertzel_fc(samp_rate, 4000, 853)
        self.tone_det_1 = fft.goertzel_fc(samp_rate, 4000, 960)
        self.tone_det_2 = fft.goertzel_fc(samp_rate, 4000, 1050)
        self.wat_thresh_msg = same.wat_thresh_msg(self.msg_queue, 1, 0.05, 0.01)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.src, 0), (self.rational_resampler_44k, 0))
        self.connect((self.rational_resampler_44k, 0), (self.agc, 0))
        self.connect((self.agc, 0), (self.analog_pwr_squelch_xx_0, 0))


        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.digital_gmsk_demod_0, 0))
        self.connect((self.digital_gmsk_demod_0, 0), (self.same_dec_0, 0))

        self.connect((self.agc, 0), (self.tone_det_0, 0), (self.wat_thresh_msg, 0))
        self.connect((self.agc, 0), (self.tone_det_1, 0), (self.wat_thresh_msg, 1))
        self.connect((self.agc, 0), (self.tone_det_2, 0), (self.wat_thresh_msg, 2))

        self._watcher = _queue_watcher_thread(self.msg_queue)

class _queue_watcher_thread(_threading.Thread):
    def __init__(self, msg_q):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.msg_q = msg_q
        self.keep_running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # FIXME: these should not be hardcoded
        self.mon_id = 'KPLU'
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
            elif msg.type() == 1: # Tone detection event
                self.send_eas_packet('T %s %d %d' % (self.mon_id, int(msg.arg1()), int(msg.arg2())))
            elif msg.type() == 10: # Preamble detection event
                self.send_eas_packet('P')
                 
if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."

    tb = top_block()
    tb.start()
    tb.wait()

