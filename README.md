[> Intro
--------
PDMmic provides a simple PDM microphone interface.

The implementation of PDM to PCM filter pipeline is based on [Tom Verbeure's articles for PDM to PCM conversion](https://tomverbeure.github.io/2020/12/20/Design-of-a-Multi-Stage-PDM-to-PCM-Decimation-Pipeline.html).

![Filter Pipeline](https://github.com/kazkojima/pdmmic-example/blob/main/doc/filter-pipeline.png)

Each filter in the pipeline is implemented with the Amaranth HDL as an [amlib](https://github.com/amaranth-community-unofficial/amlib) library.

examples/gsd_butterstick.py is a running example using LiteX on Greg Davill's ButterStick board. It consumes 12 multipliers when 24-bit width arithmetic is specified. To make this example work, you need to add a few lines for the microphone like
```
--- a/litex_boards/platforms/gsd_butterstick.py
+++ b/litex_boards/platforms/gsd_butterstick.py
@@ -128,7 +128,14 @@ _io_r1_0 = [
         Subsignal("stp",   Pins("C8")),
         Subsignal("rst",   Pins("C9")),
         IOStandard("LVCMOS18"),Misc("SLEWRATE=FAST")
-    ), 
+    ),
+
+    # PDM mic
+    ("pdmmic", 0,
+        Subsignal("data", Pins("L5")),
+        Subsignal("clk", Pins("M4")),
+        IOStandard("LVCMOS33")
+    ),
 ]
 
 # Connectors ---------------------------------------------------------------------------------------
```
to the litex platform description file platform/gsd_butterstick.py.

The following code snippet added to litex bios will send 1M samples to host udp 6000 port.
```
unsigned int test_pdmmic()
{
       unsigned int ip;

       printf("Generate packets with PCM (%dM samples)\n", mb);
       printf("Local IP : %d.%d.%d.%d\n", LOCALIP1, LOCALIP2, LOCALIP3, LOCALIP4);
       printf("Remote IP: %d.%d.%d.%d\n", REMOTEIP1, REMOTEIP2, REMOTEIP3, REMOTEIP4);

       ip = IPTOINT(REMOTEIP1, REMOTEIP2, REMOTEIP3, REMOTEIP4);
       udp_start(macadr, IPTOINT(LOCALIP1, LOCALIP2, LOCALIP3, LOCALIP4));

        if(!udp_arp_resolve(ip)) {
               printf("arp resolve fail\n");
                return -1;
       }

       int i, j;
       unsigned short rdat[512];
       char *buf;

       for (i = 0; i < 2*1024; i++) {
               for (j = 0; j < 512; j++) {
                       while (*(volatile char *)CSR_PDMMIC_READY_ADDR == 0) ;
                       rdat[j] = *(volatile short *)CSR_PDMMIC_DATA_ADDR;
               }
               buf = udp_get_tx_buffer();
               for (j = 0; j < 512*2; j++)
                       buf[j] = ((char *)rdat)[j];
               udp_send(6001, 6000, 512*2);
       }
       return 0;
}
```

[> Features
-----------
**TODO**

[> Getting started
------------------
**TODO**

PDMMic module is writen with Amaranth and its verilog output is needed to use it from LiteX. The command below will generate the verilog file. 
```
pushd pdmmic/verilog
make
popd
```

[> Tests
--------
**TODO**

[> Links
-------------

[1] Tom Verbeure, articles
* [An Intuitive Look at Moving Average and CIC Filters](https://tomverbeure.github.io/2020/09/30/Moving-Average-and-CIC-Filters.html)
* [PDM Microphones and Sigma-Delta A/D Conversion](https://tomverbeure.github.io/2020/10/04/PDM-Microphones-and-Sigma-Delta-Conversion.html)
* [Designing Generic FIR Filters with pyFDA and NumPy](https://tomverbeure.github.io/2020/10/11/Designing-Generic-FIR-Filters-with-pyFDA-and-Numpy.html)
* [From Microphone Datasheet to Filter Design Specification](https://tomverbeure.github.io/2020/10/17/From-Microphone-Datasheet-to-Design-Specification.html)
* [Half-Band Filters, a Workhorse of Decimation Filters](https://tomverbeure.github.io/2020/12/15/Half-Band-Filters-A-Workhorse-of-Decimation-Filters.html)
* [Design of a Multi-Stage PDM to PCM Decimation Pipeline](https://tomverbeure.github.io/2020/12/20/Design-of-a-Multi-Stage-PDM-to-PCM-Decimation-Pipeline.html)

