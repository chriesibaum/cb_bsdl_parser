
import os
import re
from antlr4.InputStream import InputStream
from antlr4.CommonTokenStream import CommonTokenStream
from collections import OrderedDict
from cb_bsdl_parser.CBBsdlLexer import CBBsdlLexer
from cb_bsdl_parser.CBBsdlParser import CBBsdlParser

import logging
log = logging.getLogger(__name__)


class SkipError(Exception):
    """Exception raised to indicate that a check should be skipped."""
    pass


class CBBsdl():
    def __init__(self, bsdl_file=None, run_checks=True,
                 verbose=False):

        self.bsdl_file = None
        self.run_checks = run_checks
        self.verbose = verbose

        # check if bsdl_file is a file or a file_blob
        if os.path.isfile(bsdl_file):
            self.bsdl_file = bsdl_file

            with open(self.bsdl_file, 'r') as file:
                self.bsdl_blob = file.read()
        else:
            self.bsdl_blob = bsdl_file

        lexer = CBBsdlLexer(InputStream(self.bsdl_blob))
        stream = CommonTokenStream(lexer)
        parser = CBBsdlParser(stream)

        self.tree = parser.bsdl()

        self.build_ports_content()
        self.build_pin_map_content()
        self.build_bsr_content()
        self.compile_bsr_ctrl_cells()

        if self.run_checks:
            self.check()

    def check(self):
        """Performs all checks on the BSDL content."""
        self.check_entity_name()
        self.check_bsr_length()
        self.check_ports_and_pin_map_length()
        self.check_port_to_pin_mapping()
        self.check_pin_to_port_mapping()
        self.check_bsr_to_ports_mapping()
        self.check_pin_count()
        self.check_missing_pins()
        self.check_extra_pins()

    def check_entity_name(self):
        """Checks if the entity name is present in the BSDL content."""
        e0 = self.tree.entity().entity_name()[0].getText()
        e1 = self.tree.entity().entity_name()[1].getText()
        if e0 != e1:
            raise ValueError(
                f'Entity name is malformed in the BSDL content. {e0} != {e1}')

        return True

    def check_bsr_length(self):
        """Checks if the BSR length is present in the BSDL content."""

        attr_bsr_len0 = self.get_bsr_len()
        attr_bsr_len1 = len(self.tree.entity().body().attr_bsr()[0].bsr_def())

        if self.verbose:
            log.debug(
                f'attr_bsr_len0: {attr_bsr_len0}, '
                f'attr_bsr_len1: {attr_bsr_len1}')

        if attr_bsr_len0 != attr_bsr_len1:
            raise ValueError(
                f'BSR length not consistent: BOUNDARY_LENGTH: '
                f'{attr_bsr_len0} != len(BOUNDARY_REGISTER){attr_bsr_len1}')

        return True

    def check_ports_and_pin_map_length(self):
        """Checks if the port and pin map lengths are consistent."""
        ports = self.get_ports()
        pin_map = self.get_pin_map()

        if len(ports) != len(pin_map):
            raise ValueError(
                'Port and pin map lengths are inconsistent: '
                f'{len(ports)} != {len(pin_map)}')

        return True

    def check_port_to_pin_mapping(self):
        """Checks if all ports are mapped to pins in the pin map."""
        ports = self.get_ports()
        pin_map = self.get_pin_map()

        unmapped_ports = []

        for port_name in ports.keys():
            if port_name not in pin_map.values():
                unmapped_ports.append(port_name)

        if len(unmapped_ports) > 0:
            raise ValueError(
                f'The following ports are not mapped to any '
                f'pin: {unmapped_ports}')

        return True

    def check_pin_to_port_mapping(self):
        """Checks if all pins in the pin map correspond to defined ports."""
        ports = self.get_ports()
        pin_map = self.get_pin_map()

        unmapped_pins = []

        for pin_num, port_name in pin_map.items():
            if port_name not in list(ports.keys()):
                unmapped_pins.append(pin_num)

        if len(unmapped_pins) > 0:
            raise ValueError(
                f'The following pins are not mapped to any '
                f'port: {unmapped_pins}')

        return True

    # TODO: add check_ports_to_bsr_mapping()!

    def check_bsr_to_ports_mapping(self):
        """Checks if all BSR cells correspond to defined ports."""
        ports = self.get_ports()
        bsr = self.get_bsr()

        unmapped_bsr_cells = []

        for bsr_cell in bsr.keys():
            cell_desc = bsr[bsr_cell]['cell_desc']

            # Skip checks for control cells
            if cell_desc in ['*']:
                continue

            if cell_desc not in ports.keys():
                unmapped_bsr_cells.append(bsr_cell)

        if len(unmapped_bsr_cells) > 0:
            raise ValueError(
                f'The following BSR cells are not mapped '
                f'to any port: {unmapped_bsr_cells}')

        return True

    def get_expected_pin_numbers(self):
        """Returns the expected pin numbers based on the physical pin map."""
        physical_pin_map = self.get_physical_pin_map()

        def i_to_str(pin_range):
            pin_numbers = set()
            for i in pin_range:
                pin_numbers.add(str(i))
            return pin_numbers

        if 'LQFP32' in physical_pin_map or \
           'UQFN32' in physical_pin_map or \
           'UFQFPN32' in physical_pin_map:
            return i_to_str(range(1, 32 + 1))
        if 'LQFP48' in physical_pin_map or \
           'UQFN48' in physical_pin_map or \
           'UFQFPN48' in physical_pin_map:
            return i_to_str(range(1, 48 + 1))
        if 'LQFP64' in physical_pin_map:
            return i_to_str(range(1, 64 + 1))
        if 'LQFP80' in physical_pin_map:
            return i_to_str(range(1, 80 + 1))
        if 'LQFP100' in physical_pin_map:
            return i_to_str(range(1, 100 + 1))
        if 'LQFP128' in physical_pin_map:
            return i_to_str(range(1, 128 + 1))
        if 'LQFP144' in physical_pin_map:
            return i_to_str(range(1, 144 + 1))
        if 'WLCSP' in physical_pin_map or \
           'UFBGA' in physical_pin_map or \
           'LBGA' in physical_pin_map or \
           'TFBGA' in physical_pin_map or \
           'FBGA' in physical_pin_map or \
           'NONE' in physical_pin_map:
            raise SkipError(f'Physical pin map {physical_pin_map} skipped')

        else:   # pragma: no cover
            raise NotImplementedError(
                f'Physical pin map {physical_pin_map} not supported yet.')

    def check_pin_count(self):
        """Checks if the expected pin count is consistent."""
        pin_map = self.get_pin_map()
        pin_numbers_expected = self.get_expected_pin_numbers()

        # check pin count
        if len(pin_map) != len(pin_numbers_expected):
            raise ValueError(
                'Pin count in pin map is inconsistent: '
                f'expected {len(pin_numbers_expected)} pins, '
                f'found {len(pin_map)} pins')

    def check_missing_pins(self):
        """Checks for missing pins in the pin map."""
        pin_numbers_expected = self.get_expected_pin_numbers()
        pin_map = self.get_pin_map()

        missing_pins = []
        for pin in pin_numbers_expected:
            if pin not in pin_map.keys():
                missing_pins.append(pin)

        if missing_pins:
            raise ValueError(
                f'Missing pin numbers in the pin map: {sorted(missing_pins)}')

    def check_extra_pins(self):
        """Checks for extra pins in the pin map."""
        pin_numbers_expected = self.get_expected_pin_numbers()
        pin_map = self.get_pin_map()

        extra_pins = []
        for pin in pin_map.keys():
            if pin not in pin_numbers_expected:
                extra_pins.append(pin)

        if extra_pins:
            raise ValueError(
                f'Extra pin numbers in the pin map: {sorted(extra_pins)}')

    def check_double_assigned_pins(self):
        """Checks for double assigned pins in the pin map."""

        pin_numbers = self.pin_numbers
        pin_numbers_expected = self.get_expected_pin_numbers()

        double_assigned_pins = []
        for pin in pin_numbers:
            if pin in pin_numbers_expected:
                pin_numbers_expected.remove(pin)
            else:
                double_assigned_pins.append(pin)

        if double_assigned_pins:
            raise ValueError(
                f'Double assigned pin numbers in the pin map: '
                f'{sorted(double_assigned_pins)}')

        return True

    def get_entity_name(self):
        """Extracts the entity name from the BSDL content."""
        return self.tree.entity().entity_name()[0].getText()

    def get_physical_pin_map(self):
        """Extracts the physical pin map from the BSDL content."""
        return self.tree.entity().body().generic_phys_pin_map()[0].phys_pin_map_name().getText()  # noqa: E501

    def get_instr_len(self):
        """Extracts the instruction length from the BSDL content."""
        return int(self.tree.entity().body().attr_instr_len()[0].instr_len().getText())  # noqa: E501

    def get_id_code(self):
        """Extracts the IDCODE_REGISTER value from the BSDL content."""
        body = self.tree.entity().body()

        # Forward compatibility: if grammar later contains explicit
        # attr_idcode_reg, use it directly.
        if hasattr(body, 'attr_idcode_reg'):
            attr_idcode = body.attr_idcode_reg()
            if len(attr_idcode) > 0:
                idcode_parts = attr_idcode[0].idcode_reg().idcode_reg_part()
                return ''.join([part.getText() for part in idcode_parts])

        # Current grammar parses IDCODE_REGISTER statements as undef_part.
        for undef in body.undef_part():
            undef_text = undef.getText()
            if 'IDCODE_REGISTER' not in undef_text.upper():
                continue

            idcode_parts = re.findall(r'"([^"]+)"', undef_text)
            if len(idcode_parts) == 0:
                raise ValueError(
                    'IDCODE_REGISTER found but no quoted ID code parts parsed')

            return ''.join(idcode_parts)

        raise ValueError('IDCODE_REGISTER not found in BSDL content')

    def get_bsr_len(self):
        """Extracts the BSR length from the BSDL content."""
        return int(self.tree.entity().body().attr_bsr_len()[0].bsr_len().getText())  # noqa: E501

    def ports_add(self, port_name_str, port_function, port_type):
        self.ports[port_name_str] = {
            'function': port_function,
            'type': port_type
        }

    def build_ports_content(self):
        """Builds the port declaration content from the BSDL tree."""

        self.ports = {}

        for port_def in self.tree.entity().body().port_dec()[0].port_def():
            for port_name in port_def.port_name():
                if port_def.port_type().getText() == 'bit':
                    port_name_str = port_name.getText()
                    port_function = port_def.port_function().getText()
                    port_type = port_def.port_type().getText()

                    self.ports_add(port_name_str, port_function, port_type)

                elif 'bit_vector' in port_def.port_type().getText():
                    bit_0 = int(port_def.port_type().bit_vector().bit_range().INTEGER()[0].getText())  # noqa: E501
                    bit_1 = int(port_def.port_type().bit_vector().bit_range().INTEGER()[1].getText())  # noqa: E501
                    for bit in range(bit_0, bit_1 + 1):
                        port_name_str = f'{port_name.getText()}.{bit}'
                        port_function = port_def.port_function().getText()
                        port_type = 'bit'

                        self.ports_add(port_name_str, port_function, port_type)

                else:
                    raise NotImplementedError(
                        f"Port Type '{port_def.port_type().getText()}' "
                        'not supported yet')

    def get_ports(self):
        """Returns the port declaration content."""
        return self.ports

    def _parse_pin_map_from_pin_def(self, pin_map_node):
        """Parse pin map from pin_def children (STM32 style)."""
        pin_map_len = len(pin_map_node.pin_def())

        for i in range(pin_map_len):
            port_name = pin_map_node.pin_def()[i].port_name().getText()

            if pin_map_node.pin_def()[i].pin_num() is not None:
                pin_num = pin_map_node.pin_def()[i].pin_num().getText()
                self.pin_map[pin_num] = port_name
                self.pin_numbers.append(pin_num)
            else:
                pin_num_arr_len = len(pin_map_node.pin_def()[i].pin_num_arr().pin_num())
                for j in range(pin_num_arr_len):
                    pin_num = pin_map_node.pin_def()[i].pin_num_arr().pin_num()[j].getText()
                    self.pin_map[pin_num] = f'{port_name}.{j}'
                    self.pin_numbers.append(pin_num)

        log.info(f"Parsed {len(self.pin_map)} pin mappings from pin_def")

    def _parse_pin_map_from_constant(self, pin_map_node):
        """Parse PIN_MAP_STRING constant (Altera/Intel format).

        In Altera BSDL files, the pin map is defined as:
        constant <name> : PIN_MAP_STRING := "<port>:<pin>, ..." ;
        """
        source = pin_map_node
        log.debug(f"Parsing PIN_MAP_STRING constant with {source.getChildCount()} children")

        # Parse the token stream
        skip_tokens = {'"', '&', 'constant', 'CONSTANT', ';', ':=', 'PIN_MAP_STRING'}

        child_count = source.getChildCount()
        i = 0
        inside_data = False

        # Skip until we find := which marks the start of actual pin mappings
        while i < child_count:
            child = source.getChild(i)
            if hasattr(child, 'getText') and child.getText() == ':=':
                inside_data = True
                i += 1
                break
            i += 1

        if not inside_data:
            log.warning("Could not find := in PIN_MAP_STRING constant")
            return

        while i < child_count:
            child = source.getChild(i)
            if not hasattr(child, 'getText'):
                i += 1
                continue

            token_text = child.getText()

            # Skip structural tokens
            if token_text in skip_tokens or token_text.isspace():
                i += 1
                continue

            # Look for port_name : pin_num , pattern
            if i + 3 < child_count:
                next1 = source.getChild(i + 1).getText() if hasattr(source.getChild(i + 1), 'getText') else ''
                next2 = source.getChild(i + 2).getText() if hasattr(source.getChild(i + 2), 'getText') else ''
                next3 = source.getChild(i + 3).getText() if hasattr(source.getChild(i + 3), 'getText') else ''

                # Check for simple mapping: PORT : PIN ,
                if next1 == ':' and next3 == ',' and next2 not in skip_tokens:
                    port_name = token_text
                    pin_num = next2

                    # Validate that this looks like a valid port and pin
                    if (len(port_name) > 0 and port_name[0].isalpha() and
                            len(pin_num) > 0 and port_name not in skip_tokens):
                        self.pin_map[pin_num] = port_name
                        self.pin_numbers.append(pin_num)

                    i += 4  # Skip past this mapping
                    continue

                # Check for array mapping: PORT : ( ... )
                if next1 == ':' and next2 == '(':
                    port_name = token_text
                    if port_name in skip_tokens or not port_name[0].isalpha():
                        i += 1
                        continue

                    # Find matching closing parenthesis and extract pins
                    j = i + 3
                    pins = []
                    while j < child_count:
                        token = source.getChild(j).getText() if hasattr(source.getChild(j), 'getText') else ''
                        if token == ')':
                            break
                        elif token and token not in [',', ' ', '\t', '\n', '&', '"'] and len(token) > 0:
                            pins.append(token)
                        j += 1

                    # Add each pin with indexed port name
                    for idx, pin in enumerate(pins, start=1):
                        self.pin_map[pin] = f'{port_name}.{idx}'
                        self.pin_numbers.append(pin)

                    i = j + 1  # Skip past the closing parenthesis
                    continue

            i += 1

        log.info(f"Parsed {len(self.pin_map)} pin mappings from PIN_MAP_STRING constant")

    def build_pin_map_content(self):
        """Builds the pin map content from the BSDL tree."""

        self.pin_map = {}
        self.pin_numbers = []

        # Check if pin_map exists
        pin_maps = self.tree.entity().body().pin_map()

        if pin_maps and len(pin_maps) > 0:
            pin_map_node = pin_maps[0]

            # Check if it has pin_def children (STM32 style)
            if pin_map_node.pin_def() and len(pin_map_node.pin_def()) > 0:
                # STM32 style: inline pin definitions
                self._parse_pin_map_from_pin_def(pin_map_node)
                return

        # Altera/Intel style: Look in undef_part for PIN_MAP_STRING constant
        # (until parser is regenerated to recognize the combined grammar rule)
        undef_parts = self.tree.entity().body().undef_part()
        if undef_parts:
            for undef in undef_parts:
                text = undef.getText()
                if 'PIN_MAP_STRING' in text:
                    self._parse_pin_map_from_constant(undef)
                    return

        log.debug("No pin_map found")

    def get_pin_map(self):
        """Returns the pin map content."""
        return self.pin_map

    def build_bsr_content(self):
        """Builds the BSR content from the BSDL tree."""

        self.bsr = {}

        bsr_len = len(self.tree.entity().body().attr_bsr()[0].bsr_def())

        for i in range(bsr_len):
            data_cell = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].data_cell().getText())  # noqa: E501

            if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0() is not None:  # noqa: E501
                cell_type = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_type().getText()  # noqa: E501
                if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_desc() is not None:  # noqa: E501
                    cell_desc = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_desc().getText()  # noqa: E501
                else:
                    cell_desc = '*'

                cell_func = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_func().getText()  # noqa: E501
                cell_val = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_val().getText()  # noqa: E501
                ctrl_cell = 0
                disval = 0

            elif self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1() is not None:  # noqa: E501
                cell_type = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_type().getText()  # noqa: E501
                if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_desc() is not None:  # noqa: E501
                    cell_desc = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_desc().getText()  # noqa: E501
                else:
                    cell_desc = '*'  # pragma: no cover

                cell_func = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_func().getText()  # noqa: E501
                cell_val = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_val().getText()  # noqa: E501
                ctrl_cell = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().ctrl_cell().getText())  # noqa: E501
                disval = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().disval().getText())  # noqa: E501

            else:  # pragma: no cover
                data_cell = 0
                cell_type = 'undef'
                cell_desc = 'undef'
                cell_func = 'undef'
                cell_val = 'undef'
                ctrl_cell = 0
                disval = 0

            bsr_cell = {
                'data_cell': data_cell,
                'cell_type': cell_type,
                'cell_desc': cell_desc,
                'cell_func': cell_func,
                'cell_val': cell_val,
                'ctrl_cell': ctrl_cell,
                'disval': disval
            }

            if cell_desc == '*':
                cell_desc = f'cell_{data_cell}'

            if cell_func.upper() in ['INPUT', 'OBSERVE_ONLY']:
                key_a = 'in'
            elif cell_func.upper() in ['OUTPUT', 'OUTPUT2', 'OUTPUT3']:
                key_a = 'out'
            elif cell_func.upper() in ['CONTROL']:
                key_a = 'ctrl'
            elif cell_func.upper() in ['INTERNAL']:
                key_a = ''
            else:
                raise NotImplementedError(
                    f"Cell_func '{cell_func}' not recognized for "
                    f"cell_desc '{cell_desc}'")

            if key_a != '':
                key = f'{cell_desc}_{key_a}'
            else:
                key = cell_desc

            self.bsr[key] = bsr_cell

    def compile_bsr_ctrl_cells(self):
        """Compiles control cells from the BSR content."""

        for i in range(len(self.bsr)):
            cell_desc = list(self.bsr.keys())[i]
            cell = self.bsr[cell_desc]

            ctrl_cell_used = 0

            if cell_desc.endswith('_out'):
                if self.verbose:
                    log.debug(
                        f'Control cell found: {cell_desc}, '
                        f'data_cell: {cell['data_cell']} '
                        f'ctrl_cell: {cell['ctrl_cell']}   ', end='')

                for key, ccell in self.bsr.items():
                    if ccell['ctrl_cell'] != '' and \
                            int(ccell['ctrl_cell']) == int(cell['ctrl_cell']):
                        ctrl_cell_used += 1
                        if self.verbose:
                            log.debug(
                                f'  {key} has ctrl_cell {ccell['ctrl_cell']}')

                if ctrl_cell_used == 1:
                    new_key_ctrl_cell = f'{cell['cell_desc']}_ctrl'
                    old_key_ctrl_cell = f'cell_{cell['ctrl_cell']}_ctrl'

                    if self.verbose:
                        log.debug(
                            f'modify key: {old_key_ctrl_cell} -> '
                            f'{new_key_ctrl_cell}  ')

                    if int(cell['data_cell']) != int(cell['ctrl_cell']):
                        self.bsr[new_key_ctrl_cell] = self.bsr.pop(
                            old_key_ctrl_cell)
                    else:
                        log.warning(
                            f'Warning: {cell['cell_desc']} does not have '
                            'a separate ctrl_cell')

        # Sort the BSR content by data_cell
        self.bsr = OrderedDict(
            sorted(self.bsr.items(), key=lambda t: t[1]['data_cell']))

    def get_bsr(self):
        """Returns the BSR content."""
        return self.bsr

    def print_bsr_table(self):
        """Prints the BSDL BSR content information."""
        print(f'BSDL file: {self.bsdl_file}')
        print(f'Entity name: {self.get_entity_name()}')
        print(f'Physical pin map: {self.get_physical_pin_map()}')
        print(f'BSR length: {self.get_bsr_len()}')
        print('BSR content:')
        for bsr_cell in self.bsr.keys():

            if self.bsr[bsr_cell]['cell_func'] != 'internal':
                print(f'  {bsr_cell:10s} '
                      f'{self.bsr[bsr_cell]['data_cell']:3d}   '
                      f'type: {self.bsr[bsr_cell]['cell_type']:4s}   '
                      f'desc: {self.bsr[bsr_cell]['cell_desc']:6s}   '
                      f'func: {self.bsr[bsr_cell]['cell_func']:9s}   '
                      f'val: {self.bsr[bsr_cell]['cell_val']:1s}   '
                      f'ctrl_cell: {self.bsr[bsr_cell]['ctrl_cell']:3d}')

    def get_bsr_data_cell(self, bsr_cell):
        """Returns the cell number for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['data_cell']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_cell_type(self, bsr_cell):
        """Returns the cell type for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_type']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_cell_desc(self, bsr_cell):
        """Returns the cell description for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_desc']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_cell_func(self, bsr_cell):
        """Returns the cell function for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_func']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_cell_val(self, bsr_cell):
        """Returns the cell value for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_val']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_ctrl_cell(self, bsr_cell):
        """Returns the control cell for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['ctrl_cell']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")

    def get_bsr_disval(self, bsr_cell):
        """Returns the disable value for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['disval']
        else:
            raise ValueError(f"BSR cell '{bsr_cell}' not found in BSR content.")
