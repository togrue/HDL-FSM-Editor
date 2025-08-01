-- Filename: multiply_wt_booth_control.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;

entity multiply_wt_booth_control is
    generic (
        g_counter_max : natural := 8
    );
    port (
        res_i        : in  std_logic;
        clk_i        : in  std_logic;
        start_i      : in  std_logic;
        ready_o      : out std_logic;
        reg_enable_o : out std_logic
    );
end entity;
library ieee;
use ieee.std_logic_1164.all;

architecture fsm of multiply_wt_booth_control is
    type t_state is (idle, run);
    signal state : t_state;
    signal counter : natural range 0 to g_counter_max;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= idle;
            counter   <=  0 ;
            ready_o   <= '0';
        elsif rising_edge(clk_i) then
            -- State Machine:
            case state is
                when idle =>
                    if start_i='1' then
                        ready_o <= '0';
                        if counter=g_counter_max then
                            ready_o   <= '1';
                            counter   <=  0 ;
                        else
                            counter <= counter + 1;
                            state <= run;
                        end if;
                    else
                        ready_o <= '0';
                    end if;
                when run =>
                    if counter=g_counter_max then
                        ready_o   <= '1';
                        counter   <=  0 ;
                        state <= idle;
                    else
                        counter <= counter + 1;
                    end if;
            end case;
        end if;
    end process;
    p_state_actions: process (start_i, state)
    begin
        -- State Actions:
        case state is
            when idle=>
                if start_i='1' then
                    reg_enable_o <= '1';
                else
                    reg_enable_o <= '0';
                end if;
            when run=>
                reg_enable_o <= '1';
        end case;
    end process;
end architecture;
