-- Filename: fifo_control_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity fifo_control is
    generic (
        g_fifo_depth        : natural := 16;
        g_ram_address_width : natural := 4 
    );
    port (
        res_i            : in std_logic;
        clk_i            : in std_logic;
        write_fifo_i     : in std_logic;
        read_fifo_i      : in std_logic;
        fifo_underflow_o : out std_logic;
        fifo_overflow_o  : out std_logic;
        ram_address_o    : out std_logic_vector(g_ram_address_width-1 downto 0);
        fifo_empty_o     : out std_logic;
        fifo_full_o      : out std_logic;
        write_ram_o     : out std_logic;
        last_o           : out std_logic 
    );
end entity;
