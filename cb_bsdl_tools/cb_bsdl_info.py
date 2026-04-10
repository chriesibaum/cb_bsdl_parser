#!/usr/bin/env python3

import sys
import argparse
from cb_bsdl_parser.cb_bsdl import CBBsdl


def print_bsr_table(bsdl, bsdl_file):
    print(f'BSDL file: {bsdl_file}')
    bsdl.print_bsr_table()


def print_cell_info(bsdl, cell):
    print(f'Information for cell: {cell}')
    try:
        print(f'  data_cell:  {bsdl.get_bsr_data_cell(cell)}')
        print(f'  cell_type: {bsdl.get_bsr_cell_type(cell)}')
        print(f'  cell_desc: {bsdl.get_bsr_cell_desc(cell)}')
        print(f'  cell_func: {bsdl.get_bsr_cell_func(cell)}')
        print(f'  cell_val:  {bsdl.get_bsr_cell_val(cell)}')
        print(f'  ctrl_cell: {bsdl.get_bsr_ctrl_cell(cell)}')
    except Exception as e:
        print(f'Error retrieving information for cell {cell}: {e}')


def print_pin_map(bsdl):
    print('pin map:')
    for pin_num, pin_desc in bsdl.get_pin_map().items():
        print(f'  {pin_num}: {pin_desc}')


def print_device_info(bsdl):
    print('Device information:')
    print(f'  Entity name: {bsdl.get_entity_name()}')
    print(f'  Physical pin map: {bsdl.get_physical_pin_map()}')
    print(f'  Instruction length: {bsdl.get_instr_len()}')
    print(f'  BSR length: {bsdl.get_bsr_len()}')
    id_code = bsdl.get_id_code()
    if id_code is not None:
        print(f'  IDCODE_REGISTER: {id_code}')
        print(f'    Version: {bsdl.get_id_code_version()}')
        print(f'    Manufacturer Identity: {bsdl.get_id_code_manufacturer_identity():#05x}')
        print(f'    Part Number: {bsdl.get_id_code_part_number():#06x}')
    else:
        print('  IDCODE_REGISTER: Not found')


def main():
    parser = argparse.ArgumentParser(
        description='Process a BSDL file.',
        usage='%(prog)s <bsdl_file> [--cell CELL] [--print-bsr-table]')
    parser.add_argument('bsdl_file', type=str, help='Path to the BSDL file')
    parser.add_argument('-c', '--cell', type=str,
                        default=None, help='Cell name to query')
    parser.add_argument('-b', '--print-bsr-table',
                        action='store_true', help='Print the BSR table')
    parser.add_argument('-p', '--print-pin-map',
                        action='store_true', help='Print the pin map')
    parser.add_argument('-i', '--info',
                        action='store_true', help='Print device information')

    if len(sys.argv) == 1:
        parser.print_usage()
        sys.exit(1)

    args = parser.parse_args()

    bsdl = CBBsdl(args.bsdl_file, run_checks=False)

    if args.print_bsr_table:
        print_bsr_table(bsdl, args.bsdl_file)

    if args.cell is not None:
        print_cell_info(bsdl, args.cell)

    if args.print_pin_map:
        print_pin_map(bsdl)

    if args.info:
        print_device_info(bsdl)


if __name__ == '__main__':
    main()
