import sys
from cb_bsdl_tools.cb_bsdl_info import main


class Test_cb_bsdl_info_functions:
    def test_main_exists(self):
        assert callable(main)

    def test_main_usage_no_args(self, capsys):
        test_args = ['cb_bsdl_info.py']
        sys.argv = test_args

        try:
            main()
        except SystemExit as e:
            assert e.code == 1

        captured = capsys.readouterr()
        assert 'usage:' in captured.out

    def test_info_non_existent_file(self, capsys):
        test_args = ['cb_bsdl_info.py', 'non_existent_file.bsdl', '-i']
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with non-existent file: {e}')
            assert 'BSDL input is neither a valid file path nor a file blob (bsdl input : non_existent_file.bsdl...)' in str(e)    # noqa: E501

        # test if the exception was raised and captured correctly
        captured = capsys.readouterr()
        assert 'BSDL input is neither a valid file path nor a file blob' in captured.out

    def test_help(self, capsys):
        test_args = ['cb_bsdl_info.py', '-h']
        sys.argv = test_args

        try:
            main()
        except SystemExit as e:
            assert e.code == 0

        captured = capsys.readouterr()
        assert 'usage:' in captured.out

    def test_cell_name_query(self, capsys):
        test_args = ['cb_bsdl_info.py', './test/bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl', '-c', 'PB9_out']    # noqa: E501
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with valid file and cell query: {e}')
            assert False, f'Exception occurred: {e}'

        captured = capsys.readouterr()
        assert 'Information for cell: PB9_out' in captured.out
        assert '  cell_num:       7' in captured.out
        assert '  cell_type:      BC_1' in captured.out
        assert '  cell_port_name: PB9' in captured.out
        assert '  cell_func:      OUTPUT3' in captured.out
        assert '  cell_safe:      X' in captured.out
        assert '  cell_ccell:     8' in captured.out

    def test_print_bsr_table(self, capsys):
        test_args = ['cb_bsdl_info.py', './test/bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl', '-b']    # noqa: E501
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with valid file and print BSR table: {e}')
            assert False, f'Exception occurred: {e}'

        captured = capsys.readouterr()
        assert 'Entity name: STM32G471_473_474_483_484_LQFP64' in captured.out
        assert 'Physical pin map: LQFP64_PACKAGE' in captured.out
        assert 'PC13_ctrl  287   type: BC_1   port name: *        func: CONTROL     safe: 1   ccell:   0' in captured.out    # noqa: E501

    def test_print_bsr_safe_val(self, capsys):
        test_args = ['cb_bsdl_info.py', './test/bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl', '-s']    # noqa: E501
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with valid file and print BSR safe value: {e}')
            assert False, f'Exception occurred: {e}'

        captured = capsys.readouterr()
        assert 'Calculating BSR safe value...' in captured.out
        assert 'BSR safe value: 0x000920000024924124924924900000000000924900000024000124924124000004000124900' in captured.out     # noqa: E501

    def test_pin_map(self, capsys):
        test_args = ['cb_bsdl_info.py', './test/bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl', '-p']    # noqa: E501
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with valid file and print pin map: {e}')
            assert False, f'Exception occurred: {e}'

        captured = capsys.readouterr()
        assert 'pin map:' in captured.out
        assert '1: VBAT' in captured.out

    def test_info(self, capsys):
        test_args = ['cb_bsdl_info.py', './test/bsdl_files/STM32G471_473_474_483_484_LQFP64.bsdl', '-i']    # noqa: E501
        sys.argv = test_args

        try:
            main()
        except Exception as e:
            print(f'Error running main with valid file: {e}')
            assert False, f'Exception occurred: {e}'

        captured = capsys.readouterr()
        assert 'Device information:' in captured.out
        assert 'Entity name: STM32G471_473_474_483_484_LQFP64' in captured.out
