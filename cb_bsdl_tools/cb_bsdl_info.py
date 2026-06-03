#!/usr/bin/env python3

import sys
import argparse
from cb_bsdl_parser.cb_bsdl import CBBsdl


def print_bsr_table(bsdl, bsdl_file):
    print(f'BSDL file: {bsdl_file}')
    bsdl.print_bsr_table()


def print_bsr_cell_safe(bsdl):
    print('Calculating BSR safe value...')
    bsr = bsdl.get_bsr_safe_vals()
    # print in hex with leading zeros, width based on BSR length
    print(f'BSR safe value: {bsr:#0{bsdl.get_bsr_len() // 4 + 2}x}')

    # print the safe value in binary, with leading zeros, grouped in 16-bit blocks
    bsr_len = bsdl.get_bsr_len()
    bsr_bin = f'{bsr:0{bsr_len}b}'
    print('BSR safe value (binary):')
    pad = (16 - bsr_len % 16) % 16
    padded = ' ' * pad + bsr_bin
    for i in range(0, len(padded), 16):
        block = padded[i:i + 16]
        bit_num = bsr_len - 1 - max(i - pad, 0)
        grouped = ' '.join(block[j:j + 4] for j in range(0, 16, 4))
        actual_bits = block.replace(' ', '')
        hex_width = (len(actual_bits) + 3) // 4
        hex_str = f'{int(actual_bits, 2):0{hex_width}x}' if actual_bits else ''
        print(f'  [{bit_num:>4}]: {grouped}  0x{hex_str}')


def print_cell_info(bsdl, cell):
    print(f'Information for cell: {cell}')
    try:
        print(f'  cell_num:       {bsdl.get_bsr_cell_num(cell)}')
        print(f'  cell_type:      {bsdl.get_bsr_cell_type(cell)}')
        print(f'  cell_port_name: {bsdl.get_bsr_cell_port_name(cell)}')
        print(f'  cell_func:      {bsdl.get_bsr_cell_func(cell)}')
        print(f'  cell_safe:      {bsdl.get_bsr_cell_safe(cell)}')
        print(f'  cell_ccell:     {bsdl.get_bsr_cell_ccell(cell)}')
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
    parser.add_argument('-s', '--print-bsr-safe-val',
                        action='store_true', help='Print the BSR safe value')
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

    if args.print_bsr_safe_val:
        print_bsr_cell_safe(bsdl)

    if args.cell is not None:
        print_cell_info(bsdl, args.cell)

    if args.print_pin_map:
        print_pin_map(bsdl)

    if args.info:
        print_device_info(bsdl)


if __name__ == '__main__':  # pragma: no cover
    main()
