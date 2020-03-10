
SRCS	:= $(wildcard *.html *.sgml *.xml)
NSGMLS	:= $(shell if command -v onsgmls 2>/dev/null; then	 \
			:					;\
		   elif command -v nsgmls 2>/dev/null; then	 \
			:					;\
		   else						 \
			echo "false"				;\
			echo "warning: no nsgmls found" 1>&2	;\
		   fi)

.PHONY: validate
validate:	$(addsuffix .validate,$(SRCS))

%.xml.validate : %.xml
	xmllint --noout --valid --nonet $<

%.xml.validate.nsgmls : %.xml
	SP_CHARSET_FIXED=YES SP_ENCODING=XML $(NSGMLS) -wxml -wall -gues /usr/share/xml/declaration/xml.dcl $<

%.xml.validate.rxp : %.xml
	rxp -sNVV $<

%.validate : %
	$(NSGMLS) -wall -gues $<

clean:
	rm -f /tmp/debian-man-ref.ent
