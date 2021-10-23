#!/usr/bin/env python3
# vim: expandtab:ts=4:
# Written by Chuck McManis August, 2021
# Not a lot of useful stuff here feel free to use it how you would like.
#
# first import all the things from Migen ...
#
from migen import *

# base class is the Platform()
from litex.build.generic_platform import *

#
# Okay, so unlike in 01_Blink, this version just grabs the predefined
# platform from litex_boards.platforms.icebreaker and the break_off_pmod
# definition that is also in that module.
#
from litex_boards.platforms.icebreaker import Platform, break_off_pmod

#
# Create an instance of an icebreaker from it. This has the various LEDs
# and connectors pre-defined.
#
icebreaker = Platform()
#
# The following makes the break_off_pmod bits available for use in the
# code if requested.
#
icebreaker.add_extension(break_off_pmod)

#
# Using python to automate some typing.
#
# This function loops through 0 to 7 and defines Subsignals of the form
# "led<n>", "PMODx:<n>".
#
# Two interesting things going on here, Subsignals and Connections.
#
# Subsignal(...) gives a name to one or more of the signals that are part of a
# Signal(...) definition. If you look in the platform definition for the
# icebreaker you will see there is a definition of 'serial' with two sub-signals
# one called 'rx' and one called 'tx'. This creates a new signal called 'led8'
# which has 8 sub-signals led0 through led7.
#
# Connections(...) are I/O pins that go off board or to a connector. In this
# case there are three PMOD connectors, each has eight I/Os. In the platform
# definition file they are assigned to pins on the FPGA and named one of PMOD1
# PMOD2, or PMOD3. Unlike signals they are simply a text map from a connector
# name : pin number (0 - n) to the string to give to the Pin(...) class that
# connects that to the FPGA proper. So PMOD3:0 is pin 0, of connector PMOD3.
#
# The net effect of this code is to generate an 8 bit wide signal with each
# line of that signal having its own subname. They are then used in module
# code with something like "<SignalName>.led0" to talk to the first LED.
#
def gen_led8(pmod_port, num):
    led8 = ["led8", num]
    for i in range(8):
        led8.append(
            Subsignal(f"led{i}", Pins(f"{pmod_port}:{i}"),
                                 IOStandard("LVCMOS33")))
    return tuple(led8)

#
# Two LED8 Pmods are attached, one to PMOD1A and one to PMOD1B.
# The gen_led8 code creates a tuple that defines an "extension." Module
# code can then request that extension from the platform later and that
# is what we do in this code. We add a different unit number to them so
# that we can pick which one we want to wire up in our module code.
#
icebreaker.add_extension([gen_led8("PMOD1A", 0)])
icebreaker.add_extension([gen_led8("PMOD1B", 1)])

#
# At this point we have an augmented platform with extensions describing
# the connection to two LED8 PMODs. At this point then we define a top
# level module like we did in Blink to send some data to them.
#
# If you don't understand why it's called 'Cylon' look up Battlestar
# Galactica on the Internet :-). I suppose I could also name it Night Rider
# but that is more typing.
#
class Cylon(Module):
    """
        A module that has an LED bouncing back and forth on two LED8
        PMODs connected to PMOD port 1a and PMOD port 1b 
    """
    def __init__(self, blink_freq):
        #
        # As with the Blink example, we "request" the signals associated
        # with the name "led8" because we're going to be talking to them.
        #
        leds = icebreaker.request("led8", 0)
        more_leds = icebreaker.request("led8", 1)
 
        # Now we define a 'display' register which will hold the state
        # of 16 LEDs and we add the parameter 'reset=1' which means that
        # the reset state will set the value to 0b0000000000000001
        display = Signal(16, reset=0x7)

        #
        # Direction remembers if we are going left or right.
        #
        direction = Signal(1)

        #
        # Hold the button down to go around and around
        #
        button = icebreaker.request("user_btn")

        #
        # Same counter/ticks like we used in Blink, look at the comments
        # in that code for why 24 is enough bits of counter or how we
        # compute ticks.
        counter = Signal(24)
        ticks = int(500e6 / (blink_freq * icebreaker.default_clk_period)) - 1


        #
        # And this is a contrived example (in a planned example they would have
        # been defined this way) but it demonstrates an FHDL function i
        # 'Cat(...)' which is short for concatenate.
        #
        # This code is essentially punning (symlinking?) the 16 leds in the
        # two LED8 PMODs into a single bus called "all_leds" which has a 'shape'
        # of 16. What that means is we can assign a 16 bit value to this bus
        # and it will change all of the LEDs at once. (We don't need to turn
        # each one on individually). Now this example is just adding them in
        # order, but the nice thing here is that you could combine a bunch of
        # signals into a single bus for easier assignment or reading.
        #
        all_leds = Cat(
                more_leds.led7, more_leds.led6, more_leds.led5, more_leds.led4,
                more_leds.led3, more_leds.led2, more_leds.led1, more_leds.led0,
                leds.led7, leds.led6, leds.led5, leds.led4,
                leds.led3, leds.led2, leds.led1, leds.led0,
        )

        #
        # Now for the synchronous part.
        #
        # When enough ticks have gone by (the If() statement) the code does
        # the following:
        #
        #    if the direction is LEFT then
        #        it rotates the display value left
        #    else
        #        it rotates the display value right
        #
        #    if it has done 12 rotations it switches direction.
        #
        # Many will immediately recognize that this is the algorithm for
        # having a light ping pong from one end of a string of lights to
        # the other.
        #
        # For a bit of added fun, if you push and hold button 1 on the break
        # off pmod it will not change direction and continue rotating in
        # the direction it was rotating.
        #
        fin = Signal(5)
        self.sync += [
            counter.eq(counter + 1),
            If(counter == ticks,
                counter.eq(0),
                fin.eq(fin + 1),
                If(fin == 12,
                    fin.eq(0),
                    If(button == 0,
                        direction.eq(~direction)
                    ),
                ),
                #
                # This is the chaser code, depending on which way
                # the chaser is running, it rotates the display left
                # or right.
                #
                If(direction == 0,
                    display.eq(display << 1 | display[-1]),
                ).Else(
                    display.eq(display >> 1 | (display[0] << (len(display)-1))),
                ),
            )
        ]
        #
        # This is the combinatorial code. 
        # This code sends the state of the display register to
        # all 16 LEDs.
        # 
        #
        self.comb += [
            all_leds.eq(display),
        ]

#
# now we instantiate our LED chaser.
#
led_module = Cylon(15);

#
# And "build" this into a bit file
#
icebreaker.build(led_module)

