-- Filename: count10_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity count10 is
    generic (
        g_reset_value   : std_logic := '0';
        g_counter_width : integer   := 4
    );
    port (
        res_i : in std_logic;
        clk_i : in std_logic;
        
        start_i   : in std_logic;
        enable_i  : in std_logic;
        disable_forever_i : in std_logic;
        counter_o : out std_logic_vector(g_counter_width-1 downto 0);
        running_o : out std_logic;
        ready_o   : out std_logic;
        half_o    : out std_logic
    );
end entity;
