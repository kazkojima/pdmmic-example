#
# This file is part of PDMmic.
#
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.fhdl.specials import Tristate

from litex.gen import *

from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *

from . import data_file

class PDMmic(Module, AutoCSR):
    def __init__(self, platform, pads):

        platform.add_source(data_file("pdm2pcm.v"), "verilog")
    
        self.submodules.fifo = fifo = stream.SyncFIFO([("data", 16)], 512)

        # CPU side
        self.ready = CSRStatus(1)
        self.data = CSRStatus(16)
        self.comb += [
            fifo.source.ready.eq(self.data.we),
            self.data.status.eq(fifo.source.data),
            self.ready.status.eq(fifo.source.valid)
        ]
        self.ctl = CSRStorage(fields=[
            CSRField("clock_in_en", size=1, reset=0, description="Enable external PDM clock")
        ])
        clock_in_en = self.ctl.fields.clock_in_en

        # MIC side
        pcm = Signal(24)
        pcm_strobe_out = Signal()
        self.comb += [
            fifo.sink.data.eq(pcm >> 8),
            fifo.sink.valid.eq(pcm_strobe_out)
        ]

        clko = Signal()
        clki = Signal()
        self.specials += Tristate(pads.clk,
                                  o = clko,
                                  oe = ~clock_in_en,
                                  i = clki)

        self.specials += Instance("PDM2PCM",
                                  i_clk = ClockSignal(),
                                  i_rst = ResetSignal(),
                                  i_pdm_data_in = pads.data,
                                  i_pdm_clock_in_en = clock_in_en,
                                  i_pdm_clock_in = clki,
                                  o_pcm_data_out = pcm,
                                  o_pcm_strobe_out = pcm_strobe_out,
                                  o_pdm_clock_out = clko)
