#!/usr/bin/env python3
#
# Copyright (c) 2021 Kaz Kojima <kkojima@rr.iij4u.or.jp>
# SPDX-License-Identifier: CERN-OHL-W-2.0

from amaranth import *
from amaranth.lib.fifo import SyncFIFO
from amaranth.hdl.ast import Rose, Fell
from amaranth.cli import main

from amlib.test import GatewareTestCase, sync_test_case
from amlib.utils import SimpleClockDivider
from amlib.dsp import FixedPointCICFilter, FixedPointHBFilter, FixedPointFIRFilter

import numpy as np

class PDM2PCM(Elaboratable):
    """ PDM to PCM filter pipeline

        Attributes
        ----------
        pdm_clock_out: Signal(), output
            PDM clock signal
        pdm_data_in: Signal(), input
            PDM data signal
        pcm_strobe_out: Signal(), out
            PCM clock signal
        pcm_data_out: Signal(width), out
            PCM data signal

        Parameters
        ----------
        divisor: int
            clock divisor constant
        bitwidth: int
            width
        fraction_width: int
            fraction width
        cic_stage: int
            stage number of CIC filter
        cic_decimation: int
            decimation constant of CIC filter
        hb1_order: int
            order of the 1st Half-band filter
        hb2_order: int
            order of the 2nd Half-band filter
        fir_order: int
            order of FIR filter
        fir_cutoff: list
            start/stop band frequencies of FIR filter
        fir_rpl_att: list
            ripple/attenuation of pass/stop bands
        """
    def __init__(self,
                 divisor: int=28,
                 bitwidth: int=24,
                 fraction_width: int=24,
                 cic_stage: int=6,
                 cic_decimation: int=12,
                 hb1_order: int=11,
                 hb2_order: int=19,
                 fir_order: int=51,
                 fir_fs: int=48000,
                 fir_cutoff: list=[10000, 14000],
                 fir_rpl_att: list=[0.05, 60]):
        self.pdm_clock_out = Signal()
        self.pdm_data_in = Signal()
        self.pcm_strobe_out = Signal()
        self.pcm_data_out = Signal(signed(bitwidth))

        self.divisor = divisor
        self.bitwidth = bitwidth
        self.fraction_width = fraction_width
        assert bitwidth <= fraction_width, f"Bitwidth {bitwidth} must not exceed {fraction_width}"
        self.cic_stg = cic_stage
        self.cic_decim = cic_decimation
        self.hb1_order = hb1_order
        self.hb2_order = hb2_order
        self.fir_order = fir_order
        self.fir_fs = fir_fs
        self.fir_cutoff = fir_cutoff

        Apb = fir_rpl_att[0]
        Asb = fir_rpl_att[1]
        err_pb = (1 - 10**(-Apb/20))/2
        err_sb = 10**(-Asb/20)
        self.fir_weight = [1/err_pb, 1/err_sb]

    def elaborate(self, platform) -> Module:
        m = Module()

        clk_divider = SimpleClockDivider(self.divisor)
        m.submodules.clk_divider = clk_divider
        m.d.comb += [
            clk_divider.clock_enable_in.eq(1),
            self.pdm_clock_out.eq(clk_divider.clock_out)
        ]
        strobe_in = Rose(clk_divider.clock_out, domain="sync")
        strobe_out = Signal()

        bw = self.bitwidth
        fbw = self.fraction_width

        cic = FixedPointCICFilter(bitwidth=bw,
                                  filter_stage=self.cic_stg,
                                  decimation=self.cic_decim,
                                  verbose=False)
        m.submodules.cic = cic
        hb1 = FixedPointHBFilter(bitwidth=bw,
                                 fraction_width=fbw,
                                 filter_order=self.hb1_order,
                                 mac_loop=True,
                                 verbose=False)
        m.submodules.hb1 = hb1
        hb2 = FixedPointHBFilter(bitwidth=bw,
                                 fraction_width=fbw,
                                 filter_order=self.hb2_order,
                                 mac_loop=True,
                                 verbose=False)
        m.submodules.hb2 = hb2
        fir = FixedPointFIRFilter(samplerate=self.fir_fs,
                                  bitwidth=bw,
                                  fraction_width=fbw,
                                  cutoff_freq=self.fir_cutoff,
                                  filter_order=self.fir_order,
                                  weight=self.fir_weight,
                                  mac_loop=True,
                                  verbose=False)
        m.submodules.fir = fir

        with m.If(self.pdm_data_in):
            m.d.comb += cic.signal_in.eq(1)
        with m.Else():
            m.d.comb += cic.signal_in.eq(-1)

        m.d.comb += [
            cic.strobe_in.eq(strobe_in),
            hb1.strobe_in.eq(cic.strobe_out),
            hb2.strobe_in.eq(hb1.strobe_out),
            strobe_out.eq(hb2.strobe_out),
            fir.enable_in.eq(strobe_out),
            self.pcm_strobe_out.eq(strobe_out),
            hb1.signal_in.eq(cic.signal_out),
            hb2.signal_in.eq(hb1.signal_out),
            fir.signal_in.eq(hb2.signal_out)
        ]

        with m.If(strobe_out):
            m.d.sync += self.pcm_data_out.eq(fir.signal_out)

        return m

with_deltasigma = False
if with_deltasigma:
    from deltasigma import *

class PDM2PCMTest(GatewareTestCase):
    FRAGMENT_UNDER_TEST = PDM2PCM
    FRAGMENT_ARGUMENTS = dict(divisor=8)

    @sync_test_case
    def test_pdm2pcm(self):
        dut = self.dut
        N = 8192
        if with_deltasigma:
            OSR = 32
            H = synthesizeNTF(1, OSR, 1)
            f = 1
            u = 0.75*np.sin(2*np.pi*f/N*np.arange(N))
            v = simulateDSM(u, H)[0]
        else:
            v = np.load('test/sine_ord4_osr64.npy')
        for i in range(N*8):
            yield dut.pdm_data_in.eq(1 if v[i//8] > 0 else 0)
            yield

 
if __name__ == "__main__":

    pdm2pcm = PDM2PCM()

    ports = [
        pdm2pcm.pdm_clock_out,
        pdm2pcm.pdm_data_in,
        pdm2pcm.pcm_strobe_out,
        pdm2pcm.pcm_data_out
    ]
    main(pdm2pcm, name="PDM2PCM", ports=ports)
