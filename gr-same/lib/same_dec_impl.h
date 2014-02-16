/* -*- c++ -*- */
/* 
 * Copyright 2013 Karl Koscher <supersat@uwave.fm>
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

#ifndef INCLUDED_SAME_SAME_DEC_IMPL_H
#define INCLUDED_SAME_SAME_DEC_IMPL_H

#include <same/same_dec.h>
#include <string>

namespace gr {
  namespace same {

    class same_dec_impl : public same_dec
    {
     private:
      msg_queue::sptr d_queue;
      std::string same_msg;

      bool d_is_synced;
      int d_dashes_received; // -1 if a plus '+' hasn't been received yet


      // Ring buffer, stores the last 128 incoming bits when not synced
      char d_incoming_bits[128];
      int d_incoming_bits_next_free_index;

      void process_char();
      void send_same_message();
      void send_eom_message();
      bool check_sync();

     public:
      same_dec_impl(msg_queue::sptr queue);
      ~same_dec_impl();

      // Where all the action really happens
      int work(int noutput_items,
	       gr_vector_const_void_star &input_items,
	       gr_vector_void_star &output_items);
    };

  } // namespace same
} // namespace gr

#endif /* INCLUDED_SAME_SAME_DEC_IMPL_H */

