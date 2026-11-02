"""BMS / monitor board (concept, rev A, 2026-11-02) -- complete part/net definition.

Ratings come from params/product_params.py (BMS dict).  Run through pcb/tools/gen_project.py.
Every net is named; nets starting with CHnn_ / SH_ are galvanically-isolated HV islands,
ICAN_ / I485_ are the isolated comms domains (see pcb_assumptions.md).
"""
import os, sys
LAB = "/Volumes/Aditya ssd/Salt-Battery-Lab"
sys.path.insert(0, LAB)
sys.path.insert(0, os.path.join(LAB, "pcb", "tools"))
from params.product_params import BMS, MONOBLOC, MODULE48, CABINET, R1_CELL_V_MAX  # noqa: E402
import kigen as K  # noqa: E402

NAME = "bms_monitor"
N_CH = BMS["series_groups_per_board"]          # 16
N_NTC = BMS["ntc_channels"]                    # 8
V_BLOCK_FS = BMS["block_v_range"][1]           # 20 V per channel full scale
SHUNT_MOHM = BMS["shunt_mohm"]                 # 0.25 mOhm
I_MAX = BMS["shunt_A_max"]                     # 200 A
V_SHUNT_FS = I_MAX * SHUNT_MOHM * 1e-3         # 0.050 V  -> AMC3302 +/-50 mV linear range
VIN_MIN, VIN_MAX = BMS["supply_V"]             # 9..60 V

# divider for the AMC3330 (+/-1 V linear input, gain 2) feeding an ADS131M08 (FSR +/-1.2 V at gain 1):
R_TOP, R_BOT = 1.00e6, 30.1e3
DIV = R_BOT / (R_TOP + R_BOT)                  # 0.02922 -> 20 V -> 0.584 V at AMC input -> 1.169 V at ADC
assert V_BLOCK_FS * DIV * 2.0 < 1.2, "ADC would clip"
assert abs(V_SHUNT_FS - 0.050) < 1e-9

LIB_DIR = os.path.join(LAB, "pcb", "lib")
CUSTOM_LIB = os.path.join(LIB_DIR, "salt_pcb.kicad_sym")

FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R1206 = "Resistor_SMD:R_1206_3216Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_C1210 = "Capacitor_SMD:C_1210_3225Metric"
FP_XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
FP_MKDS2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
FP_MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
FP_MC3 = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_3-G-3.5_1x03_P3.50mm_Horizontal"
FP_MC6 = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_6-G-3.5_1x06_P3.50mm_Horizontal"
FP_LED = "LED_SMD:LED_0603_1608Metric"
FP_FB = "Inductor_SMD:L_0603_1608Metric"


def ensure_custom_lib():
    os.makedirs(LIB_DIR, exist_ok=True)
    K.make_custom_lib(CUSTOM_LIB, [
        ("AMC3302", "Isolator_Analog:AMC3330", {
            "Value": "AMC3302",
            "Datasheet": "https://www.ti.com/lit/ds/symlink/amc3302.pdf",
            "Description": "TI AMC3302 +/-50 mV input reinforced isolated amplifier, gain 41, integrated DC/DC, SOIC-16 DWE "
                           "(pinout identical to AMC3330 per SBASA11B Table 5-1)"}),
    ])
    K.EXTRA_LIBS["salt_pcb"] = CUSTOM_LIB


def build():
    ensure_custom_lib()
    d = K.Design(NAME, "Salt-Battery 16-ch BMS/monitor")
    d.comments = ["CONCEPT – NOT FOR PRODUCTION", "rev A 2026-11-02, ratings from params/product_params.py (BMS)",
                  "16 x 0-%g V isolated block channels, 8 NTC, +/-%g A shunt, H2 + pressure" % (V_BLOCK_FS, I_MAX), ""]
    P = d.sheet("power", "Power input 9-60 V, regulators")
    M = d.sheet("mcu", "MCU STM32G474, ADCs, NTC & gas inputs")
    S = [d.sheet("cells%d" % i, "Isolated block sense ch%d-%d" % (4 * i + 1, 4 * i + 4)) for i in range(4)]
    I = d.sheet("current", "Isolated shunt current sense")
    C = d.sheet("comms", "Isolated CAN + RS-485, outputs")

    def R(sh, val, a, b, fp=FP_R0603, ref=None, **kw):
        return d.add(sh, "Device:R", val, {"1": a, "2": b}, footprint=fp, ref=ref, **kw)

    def Cc(sh, val, a, b, fp=FP_C0603, ref=None, **kw):
        return d.add(sh, "Device:C", val, {"1": a, "2": b}, footprint=fp, ref=ref, **kw)

    # ---------------------------------------------------------------- power
    d.add(P, "Connector_Generic:Conn_01x02", "PWR_IN 9-60V", {"1": "VIN_RAW", "2": "GND"}, footprint=FP_MKDS2, ref="J1",
          MPN="1715721", Manufacturer="Phoenix Contact", Notes="MKDS 1,5/2-5,08")
    d.add(P, "Device:Fuse", "2A", {"1": "VIN_RAW", "2": "VIN_F"}, footprint="Fuse:Fuse_Littelfuse-NANO2-451_453", ref="F1",
          MPN="0451002.MRL", Manufacturer="Littelfuse")
    d.add(P, "Device:D_Schottky", "STPS2H100A", {"A": "VIN_F", "K": "VIN_P"}, footprint="Diode_SMD:D_SMA", ref="D1",
          MPN="STPS2H100A", Manufacturer="STMicroelectronics", Notes="reverse-polarity series diode 100 V 2 A")
    d.add(P, "Device:D_TVS", "SMBJ60CA", {"A1": "VIN_P", "A2": "GND"}, footprint="Diode_SMD:D_SMB", ref="D2",
          MPN="SMBJ60CA", Manufacturer="Littelfuse", Notes="60 V standoff, ~97 V clamp; buck rated 100 V")
    Cc(P, "2.2u 100V", "VIN_P", "GND", FP_C1210, ref="C1"); Cc(P, "2.2u 100V", "VIN_P", "GND", FP_C1210, ref="C2")
    R(P, "432k", "VIN_P", "EN_UVLO", ref="R1"); R(P, "100k", "EN_UVLO", "GND", ref="R2", Notes="UVLO rising ~8.0 V")
    for (u, out, ron, rfb1, ra, lval, pg, sfx) in (("U1", "+5V", "31.6k", "158k", "165k", "33u", "PG_5V", "1"),
                                                   ("U2", "+3V3A", "20.5k", "86.6k", "115k", "22u", "PG_3V3A", "2")):
        d.add(P, "Regulator_Switching:LM5164DDA", "LM5164DDA", {"GND": "GND", "VIN": "VIN_P", "EN/UVLO": "EN_UVLO",
              "RON": "RON" + sfx, "FB": "FB" + sfx, "PGOOD": pg, "BST": "BST" + sfx, "SW": "SW" + sfx, "EP": "GND"}, ref=u,
              MPN="LM5164DDAR", Manufacturer="Texas Instruments", Notes="100 V 1 A COT buck, %s" % out)
        R(P, ron, "RON" + sfx, "GND", Notes="~400 kHz")
        Cc(P, "2.2n", "BST" + sfx, "SW" + sfx)
        d.add(P, "Device:L", lval, {"1": "SW" + sfx, "2": out}, footprint="Inductor_SMD:L_Bourns_SRN6045TA",
              prefix="L", MPN={"33u": "SRN6045TA-330M", "22u": "SRN6045TA-220M"}[lval], Manufacturer="Bourns")
        R(P, rfb1, out, "FB" + sfx); R(P, "49.9k", "FB" + sfx, "GND")
        R(P, ra, "SW" + sfx, "RIP" + sfx, Notes="type-3 ripple injection RA")
        Cc(P, "3.3n", "RIP" + sfx, out, Notes="ripple injection CA"); Cc(P, "56p C0G", "RIP" + sfx, "FB" + sfx, Notes="CB")
        Cc(P, "22u 10V", out, "GND", FP_C1206); Cc(P, "22u 10V", out, "GND", FP_C1206)
        R(P, "10k", pg, "+3V3")
    d.add(P, "Regulator_Linear:AP7361C-33E", "AP7361C-33E", {"VI": "+5V", "GND": "GND", "VO": "+3V3"}, ref="U3",
          MPN="AP7361C-33E-13", Manufacturer="Diodes Inc")
    Cc(P, "10u", "+5V", "GND", FP_C0805); Cc(P, "10u", "+3V3", "GND", FP_C0805)
    d.add(P, "Device:FerriteBead_Small", "BLM18PG221SN1D", {"1": "+3V3", "2": "+3V3_ADC"}, footprint=FP_FB, ref="FB1",
          MPN="BLM18PG221SN1D", Manufacturer="Murata")
    Cc(P, "10u", "+3V3_ADC", "GND", FP_C0805); Cc(P, "100n", "+3V3_ADC", "GND")
    R(P, "200k", "VIN_P", "VIN_SNS"); R(P, "10k", "VIN_SNS", "GND"); Cc(P, "100n", "VIN_SNS", "GND")
    R(P, "1k", "+3V3", "LED_PWR"); d.add(P, "Device:LED", "green", {"A": "LED_PWR", "K": "GND"}, footprint=FP_LED, prefix="D")

    # ---------------------------------------------------------------- MCU
    mcu = {"VBAT": "+3V3", "VDD": "+3V3", "VSS": "GND", "VSSA": "GND", "VDDA": "VDDA", "VREF+": "VDDA",
           "PF0": "OSC_IN", "PF1": "OSC_OUT", "PG10": "NRST",
           "PA0": "I_ADCP", "PA1": "I_ADCN", "PA2": "NTC1_ADC", "PA3": "NTC2_ADC",
           "PC0": "NTC3_ADC", "PC1": "NTC4_ADC", "PC2": "NTC5_ADC", "PC3": "NTC6_ADC", "PB0": "NTC7_ADC", "PB1": "NTC8_ADC",
           "PA4": "H2_ADC", "PC4": "PRESS_ADC", "PC5": "P5V_ADC", "PB2": "VIN_SNS",
           "PA5": "SPI_SCK", "PA6": "SPI_MISO", "PA7": "SPI_MOSI", "PA8": "ADC_CLK",
           "PB12": "ADC_CS1", "PB13": "ADC_CS2", "PC6": "ADC_DRDY1", "PC7": "ADC_DRDY2", "PC8": "ADC_SYNC",
           "PA11": "CAN_RX", "PA12": "CAN_TX", "PC9": "CAN_STB", "PC10": "CAN_FLT",
           "PB10": "RS485_TX", "PB11": "RS485_RX", "PB14": "RS485_DE",
           "PA13": "SWDIO", "PA14": "SWCLK", "PB3": "SWO",
           "PB4": "CONT_EN", "PB5": "ALARM_EN", "PB6": "LED_RUN", "PB7": "LED_FLT", "PB8": "BOOT0",
           "PA15": "ADDR0", "PC11": "ADDR1", "PC12": "ADDR2", "PD2": "ADDR3",
           "PB15": "AMC_DIAG", "PC13": "PG_5V", "PB9": "PG_3V3A",
           "PA9": None, "PA10": None, "PC14": None, "PC15": None}
    d.add(M, "MCU_ST_STM32G4:STM32G474RETx", "STM32G474RET6", mcu, ref="U4",
          MPN="STM32G474RET6", Manufacturer="STMicroelectronics", Notes="Cortex-M4 170 MHz, FDCAN (CAN 2.0B/FD), 5x12-bit ADC")
    for _ in range(4):
        Cc(M, "100n", "+3V3", "GND")
    Cc(M, "4.7u", "+3V3", "GND", FP_C0805)
    d.add(M, "Device:FerriteBead_Small", "BLM18PG221SN1D", {"1": "+3V3", "2": "VDDA"}, footprint=FP_FB, ref="FB2",
          MPN="BLM18PG221SN1D", Manufacturer="Murata")
    Cc(M, "1u", "VDDA", "GND"); Cc(M, "100n", "VDDA", "GND")
    d.add(M, "Device:Crystal_GND24", "8MHz", {"1": "OSC_IN", "3": "OSC_OUT", "2": "GND"},
          footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", ref="Y1", MPN="ABM8-8.000MHZ-B2-T", Manufacturer="Abracon",
          Notes="CL 18 pF; HSE also clocks both ADS131M08 via MCO (PA8)")
    Cc(M, "27p C0G", "OSC_IN", "GND"); Cc(M, "27p C0G", "OSC_OUT", "GND")
    R(M, "10k", "BOOT0", "GND"); Cc(M, "100n", "NRST", "GND")
    d.add(M, "Connector_Generic:Conn_02x05_Odd_Even", "SWD", {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND",
          "6": "SWO", "7": None, "8": None, "9": "GND", "10": "NRST"},
          footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD", ref="J2", Notes="Arm Cortex 10-pin SWD")
    d.add(M, "Switch:SW_DIP_x04", "ADDR", {"1": "ADDR0", "2": "ADDR1", "3": "ADDR2", "4": "ADDR3",
          "5": "GND", "6": "GND", "7": "GND", "8": "GND"},
          footprint="Button_Switch_SMD:SW_DIP_SPSTx04_Slide_6.7x11.72mm_W8.61mm_P2.54mm_LowProfile", ref="SW1",
          Notes="daisy-chain board address (MCU internal pull-ups)")
    R(M, "1k", "LED_RUN", "LED_RUN_A"); d.add(M, "Device:LED", "green RUN", {"A": "LED_RUN_A", "K": "GND"}, footprint=FP_LED, prefix="D")
    R(M, "1k", "LED_FLT", "LED_FLT_A"); d.add(M, "Device:LED", "red FAULT", {"A": "LED_FLT_A", "K": "GND"}, footprint=FP_LED, prefix="D")
    R(M, "10k", "AMC_DIAG", "+3V3")
    # ADS131M08 x2
    for a, (u, cs, drdy) in enumerate((("U5", "ADC_CS1", "ADC_DRDY1"), ("U6", "ADC_CS2", "ADC_DRDY2"))):
        pins = {"AGND": "GND", "DGND": "GND", "AVDD": "+3V3_ADC", "DVDD": "+3V3", "REFIN": "GND", "CAP": "ADC%d_CAP" % (a + 1),
                "~{SYNC}/~{RESET}": "ADC_SYNC", "~{CS}": cs, "~{DRDY}": drdy, "SCLK": "SPI_SCK", "DOUT": "SPI_MISO",
                "DIN": "SPI_MOSI", "XTAL2": None, "XTAL1/CLKIN": "ADC_CLK"}
        for ch in range(8):
            k = a * 8 + ch + 1
            pins["AIN%dP" % ch] = "AIN%02d_P" % k
            pins["AIN%dN" % ch] = "AIN%02d_N" % k
        d.add(M, "Analog_ADC:ADS131M08xPBS", "ADS131M08IPBS", pins, ref=u, MPN="ADS131M08IPBSR", Manufacturer="Texas Instruments",
              Notes="8-ch simultaneous 24-bit delta-sigma; ch%d-%d; internal 1.2 V ref (REFIN tied AGND)" % (a * 8 + 1, a * 8 + 8))
        Cc(M, "1u", "+3V3_ADC", "GND"); Cc(M, "100n", "+3V3_ADC", "GND")
        Cc(M, "1u", "+3V3", "GND"); Cc(M, "100n", "+3V3", "GND")
        Cc(M, "220n", "ADC%d_CAP" % (a + 1), "GND")
    # NTC inputs
    d.add(M, "Connector_Generic:Conn_02x08_Odd_Even", "NTC x8", dict(
        [(str(2 * i + 1), "NTC%d" % (i + 1)) for i in range(N_NTC)] + [(str(2 * i + 2), "GND") for i in range(N_NTC)]),
        footprint="Connector_IDC:IDC-Header_2x08_P2.54mm_Vertical", ref="J3", Notes="10k B3435 NTC to GND, one pair per sensor")
    for i in range(1, N_NTC + 1):
        R(M, "10k 0.1%", "VDDA", "NTC%d" % i, Notes="ratiometric pull-up (VREF+=VDDA)")
        R(M, "1k", "NTC%d" % i, "NTC%d_ADC" % i)
        Cc(M, "100n", "NTC%d_ADC" % i, "GND")
    # gas / pressure (aqueous-specific)
    d.add(M, "Connector_Generic:Conn_01x06", "GAS H2+P", {"1": "LOOP_PWR", "2": "H2_IN", "3": "GND", "4": "P5V_SENS",
          "5": "PRESS_IN", "6": "GND"}, footprint=FP_MC6, ref="J4", MPN="1803316", Manufacturer="Phoenix Contact",
          Notes="1: 4-20 mA loop supply (=VIN via PTC) 2: H2 loop return 4: 5 V excitation 5: 0.5-4.5 V ratiometric")
    d.add(M, "Device:Polyfuse", "MF-MSMF010-2", {"1": "VIN_P", "2": "LOOP_PWR"}, footprint="Fuse:Fuse_1812_4532Metric",
          prefix="F", MPN="MF-MSMF010-2", Manufacturer="Bourns", Notes="0.1 A hold / 60 V")
    R(M, "100R 0.1%", "H2_IN", "GND", FP_R1206, Notes="4-20 mA burden -> 0.4-2.0 V")
    R(M, "10k", "H2_IN", "H2_ADC"); Cc(M, "100n", "H2_ADC", "GND")
    d.add(M, "Device:Polyfuse", "MF-NSMF012-2", {"1": "+5V", "2": "P5V_SENS"}, footprint="Fuse:Fuse_1206_3216Metric",
          prefix="F", MPN="MF-NSMF012-2", Manufacturer="Bourns", Notes="pressure transducer excitation")
    R(M, "10k", "PRESS_IN", "PRESS_ADC"); R(M, "20k", "PRESS_ADC", "GND"); Cc(M, "100n", "PRESS_ADC", "GND")
    R(M, "10k", "P5V_SENS", "P5V_ADC"); R(M, "20k", "P5V_ADC", "GND"); Cc(M, "100n", "P5V_ADC", "GND")

    # ---------------------------------------------------------------- 16 isolated block channels
    for k in range(1, N_CH + 1):
        sh = S[(k - 1) // 4]
        t = "CH%02d_" % k
        d.add(sh, "Connector_Generic:Conn_01x02", "BLK%d" % k, {"1": t + "P", "2": t + "GND"}, footprint=FP_XH2, ref="J%d" % (100 + k),
              MPN="B2B-XH-A", Manufacturer="JST", Notes="monobloc %d (+,-); harness per block" % k)
        R(sh, "1M 0.1%", t + "P", t + "VS", FP_R1206, ref="R%d" % (100 + k), Notes="divider top, 200 V rated 1206")
        R(sh, "30.1k 0.1%", t + "VS", t + "GND", ref="R%d" % (200 + k), Notes="20 V FS -> 0.584 V")
        Cc(sh, "100n", t + "VS", t + "GND", ref="C%d" % (100 + k), Notes="AA filter fc~53 Hz")
        d.add(sh, "Isolator_Analog:AMC3330", "AMC3330DWE", {"DCDC_OUT": t + "DCDC", "DCDC_HGND": t + "GND", "HLDO_IN": t + "DCDC",
              "HLDO_OUT": t + "HLDO", "INP": t + "VS", "INN": t + "GND", "HGND": t + "GND", "GND": "GND", "OUTN": "VO%02d_N" % k,
              "OUTP": "VO%02d_P" % k, "VDD": "+3V3A", "LDO_OUT": "LDO%02d" % k, "DIAG": None, "DCDC_GND": "GND",
              "DCDC_IN": "LDO%02d" % k}, ref="U%d" % (100 + k), MPN="AMC3330DWER", Manufacturer="Texas Instruments",
              Notes="+/-1 V input, gain 2, reinforced isolation, integrated DC/DC")
        Cc(sh, "1u", t + "DCDC", t + "GND", ref="C%d" % (200 + k))
        Cc(sh, "100n", t + "HLDO", t + "GND", ref="C%d" % (300 + k))
        Cc(sh, "100n", "LDO%02d" % k, "GND", ref="C%d" % (400 + k))
        Cc(sh, "1u", "+3V3A", "GND", ref="C%d" % (500 + k))
        R(sh, "1k", "VO%02d_P" % k, "AIN%02d_P" % k, ref="R%d" % (300 + k))
        R(sh, "1k", "VO%02d_N" % k, "AIN%02d_N" % k, ref="R%d" % (400 + k))
        Cc(sh, "10n C0G", "AIN%02d_P" % k, "AIN%02d_N" % k, ref="C%d" % (600 + k))

    # ---------------------------------------------------------------- shunt current
    d.add(I, "Connector_Generic:Conn_01x02", "SHUNT 0.25mOhm", {"1": "SH_P", "2": "SH_GND"}, footprint=FP_XH2, ref="J117",
          MPN="B2B-XH-A", Manufacturer="JST", Notes="Kelvin sense leads of external 200 A / 50 mV shunt")
    R(I, "10R", "SH_P", "SH_FP", ref="R117"); R(I, "10R", "SH_GND", "SH_FN", ref="R217")
    Cc(I, "10n C0G", "SH_FP", "SH_FN", ref="C117")
    d.add(I, "salt_pcb:AMC3302", "AMC3302DWE", {"DCDC_OUT": "SH_DCDC", "DCDC_HGND": "SH_GND", "HLDO_IN": "SH_DCDC",
          "HLDO_OUT": "SH_HLDO", "INP": "SH_FP", "INN": "SH_FN", "HGND": "SH_GND", "GND": "GND", "OUTN": "I_OUTN", "OUTP": "I_OUTP",
          "VDD": "+3V3A", "LDO_OUT": "LDO_SH", "DIAG": "AMC_DIAG", "DCDC_GND": "GND", "DCDC_IN": "LDO_SH"},
          footprint="Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm", ref="U117", MPN="AMC3302DWER", Manufacturer="Texas Instruments",
          Notes="+/-50 mV = +/-200 A on 0.25 mOhm, gain 41")
    Cc(I, "1u", "SH_DCDC", "SH_GND", ref="C217"); Cc(I, "100n", "SH_HLDO", "SH_GND", ref="C317")
    Cc(I, "100n", "LDO_SH", "GND", ref="C417"); Cc(I, "1u", "+3V3A", "GND", ref="C517")
    R(I, "220R", "I_OUTP", "I_ADCP", ref="R317"); R(I, "220R", "I_OUTN", "I_ADCN", ref="R417")
    Cc(I, "2.2n C0G", "I_ADCP", "I_ADCN", ref="C617")

    # ---------------------------------------------------------------- isolated CAN
    d.add(C, "Interface_CAN_LIN:ISOW1044", "ISOW1044DFMR", {"VIO": "+3V3", "IN": "GND", "TXD": "CAN_TX", "STB": "CAN_STB",
          "RXD": "CAN_RX", "GNDIO": "GND", "EN/FLT": "CAN_FLT", "VDD": "+5V", "GND1": "GND", "GND2": "ICAN_GND",
          "VISOOUT": "ICAN_VISO", "VSIN": "ICAN_VISO", "OUT": None, "GISOIN": "ICAN_GND", "CANL": "ICAN_L", "CANH": "ICAN_H",
          "VISOIN": "ICAN_VISO"}, ref="U7", MPN="ISOW1044DFMR", Manufacturer="Texas Instruments",
          Notes="5 kVrms isolated CAN FD (CAN 2.0B compatible) with integrated isolated DC/DC")
    Cc(C, "10u", "+5V", "GND", FP_C0805); Cc(C, "100n", "+5V", "GND"); Cc(C, "100n", "+3V3", "GND")
    R(C, "10k", "CAN_STB", "+3V3", Notes="standby until MCU drives low"); R(C, "10k", "CAN_FLT", "+3V3")
    Cc(C, "10u", "ICAN_VISO", "ICAN_GND", FP_C0805); Cc(C, "100n", "ICAN_VISO", "ICAN_GND")
    d.add(C, "Power_Protection:NUP2105L", "NUP2105L", {"A": "ICAN_GND", "1": "ICAN_H", "2": "ICAN_L"}, prefix="D",
          MPN="NUP2105LT1G", Manufacturer="onsemi")
    d.add(C, "Jumper:SolderJumper_2_Open", "TERM", {"A": "ICAN_H", "B": "ICAN_TERM"},
          footprint="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", prefix="JP")
    R(C, "60.4R", "ICAN_TERM", "ICAN_SPLIT"); R(C, "60.4R", "ICAN_SPLIT", "ICAN_L"); Cc(C, "4.7n", "ICAN_SPLIT", "ICAN_GND")
    for ref in ("J5", "J6"):
        d.add(C, "Connector_Generic:Conn_01x03", "CAN", {"1": "ICAN_H", "2": "ICAN_L", "3": "ICAN_GND"}, footprint=FP_MC3, ref=ref,
              MPN="1803280", Manufacturer="Phoenix Contact", Notes="daisy-chain in/out (paralleled)")
    # ---------------------------------------------------------------- isolated RS-485
    d.add(C, "Interface_UART:ADM2687E", "ADM2687EBRIZ", {"GND1": "GND", "VCC": "+3V3", "RXD": "RS485_RX", "~{RE}": "RS485_DE",
          "DE": "RS485_DE", "TXD": "RS485_TX", "GND2": "I485_GND", "VISOOUT": "I485_VISO", "Y": "I485_A", "Z": "I485_B",
          "B": "I485_B", "A": "I485_A", "VISOIN": "I485_VISO"}, ref="U8", MPN="ADM2687EBRIZ", Manufacturer="Analog Devices",
          Notes="5 kVrms isolated RS-485 (Modbus RTU) with isoPower; half duplex (A=Y, B=Z)")
    Cc(C, "10u", "+3V3", "GND", FP_C0805); Cc(C, "100n", "+3V3", "GND")
    R(C, "10k", "RS485_DE", "GND", Notes="driver off at reset")
    Cc(C, "10u", "I485_VISO", "I485_GND", FP_C0805); Cc(C, "100n", "I485_VISO", "I485_GND")
    d.add(C, "Diode:SM712_SOT23", "SM712", {"A1": "I485_A", "A2": "I485_B", "common": "I485_GND"}, prefix="D",
          MPN="SM712.TCT", Manufacturer="Semtech")
    d.add(C, "Jumper:SolderJumper_2_Open", "TERM", {"A": "I485_A", "B": "I485_TERM"},
          footprint="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", prefix="JP")
    R(C, "120R", "I485_TERM", "I485_B", FP_R1206)
    for ref in ("J7", "J8"):
        d.add(C, "Connector_Generic:Conn_01x03", "RS485", {"1": "I485_A", "2": "I485_B", "3": "I485_GND"}, footprint=FP_MC3, ref=ref,
              MPN="1803280", Manufacturer="Phoenix Contact", Notes="daisy-chain in/out (paralleled)")
    # ---------------------------------------------------------------- contactor + alarm relay
    d.add(C, "74xGxx:74AHCT1G125", "74AHCT1G125", {"1": "GND", "2": "CONT_EN", "3": "GND", "4": "CONT_DRV", "5": "+5V"},
          footprint="Package_TO_SOT_SMD:SOT-23-5", prefix="U", MPN="74AHCT1G125GW", Manufacturer="Nexperia",
          Notes="3.3 V -> 5 V gate drive (TTL input)")
    Cc(C, "100n", "+5V", "GND")
    R(C, "100k", "CONT_EN", "GND", Notes="contactor off at reset")
    R(C, "100R", "CONT_DRV", "CONT_G"); R(C, "100k", "CONT_G", "GND")
    d.add(C, "Transistor_FET:DMN10H220L", "DMN10H220L", {"G": "CONT_G", "S": "GND", "D": "CONT_OUT"}, prefix="Q",
          MPN="DMN10H220L-7", Manufacturer="Diodes Inc", Notes="100 V low-side coil driver; coil <=1 A (economised contactor)")
    d.add(C, "Device:D_Schottky", "STPS2H100A", {"A": "CONT_OUT", "K": "VIN_P"}, footprint="Diode_SMD:D_SMA", prefix="D",
          MPN="STPS2H100A", Manufacturer="STMicroelectronics", Notes="coil freewheel")
    d.add(C, "Connector_Generic:Conn_01x02", "CONTACTOR", {"1": "VIN_P", "2": "CONT_OUT"}, footprint=FP_MKDS2, ref="J9",
          MPN="1715721", Manufacturer="Phoenix Contact", Notes="coil between pins; coil voltage = supply")
    d.add(C, "Transistor_Array:TPL7407LAD", "TPL7407LAD", {"IN1": "ALARM_EN", "IN2": "GND", "IN3": "GND", "IN4": "GND",
          "IN5": "GND", "IN6": "GND", "IN7": "GND", "GND": "GND", "COM": "+5V", "OUT1": "RLY_COIL", "OUT2": None, "OUT3": None,
          "OUT4": None, "OUT5": None, "OUT6": None, "OUT7": None}, prefix="U", MPN="TPL7407LADR", Manufacturer="Texas Instruments",
          Notes="relay driver, integrated freewheel diodes")
    d.add(C, "Relay:G5V-1", "G5V-1-DC5", {"2": "+5V", "9": "RLY_COIL", "5": "ALM_COM", "1": "ALM_NC", "10": "ALM_NO"},
          ref="K1", MPN="G5V-1 DC5", Manufacturer="Omron", Notes="alarm dry contact 1 A 24 VDC")
    d.add(C, "Connector_Generic:Conn_01x03", "ALARM", {"1": "ALM_NO", "2": "ALM_COM", "3": "ALM_NC"}, footprint=FP_MKDS3, ref="J10",
          MPN="1715734", Manufacturer="Phoenix Contact")
    for i in range(1, 5):
        d.add(P, "Mechanical:MountingHole", "M3", {}, footprint="MountingHole:MountingHole_3.2mm_M3", ref="H%d" % i)

    # notes
    d.notes["root"] = [
        "CONCEPT – NOT FOR PRODUCTION.  rev A  2026-11-02.  Salt-Battery-Lab aqueous Na-ion (R1) 12 V monobloc string monitor.",
        "Ratings (params/product_params.py BMS): %d series groups/board, %g-%g V per monobloc channel, %d NTC, +/-%g A on %g mOhm shunt,"
        % (N_CH, BMS["block_v_range"][0], BMS["block_v_range"][1], N_NTC, I_MAX, SHUNT_MOHM),
        "  2 gas inputs (H2 4-20 mA + pressure 0.5-4.5 V ratiometric), CAN 2.0B + RS-485 Modbus RTU, %g kV isolation, supply %g-%g V."
        % (BMS["isolation_kV"], VIN_MIN, VIN_MAX),
        "Cell-voltage approach: one isolated amplifier per 12 V monobloc (AMC3330, integrated isolated DC/DC) behind a 1 M / 30.1 k divider",
        "  -> each channel floats at its own block potential, so the same board works anywhere in a 48 V module or a 480 V UPS string",
        "  (boards daisy-chain over isolated CAN). Li-ion AFEs (BQ79616, LTC6813...) assume 0-5 V per input in a common stack; an",
        "  aqueous R1 monobloc is 6-17.5 V (10 cells x 0.6-1.75 V) so they cannot read it directly, and per-cell use wastes channels.",
        "Each block draws only ~17 uA (divider) -> no balancing load mismatch; AMC power (~29 mA typ each) comes from the board side.",
        "Isolation domains: HV islands CH01..CH16 + SH (6.4 mm min to logic), ICAN / I485 (3.2 mm min), enforced by DRC custom rules.",
    ]
    d.notes["cells0"] = ["Each channel: block terminals -> 1 M / 30.1 k (0.1 %) divider + 100 nF -> AMC3330 (gain 2) -> RC -> ADS131M08.",
                         "Channel k HGND = block k negative terminal.  Full scale %.0f V -> %.3f V AMC input -> %.3f V ADC (FSR 1.2 V)."
                         % (V_BLOCK_FS, V_BLOCK_FS * DIV, V_BLOCK_FS * DIV * 2)]
    d.notes["current"] = ["Shunt %.2f mOhm x %d A = %.0f mV = AMC3302 linear full scale; output to STM32 ADC1 differential (PA0/PA1)."
                          % (SHUNT_MOHM, I_MAX, V_SHUNT_FS * 1000)]
    d.notes["power"] = ["9-60 V in: 2 A fuse, STPS2H100A series diode (reverse polarity), SMBJ60CA TVS, two LM5164 (100 V) bucks:",
                        "+5V (comms DC/DC, sensors, relay) and +3V3A (17 isolated amplifiers, ~0.5 A typ); AP7361C LDO +3V3 logic."]
    add_pwr_flags(d)
    return d


def add_pwr_flags(d):
    """PWR_FLAG on every net that has power-input pins but no power-output pin (ERC 'power pin not driven')."""
    types = {}
    for p in d.parts:
        si = K.syminfo(p.lib_id)
        for pin in si.pins:
            n = p.nets.get(pin["number"])
            if n:
                types.setdefault(n, set()).add(pin["type"])
    i = 0
    for n in sorted(types):
        t = types[n]
        if "power_in" in t and "power_out" not in t:
            i += 1
            d.add("power", "power:PWR_FLAG", "PWR_FLAG", {"1": n}, ref="#FLG%02d" % i)


# ------------------------------------------------------------------------------------------
# board geometry (mm, board origin top-left, y down)
# ------------------------------------------------------------------------------------------
BOARD_W, BOARD_H = 160.0, 100.0
COL_PITCH = 12.0


def col_x(k):
    """centre x of the column of channel k (1..16), 17 = shunt"""
    if k == 17:
        return 106.5
    i = (k - 1) % 8
    return 7.5 + COL_PITCH * i


def is_bottom(k):
    return 9 <= k <= 16


AMC_Y = 16.8          # AMC centre y in the top strip
HV_EDGE = AMC_Y - 3.2  # HV island lower boundary (top strip)


def regions():
    """domain -> list of rects (x0,y0,x1,y1).  LV is everything else minus clearances."""
    r = {}
    for k in range(1, 18):
        xc = col_x(k)
        if is_bottom(k):
            r["CH%02d" % k] = [(xc - 5.5, BOARD_H - HV_EDGE, xc + 5.5, BOARD_H - 0.3)]
        else:
            r["CH%02d" % k if k <= 16 else "SH"] = [(xc - 5.5, 0.3, xc + 5.5, HV_EDGE)]
    r["ICAN"] = [(135.6, 0.3, BOARD_W - 0.3, 32.5)]
    r["I485"] = [(135.6, 35.7, BOARD_W - 0.3, 64.0)]
    return r


DOMAIN_GAP = {("HV", "LV"): 6.4, ("HV", "ISO"): 6.4, ("ISO", "LV"): 3.2, ("ISO", "ISO"): 3.2, ("HV", "HV"): 1.0}


def domain_kind(dom):
    if dom.startswith("CH") or dom == "SH":
        return "HV"
    if dom in ("ICAN", "I485"):
        return "ISO"
    return "LV"


def net_domain(net):
    if net.startswith("CH") and net[2:4].isdigit() and net[4] == "_":
        return net[:4]
    if net.startswith("SH_"):
        return "SH"
    if net.startswith("ICAN_"):
        return "ICAN"
    if net.startswith("I485_"):
        return "I485"
    return "LV"


POWER_NETS = {"VIN_RAW": 0.8, "VIN_F": 0.8, "VIN_P": 0.8, "+5V": 0.5, "+3V3A": 0.5, "+3V3": 0.4, "SW1": 0.6, "SW2": 0.6,
              "CONT_OUT": 0.6, "ICAN_VISO": 0.4, "I485_VISO": 0.4, "+3V3_ADC": 0.3, "VDDA": 0.3}
# plane nets: net -> (layer, list of rects); LV GND plane = LV region polygon (computed)
PLANES = {
    "GND": ("In1.Cu", "LV"),
    "ICAN_GND": ("In1.Cu", "ICAN"),
    "I485_GND": ("In1.Cu", "I485"),
    "+3V3A": ("In2.Cu", [(0.3, 0.3, 113.0, 27.0), (0.3, 73.0, 113.0, BOARD_H - 0.3)]),
    "+3V3": ("In2.Cu", [(0.3, 27.6, 113.0, 72.4), (113.6, 0.3, BOARD_W - 0.3, BOARD_H - 0.3)]),
}


def fixed_placement():
    """ref -> (x, y, rot_deg, side) for everything that must sit at a planned spot."""
    pl = {}
    for k in range(1, 18):
        xc = col_x(k)
        items = [("J%d", xc - 4.25, 3.4, 0), ("R%d", xc + 3.0, 3.4, 90),
                 ("R2%02d", xc - 3.6, 9.2, 90), ("C1%02d", xc - 1.2, 9.2, 90), ("C2%02d", xc + 1.2, 9.2, 90), ("C3%02d", xc + 3.6, 9.2, 90),
                 ("U%d", xc, AMC_Y, 270),
                 ("C4%02d", xc + 4.8, 24.4, 90), ("C5%02d", xc + 2.4, 24.4, 90),
                 ("R3%02d", xc + 0.0, 24.4, 90), ("C6%02d", xc - 2.4, 24.4, 90), ("R4%02d", xc - 4.8, 24.4, 90)]
        for fmt, x, y, rot in items:
            if fmt in ("J%d", "R%d", "U%d"):
                ref = fmt % (100 + k)
            else:
                ref = fmt[0] + str(int(fmt[1]) * 100 + k)
            if is_bottom(k):
                x, y, rot = 2 * xc - x, BOARD_H - y, (rot + 180) % 360
            pl[ref] = (x, y, rot, "F")
    pl.update({
        # MCU / ADC
        "U5": (52.0, 33.5, 0, "F"), "U4": (52.0, 50.0, 0, "F"), "U6": (52.0, 66.5, 0, "F"),
        "J3": (4.0, 33.0, 0, "F"), "Y1": (40.0, 44.0, 0, "F"),
        "J2": (75.0, 40.0, 0, "F"), "SW1": (88.0, 50.0, 0, "F"),
        # comms
        "U7": (134.0, 16.0, 0, "F"), "J5": (151.5, 12.0, 90, "F"), "J6": (151.5, 27.5, 90, "F"),
        "U8": (134.0, 50.0, 0, "F"), "J7": (151.5, 46.5, 90, "F"), "J8": (151.5, 62.0, 90, "F"),
        # power
        "J1": (153.5, 78.0, 270, "F"),
        "U1": (120.0, 36.0, 0, "F"), "L1": (120.0, 45.0, 0, "F"),
        "U2": (120.0, 56.0, 0, "F"), "L2": (120.0, 65.0, 0, "F"),
        "U3": (104.0, 62.0, 0, "F"),
        # outputs / sensors
        "J4": (106.5, 91.0, 0, "F"), "J9": (136.0, 94.0, 180, "F"), "J10": (153.0, 94.0, 180, "F"),
        "K1": (124.0, 76.0, 0, "F"),
        # holes
        "H1": (118.5, 4.0, 0, "F"), "H2": (100.5, 47.0, 0, "F"), "H3": (4.0, 66.0, 0, "F"), "H4": (155.5, 69.5, 0, "F"),
    })
    return pl


if __name__ == "__main__":
    d = build()
    print(len(d.parts), "parts", len(d.nets()), "nets")


# ------------------------------------------------------------------------------------------
# net classes (used by gen_project.py for .kicad_pro + .kicad_dru)
# ------------------------------------------------------------------------------------------
LV_CLASSES = ["Default", "Power"]


def netclass_of_domain(dm):
    if dm.startswith("CH"):
        return "HV_" + dm
    return {"SH": "HV_SH", "ICAN": "ISO_CAN", "I485": "ISO_485"}.get(dm, "Default")


def netclasses():
    base = dict(track=0.2, clearance=0.2, via_d=0.6, via_drill=0.3)
    nc = {"Default": base, "Power": dict(base, track=0.5)}
    for dm in regions():
        nc[netclass_of_domain(dm)] = dict(base, track=0.25)
    return nc


def netclass_patterns(d):
    pats = []
    for dm in sorted(regions()):
        if dm.startswith("CH"):
            pats.append((netclass_of_domain(dm), dm + "_*"))
    pats += [("HV_SH", "SH_*"), ("ISO_CAN", "ICAN_*"), ("ISO_485", "I485_*")]
    for n in sorted(POWER_NETS):
        if net_domain(n) == "LV":
            pats.append(("Power", n))
    pats.append(("Power", "GND"))
    return pats


TITLE = "Salt-Battery 16-ch BMS / monitor (concept)"
RESERVED = [(63.0, 57.5, 99.0, 63.5)]     # keep free for the F.SilkS legend


def silk_texts():
    return [
        ("SALT-BATTERY-LAB  BMS/MONITOR 16S  rev A  2026-11-02", 63.5, 58.5, 1.0, "F.SilkS", False),
        ("CONCEPT – NOT FOR PRODUCTION", 63.5, 61.0, 1.5, "F.SilkS", False),
        ("CONCEPT – NOT FOR PRODUCTION  rev A 2026-11-02", 120.0, 52.0, 2.0, "B.SilkS", True),
        ("HV ISLANDS: 6.4 mm MIN TO LOGIC", 96.0, 57.0, 1.5, "B.SilkS", True),
    ]
