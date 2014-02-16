/* -*- c++ -*- */
/* 
 * Copyright 2014 <+YOU OR YOUR COMPANY+>.
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


#ifndef INCLUDED_SAME_WAT_THRESH_MSG_H
#define INCLUDED_SAME_WAT_THRESH_MSG_H

#include <same/api.h>
#include <gnuradio/sync_block.h>
#include <gnuradio/msg_queue.h>

namespace gr {
  namespace same {

    /*!
     * \brief <+description of block+>
     * \ingroup same
     *
     */
    class SAME_API wat_thresh_msg : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<wat_thresh_msg> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of same::wat_thresh_msg.
       *
       * To avoid accidental use of raw pointers, same::wat_thresh_msg's
       * constructor is in a private implementation
       * class. same::wat_thresh_msg::make is the public interface for
       * creating new instances.
       */
      static sptr make(msg_queue::sptr queue, long msg_type, float lo, float hi);
    };

  } // namespace same
} // namespace gr

#endif /* INCLUDED_SAME_WAT_THRESH_MSG_H */

