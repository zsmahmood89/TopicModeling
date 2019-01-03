#TopicModeling

#Written in Python 2. 

#####################################

(1) 0_UNGA_dtm_prep.py

	This file compiles a unique reference vocabulary for your data.

	To use, input user options as specified in the script.

	This script allows you the option of specifying your own regular expressions to remove from your text, and your own list of words to remove from the text. It also allows you the option of importing multiple CSV files. 

	REQUIRED: 

		header = ['id','day','month','year','speaker','speech']

	If you don't have these headers, this code won't work. 

	OUTPUT:

		"full-reflist.dat"

(2) 1_UNGA_dtm_mult.py
	
	This file takes the reference list and generates a full-mult.dat file, for use in Blei's DTM. It does so per year, for speed and parallelization.

	OUTPUT:

		- Lots of meta, mult, and full files if needed.

(3) 2_UNGA_dtm_cons.py

	This file takes the previously generated files and consolidates them to create the final product for Blei's DTM.

	OUTPUT: 

		"full-mult.dat"


