-- Filename: uart_receive_fsm.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.std_logic_1164.all;
use ieee.math_real.all;

architecture fsm of uart_receive is
    type t_state is (start_bit, wait_for_enable, idle, stop_bit, parity_bit, data_bit);
    signal state : t_state;
    function get_counter_bit_number return natural is
        variable counter_load_value_1_max : natural;
        variable counter_load_value_2     : natural;
        variable max_load_value           : natural;
    begin
        counter_load_value_1_max := 2**g_divisor_width - 1 + 2**(g_divisor_width-1) - 1 - 4;
        counter_load_value_2     := g_data_width;
        if counter_load_value_1_max>counter_load_value_2 then
            max_load_value := counter_load_value_1_max;
        else
            max_load_value := counter_load_value_2;
        end if;
        -- How many bits are needed for max_load_value?
        -- With n bits the biggest number is 2**n-1.
        --   max_load_value <= 2**n-1
        --             2**n >= max_load_value + 1
        --                n >= ld(max_load_value + 1)   True only as logarithmus dualis ld() is a monoton increasing function.
        -- As ieee.math_real.all only has a logarithmus function with base e, the calculation is:
        return integer(ceil(log(real(max_load_value+1))/log(2.0)));
    end function;
    signal counter    : unsigned(get_counter_bit_number-1 downto 0);
    signal data       : std_logic_vector(g_data_width-1 downto 0);
    signal parity_sum : std_logic;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= idle;
            enable_receive_clock_divider_o <= '0';
            counter                        <= (others => '0');
            data                           <= (others => '0');
            parity_sum                     <= '0';
            parity_err_o                   <= '0';
            ready_receive_o                <= '0';
        elsif rising_edge(clk_i) then
            -- State Machine:
            case state is
                when start_bit =>
                    if counter=0 then
                        enable_receive_clock_divider_o <= '1';
                        counter <= to_unsigned(g_data_width, counter'length);
                        state <= wait_for_enable;
                    else
                        counter <= counter - 1;
                    end if;
                when wait_for_enable =>
                    if receive_clock_enable_i='1' then
                        data <= rx_sync_i & data(data'high downto 1);
                        counter <= counter - 1;
                        parity_sum <= parity_sum xor rx_sync_i;
                        state <= data_bit;
                    end if;
                when idle =>
                    if rx_sync_i='0' then
                        -- receive_clock_enable_i must first be active in the middle
                        -- of the first databit.
                        -- The startbit has divisor_i clock-periods.
                        -- The middle of the databit is after divisor_i/2 clock-periods.
                        -- One clock period is lost at this transition.
                        -- A second is lost at activating enable_receive_clock_divider_o.
                        -- A third is lost at activating receive_clock_enable_i.
                        -- A fourth is lost at sampling rx_sync_i.
                        counter <= to_unsigned(to_integer(divisor_i)+to_integer(divisor_i)/2 - 4, counter'length);
                        parity_sum   <= '0';
                        parity_err_o <= '0';
                        state <= start_bit;
                    end if;
                when stop_bit =>
                    enable_receive_clock_divider_o <= '0';
                    ready_receive_o <= '0';
                    state <= idle;
                when parity_bit =>
                    if receive_clock_enable_i='1' then
                        if (parity_sum='1' and g_odd_parity=false) or
                           (parity_sum='0' and g_odd_parity=true) then
                            parity_err_o <= '1';
                        end if;
                        ready_receive_o <= '1';
                        state <= stop_bit;
                    end if;
                when data_bit =>
                    if receive_clock_enable_i='1' then
                        if counter=0 then
                            if g_has_parity=true then
                                parity_sum <= parity_sum xor rx_sync_i;
                                state <= parity_bit;
                            else
                                ready_receive_o <= '1';
                                state <= stop_bit;
                            end if;
                        else
                            data <= rx_sync_i & data(data'high downto 1);
                            counter <= counter - 1;
                            parity_sum <= parity_sum xor rx_sync_i;
                        end if;
                    end if;
            end case;
        end if;
    end process;
    -- Global Actions combinatorial:
    data_o <= data;
end architecture;
