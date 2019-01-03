######################
#This file allows you to output text files per topic of the top (y) words per time slice
#	INPUT = "lda-seq" folder from Blei output folder
#	INPUT = reference list of words used to generate mult.dat file
#	OUTPUT = tab-delimited "topic1.txt"-"topic(y).txt", where each row is a time slice
######################

#install.packages("lda")
library(lda)

##############
#USER INPUTS
##############

basewd<-"/Users/Z/Dropbox/z/michigan state 2013/Dissertation/15_chapters/0_ungavoting/OUTPUT/0_topicmodel/"
ldaseqwd<-paste(basewd,"4_dtmoutput/SOURCE/t15/lda-seq/",sep="")
reflistwd<-paste(basewd,"3_dtmprep/1_multgen/",sep="")
outwd<-paste(basewd,"4_dtmoutput/OUTPUT/t15/1_model_topic_words/",sep="")

x=47 #no. of time slices
y=20 #no. words to print per time slice within each topic

reflistname<-"full-reflist.txt"
#######################
#CODE
#######################
setwd(reflistwd)
words<-read.vocab(reflistname)

setwd(ldaseqwd)
file.list <- system("ls topic-*-var-e-log-prob.dat", intern=TRUE)

counter=1
for (file in file.list) {
    a=scan(file)
    b=matrix(a,ncol=x,byrow=TRUE)
    b[]<-exp(b)
    topicfile=paste("topic",counter,".txt",sep="")
    for (i in 1:x) {
        try.df<-data.frame(b[,i],words, stringsAsFactors=FALSE)
        var.col<-colnames(try.df)
        var<-var.col[1] 
        to.sort<-try.df[order(-try.df[[var]]), ]
        setwd(outwd)
        cat(head(to.sort$words, y),"\n",sep="\t",file=topicfile,append=TRUE)
        setwd(ldaseqwd)
     }
     counter<-counter+1
}

