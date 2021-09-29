#
# build the 7 segment display example
#
DESIGN=display

$(DESIGN).bit:	build/top.txt
	icepack $< $@

build/top.txt: $(DESIGN).py led7segment.py
	./$(DESIGN).py

flash: $(DESIGN).bit
	iceprog $<

clean:
	rm -rf build $(DESIGN).bit __pycache__
