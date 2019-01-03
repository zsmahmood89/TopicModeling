#TopicModeling

#Written in Python 2. 

#Coming soon:
	(1) Python 3
	(2) Command-line-hashable script.

#####################################

(1) dtm_mult_gen.py

	This file allows you to generate the "*mult.dat" file to run David Blei's (2003) Dynamic Topic Model, a la the C code on his website. The code will output a file called "full-mult.dat". It will also generate a full reference list ("full-ref.txt") to match words to index, as well as a csv file containing meta-information to match row indices to the "*mult.dat" file. 

	To use, simply open it in a compiler (e.g. Enthought) and put in your user options as instructed. 

	This script allows you the option of specifying your own regular expressions to remove from your text, and your own list of words to remove from the text. It also allows you the option of importing multiple CSV files. 

	REQUIRED: 

		header = ['id','day','month','year','speaker','speech']

	If you don't have these headers, this code won't work. 

	OUTPUT:

		"full-mult.dat"
		"full-reflist.dat"

(2) dtm_seq_gen.py

	This file takes the output from the previous script, and creates the "*seq.dat" file to run David Blei's (2003) Dynamic Topic Model. 

	You'll have the option of interactively editing the months, should you choose. For example, if you misspelled a month "Nvember", my function won't recognize it so I can convert it to a number; the "interactive" mode will allow you to directly input it in your compiler as "11". 

	You also have the option of specifying daily; monthly; quarterly; bi-annual; or annual time slices. 

	OUTPUT:

		"full-seq.dat"


