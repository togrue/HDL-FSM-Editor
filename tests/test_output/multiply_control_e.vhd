-- Filename: multiply_control_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity multiply_control is
    generic (
        g_counter_max : natural := 8
    );
    port (
        res_i        : in  std_logic;
        clk_i        : in  std_logic;
        start_i      : in  std_logic;
        last_step_o  : out std_logic;
        ready_o      : out std_logic;
        reg_enable_o : out std_logic
    );
end entity;
