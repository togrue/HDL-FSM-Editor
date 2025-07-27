-- Filename: count10_fsm.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

architecture fsm of count10 is
    type t_state is (disabled, running, idle);
    signal state : t_state;
    signal counter : unsigned(g_counter_width-1 downto 0);
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= idle;
            counter <= (others => '0');
            half_o <= '0';
        elsif rising_edge(clk_i) then
            -- Global Actions before:
            half_o <= '0'; -- Default value
            -- State Machine:
            case state is
                when disabled =>
                when running =>
                    if disable_forever_i='1' then
                        state <= disabled;
                    elsif counter=10 then
                        counter <= (others => '0');
                        state <= idle;
                    else
                        if counter=5 then
                            half_o <= '1';
                        end if; 
                        counter <= counter + 1;
                    end if;
                when idle =>
                    -- test1
                    -- test2
                    if start_i='1' then
                        counter <= counter + 1;
                        state <= running;
                    end if;
            end case;
            -- Global Actions after:
            if enable_i='0' then
                counter <= (others => '0');
            else
                counter <= (others => '1');
            end if; 
        end if;
    end process;
    p_state_actions: process (start_i, counter, state)
    begin
        -- Default State Actions:
        running_o <= start_i;
        ready_o <= '0';
        -- State Actions:
        case state is
            when disabled=>
                null;
            when running=>
                running_o <= '1';
                if (counter=10) then
                    ready_o <= '1';
                end if;
            when idle=>
                null;
        end case;
    end process;
    -- Global Actions combinatorial:
    counter_o <= std_logic_vector(counter);
end architecture;
