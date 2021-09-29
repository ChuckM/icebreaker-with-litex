#
# build a led chaser design example using Litex/Migen
#
DESIGN=cylon

$(DESIGN).bit:	build/top.txt
	icepack $< $@

build/top.txt: $(DESIGN).py
	./$(DESIGN).py

flash: $(DESIGN).bit
	iceprog $<

clean:
	rm -rf build $(DESIGN).bit
