#!/usr/bin/env python3
"""Physics arithmetic for the 1,500 km / 5-minute vehicle target.

This is not a battery simulation or a prediction. It converts a user-specified
vehicle consumption/range into required battery energy and average charging
power, then compares the cell mass implied by a user-specified cell Wh/kg.
"""
import argparse


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--consumption-low', type=float, default=15.0, help='kWh/100 km lower bound')
    p.add_argument('--consumption-high', type=float, default=20.0, help='kWh/100 km upper bound')
    p.add_argument('--range-km', type=float, default=1500.0)
    p.add_argument('--charge-minutes', type=float, default=5.0)
    p.add_argument('--cell-whkg', type=float, default=875.0,
                   help='Hypothetical cell-level energy density for mass arithmetic only')
    a = p.parse_args()
    if min(a.consumption_low, a.consumption_high, a.range_km, a.charge_minutes, a.cell_whkg) <= 0:
        p.error('All inputs must be positive.')
    if a.consumption_low > a.consumption_high:
        p.error('consumption-low must be <= consumption-high.')

    e_low = a.range_km / 100 * a.consumption_low
    e_high = a.range_km / 100 * a.consumption_high
    hours = a.charge_minutes / 60
    p_low, p_high = e_low / hours, e_high / hours
    mass_low, mass_high = e_low * 1000 / a.cell_whkg, e_high * 1000 / a.cell_whkg

    print('VEHICLE TARGET REQUIREMENT CALCULATOR — NOT A BATTERY PERFORMANCE MODEL')
    print(f'Range: {a.range_km:,.0f} km')
    print(f'Consumption assumption: {a.consumption_low:g}–{a.consumption_high:g} kWh/100 km')
    print(f'Usable energy required: {e_low:,.1f}–{e_high:,.1f} kWh')
    print(f'Average terminal charging power for {a.charge_minutes:g} minutes: {p_low:,.2f}–{p_high:,.2f} kW')
    print(f'Hypothetical cell-level energy density: {a.cell_whkg:,.1f} Wh/kg')
    print(f'Ideal active cell mass only: {mass_low:,.1f}–{mass_high:,.1f} kg')
    print('Pack mass and station input power would be higher after inactive pack mass and losses.')
    print('No chemistry, fast-charge capability, range or safety performance is predicted.')


if __name__ == '__main__':
    main()
