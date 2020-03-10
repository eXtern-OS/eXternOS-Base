sort: sort-corrections sort-corrections-case sort-corrections-multiword

sort-%: %
	csplit --prefix $<- $< '/^$$/'
	LC_ALL=en_US sort -u $<-01 | cat $<-00 - > $<
	rm -f $<-0[01]
