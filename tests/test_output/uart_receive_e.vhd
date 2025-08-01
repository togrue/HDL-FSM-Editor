-- Filename: uart_receive_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_receive is
    generic (
        constant g_divisor_width : natural := 8;
        constant g_data_width    : natural := 8;
        constant g_has_parity    : boolean := true;
        constant g_odd_parity    : boolean := false 
    );
    port (
        res_i                          : in std_logic;
        clk_i                          : in std_logic;
        rx_sync_i                      : in std_logic;
        receive_clock_enable_i         : in std_logic;
        divisor_i                      : in unsigned(g_divisor_width-1 downto 0);
        enable_receive_clock_divider_o : out std_logic;
        data_o                         : out std_logic_vector(g_data_width-1 downto 0);
        parity_err_o                   : out std_logic;
        ready_receive_o                : out std_logic 
    );
end entity;
