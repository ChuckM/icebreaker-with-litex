#
# Build a module and a sub-module
#

DESIGN=display_two

$(DESIGN).bit:	build/top.txt
	icepack $< $@

led7segment.py: ../pmod/led7segment.py
	ln -s ../pmod/led7segment.py $@

build/top.txt: $(DESIGN).py led7segment.py
	./$(DESIGN).py

flash: $(DESIGN).bit
	iceprog $<

clean:
	rm -rf build $(DESIGN).bit __pycache__ led7segment.py

