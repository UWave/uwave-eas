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

#ifndef INCLUDED_SAME_LEVEL_THRESH_MSG_IMPL_H
#define INCLUDED_SAME_LEVEL_THRESH_MSG_IMPL_H

#include <same/level_thresh_msg.h>

namespace gr {
  namespace same {

    class level_thresh_msg_impl : public level_thresh_msg
    {
     private:
      msg_queue::sptr d_queue;
      long d_msg_type;
      float d_arg1;
      float d_lo, d_hi;
      bool d_thresh_exceeded;

      void send_update();

     public:
      level_thresh_msg_impl(msg_queue::sptr queue, long msg_type, float arg1, float lo, float hi);
      ~level_thresh_msg_impl();

      // Where all the action really happens
      int work(int noutput_items,
	       gr_vector_const_void_star &input_items,
	       gr_vector_void_star &output_items);
    };

  } // namespace same
} // namespace gr

#endif /* INCLUDED_SAME_LEVEL_THRESH_MSG_IMPL_H */

