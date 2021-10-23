Simple Tone generator
---------------------

This increases the complexity a bit further, the goal here is to generate
a single tone.

The "easy" way to do this would be to just re-use the blink code and set
the blink frequency into the audio range like 440Hz (that's the frequency
of the musical note 'middle A'). 

However, instead of generating a square wave, we would like to generate a
sine wave. And to generate a sine wave we need a way of converting a digital
value to an analog value. That is to say that the number 0 might represent
0 volts and the number 256 might represent 2.56 volts.

If you've used Arduinos or other micro processors you may have used pulse
width modulation. That generates a square wave and feeds it through an 
analog low pass filter consisting of a capacitor and a resistor. While crude,
that technique works for relatively low frequency outputs.

A better scheme is to use pulse density modulation or PDM which is done in 
[this video](https://www.youtube.com/watch?v=2pAy5DvuidA)

But if you're goal is to do audio, there is a whole class of chips based
on the Phillips [i2s](https://en.wikipedia.org/wiki/I%C2%B2S) protocol
which is widely supported by microprocessors and a lot of software.

Since I had one of those on hand, my goal in this example is to use it's
DAC to translate the sine wave values into a voltage.

## Overview of the design

The design implements three modules, the top module named `Tone`, a PLL
module named `PLL` that lets us create a clock that is faster than the
12 MHz that the crystal creates, and a module named `I2S` that implements
the i2s protocol and connects to the Digilent PMOD.

In this example the tone generator is super simple, it generates exactly one
tone at one frequency. That is all we need to do however to prove to ourselves
that our i2s module is working properly and once we have that we can replace
the simple tone generator with something that is more complex.
