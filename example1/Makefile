#
# Blink the LED example using Litex/Migen
#
blinky.bit:	build/top.txt
	icepack $< $@

build/top.txt: blinky.py
	./blinky.py

flash: blinky.bit
	iceprog blinky.bit

clean:
	rm -rf build blinky.bit
