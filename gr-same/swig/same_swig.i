/* -*- c++ -*- */

#define SAME_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "same_swig_doc.i"

%{
#include "same/same_dec.h"
#include "same/wat_thresh_msg.h"
%}


%include "same/same_dec.h"
GR_SWIG_BLOCK_MAGIC2(same, same_dec);
%include "same/wat_thresh_msg.h"
GR_SWIG_BLOCK_MAGIC2(same, wat_thresh_msg);
