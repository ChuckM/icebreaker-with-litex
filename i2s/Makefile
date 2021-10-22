#
# Build a simple tone generator
#
DESIGN=simple_tone

$(DESIGN).bit:	build/top.txt
	icepack $< $@

build/top.txt: $(DESIGN).py
	./$(DESIGN).py

flash: $(DESIGN).bit
	iceprog $<

clean:
	rm -rf build $(DESIGN).bin __pycache__

