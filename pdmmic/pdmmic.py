#
# This file is part of PDMmic.
#
# SPDX-License-Identifier: BSD-2-Clause

from migen import *

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

        # MIC side
        pcm = Signal(24)
        pcm_strobe_out = Signal()
        self.comb += [
            fifo.sink.data.eq(pcm >> 8),
            fifo.sink.valid.eq(pcm_strobe_out)
        ]

        self.specials += Instance("PDM2PCM",
                                  i_clk = ClockSignal(),
                                  i_rst = ResetSignal(),
                                  i_pdm_data_in = pads.data,
                                  o_pcm_data_out = pcm,
                                  o_pcm_strobe_out = pcm_strobe_out,
                                  o_pdm_clock_out = pads.clk)
