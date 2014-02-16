/* -*- c++ -*- */
/* 
 * Copyright 2014 Karl Koscher <supersat@uwave.fm>.
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

#include <gnuradio/io_signature.h>
#include "wat_thresh_msg_impl.h"

#include <stdio.h>

namespace gr {
  namespace same {

    wat_thresh_msg::sptr
    wat_thresh_msg::make(msg_queue::sptr queue, long msg_type, float lo, float hi)
    {
      return gnuradio::get_initial_sptr
        (new wat_thresh_msg_impl(queue, msg_type, lo, hi));
    }

    /*
     * The private constructor
     */
    wat_thresh_msg_impl::wat_thresh_msg_impl(msg_queue::sptr queue, long msg_type, float lo, float hi)
      : gr::sync_block("wat_thresh_msg",
              gr::io_signature::make(1, 3, 2*sizeof(float)),
              gr::io_signature::make(0, 0, 0)),
              d_queue(queue),
              d_msg_type(msg_type),
              d_lo(lo),
              d_hi(hi)
    {
        d_thresh_exceeded[0] = false;
        d_thresh_exceeded[1] = false;
        d_thresh_exceeded[2] = false;

        set_max_noutput_items(1);
    }

    /*
     * Our virtual destructor.
     */
    wat_thresh_msg_impl::~wat_thresh_msg_impl()
    {
    }

    void wat_thresh_msg_impl::send_update(int chan)
    {
        message::sptr msg = message::make(d_msg_type, chan, d_thresh_exceeded[chan]);
        d_queue->insert_tail(msg);
    }

    int
    wat_thresh_msg_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
        for (int j = 0; j < input_items.size(); j++) {
            const float *in = (const float *) input_items[j];

            for (int i = 0; i < noutput_items; i++) {
                float mag = sqrtf(in[2*i] * in[2*i] + in[2*i+1] * in[2*i+1]);
                //printf("%f ", mag);
                if (!d_thresh_exceeded[j] && mag > d_hi) {
                    d_thresh_exceeded[j] = true;
                    send_update(j);
                } else if (d_thresh_exceeded[j] && mag < d_lo) {
                    d_thresh_exceeded[j] = false;
                    send_update(j);
                }
            }
        }

        //printf("\n");

        return noutput_items;
    }

  } /* namespace same */
} /* namespace gr */

