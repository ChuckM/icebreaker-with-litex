#!/usr/bin/env python3
#
# Written by Chuck McManis September, 2021
# still just easy stuff
#
from migen import *
from litex.build.generic_platform import *
from litex_boards.platforms.icebreaker import Platform, break_off_pmod
from led7segment import SevenSegmentLedDisplay

# we'll call it an icebreaker of type Platform()
icebreaker = Platform()

#
# This is the 'standard' break off PMOD that is attached to the board,
# it is defined in the litex_boards.platforms.icebreaker module.
#
icebreaker.add_extension(break_off_pmod)

class Counter(Module):
	def __init__(self, count_speed):
		#
		# This is going to be our count (now 16 bits wide)
		#
		count = Signal(16)
		#
		# The LEDs on the break off PMOD are a sub-count (they
		# count in a circle and each complete circle the digits
		# count up by one (1)
		#
		leds = Array([
			icebreaker.request("user_ledg", 0),
			icebreaker.request("user_ledg", 2),
			icebreaker.request("user_ledg", 1),
			icebreaker.request("user_ledg", 3),
		])

		#
		# The 'standard' divide by n clock divider
		#
		divisor = Signal(24)
		ticks = int((500e6/(count_speed * icebreaker.default_clk_period))) - 1
		index = Signal(3)

		self.sync += [
			divisor.eq(divisor + 1),
			If(divisor == ticks,
				divisor.eq(0),
				If(index == 3,
					index.eq(0),
					#
					# We have to add several new tests for roll over in the 
					# hundreds and thousands places, as well as a new reset
					# test for 9999.
					#
					If(count == 0x9999,
						count.eq(0)
					).Elif(count[:12] == 0x999,
						count.eq(count + 0x667)
					).Elif(count[:8] == 0x99,
						count.eq(count + 0x67)
					).Elif(count[:4] == 9,
						count.eq(count + 0x7)
					).Else(
						count.eq(count + 1)
					),
				).Else (
					index.eq(index + 1),
				),
			),
		]
		self.comb += [
			#
			# This drives the break off PMOD LEDs based on the
			# current index count
			#
			If(index == 0, leds[0].eq(1)).Else(leds[0].eq(0)),
			If(index == 1, leds[1].eq(1)).Else(leds[1].eq(0)),
			If(index == 2, leds[2].eq(1)).Else(leds[2].eq(0)),
			If(index == 3, leds[3].eq(1)).Else(leds[3].eq(0)),
 		]
		# we will put the 'upper' two digits on PMOD1
		self.submodules += [SevenSegmentLedDisplay(icebreaker, "PMOD1A", 
															value=count[8:])]
		# and the 'lower' two digits on PMOD2
		self.submodules += [SevenSegmentLedDisplay(icebreaker, "PMOD1B", 
															value=count[:8])]


#
# Now instantiate a counter, which instantiates an LED display
# sub-module which is showing the count.
#
count_module = Counter(4);

#
# And "build" this into a bit file
#

icebreaker.build(count_module)

