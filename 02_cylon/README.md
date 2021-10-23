New features, new module
------------------------

Now that we've proven the toolchain works, this example goes on to
use some more features of LiteX.

The first thing is that this example uses the 'built in' board
definition for the 1bitsquared Icebreaker board. What that gives us is
that all the pins are already defined so we don't have to define them
and it uses a new construct called `Connector` which describes the three
PMOD ports (1A, 1B, and 2). It also gives us a definition for the signals
that drive the "break off" PMOD, the buttons and LEDs that are attached
to the board when it arrives. 

The second thing this example does is to programmatically define the signals
of a new PMOD, which in this case is the 
[Digilent 8 LED PMOD](https://store.digilentinc.com/pmod-8ld-eight-high-brightness-leds/).

The code in `led8_mod` takes a single argument, the connector that the PMOD
is plugged into. Since we are using two we use this function twice, once for
the PMOD connected to PMOD1A and once for the PMOD connected to PMOD1B.

That is followed by a call to `platform.add_extension()` which adds those
PMOD signal resources to our design.

And finally our simple design module, called `Chaser` expects that these LED8
PMODs are present, and it finds them using `platform.request("led8")` which
it does twice, to get access to the signal definitions for both PMODs.

The module defines `display` which holds the state of 16 LEDs in it, and
because it is assigned in the `sync` block it will become a register. There
is also a 1 bit flip flop assigned to the value `direction` to indicate if
the chaser is moving left or right.

The same count down timer/divider is used to convert the clock in signal to
a clock at the frequency that the LED will change state. I find 10Hz provides
a reasonable speed.

In the combinatorial section, the value in the `display` register is routed
to the LED8 PMODs. This is done with an assignment much like the `Blinker`
code in example 1 did but with more LEDs. I've left in the code the three
different ways I tried to make this work. Two of them do what I wanted and
one does not.

The final working solution (which I like because the intent is clear without
being too wordy), was to use the `Cat()` operation to create a new 16 wide 
Signal called `all_leds` which aliases the two PMOD's individual signals
to a single bus. The combinatorial code then does an assignment to this
bus from the state of the `display` register and it appears on the LEDs.

### A note about bits

One of the important things to keep in mind (and this is useful in a later
example) is the "order" of the bits in a multi-bit `Signal`. Bit 0 is the LSB
and bit `<name>.len - 1` is the most significant bit or MSB. This is the
reverse of most HDLs where bit 0 is the MSB and the last bit is the LSB.

Because LiteX is built on top of python, it knows about "slices" which are
subsets of an array. And bit subsets are the same with one 
**important difference.** The second value of a slice is not included in 
the slice. So if in python you wrote `array_name[2:5]` that would be an
array of _four_ elements (2, 3, 4, 5), but in LiteX it is only _three_
elements (2, 3, and 4). The last element is still -1, so slices that refer
to -1 _will include_ the last element. 

### Bit Ordering and Orientation

When I did this example I had my icebreaker on my desk (held by a small vise)
with PMOD1A and PMOD1B pointed "up", and that puts the break off pmod to the
right. Thus when I defined a `all_leds` I made the least significant bit (bit
0 remember) to be the rightmost LED and the most significant bit to be the
leftmost LED. That choice is of course arbitrary and you could define them
any way you find convenient. It is harder to debug however when it doesn't
work. My first attempt had the two PMODs swapped in the definition so
the LSB through mid-point were on the left set of LEDs and the upper midpoint
to the MSB were on the rightmost LEDs! 

