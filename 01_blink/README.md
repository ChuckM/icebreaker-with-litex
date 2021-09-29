Very 'simple' Blinker
---------------------

This example/test was created to see if I even understood what was going
on with LiteX. The enjoy-digital folks are really cool but their documentation
leaves a bit to be desired so there was some experiementation here to get
to this point.

A very good reference for the Migen "FHDL" language is 
located at [https://m-labs.hk/migen/manual/](https://m-labs.hk/migen/manual/).

## What it does

Basically this file creates a "platform" file which is an essential element
of Litex. If you are used to embedded systems development this is sort of
like the "BSP" for the board, it pre-defines where things are, the kind of
chip you are using, Etc. Because Litex also includes a build system this
is where you define what tool chain you want to use to build the board.

From a class heirarchy point of view you have a generic `Platform()` class
which you subclass with a build class which in this case is `LatticePlatform()`
and then you subclass _that_ with a definition of your board, telling
Litex what pin has the clock, what the default clock speed is, and if you
have things attached to specific IO pins, you define those as well.

From that you can then instantiate a `Module` which is what an FPGA
designer would think of as the "top" module. We'll get into module
heirarchies in a bit.

## How to use it

So from this directory, assuming you have an icebreaker attached to the
computer, you can just type `make flash` and the "built-in" PMOD will start
flashing alternately red and then green. If you push button 2 it will flash
both red and green simultaneously.
