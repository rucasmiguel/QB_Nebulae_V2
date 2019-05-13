# Example 7 - Communicating continuous values with Csound's Channel System
# Author: Steven Yi <stevenyi@gmail.com>
# 2013.10.28
#
# This example introduces using Csound's Channel System to communicate 
# continuous control data (k-rate) from a host program to Csound. The 
# first thing to note is the RandomLine class. It takes in a base value
# and a range in which to vary randomly.  The reset functions calculates
# a new random target value (self.end), a random duration in which to 
# run (self.dur, expressed as # of audio blocks to last in duration), and
# calculates the increment value to apply to the current value per audio-block.
# When the target is met, the Randomline will reset itself to a new target
# value and duration.
# 
# In this example, we use two RandomLine objects, one for amplitude and 
# another for frequency.  We start a Csound instrument instance that reads
# from two channels using the chnget opcode. In turn, we update the values
# to the channel from the host program.  In this case, because we want to 
# keep our values generating in sync with the audio engine, we use a 
# while-loop instead of a CsoundPerformanceThread. To update the channel,
# we call the SetChannel method on the Csound object, passing a channel name
# and value.  Note: The getValue method on the RandomLine not only gets
# us the current value, but also advances the internal state by the increment
# and by decrementing the duration.

import csnd6
from random import randint, random
import time

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0

class RandomLine(object):
    def __init__(self, base, range):
        self.curVal = 0.0
        self.reset()
        self.base = base
        self.range = range

    def reset(self):
        self.dur = randint(256,512) 
        self.end = random() 
        self.increment = (self.end - self.curVal) / self.dur

    def getValue(self):
        self.dur -= 1
        if(self.dur < 0):
            self.reset()
        retVal = self.curVal
        self.curVal += self.increment
        return self.base + (self.range * retVal)

class InputData(object):
    def __init__(self, channel):
        self.curVal = 0.0
        self.channel = channel
        self.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

    def getValue(self):
        self.curVal = self.mcp.read_adc(self.channel)
        return self.curVal

# Declare Freq with an init value
# Our Orchestra for our project
orc = """
sr=44100
ksmps=32
nchnls=2
0dbfs=1

instr 1 
kamp chnget "amp"
kfreq chnget "freq"
printk 0.5, kamp
printk 0.5, kfreq
aout vco2 kamp, kfreq
aout moogladder aout, 2000, 0.25
outs aout, aout
endin"""

c = csnd6.Csound()    # create an instance of Csound
c.SetOption("-odac")  # Set option for Csound
c.SetOption("-+rtaudio=alsa") # Set option for Csound
c.SetOption("-m7")  # Set option for Csound
c.CompileOrc(orc)     # Compile Orchestra from String

sco = "i1 0 60\n"

c.ReadScore(sco)     # Read in Score generated from notes 
c.Start()             # When compiling from strings, this call is necessary before doing any performing


# The following is our main performance loop. We will perform one block of sound at a time 
# and continue to do so while it returns 0, which signifies to keep processing.  


#amp = RandomLine(.4, .2)    # create RandomLine for use with Amplitude
#freq = RandomLine(400, 80)  # create RandomLine for use with Frequency 
amp = InputData(0)
freq = 220;

c.SetChannel("amp", (amp.getValue()/1023.00))     # Initialize channel value before running Csound
# c.SetChannel("freq", freq.getValue())   # Initialize channel value before running Csound
#c.SetChannel("freq", freq.getValue())   # Initialize channel value before running Csound
c.SetChannel("freq", freq)   # Initialize channel value before running Csound

#print amp.getValue()
#print freq.getValue()

while (c.PerformKsmps() == 0):
    c.SetChannel("amp", 1.0 - (amp.getValue()/1023.00))   # update channel value 
    #c.SetChannel("freq", freq.getValue())
    c.SetChannel("freq", freq)
    #c.SetChannel("freq", freq.getValue()) # update channel value 

c.Stop()




