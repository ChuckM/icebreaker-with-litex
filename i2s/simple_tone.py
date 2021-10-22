#!/usr/bin/env python3
# vim: expandtab:ts=4:
# Written by Chuck McManis September, 2021
# still just easy stuff
#
from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.generic_platform import *
from litex_boards.platforms.icebreaker import Platform, break_off_pmod
import math

# we'll call it a icebreaker of type Platform()
icebreaker = Platform()

#
# Create named resources for each PMOD pin on PMOD1A
#
io = [
        ("pmod1_0", 0, Pins("PMOD1A:0"), IOStandard("LVCMOS33")),
        ("pmod1_1", 0, Pins("PMOD1A:1"), IOStandard("LVCMOS33")),
        ("pmod1_2", 0, Pins("PMOD1A:2"), IOStandard("LVCMOS33")),
        ("pmod1_3", 0, Pins("PMOD1A:3"), IOStandard("LVCMOS33")),
        ("pmod1_4", 0, Pins("PMOD1A:4"), IOStandard("LVCMOS33")),
        ("pmod1_5", 0, Pins("PMOD1A:5"), IOStandard("LVCMOS33")),
        ("pmod1_6", 0, Pins("PMOD1A:6"), IOStandard("LVCMOS33")),
        ("pmod1_7", 0, Pins("PMOD1A:7"), IOStandard("LVCMOS33")),
        ("pmod2_0", 0, Pins("PMOD1B:0"), IOStandard("LVCMOS33")),
        ("pmod2_1", 0, Pins("PMOD1B:1"), IOStandard("LVCMOS33")),
        ("pmod2_2", 0, Pins("PMOD1B:2"), IOStandard("LVCMOS33")),
        ("pmod2_3", 0, Pins("PMOD1B:3"), IOStandard("LVCMOS33")),
        ("pmod2_4", 0, Pins("PMOD1B:4"), IOStandard("LVCMOS33")),
        ("pmod2_5", 0, Pins("PMOD1B:5"), IOStandard("LVCMOS33")),
        ("pmod2_6", 0, Pins("PMOD1B:6"), IOStandard("LVCMOS33")),
        ("pmod2_7", 0, Pins("PMOD1B:7"), IOStandard("LVCMOS33")),
    ]
icebreaker.add_extension(io)
icebreaker.add_extension(break_off_pmod)

#
# Construct a 256 sample table of Sine wave values.
#
sine_wave_data = []
for i in range(256):
    x = (2.0 * math.pi) * ( i / 256.0)
    a = 8388607 * math.sin(x)
    sine_wave_data.append(C(int(a),24))
    print("C(0x{:06x}), # {}".format(int(a),a))

print("Bit width of waveform data: {}".format(len(sine_wave_data[0])))

#triangle_wave_data = []
#for i in range(256):
#    a = int((2**16-1) * (i / 256.0))
#    triangle_wave_data.append(C(int(a)))
#    print("C(0x{:04x}), # {}".format(int(a),a))

wave = Array(sine_wave_data)

#
# This sets up the ICE40 PLL hard block.
#
class PLL(Module):
    """
        This sets up the built-in PLL hardware to generate a clock
        based on the input crystal which is higher in frequency
        than the crystal. It does this using a PLL.

        The output frequency is (12 Mhz * DIVF)/(2^DIVQ * DIVR) in
        simple feedback mode. You can run it faster in one of the
        more advanced modes. 

        This code was taken largely from @tnt's NitroFPGA
        repos. 

        Note frequency has has to be between 45 and 85 it is in
        MHz.
    """
    def __init__(self, plat, freq):
        """
            Takes platform and frequency, but it doesn't use
            frequency yet (currently hard coded to 48 MHz) it
            should likely take a clock domain for Global A and
            one for Global B so that it is a bit more flexible.
        """
        # our copy of reset
        self.rst = Signal(1)

        #
        # These steps add three new clock domains. Previously
        # there was only one domain which is the default reference
        # domain (sys). Clock domains are global to the design so
        # when you create them they are available in all modules.
        #
        # They are named "cd_<xxx>" (cd is "clock domain") and is
        # required. So these three domains are sys, por, and i2s.
        #
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        self.clock_domains.cd_i2s = ClockDomain()

        #
        # We'll use the 12 MHz clock to feed the PLL
        #
        clk12 = plat.request("clk12")
        #
        # This is the  button on the icebreaker, we'll treat it as
        # reset.
        #
        rst_n = plat.request("user_btn_n")

        # Power on Reset
        #
        # PLLs don't "lock" right away, they have to synchronize the VCO
        # with the source clock so that they are stable. So at power-on there
        # will be some time before the PLL is "locked" onto it's frequency.
        # This code has a 16 bit counter (por_count) that counts down from
        # 65535 to 0 as the power on delay. It is tied to the clock input
        # which will be 12 MHz so it will take about 5.4mS for it to count down.
        #
        por_count = Signal(16, reset=2**16-1)
        por_done = Signal(1)
        #
        # This combinatorial code wires ClockSignal() to the power on
        # reset clock domain's clk line. This is why it runs at 12MHz
        #
        self.comb += self.cd_por.clk.eq(ClockSignal())

        #
        # This combinatorial code sets the state of "por_done" to the boolean
        # por_count == 0, which is to say power on reset is "done" once the
        # por_count register has been decremented to 0.
        #
        self.comb += por_done.eq(por_count == 0)
        
        #
        # This sequential code is running in the power on reset clock domain
        # which you can tell because it isn't self.sync, rather 
        # it is self.sync.por All clock domains are name self.sync.<domain>
        # which is the name minus the 'cd_' prefix.
        #
        # The code just decrements por_count until por_done goes True (which
        # will happen by the above combinatorial code)
        #
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        #
        # This is a signal that comes off the PLL that says it is locked.
        #
        pll_locked = Signal(1)
        #
        # And this is a bit magical. There is a "hard block" (which means
        # not configurable gates but a specific circuit for doing a specific
        # thing) for the PLL. You can look up its I/Os in the Ice40 datasheet
        # and the ones we're using are assigned in this call to 'Instance'
        #
        # The Instance definition has named parameters for all of the i/os
        # that go to and come from the hard block, during the invocation
        # it is our job to wire them to things in our module.
        #
        # The important ones are wiring the outputs (GLOBALA and GLOBALB)
        # to clock domains, connecting the clk12 pin to the input, and
        # wiring the PLL locked indication to a signal we can use in our
        # code.
        #
        # Instance is a migen function that instantiates a hard block. We'll
        # use this again later for other hardware in the chip.
        #
        # This code sets DIVF to 'freq' and freq must be between 45 and 85.
        # This is multiplied by the system clock (12MHz) to give the VCO clock
        # and that clock must be in the range of 533MHz to 1066MHz in order
        # for the VCO to lock in "simple" mode.
        #
        # We set DIVQ to 2 since 2^2 is 4, and DIVR to 2 since
        # the clock divisor will be 2^DIVQ * (DIVR + 1). By selecting these
        # two the divisor is '12'.
        #
        # By setting DIVQ and DIVR this way we divide by 12 the VCO which was
        # the desired frequency multiplied by 12. So the output frequency is
        # (12 * freq) / 12 MHz or freq MHz. Easy right?
        #
        self.specials += Instance("SB_PLL40_2F_PAD",
            p_DIVR = 2,                    # this sets DIVR to '3'
            p_DIVF = freq-1,            # this sets DIVF to frequency
            p_DIVQ = 2,                    # this makes DIVQ 2^2 or 4.
            p_FILTER_RANGE = 1,
            p_FEEDBACK_PATH = "SIMPLE",    # simple feedback
            p_PLLOUT_SELECT_PORTA = "GENCLK",
            p_PLLOUT_SELECT_PORTB = "GENCLK",
            i_PACKAGEPIN = clk12,
            o_PLLOUTGLOBALA = self.cd_sys.clk,
            o_PLLOUTGLOBALB = self.cd_i2s.clk,
            i_RESETB = rst_n,
            o_LOCK = pll_locked,
        )

        #
        # The Reset Synchronizer makes sure that the clock domains are
        # synchronized. In this case they are synchronized to the power
        # on countdown being done.
        #
        self.specials += [
            AsyncResetSynchronizer(self.cd_sys, ~por_done | ~pll_locked),
            AsyncResetSynchronizer(self.cd_i2s, ~por_done | ~pll_locked),
        ]

        #
        # These lines add constraints to the platform clock periods so
        # that the build tools can insure that the final design will meet
        # the necessary timing requirements.
        #
        plat.add_period_constraint(self.cd_sys.clk, 1e9/(freq * 1e6))
        plat.add_period_constraint(self.cd_i2s.clk, 1e9/(freq * 1e6))
        plat.default_clk_period = 1e9/(freq * 1e6)
        
class I2S(Module):
    """
        This class implements an I2S interface to talk to a CODEC
        chip on the Digilent PMOD.

        The plan is to run it off the i2s clock at some point but for
        now it is running off the system clock domain.

    """
    def __init__(self, platform, left_dr, right_dr, mclk, sclk, lrclk, sdo):
        """
            Initialize the i2s engine.

            This code is for output only at the moment, so it isn't
            reading data from the receive side.

            left_dr and right_dr are either a Signal(16) or a Signal(24)
            depending on if you're sending 16 bit samples or 24 bit samples.
            The former are padded with 8 zeros to make them 24 bit samples.
            
            mclk is the master clock output
            sclk is the serial clock (or bit clock) output
            lrclk is the left/right channel select clock
            sdo is the serial bitstream of samples, sent MSB first.
            
            This module creates a clock domain, sample_clk which clocks
            each time a new sample is required. This lets you synchronize
            with this module easily.
        """
        delay = Signal(8)
        shift_count = Signal(8)
        self.clock_domains.cd_sample_clk = ClockDomain("cd_sample_clk")
        self.cd_sample_clk.clk = lrclk

        # used to trigger the oscilloscope
        d6 = platform.request("pmod1_6")
        #
        # Shift register holding data going out (one sample @ 24 bits)
        #
        xmit_reg = Signal(24)

        #
        # Serial Digital Out reflects the MSB of the transmit
        # shift register.
        #
        self.comb += [
            # this reflects the MSB of the transmit register to SDO
            sdo.eq(xmit_reg[-1]),
        ]

        sticks = Signal(4)
        lrticks = Signal(7)
        
        #
        # This sequential block generates the MCLK (master clock),
        # LRCLK (left/right clock), and the SCLK (serial clock).
        # The ratio of the master clock to the LRCLK determines
        # the bitwidth. We go for a 768x ratio starting with
        # a 25MHz master clock, which makes for a 48 bit
        # sample (2 x 24) sample period of 32.552 kHz
        #
        self.sync += [
            mclk.eq(~mclk),    # running at 1/2 the clock rate (25MHz)
            # @posedge of MCLK
            If(mclk == 0,
                If(sticks == 7,
                    sticks.eq(0),
                    sclk.eq(~sclk),
                    # @negedge of SCLK
                    If(sclk == 1,
                        shift_count.eq(shift_count + 1),
                        # generate LRCLK
                        If(shift_count == 23,
                            shift_count.eq(0),
                            lrclk.eq(~lrclk),
                        ),
                        # shift out bits
                        # Align sample to the MSB of the shift register
                        # before assigning it to the shift register.
                        If(shift_count == 0,
                            If(lrclk == 1,
                                xmit_reg.eq(left_dr << (24 - len(left_dr))),
                            ).Else(
                                xmit_reg.eq(right_dr << (24 - len(right_dr))),
                            )
                        ).Else(
                            xmit_reg.eq((xmit_reg[:-1] << 1) | xmit_reg[-1]),
                        ),
                    ),
                ).Else( sticks.eq(sticks + 1)),
            )
        ]

class Tone(Module):
    """
        This is a tone generator, it generates samples to send
        to the I2S unit which is is running at 24 kHz.
    
        freq is the tone frequency (should be < 12 kHz)
    """
    def __init__(self, freq):
        #
        # This is going to be our count (now 16 bits wide)
        #
        count = Signal(16)
        index = Signal(8)
        sample = Signal(8)
        left = Signal(24)
        right = Signal(24)
        left_reg = Signal(24)
        right_reg = Signal(24)
        busy = Signal(1)

        mclk = icebreaker.request("pmod1_3")
        sclk = icebreaker.request("pmod1_0")
        lrclk = icebreaker.request("pmod1_1")
        sdo = icebreaker.request("pmod1_2")
#
# Top connector (1 - 6)
#
        real_mclk = icebreaker.request("pmod2_0")
        real_lrclk = icebreaker.request("pmod2_1")
        real_sclk = icebreaker.request("pmod2_2")
        real_sdo = icebreaker.request("pmod2_3")

        txe = Signal(1)
        d7 = icebreaker.request("pmod1_7")
        wr = Signal(1)
        self.submodules += [
                I2S(icebreaker, left_reg, right_reg,
                            mclk, sclk, lrclk, sdo),
                PLL(icebreaker, 50)]

        sample_period_ns = 1e9/24.414e3

        #
        # The 'standard' divide by n clock divider
        #
        divisor = Signal(48)
        ticks = int(500e6/(freq * 256 * (1e9/100e6))) - 1
        print(f"Freq {freq}, ticks={ticks}")

        self.comb += [
            real_sclk.eq(sclk),
            real_sdo.eq(sdo),
            real_lrclk.eq(lrclk),
            real_mclk.eq(mclk),
            If(index == 0,
                d7.eq(1),
            ).Else(
                d7.eq(0)
            ),
        ]

        #
        # Feed the current sample to the i2s device
        #
        self.sync.sample_clk += [
            left_reg.eq(left),
            right_reg.eq(right),
        ]

        flip = Signal(1)
        self.sync += [
            divisor.eq(divisor + 1),
            If(divisor == ticks,
                divisor.eq(0),
                #
                # Generate a new sample for our tone, in this version
                # we are generating a simple sawtooth.
                #
                index.eq(index+1),
#debug code
                # two 24 bit samples, trigger on LRCLK to see
                # them in the scope trace
#               left.eq(0xAABBCC),
#               right.eq(0x112233),
# actual code
                left.eq(wave[index]),
                right.eq(wave[(index + 63)]),
# Debug code (goes from 0 to n)
#                sample.eq(index),
# at 10 steps per second.
        ).Else(
            divisor.eq(divisor + 1)
        ),
        ]

#
# Now instantiate a tone generator
#
tone_module = Tone(880);

#
# And "build" this into a bit file
#

icebreaker.build(tone_module)

