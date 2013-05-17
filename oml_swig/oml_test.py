#!/usr/bin/env python

from oml import *

import sys, pdb

result = omlc_init("My_Client", sys.argv, None)

print result

mp_def = [
  ( "source", OML_UINT32_VALUE ),
  ( "destination", OML_UINT32_VALUE ),
  ( "length", OML_UINT32_VALUE ),
  ( "weight", OML_DOUBLE_VALUE ),
  ( "protocol", OML_STRING_VALUE ), 
  ( "protocol1", OML_STRING_VALUE ), 
  ( "protocol2", OML_STRING_VALUE ), 
  ( "protocol3", OML_STRING_VALUE ), 
  ( "protocol4", OML_STRING_VALUE ), 
  ( "protocol5", OML_STRING_VALUE ), 
]

mp = omlc_add_mp ("packet_info", mp_def);

print mp


omlc_start()


for i in range(1000):
 	print i
	values = OmlValueUArray(len(mp_def));

	omlc_zero_array(values.cast(), len(mp_def));

	source_id = 123
	destination_id = 456 
	packet_length = 789 * i
	weight = 1.7
	tab  = []
	for j in range(6):
	 	s = "toto %d %d" % (i , j)
		tab.append(s) 
        	c_omlc_set_string (values.cast(), 4 + j, s);
	   

	# protocol = "toto %i" % i
 	protocol = "toto" 

	c_omlc_set_int32 (values.cast(), 0, source_id);
	c_omlc_set_uint32 (values.cast(), 1, destination_id);
	c_omlc_set_uint32 (values.cast(), 2, packet_length);
	c_omlc_set_double (values.cast(), 3, weight);

	omlc_inject (mp, values.cast());

 	for j in range(6):
		c_omlc_reset_string(values.cast(), 4 + j)

omlc_close()


