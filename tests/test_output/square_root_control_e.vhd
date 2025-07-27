-- Filename: square_root_control_e.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity square_root_control is
    generic (
        constant g_counter_max : natural := 16
    );
    port (
        clk_i          : in  std_logic;
        res_i          : in  std_logic;
        start_i        : in  std_logic;
        enable_reg_o   : out std_logic;
        counter_o      : out natural range 0 to g_counter_max;
        ready_steps_o  : out std_logic;
        first_step_o   : out std_logic
    );
end entity;
