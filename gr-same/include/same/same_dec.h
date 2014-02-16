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


#ifndef INCLUDED_SAME_SAME_DEC_H
#define INCLUDED_SAME_SAME_DEC_H

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
    class SAME_API same_dec : virtual public gr::sync_block
    {
     public:
      typedef boost::shared_ptr<same_dec> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of same::same_dec.
       *
       * To avoid accidental use of raw pointers, same::same_dec's
       * constructor is in a private implementation
       * class. same::same_dec::make is the public interface for
       * creating new instances.
       */
      static sptr make(msg_queue::sptr queue);
    };

  } // namespace same
} // namespace gr

#endif /* INCLUDED_SAME_SAME_DEC_H */

