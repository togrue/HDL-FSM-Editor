-- Filename: cordic_square_root_control_fsm.vhd
-- Created by HDL-FSM-Editor

architecture fsm of cordic_square_root_control is
    type t_state is (count, idle);
    signal state : t_state;
    signal counter : natural range 0 to g_counter_max;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= idle;
            ready_steps_o <= '0';
            counter       <= 0;
            first_step_o  <= '1';
        elsif rising_edge(clk_i) then
            -- State Machine:
            case state is
                when count =>
                    if counter=g_counter_max then
                        ready_steps_o <= '1';
                        counter       <= 0;
                        first_step_o  <= '1';
                        state <= idle;
                    else
                        counter <= counter + 1;
                    end if;
                when idle =>
                    ready_steps_o <= '0';
                    if start_cordic_i='1' then
                        first_step_o <= '0';
                        if counter=g_counter_max then
                            ready_steps_o <= '1';
                            counter       <= 0;
                            first_step_o  <= '1';
                        else
                            counter <= counter + 1;
                            state <= count;
                        end if;
                    else
                    end if;
            end case;
        end if;
    end process;
    p_state_actions: process (start_cordic_i, state)
    begin
        -- State Actions:
        case state is
            when count=>
                enable_reg_o <= '1';
            when idle=>
                if start_cordic_i='1' then
                    enable_reg_o <= '1';
                else
                    enable_reg_o <= '0';
                end if;
        end case;
    end process;
    -- Global Actions combinatorial:
    counter_o <= counter;
end architecture;
