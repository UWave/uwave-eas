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
#include "mag_thresh_msg_impl.h"

#include <stdio.h>

namespace gr {
  namespace same {

    mag_thresh_msg::sptr
    mag_thresh_msg::make(msg_queue::sptr queue, long msg_type, float arg1, float lo, float hi)
    {
      return gnuradio::get_initial_sptr
        (new mag_thresh_msg_impl(queue, msg_type, arg1, lo, hi));
    }

    /*
     * The private constructor
     */
    mag_thresh_msg_impl::mag_thresh_msg_impl(msg_queue::sptr queue, long msg_type, float arg1, float lo, float hi)
      : gr::sync_block("mag_thresh_msg",
              gr::io_signature::make(1, 1, 2*sizeof(float)),
              gr::io_signature::make(0, 0, 0)),
              d_queue(queue),
              d_msg_type(msg_type),
              d_arg1(arg1),
              d_lo(lo),
              d_hi(hi),
              d_thresh_exceeded(false)
    {
        set_max_noutput_items(1);
    }

    /*
     * Our virtual destructor.
     */
    mag_thresh_msg_impl::~mag_thresh_msg_impl()
    {
    }

    void mag_thresh_msg_impl::send_update()
    {
        message::sptr msg = message::make(d_msg_type, d_arg1, d_thresh_exceeded);
        d_queue->insert_tail(msg);
    }

    int
    mag_thresh_msg_impl::work(int noutput_items,
			  gr_vector_const_void_star &input_items,
			  gr_vector_void_star &output_items)
    {
        const float *in = (const float *) input_items[0];

        for (int i = 0; i < noutput_items; i++) {
            float mag = sqrtf(in[2*i] * in[2*i] + in[2*i+1] * in[2*i+1]);
            //printf("%f ", mag);
            if (!d_thresh_exceeded && mag > d_hi) {
                d_thresh_exceeded = true;
                send_update();
            } else if (d_thresh_exceeded && mag < d_lo) {
                d_thresh_exceeded = false;
                send_update();
            }
        }

        //printf("\n");

        return noutput_items;
    }

  } /* namespace same */
} /* namespace gr */

