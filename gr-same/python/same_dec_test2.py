#!/usr/bin/env python

from gnuradio import audio
from gnuradio import analog
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from optparse import OptionParser
import same_swig as same
import gnuradio.gr.gr_threading as _threading
import datetime

class top_block(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "SAME Decoder test")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 8000

        ##################################################
        # Blocks
        ##################################################
        self.rational_resampler_44k = filter.rational_resampler_fff(
                interpolation=80,
                decimation=441,
        )
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
        #self.src = audio.source(samp_rate, "plughw:CARD=PCH,DEV=2", True)
        self.blocks_wavfile_source_0 = blocks.wavfile_source("eas-test-11-7-2013.wav", False)
        self.blocks_bitstream_sink = blocks.file_sink(1, "bitstream.bin")
        self.xlat_sink = blocks.wavfile_sink("xlat.wav", 1, 8333)
        self.xlat_complex_to_float = blocks.complex_to_float()
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_ff(-50, 0.0001, 0)
        self.msg_queue = gr.msg_queue(10)
        self.same_dec_0 = same.same_dec(self.msg_queue)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.freq_xlating_fir_filter_xxx_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.xlat_complex_to_float, 0), (self.xlat_sink, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.digital_gmsk_demod_0, 0))
        self.connect((self.digital_gmsk_demod_0, 0), (self.same_dec_0, 0))
        self.connect((self.digital_gmsk_demod_0, 0), (self.blocks_bitstream_sink, 0))
        #self.connect((self.src, 0), (self.rational_resampler_44k, 0))
        #self.connect((self.rational_resampler_44k, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.blocks_wavfile_source_0, 0), (self.analog_pwr_squelch_xx_0,0))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.freq_xlating_fir_filter_xxx_0, 0))

        self._watcher = _queue_watcher_thread(self.msg_queue)

class _queue_watcher_thread(_threading.Thread):
    def __init__(self, msg_q):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.msg_q = msg_q
        self.keep_running = True
        self.start()

    def run(self):
        while self.keep_running:
            msg = self.msg_q.delete_head()
            print datetime.datetime.now().isoformat(' ') + ' ' + msg.to_string()


# QT sink close method reimplementation

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.freq_xlating_fir_filter_xxx_0.set_taps((firdes.low_pass(1, self.samp_rate, 600, 100)))

if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = top_block()
    tb.start()
    tb.wait()


