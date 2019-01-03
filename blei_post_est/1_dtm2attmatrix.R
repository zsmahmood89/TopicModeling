######################
#CREDIT: modified version of Will Issac's
#		 12 June 2014 "dtm_gammas_hpcc.R"
#
#This file generates an attention matrix from the gammas
#	INPUT = "lda-seq" folder from Blei output folder
#	INPUT = your file from DTM prep step with sequential speaker/speech info.
#	OUTPUT = "etheta.csv", where each row is a speech and each column a topic. The
#	values in each cell represent the proportion of attention given to each topic
#	in that speech. Note that very low numbers may be in scientific notation.
#	Remember, each speech represents the words of a given speaker at a given time.
#	OUTPUT = "speaker_etheta.csv" etheta file concatenated with your
#	speaker/speech file.
######################

#install.packages("stats")
#install.packages("lattice")
library(stats)
library(lattice)
##############
#USER INPUTS
##############

basewd<-"/Users/Z/Dropbox/Z/Michigan State 2013/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/"

#LDA, Speaker/Speech, and Output respectively
ldaseqwd<-paste(basewd,"4_dtmoutput/SOURCE/t15/lda-seq/",sep="")
metawd<-paste(basewd,"3_dtmprep/1_multgen/",sep="")
outwd<-paste(basewd,"4_dtmoutput/OUTPUT/t15/2_topic_perspeech/",sep="")

#number of topics
x<-15

#name of metafile with speaker info from your DTM prep
metafile<-"final_meta.csv"

#######################
#CODE
#######################

setwd(ldaseqwd)

a=scan("gam.dat")
b=matrix(a,ncol=x,byrow=TRUE)
rs=rowSums(b)
e.theta=b/rs

#Write the CSV file
setwd(outwd)
write.csv(e.theta,file="etheta.csv",row.names=FALSE)

#Merge attention matrix with your metafile
setwd(metawd)
metadf<-read.csv(metafile)
setwd(outwd)
mergeddf<-cbind(metadf,e.theta)
write.csv(mergeddf,file="attmatrix_raw.csv",row.names=FALSE)
head(mergeddf)
