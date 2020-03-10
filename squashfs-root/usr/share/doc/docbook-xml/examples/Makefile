
SRCS	:= $(wildcard *.xml)
NSGMLS	:= $(shell if command -v onsgmls 2>/dev/null; then	 \
			:					;\
		   elif command -v nsgmls 2>/dev/null; then	 \
			:					;\
		   else						 \
			echo "false"				;\
			echo "warning: no nsgmls found" >&2	;\
		   fi)

NSGMLSARGS	:= -m/usr/share/sgml/declaration/xml.soc

# settings for XML files
export SP_CHARSET_FIXED = YES
export SP_ENCODING = XML

.PHONY: validate
validate:	$(addsuffix .nsgmls,$(SRCS)) $(addsuffix .xmllint,$(SRCS))

%.xmllint  : %
	xmllint --nonet --noout --valid $<

%.nsgmls   : %
	$(NSGMLS) -E1 -wxml -wall $(NSGMLSARGS) -gues $<

.PHONY: clean
clean:
	rm -f *.html *~
