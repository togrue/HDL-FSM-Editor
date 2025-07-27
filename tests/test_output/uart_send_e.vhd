-- Filename: uart_send_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity uart_send is
    generic (
        constant g_data_width  : natural := 8;
        
        constant g_has_parity         : boolean := true;
        constant g_odd_parity         : boolean := false; -- If TRUE, the number of ones together in databits and paritybit must be odd, else even.
        constant g_number_of_stopbits : natural := 1  -- Allowed values: >= 1
    );
    port (
        res_i                       : in std_logic;
        clk_i                       : in std_logic;
        send_clock_enable_i         : in std_logic;
        send_i                      : in std_logic;
        data_i                      : in std_logic_vector(g_data_width-1 downto 0);
        tx_o                        : out std_logic;
        ready_send_o                : out std_logic;
        enable_send_clock_divider_o : out std_logic 
        
    );
end entity;
