#
# Blink the LED example using Litex/Migen
#
DESIGN=blink

$(DESIGN).bit:	build/top.txt
	icepack $< $@

build/top.txt: $(DESIGN).py
	./$(DESIGN).py

flash: $(DESIGN).bit
	iceprog $<

clean:
	rm -rf build $(DESIGN).bit
