#!/usr/bin/env python
##################################################
# Gnuradio Python Flow Graph
# Title: Eas Encoder
# Generated: Thu Nov 28 20:51:04 2013
##################################################

from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2
from argparse import ArgumentParser
import socket
import tempfile
import wave

class eas_encoder(gr.top_block):

    def __init__(self, samp_rate, src_filename, dest_filename):
        gr.top_block.__init__(self, "SAME Encoder")

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate

        ##################################################
        # Blocks
        ##################################################
        self.msg_source = blocks.file_source(1, src_filename)
        self.packed_to_unpacked = blocks.packed_to_unpacked_bb(1, gr.GR_LSB_FIRST)
        self.repeat = blocks.repeat(4, 96)
        self.chunks_to_symbols = digital.chunks_to_symbols_bf(([-1, 1]), 1)
        self.freq_mod = analog.frequency_modulator_fc(3.14159265 / 96)
        self.center_freq_src = analog.sig_source_c(50000, analog.GR_COS_WAVE, 1822.916666, 0.8, 0)
        self.freq_mult = blocks.multiply_vcc(1)
        self.rational_resampler = filter.rational_resampler_ccc(
                interpolation=samp_rate / 100,
                decimation=500,
                taps=None,
                fractional_bw=None,
        )
        self.complex_to_float = blocks.complex_to_float()
        self.float_to_short = blocks.float_to_short(1, 32767)
	self.sink = blocks.file_sink(2, dest_filename)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.msg_source, 0), (self.packed_to_unpacked, 0), (self.chunks_to_symbols, 0))
        self.connect((self.chunks_to_symbols, 0), (self.repeat, 0), (self.freq_mod, 0), (self.freq_mult, 0))
        self.connect((self.center_freq_src, 0), (self.freq_mult, 1))
        self.connect((self.freq_mult, 0), (self.rational_resampler, 0), (self.complex_to_float, 0))
        self.connect((self.complex_to_float, 0), (self.float_to_short, 0), (self.sink, 0))


if __name__ == '__main__':
    parser = ArgumentParser(description='UWave EAS SAME Encoder')
    parser.add_argument('-r', '--sample_rate', type=int, default=44100)
    parser.add_argument('same_msg')
    parser.add_argument('dest_file')
    args = parser.parse_args()
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        print "Error: failed to enable realtime scheduling."

    srcfile = tempfile.NamedTemporaryFile()
    srcfile.write('\xAB' * 16 + args.same_msg)
    srcfile.flush()

    destfile = tempfile.NamedTemporaryFile()
    tb = eas_encoder(args.sample_rate, srcfile.name, destfile.name)
    tb.start()
    tb.wait()

    # Take the raw encoded audio, add repetitions one second pauses, and package as WAV
    data = destfile.read()
    sec_of_silence = '\x00\x00' * args.sample_rate
    data = sec_of_silence + data + sec_of_silence + data + sec_of_silence + data + sec_of_silence

    destwav = wave.open(args.dest_file, 'w')
    destwav.setnchannels(1)
    destwav.setsampwidth(2)
    destwav.setframerate(args.sample_rate)
    destwav.writeframes(data)
    destwav.close()
