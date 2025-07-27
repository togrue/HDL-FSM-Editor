-- Filename: fifo_control_fsm.vhd
-- Created by HDL-FSM-Editor
library ieee;
use ieee.numeric_std.all;

architecture fsm of fifo_control is
    type t_state is (filled, empty);
    signal state : t_state;
    signal   write_address       : natural range 0 to g_fifo_depth-1;
    signal   write_address_plus1 : natural range 0 to g_fifo_depth-1;
    signal   read_address        : natural range 0 to g_fifo_depth-1;
    signal   read_address_plus1  : natural range 0 to g_fifo_depth-1;
    signal   read_address_plus2  : natural range 0 to g_fifo_depth-1;
    signal   fifo_empty          : boolean;
    signal   fifo_full           : boolean;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= empty;
            write_address    <= 0;
            read_address     <= 0;
            fifo_underflow_o <= '0';
            fifo_overflow_o  <= '0';
            last_o           <= '0';
        elsif rising_edge(clk_i) then
            -- State Machine:
            case state is
                when filled =>
                    if write_fifo_i='1' then
                        last_o <= '0';
                        if write_address=read_address then
                            fifo_overflow_o <= '1';
                        else
                            write_address <= write_address_plus1;
                        end if;
                    elsif read_fifo_i='1' then
                        read_address <= read_address_plus1;
                        if read_address_plus1=write_address then
                            last_o <= '0';
                            state <= empty;
                        else
                            if read_address_plus2=write_address then
                                last_o <= '1';
                            end if;
                        end if;
                    else
                        fifo_overflow_o <= '0';
                    end if;
                when empty =>
                    if write_fifo_i='1' then
                        write_address    <= write_address_plus1;
                        last_o           <= '1';
                        fifo_underflow_o <= '0';
                        state <= filled;
                    elsif read_fifo_i='1' then
                        fifo_underflow_o <= '1';
                    else
                        fifo_underflow_o <= '0';
                    end if;
            end case;
        end if;
    end process;
    p_state_actions: process (write_address, read_address, state)
    begin
        -- Default State Actions:
        fifo_empty <= false;
        fifo_full  <= false;
        -- State Actions:
        case state is
            when filled=>
                if write_address=read_address then
                    fifo_full <= true;
                end if;
            when empty=>
                fifo_empty <= true;
        end case;
    end process;
    -- Global Actions combinatorial:
    write_address_plus1 <= (write_address      + 1) mod g_fifo_depth;
    read_address_plus1  <= (read_address       + 1) mod g_fifo_depth;
    read_address_plus2  <= (read_address_plus1 + 1) mod g_fifo_depth;
    process(write_fifo_i, write_address, read_address_plus1)
    begin
        if write_fifo_i='1' then
            ram_address_o <= std_logic_vector(to_unsigned(write_address, g_ram_address_width));
        else
            ram_address_o <= std_logic_vector(to_unsigned(read_address_plus1, g_ram_address_width));
        end if;
    end process;
    write_ram_o  <= write_fifo_i when not fifo_full else '0';
    fifo_full_o  <= '1' when fifo_full  else '0';
    fifo_empty_o <= '1' when fifo_empty else '0';
end architecture;
