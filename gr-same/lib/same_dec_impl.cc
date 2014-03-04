/* -*- c++ -*- */
/*
 * Copyright 2014 Karl Koscher <supersat@uwave.fm>
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <stdio.h>
#include <string.h>
#include <gnuradio/io_signature.h>
#include <gnuradio/message.h>
#include "same_dec_impl.h"

static const char ab_preamble[] = {
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
    1, 1, 0, 1, 0, 1, 0, 1, // 0xAB, LSB first
};

static const char zczc_preamble[] = {
    0, 1, 0, 1, 1, 0, 1, 0, // 'Z', 0x5A, LSB first
    1, 1, 0, 0, 0, 0, 1, 0, // 'C', 0x43, LSB first
    0, 1, 0, 1, 1, 0, 1, 0, // 'Z', 0x5A, LSB first
    1, 1, 0, 0, 0, 0, 1, 0, // 'C', 0x43, LSB first
};

static const char nnnn_preamble[] = {
    0, 1, 1, 1, 0, 0, 1, 0, // 'N', 0x4E, LSB first
    0, 1, 1, 1, 0, 0, 1, 0, // 'N', 0x4E, LSB first
    0, 1, 1, 1, 0, 0, 1, 0, // 'N', 0x4E, LSB first
    0, 1, 1, 1, 0, 0, 1, 0, // 'N', 0x4E, LSB first
};

namespace gr {
  namespace same {

    same_dec::sptr
    same_dec::make(msg_queue::sptr queue, long pdmt)
    {
      return gnuradio::get_initial_sptr
        (new same_dec_impl(queue, pdmt));
    }

    /*
     * The private constructor
     */
    same_dec_impl::same_dec_impl(msg_queue::sptr queue, long pdmt)
      : gr::sync_block("same_dec",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(0, 0, sizeof(char))),
        d_is_synced(false), d_incoming_bits_next_free_index(0),
        d_queue(queue), d_preamble_detected_message_type(pdmt)
    {
        memset(d_incoming_bits, 0, sizeof(d_incoming_bits));
    }

    /*
     * Our virtual destructor.
     */
    same_dec_impl::~same_dec_impl()
    {    }

    void same_dec_impl::process_char()
    {
        char c = (d_incoming_bits[0] & 1) |
                 ((d_incoming_bits[1] & 1) << 1) |
                 ((d_incoming_bits[2] & 1) << 2) |
                 ((d_incoming_bits[3] & 1) << 3) |
                 ((d_incoming_bits[4] & 1) << 4) |
                 ((d_incoming_bits[5] & 1) << 5) |
                 ((d_incoming_bits[6] & 1) << 6) |
                 ((d_incoming_bits[7] & 1) << 7);

        if (c == 0) {
            send_same_message();
        } else if (c == '+' && d_dashes_received == -1) {
            same_msg.push_back(c);
            d_dashes_received = 0;
        } else if (c == '-' && d_dashes_received >= 0) {
            same_msg.push_back(c);
            d_dashes_received++;
            if (d_dashes_received == 3)
                send_same_message();
        } else {
            same_msg.push_back(c);
        }

        // EAS messages can only be 252 characters long (31 location codes).
        // Make sure we never exceed this limit to prevent massive messages
        // from ever accumulating in the decoder.
        if (same_msg.length() >= 252)
            send_same_message();
    }

    void same_dec_impl::send_same_message()
    {
        //fprintf(stderr, "Received SAME message: %s\n", same_msg.c_str());
        message::sptr msg = message::make_from_string(same_msg);
        d_queue->insert_tail(msg);
        d_is_synced = false;
        same_msg = "";
        memset(d_incoming_bits, 0, sizeof(d_incoming_bits));
    }

    void same_dec_impl::send_eom_message()
    {
        message::sptr msg = message::make_from_string("NNNN");
        d_queue->insert_tail(msg);
    }

    void same_dec_impl::send_preamble_detected()
    {
        message::sptr msg = message::make(d_preamble_detected_message_type);
        d_queue->insert_tail(msg);
    }

    bool same_dec_impl::check_sync()
    {
        int bit_matches = 0;

        for (int i = 0; i < sizeof(ab_preamble); i++) {
            if (d_incoming_bits[(d_incoming_bits_next_free_index + i) & 0x7F] == ab_preamble[i])
                bit_matches++;
        }

	//fprintf(stderr, "bit matches: %d\n", bit_matches);
        // Bail out if the preamble doesn't match
        if (bit_matches < 90)
            return false;

        send_preamble_detected();
        //fprintf(stderr, "Found preamble: bit_matches = %d\n", bit_matches);

        // See if we have a ZCZC or NNNN header
        bit_matches = 0;
        for (int i = 0; i < sizeof(zczc_preamble); i++) {
            if (d_incoming_bits[(d_incoming_bits_next_free_index + sizeof(ab_preamble) + i) & 0x7F] == zczc_preamble[i])
                bit_matches++;
        }

	//fprintf(stderr, "ZCZC bit matches: %d\n", bit_matches);
        if (bit_matches >= 30) {
            d_is_synced = true;
            d_dashes_received = -1;
            same_msg = "ZCZC";
            return true;
        }

        bit_matches = 0;
        for (int i = 0; i < sizeof(nnnn_preamble); i++) {
            if (d_incoming_bits[(d_incoming_bits_next_free_index + sizeof(ab_preamble) + i) & 0x7F] == nnnn_preamble[i])
                bit_matches++;
        }

	//fprintf(stderr, "NNNN bit matches: %d\n", bit_matches);
        if (bit_matches >= 30) {
            //fprintf(stderr, "NNNN received, bit matches: %d\n", bit_matches);
            send_eom_message();
            memset(d_incoming_bits, 0, sizeof(d_incoming_bits));
        }

        return false;
    }

    int
    same_dec_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
        const char *in = (const char *) input_items[0];
        int i = 0;

        while (i < noutput_items) {
            if (d_is_synced) {
                d_incoming_bits[d_incoming_bits_next_free_index++] = in[i++];

                if (d_incoming_bits_next_free_index == 8) {
                    process_char();
                    d_incoming_bits_next_free_index = 0;
                }
            }

            if (!d_is_synced) {
                while (i < noutput_items) {
                    d_incoming_bits[d_incoming_bits_next_free_index] = in[i++];
                    d_incoming_bits_next_free_index =
                        (d_incoming_bits_next_free_index + 1) & 0x7F;
                    if (check_sync()) {
                        d_incoming_bits_next_free_index = 0;
                        break;
                    }
                }
            }
        }

        return noutput_items;
    }

  } /* namespace same */
} /* namespace gr */

