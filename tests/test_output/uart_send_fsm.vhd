-- Filename: uart_send_fsm.vhd
-- Created by HDL-FSM-Editor

architecture fsm of uart_send is
    type t_state is (idle, start_bit, data_bit, parity_bit, stop_bit, waiting);
    signal state : t_state;
    signal parity      : std_logic;
    signal bit_counter : natural range 0 to g_data_width;
begin
    p_states: process (res_i, clk_i)
        variable data : std_logic;
    begin
        if res_i='1' then
            state <= idle;
            tx_o         <= '1';
            ready_send_o <= '1';
            parity       <= '0';
            bit_counter  <=  0;
            enable_send_clock_divider_o <= '0';
        elsif rising_edge(clk_i) then
            -- State Machine:
            case state is
                when idle =>
                    if send_i='1' then
                        ready_send_o <= '0';
                        enable_send_clock_divider_o <= '1';
                        state <= waiting;
                    end if;
                when start_bit =>
                    if send_clock_enable_i='1' then
                        data        := data_i(bit_counter);
                        tx_o        <= data;
                        parity      <= data xor parity;
                        bit_counter <= bit_counter + 1;
                        state <= data_bit;
                    end if;
                when data_bit =>
                    if send_clock_enable_i='1' then
                        if bit_counter=g_data_width then
                            if g_has_parity=true then
                                if g_odd_parity then
                                    tx_o <= parity xor '1';
                                else
                                    tx_o <= parity;
                                end if;
                                state <= parity_bit;
                            else
                                tx_o <= '1';
                                bit_counter <= 1;
                                state <= stop_bit;
                            end if;
                        else
                            data        := data_i(bit_counter);
                            tx_o        <= data;
                            parity      <= data xor parity;
                            bit_counter <= bit_counter + 1;
                        end if;
                    end if;
                when parity_bit =>
                    if send_clock_enable_i='1' then
                        tx_o <= '1';
                        bit_counter <= 1;
                        state <= stop_bit;
                    end if;
                when stop_bit =>
                    if send_clock_enable_i='1' then
                        if bit_counter=g_number_of_stopbits then
                            ready_send_o <= '1';
                            parity       <= '0';
                            bit_counter  <=  0;
                            enable_send_clock_divider_o <= '0';
                            state <= idle;
                        else
                            bit_counter <= bit_counter + 1;
                        end if;
                    end if;
                when waiting =>
                    if send_clock_enable_i='1' then
                        tx_o <= '0';
                        state <= start_bit;
                    end if;
            end case;
        end if;
    end process;
end architecture;
