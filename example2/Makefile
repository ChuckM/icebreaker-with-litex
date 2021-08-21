#
# Blink the LED example using Litex/Migen
#
cylon.bit:	build/top.txt
	icepack $< $@

build/top.txt: cylon.py
	./cylon.py

flash: cylon.bit
	iceprog $<

clean:
	rm -rf build cylon.bit
