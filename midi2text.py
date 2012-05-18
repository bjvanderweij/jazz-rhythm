#!/usr/bin/python

from midi import *
import sys

inp = sys.argv[1]
stream = MidiInFile.MidiInFile(MidiToText.MidiToText(), open(inp))
stream.read()
