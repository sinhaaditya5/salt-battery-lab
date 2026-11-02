"""SCM-1 salt-cell test monitor (concept, rev A, 2026-11-02) - part/net definition for pcb/tools/gen_project.py + pcbbuild.py.

Designed around the S-cell R0 chemistry (Na | beta''-alumina | NaAlCl4 | (Fe,Ni)Cl2, 180-260 C, 1.65-2.95 V trip window,
params/scell_params.py OPERATE): up to 4 cells in series (<= 12.4 V), 4 ungrounded-junction type-K thermocouples, 0-2 A,
heater SSR drive with a HARDWARE AND-gate interlock (MCU enable AND no thermocouple fault), fail-safe dry contact to the
cycler's external interlock, E-stop sense, isolated USB logging. NOT a product BMS; a lab safety monitor + logger.
Nets starting with IUSB_ are the isolated USB domain (3.2 mm min to logic, ISO7721D barrier).
"""
import os, sys
LAB = "/Volumes/Aditya ssd/Salt-Battery-Lab"
sys.path.insert(0, LAB); sys.path.insert(0, os.path.join(LAB, "pcb", "tools"))
import kigen as K  # noqa: E402
from params.scell_params import OPERATE  # noqa: E402

NAME = "scell_monitor"
TITLE = "SCM-1 salt-cell test monitor"
N_TAP = OPERATE["cell_series_max"]            # 4 cells
R_TOP, R_BOT = 100e3, 10e3                     # tap divider 1/11
V_STRING_MAX = N_TAP * 3.1                     # 12.4 V
assert V_STRING_MAX * R_BOT / (R_TOP + R_BOT) < 1.2, "ADS131M08 FSR exceeded"
SHUNT_MOHM, I_MAX = 10.0, 2.0                  # INA228 +/-163.84 mV range -> 20 mV at 2 A

FP_R0603, FP_R1206, FP_R2512 = "Resistor_SMD:R_0603_1608Metric", "Resistor_SMD:R_1206_3216Metric", "Resistor_SMD:R_2512_6332Metric"
FP_C0603, FP_C0805, FP_C1210 = "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric", "Capacitor_SMD:C_1210_3225Metric"
FP_LED, FP_FB = "LED_SMD:LED_0603_1608Metric", "Inductor_SMD:L_0603_1608Metric"
FP_MKDS2 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"
FP_MKDS3 = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3-5.08_1x03_P5.08mm_Horizontal"
FP_MC6 = "Connector_Phoenix_MC:PhoenixContact_MC_1,5_6-G-3.5_1x06_P3.50mm_Horizontal"
FP_TC = "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MPT-0,5-2-2.54_1x02_P2.54mm_Horizontal"
FP_XH2 = "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"


CUSTOM_LIB_NAME = "scm_pcb"
CUSTOM_LIB = os.path.join(LAB, "pcb", "lib", "scm_pcb.kicad_sym")


def ensure_custom_lib():
    """MAX31856 with datasheet pin types: SDO is high-Z when CS is high (tri_state), FAULT is open-drain (open_collector)."""
    K.make_custom_lib(CUSTOM_LIB, [("MAX31856_DS", "Sensor_Temperature:MAX31856",
                                    {"Description": "MAX31856 TC-to-digital; pin types per datasheet (SDO tri-state, FAULT open-drain)"},
                                    {"11": "tri_state", "13": "open_collector"})])
    K.EXTRA_LIBS[CUSTOM_LIB_NAME] = CUSTOM_LIB


def build():
    ensure_custom_lib()
    d = K.Design(NAME, TITLE)
    d.comments = ["CONCEPT – NOT FOR PRODUCTION", "rev A 2026-11-02, limits from params/scell_params.py OPERATE",
                  "4 cell taps (<=12.4 V), 4x type-K TC, 0-2 A shunt, HW heater interlock, isolated USB", ""]
    P = d.sheet("power", "Power 12-30 V, regulators"); M = d.sheet("mcu", "MCU STM32G474 + ADC")
    S = d.sheet("sense", "Cell taps, thermocouples, current"); O = d.sheet("io", "Heater interlock, relay, USB")

    def R(sh, val, a, b, fp=FP_R0603, ref=None, **kw):
        return d.add(sh, "Device:R", val, {"1": a, "2": b}, footprint=fp, ref=ref, **kw)

    def Cc(sh, val, a, b, fp=FP_C0603, ref=None, **kw):
        return d.add(sh, "Device:C", val, {"1": a, "2": b}, footprint=fp, ref=ref, **kw)

    # ---------------------------------------------------------------- power (same proven front end as bms_monitor rev A)
    d.add(P, "Connector_Generic:Conn_01x02", "PWR_IN 12-30V", {"1": "VIN_RAW", "2": "GND"}, footprint=FP_MKDS2, ref="J1",
          MPN="1715721", Manufacturer="Phoenix Contact")
    d.add(P, "Device:Fuse", "1A", {"1": "VIN_RAW", "2": "VIN_F"}, footprint="Fuse:Fuse_Littelfuse-NANO2-451_453", ref="F1",
          MPN="0451001.MRL", Manufacturer="Littelfuse")
    d.add(P, "Device:D_Schottky", "STPS2H100A", {"A": "VIN_F", "K": "VIN_P"}, footprint="Diode_SMD:D_SMA", ref="D1",
          MPN="STPS2H100A", Manufacturer="STMicroelectronics", Notes="reverse polarity")
    d.add(P, "Device:D_TVS", "SMBJ33CA", {"A1": "VIN_P", "A2": "GND"}, footprint="Diode_SMD:D_SMB", ref="D2",
          MPN="SMBJ33CA", Manufacturer="Littelfuse")
    Cc(P, "2.2u 100V", "VIN_P", "GND", FP_C1210, ref="C1"); Cc(P, "2.2u 100V", "VIN_P", "GND", FP_C1210, ref="C2")
    R(P, "432k", "VIN_P", "EN_UVLO", ref="R1"); R(P, "100k", "EN_UVLO", "GND", ref="R2", Notes="UVLO ~8 V")
    d.add(P, "Regulator_Switching:LM5164DDA", "LM5164DDA", {"GND": "GND", "VIN": "VIN_P", "EN/UVLO": "EN_UVLO", "RON": "RON1",
          "FB": "FB1", "PGOOD": "PG_5V", "BST": "BST1", "SW": "SW1", "EP": "GND"}, ref="U1", MPN="LM5164DDAR", Manufacturer="Texas Instruments")
    R(P, "31.6k", "RON1", "GND"); Cc(P, "2.2n", "BST1", "SW1")
    d.add(P, "Device:L", "33u", {"1": "SW1", "2": "+5V"}, footprint="Inductor_SMD:L_Bourns_SRN6045TA", ref="L1", MPN="SRN6045TA-330M", Manufacturer="Bourns")
    R(P, "158k", "+5V", "FB1"); R(P, "49.9k", "FB1", "GND"); R(P, "165k", "SW1", "RIP1"); Cc(P, "3.3n", "RIP1", "+5V"); Cc(P, "56p C0G", "RIP1", "FB1")
    Cc(P, "22u 10V", "+5V", "GND", FP_C0805); Cc(P, "22u 10V", "+5V", "GND", FP_C0805); R(P, "10k", "PG_5V", "+3V3")
    d.add(P, "Regulator_Linear:AP7361C-33E", "AP7361C-33E", {"VI": "+5V", "GND": "GND", "VO": "+3V3"}, ref="U2", MPN="AP7361C-33E-13", Manufacturer="Diodes Inc")
    Cc(P, "10u", "+5V", "GND", FP_C0805); Cc(P, "10u", "+3V3", "GND", FP_C0805)
    d.add(P, "Device:FerriteBead_Small", "BLM18PG221SN1D", {"1": "+3V3", "2": "+3V3_ADC"}, footprint=FP_FB, ref="FB1", MPN="BLM18PG221SN1D", Manufacturer="Murata")
    Cc(P, "10u", "+3V3_ADC", "GND", FP_C0805); Cc(P, "100n", "+3V3_ADC", "GND")
    R(P, "200k", "VIN_P", "VIN_SNS"); R(P, "10k", "VIN_SNS", "GND"); Cc(P, "100n", "VIN_SNS", "GND")
    for i in range(1, 5):
        d.add(P, "Mechanical:MountingHole", "M3", {}, footprint="MountingHole:MountingHole_3.2mm_M3", ref="H%d" % i)

    # ---------------------------------------------------------------- MCU
    used = {"VBAT": "+3V3", "VDD": "+3V3", "VSS": "GND", "VSSA": "GND", "VDDA": "VDDA", "VREF+": "VDDA", "PF0": "OSC_IN", "PF1": "OSC_OUT",
            "PG10": "NRST", "PB2": "VIN_SNS", "PA5": "SPI_SCK", "PA6": "SPI_MISO", "PA7": "SPI_MOSI", "PA8": "ADC_CLK",
            "PB12": "ADC_CS", "PC6": "ADC_DRDY", "PC10": "ADC_SYNC", "PB13": "TC_CS1", "PB14": "TC_CS2", "PB15": "TC_CS3", "PC7": "TC_CS4",
            "PB1": "TC_FAULT_N", "PC11": "INA_ALERT", "PC8": "I2C_SCL", "PC9": "I2C_SDA", "PA9": "UART_TX", "PA10": "UART_RX",
            "PB4": "HEAT_EN", "PB5": "ILK_EN", "PB6": "LED_RUN", "PB7": "LED_FLT", "PB0": "BUZ_EN", "PC12": "ESTOP_SNS", "PA0": "HEAT_FB",
            "PA13": "SWDIO", "PA14": "SWCLK", "PB3": "SWO", "PB8": "BOOT0", "PC13": "PG_5V"}
    allpins = ["PA%d" % i for i in range(16)] + ["PB%d" % i for i in range(16)] + ["PC%d" % i for i in range(16)] + ["PD2"]
    mcu = dict(used); mcu.update({p: None for p in allpins if p not in used})
    d.add(M, "MCU_ST_STM32G4:STM32G474RETx", "STM32G474RET6", mcu, ref="U3", MPN="STM32G474RET6", Manufacturer="STMicroelectronics",
          Notes="same MCU as bms_monitor so firmware drivers are shared")
    for _ in range(4):
        Cc(M, "100n", "+3V3", "GND")
    Cc(M, "4.7u", "+3V3", "GND", FP_C0805)
    d.add(M, "Device:FerriteBead_Small", "BLM18PG221SN1D", {"1": "+3V3", "2": "VDDA"}, footprint=FP_FB, ref="FB2", MPN="BLM18PG221SN1D", Manufacturer="Murata")
    Cc(M, "1u", "VDDA", "GND"); Cc(M, "100n", "VDDA", "GND")
    d.add(M, "Device:Crystal_GND24", "8MHz", {"1": "OSC_IN", "3": "OSC_OUT", "2": "GND"}, footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
          ref="Y1", MPN="ABM8-8.000MHZ-B2-T", Manufacturer="Abracon", Notes="HSE; MCO (PA8) clocks the ADS131M08")
    Cc(M, "27p C0G", "OSC_IN", "GND"); Cc(M, "27p C0G", "OSC_OUT", "GND"); R(M, "10k", "BOOT0", "GND"); Cc(M, "100n", "NRST", "GND")
    d.add(M, "Connector_Generic:Conn_02x05_Odd_Even", "SWD", {"1": "+3V3", "2": "SWDIO", "3": "GND", "4": "SWCLK", "5": "GND", "6": "SWO",
          "7": None, "8": None, "9": "GND", "10": "NRST"}, footprint="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD", ref="J8")
    R(M, "1k", "LED_RUN", "LED_RUN_A"); d.add(M, "Device:LED", "green RUN", {"A": "LED_RUN_A", "K": "GND"}, footprint=FP_LED, prefix="D")
    R(M, "1k", "LED_FLT", "LED_FLT_A"); d.add(M, "Device:LED", "red FAULT", {"A": "LED_FLT_A", "K": "GND"}, footprint=FP_LED, prefix="D")
    pins = {"AGND": "GND", "DGND": "GND", "AVDD": "+3V3_ADC", "DVDD": "+3V3", "REFIN": "GND", "CAP": "ADC_CAP", "~{SYNC}/~{RESET}": "ADC_SYNC",
            "~{CS}": "ADC_CS", "~{DRDY}": "ADC_DRDY", "SCLK": "SPI_SCK", "DOUT": "SPI_MISO", "DIN": "SPI_MOSI", "XTAL2": None, "XTAL1/CLKIN": "ADC_CLK"}
    for ch in range(8):
        if ch < N_TAP:                       # cell k = tap k+1 minus tap k
            pins["AIN%dP" % ch] = "A%d" % (ch + 1); pins["AIN%dN" % ch] = "A%d" % ch if ch > 0 else "GND"
        elif ch == N_TAP:                    # whole string
            pins["AIN%dP" % ch] = "A%d" % N_TAP; pins["AIN%dN" % ch] = "GND"
        else:                                # unused: grounded
            pins["AIN%dP" % ch] = "GND"; pins["AIN%dN" % ch] = "GND"
    d.add(M, "Analog_ADC:ADS131M08xPBS", "ADS131M08IPBS", pins, ref="U4", MPN="ADS131M08IPBSR", Manufacturer="Texas Instruments",
          Notes="ch0-3 cells (adjacent-tap differential), ch4 string, ch5-7 grounded; internal 1.2 V ref")
    Cc(M, "1u", "+3V3_ADC", "GND"); Cc(M, "100n", "+3V3_ADC", "GND"); Cc(M, "1u", "+3V3", "GND"); Cc(M, "100n", "+3V3", "GND"); Cc(M, "220n", "ADC_CAP", "GND")

    # ---------------------------------------------------------------- cell taps
    tapnets = {"1": "GND"}; tapnets.update({str(k + 1): "TAP%d" % k for k in range(1, N_TAP + 1)}); tapnets[str(N_TAP + 2)] = "GND"
    d.add(S, "Connector_Generic:Conn_01x06", "CELL TAPS", tapnets, footprint=FP_MC6, ref="J2", MPN="1803316", Manufacturer="Phoenix Contact",
          Notes="1: string - (= board GND, Kelvin), 2-5: taps 1-4 (cell tops), 6: shield")
    for k in range(1, N_TAP + 1):
        R(S, "100k 0.1%", "TAP%d" % k, "TS%d" % k, FP_R1206, Notes="tap divider top (also limits fault current to 0.12 mA)")
        R(S, "10k 0.1%", "TS%d" % k, "GND", Notes="1/11")
        R(S, "1k", "TS%d" % k, "A%d" % k); Cc(S, "100n C0G", "A%d" % k, "GND", Notes="fc ~1.6 kHz; ADC OSR does the rest")
    # thermocouples (ungrounded-junction, mineral-insulated type K)
    for k in range(1, 5):
        d.add(S, "Connector_Generic:Conn_01x02", "TC%d type-K" % k, {"1": "TC%d_P" % k, "2": "TC%d_N" % k}, footprint=FP_TC, ref="J%d" % (8 + k),
              MPN="1725656", Manufacturer="Phoenix Contact", Notes="place within 10 mm of U so the cold junction tracks the IC sensor")
        Cc(S, "10n C0G", "TC%d_P" % k, "TC%d_N" % k)
        d.add(S, "scm_pcb:MAX31856_DS", "MAX31856MUD", {"AGND": "GND", "BIAS": "TC%d_N" % k, "T-": "TC%d_N" % k, "T+": "TC%d_P" % k,
              "AVDD": "+3V3_ADC", "DNC": None, "~{DRDY}": None, "DVDD": "+3V3", "~{CS}": "TC_CS%d" % k, "SCK": "SPI_SCK", "SDO": "SPI_MISO",
              "SDI": "SPI_MOSI", "~{FAULT}": "TC_FAULT_N", "DGND": "GND"}, prefix="U", MPN="MAX31856MUD+", Manufacturer="Analog Devices",
              Notes="open-drain FAULT wired-OR; HI threshold programmed to T_trip; open-TC detect on")
        Cc(S, "100n", "+3V3_ADC", "GND"); Cc(S, "100n", "+3V3", "GND")
    R(S, "10k", "TC_FAULT_N", "+3V3", Notes="wired-OR pull-up; low = any TC fault/over-temp")
    # current
    d.add(S, "Connector_Generic:Conn_01x02", "CYCLER -", {"1": "CYC_NEG", "2": "GND"}, footprint=FP_MKDS2, ref="J3", MPN="1715721",
          Manufacturer="Phoenix Contact", Notes="1: to cycler negative lead, 2: to string negative (also J2.1)")
    R(S, "10m 1% 3W", "GND", "CYC_NEG", FP_R2512, ref="R50", MPN="WSL2512R0100FEA", Manufacturer="Vishay", Notes="2 A -> 20 mV")
    R(S, "10R", "GND", "SH_P"); R(S, "10R", "CYC_NEG", "SH_N"); Cc(S, "10n C0G", "SH_P", "SH_N")
    R(S, "1k", "TAP%d" % N_TAP, "VBUS_S")
    d.add(S, "Sensor_Energy:INA228", "INA228AIDGSR", {"A1": "GND", "A0": "GND", "~{Alert}": "INA_ALERT", "SDA": "I2C_SDA", "SCL": "I2C_SCL",
          "VS": "+3V3", "GND": "GND", "Vbus": "VBUS_S", "Vin-": "SH_N", "Vin+": "SH_P"}, prefix="U", MPN="INA228AIDGSR", Manufacturer="Texas Instruments",
          Notes="20-bit, coulomb counter; ALERT on over-current (hardware limit register)")
    Cc(S, "100n", "+3V3", "GND"); R(S, "10k", "INA_ALERT", "+3V3"); R(S, "4.7k", "I2C_SDA", "+3V3"); R(S, "4.7k", "I2C_SCL", "+3V3")

    # ---------------------------------------------------------------- heater interlock (hardware AND)
    R(O, "100k", "HEAT_EN", "GND", Notes="heater off at reset / MCU hang")
    d.add(O, "74xGxx:74LVC1G08", "74LVC1G08", {"1": "HEAT_EN", "2": "TC_FAULT_N", "3": "GND", "4": "HEAT_GATE", "5": "+3V3"},
          footprint="Package_TO_SOT_SMD:SOT-23-5", prefix="U", MPN="74LVC1G08GW", Manufacturer="Nexperia",
          Notes="HEAT_GATE = HEAT_EN AND (no TC fault) - an over-temperature trip removes heater drive without firmware")
    Cc(O, "100n", "+3V3", "GND")
    R(O, "100R", "HEAT_GATE", "HEAT_G"); R(O, "100k", "HEAT_G", "GND")
    d.add(O, "Transistor_FET:DMN10H220L", "DMN10H220L", {"G": "HEAT_G", "S": "GND", "D": "SSR_NEG"}, prefix="Q", MPN="DMN10H220L-7", Manufacturer="Diodes Inc")
    d.add(O, "Device:Polyfuse", "MF-MSMF010-2", {"1": "VIN_P", "2": "SSR_POS"}, footprint="Fuse:Fuse_1812_4532Metric", prefix="F", MPN="MF-MSMF010-2", Manufacturer="Bourns")
    d.add(O, "Connector_Generic:Conn_01x02", "SSR CTRL", {"1": "SSR_POS", "2": "SSR_NEG"}, footprint=FP_MKDS2, ref="J4", MPN="1715721",
          Manufacturer="Phoenix Contact", Notes="to DC control input of a zero-cross SSR; E-stop NC contact wired in series OFF-BOARD")
    R(O, "10k", "SSR_POS", "LED_HEAT_A"); d.add(O, "Device:LED", "amber HEAT", {"A": "LED_HEAT_A", "K": "SSR_NEG"}, footprint=FP_LED, prefix="D")
    R(O, "100k", "SSR_NEG", "HEAT_FB"); R(O, "10k", "HEAT_FB", "GND", Notes="read-back: low = heater drive on")
    # relay + buzzer
    d.add(O, "Transistor_Array:TPL7407LAD", "TPL7407LAD", {"IN1": "ILK_EN", "IN2": "BUZ_EN", "IN3": "GND", "IN4": "GND", "IN5": "GND", "IN6": "GND",
          "IN7": "GND", "GND": "GND", "COM": "+5V", "OUT1": "RLY_COIL", "OUT2": "BUZ_N", "OUT3": None, "OUT4": None, "OUT5": None, "OUT6": None,
          "OUT7": None}, prefix="U", MPN="TPL7407LADR", Manufacturer="Texas Instruments")
    R(O, "100k", "ILK_EN", "GND", Notes="relay de-energised at reset -> cycler interlock OPEN (fail-safe)")
    d.add(O, "Relay:G5V-1", "G5V-1-DC5", {"2": "+5V", "9": "RLY_COIL", "5": "ILK_COM", "1": "ILK_NC", "10": "ILK_NO"}, ref="K1", MPN="G5V-1 DC5", Manufacturer="Omron")
    d.add(O, "Connector_Generic:Conn_01x03", "CYCLER INTERLOCK", {"1": "ILK_NO", "2": "ILK_COM", "3": "ILK_NC"}, footprint=FP_MKDS3, ref="J5",
          MPN="1715734", Manufacturer="Phoenix Contact", Notes="use NO-COM: closed only while board healthy and limits OK")
    d.add(O, "Device:Buzzer", "CEM-1203(42)", {"+": "+5V", "-": "BUZ_N"}, footprint="Buzzer_Beeper:Buzzer_12x9.5RM7.6", prefix="BZ", MPN="CEM-1203(42)", Manufacturer="CUI Devices")
    d.add(O, "Connector_Generic:Conn_01x02", "E-STOP sense", {"1": "ESTOP_SNS", "2": "GND"}, footprint=FP_XH2, ref="J6", MPN="B2B-XH-A", Manufacturer="JST",
          Notes="auxiliary NC contact of the E-stop; open = stop")
    R(O, "10k", "ESTOP_SNS", "+3V3")
    # isolated USB
    d.add(O, "Connector:USB_B_Micro", "USB", {"VBUS": "IUSB_VBUS_RAW", "D-": "IUSB_DM", "D+": "IUSB_DP", "ID": None, "GND": "IUSB_GND", "Shield": "IUSB_GND"},
          footprint="Connector_USB:USB_Micro-B_Amphenol_10118194_Horizontal", ref="J7", MPN="10118194-0001LF", Manufacturer="Amphenol")
    d.add(O, "Device:Polyfuse", "MF-NSMF050-2", {"1": "IUSB_VBUS_RAW", "2": "IUSB_VBUS"}, footprint="Fuse:Fuse_1206_3216Metric", prefix="F",
          MPN="MF-NSMF050-2", Manufacturer="Bourns")
    d.add(O, "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", {"1": "IUSB_DM", "6": "IUSB_DM", "3": "IUSB_DP", "4": "IUSB_DP", "2": "IUSB_GND", "5": "IUSB_VBUS"},
          footprint="Package_TO_SOT_SMD:SOT-23-6", prefix="U", MPN="USBLC6-2SC6", Manufacturer="STMicroelectronics")
    R(O, "27R", "IUSB_DM", "IUSB_FDM"); R(O, "27R", "IUSB_DP", "IUSB_FDP")
    d.add(O, "Interface_USB:FT230XS", "FT230XS", {"TXD": "IUSB_TXD", "~{RTS}": None, "VCCIO": "IUSB_3V3", "RXD": "IUSB_RXD", "GND": "IUSB_GND",
          "~{CTS}": None, "CBUS2": None, "USBDP": "IUSB_FDP", "USBDM": "IUSB_FDM", "3V3OUT": "IUSB_3V3", "~{RESET}": None, "VCC": "IUSB_VBUS",
          "CBUS1": None, "CBUS0": None, "CBUS3": None}, prefix="U", MPN="FT230XS-R", Manufacturer="FTDI")
    Cc(O, "4.7u", "IUSB_VBUS", "IUSB_GND", FP_C0805); Cc(O, "100n", "IUSB_3V3", "IUSB_GND"); Cc(O, "47p C0G", "IUSB_FDM", "IUSB_GND"); Cc(O, "47p C0G", "IUSB_FDP", "IUSB_GND")
    d.add(O, "Isolator:ISO7721D", "ISO7721DR", {"VCC1": "IUSB_3V3", "OUTA": "IUSB_RXD", "INB": "IUSB_TXD", "GND1": "IUSB_GND", "GND2": "GND",
          "OUTB": "UART_RX", "INA": "UART_TX", "VCC2": "+3V3"}, ref="U20", MPN="ISO7721DR", Manufacturer="Texas Instruments",
          Notes="3 kVrms basic isolation; PC ground never touches the cell string")
    Cc(O, "100n", "IUSB_3V3", "IUSB_GND"); Cc(O, "100n", "+3V3", "GND")

    d.notes["root"] = ["CONCEPT – NOT FOR PRODUCTION. SCM-1 rev A 2026-11-02: S-cell R0 test monitor (Na-MCl2, 180-260 C).",
                       "Cell sense: 4 taps -> 100k/10k (0.1%) -> ADS131M08 adjacent-tap differential; FS 12.4 V string -> 1.127 V. Calibrate per channel (TP-E03).",
                       "Thermocouples MUST be ungrounded-junction (insulated): the cell case is at cell potential and the MAX31856 inputs are referenced to GND.",
                       "Hardware interlock: heater SSR drive = HEAT_EN AND TC_FAULT_N (74LVC1G08). TC HI-fault thresholds are programmed to OPERATE.T_trip_C;",
                       "  an independent bimetal cut-out and the E-stop NC contact are wired in series with the SSR/mains OFF-BOARD (build manual step E-04).",
                       "Cycler interlock K1 NO-COM closes only while firmware state is healthy; de-energised (open) at reset, brown-out or MCU hang (IWDG)."]
    add_pwr_flags(d)
    return d


def add_pwr_flags(d):
    types = {}
    for p in d.parts:
        si = K.syminfo(p.lib_id)
        for pin in si.pins:
            n = p.nets.get(pin["number"])
            if n:
                types.setdefault(n, set()).add(pin["type"])
    i = 0
    for n in sorted(types):
        if "power_in" in types[n] and "power_out" not in types[n]:
            i += 1
            d.add("power", "power:PWR_FLAG", "PWR_FLAG", {"1": n}, ref="#FLG%02d" % i)


# ---------------------------------------------------------------- board geometry (mm, origin top-left, y down)
BOARD_W, BOARD_H = 110.0, 75.0
DOMAIN_GAP = {("HV", "LV"): 6.4, ("HV", "ISO"): 6.4, ("ISO", "LV"): 3.2, ("ISO", "ISO"): 3.2, ("HV", "HV"): 1.0}
LV_CLASSES = ["Default", "Power"]

def regions():
    return {"IUSB": [(0.3, 0.3, 26.0, 40.0)]}

def domain_kind(dom):
    return "ISO" if dom == "IUSB" else "LV"

def net_domain(net):
    return "IUSB" if net.startswith("IUSB_") else "LV"

POWER_NETS = {"VIN_RAW": 0.8, "VIN_F": 0.8, "VIN_P": 0.8, "+5V": 0.5, "+3V3": 0.4, "SW1": 0.6, "CYC_NEG": 1.5, "SSR_POS": 0.4, "SSR_NEG": 0.4,
              "+3V3_ADC": 0.3, "VDDA": 0.3, "IUSB_VBUS": 0.4}
PLANES = {"GND": ("In1.Cu", "LV"), "IUSB_GND": ("In1.Cu", "IUSB"), "+3V3": ("In2.Cu", [(29.6, 0.3, BOARD_W - 0.3, BOARD_H - 0.3)])}

def fixed_placement():
    return {
        "J7": (3.5, 10.0, 270, "F"), "U20": (28.1, 24.0, 0, "F"),
        "J2": (4.5, 47.0, 270, "F"), "J3": (14.0, 71.0, 0, "F"),
        "J9": (40.0, 3.5, 0, "F"), "J10": (52.0, 3.5, 0, "F"), "J11": (64.0, 3.5, 0, "F"), "J12": (76.0, 3.5, 0, "F"),
        "J4": (105.0, 14.0, 270, "F"), "J5": (105.0, 33.0, 270, "F"), "J6": (105.5, 48.0, 270, "F"), "J1": (105.0, 64.0, 270, "F"),
        "U3": (60.0, 40.0, 0, "F"), "U4": (36.0, 46.0, 0, "F"), "J8": (78.0, 30.0, 0, "F"), "K1": (88.0, 55.0, 0, "F"),
        "H1": (33.0, 3.5, 0, "F"), "H2": (94.0, 3.5, 0, "F"), "H3": (30.0, 71.5, 0, "F"), "H4": (94.0, 71.5, 0, "F"),
    }

def silk_texts():
    return [("SCM-1 SALT-CELL TEST MONITOR  rev A  2026-11-02", 60.0, 66.0, 1.0, "F.SilkS", False),
            ("CONCEPT – NOT FOR PRODUCTION", 60.0, 68.5, 1.2, "F.SilkS", False),
            ("TC: UNGROUNDED JUNCTION ONLY", 58.0, 8.5, 1.0, "F.SilkS", False),
            ("ISOLATED USB 3 kV", 12.0, 38.5, 0.9, "F.SilkS", False)]

def netclass_of_domain(dm):
    return "ISO_USB" if dm == "IUSB" else "Default"

def netclasses():
    base = dict(track=0.2, clearance=0.2, via_d=0.6, via_drill=0.3)
    return {"Default": base, "Power": dict(base, track=0.5), "ISO_USB": dict(base, track=0.25)}

def netclass_patterns(d):
    pats = [("ISO_USB", "IUSB_*")]
    pats += [("Power", n) for n in POWER_NETS if not n.startswith("IUSB_")]
    return pats

if __name__ == "__main__":
    d = build()
    print(len(d.parts), "parts", len(d.nets()), "nets")
