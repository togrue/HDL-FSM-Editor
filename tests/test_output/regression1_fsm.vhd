-- Filename: regression1_fsm.vhd
-- Created by HDL-FSM-Editor at Wed Aug 13 17:52:13 2025

architecture fsm of regression1 is
    type t_state is (S1, S2, S3, S4, S5, S6, S7, S8, S9, S10,
    S11, S12, S13, S14, S15);
    signal state : t_state;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= S1;
        elsif rising_edge(clk_i) then
            -- Global Actions before:
            global clocked before
            -- State Machine:
            case state is
                when S1 =>
                    state <= S2;
                when S2 =>
                    action1
                    state <= S3;
                when S3 =>
                    if cond2 then
                        state <= S4;
                    end if;
                when S4 =>
                    if cond3 then
                        action3
                        state <= S5;
                    end if;
                when S5 =>
                    state <= S6;
                when S6 =>
                    if cond4 then
                        state <= S7;
                    else
                        state <= S8;
                    end if;
                when S7 =>
                    if cond5 then
                        action5
                        state <= S10;
                    else
                        action51
                        state <= S9;
                    end if;
                when S8 =>
                    if cond8 then
                        if cond10 then
                            action10
                            if cond11 then
                                state <= S15;
                            else
                                action12
                                state <= S14;
                            end if;
                        else
                            state <= S13;
                        end if;
                    end if;
                when S9 =>
                    if cond10 then
                        action10
                        if cond11 then
                            state <= S15;
                        else
                            action12
                            state <= S14;
                        end if;
                    else
                        state <= S13;
                    end if;
                when S10 =>
                    if cond6 then
                        action6
                        if cond7 then
                            action7
                            state <= S11;
                        else
                            state <= S12;
                        end if;
                    else
                        state <= S9;
                    end if;
                when S11 =>
                    if cond12 then
                    else
                        state <= S5;
                    end if;
                when S12 =>
                    if cond20 then
                        if cond21 then
                            if cond22 then
                                if cond30 then
                                    action20
                                    action21
                                    action22
                                    action30
                                    state <= S15;
                                end if;
                            elsif cond30 then
                                action20
                                action21
                                action22_else
                                action30
                                state <= S15;
                            end if;
                        elsif cond24 then
                            if cond30 then
                                action20
                                action23
                                action24
                                action30
                                state <= S15;
                            end if;
                        elsif cond25 then
                            if cond30 then
                                action20
                                action23
                                action25
                                action30
                                state <= S15;
                            end if;
                        else
                            action20
                            action23
                            state <= S15;
                        end if;
                    elsif cond10 then
                        action9
                        action10
                        if cond11 then
                            state <= S15;
                        else
                            action12
                            state <= S14;
                        end if;
                    else
                        action9
                        state <= S13;
                    end if;
                when S13 =>
                when S14 =>
                when S15 =>
            end case;
            -- Global Actions after:
            global clocked after
        end if;
    end process;
    p_state_actions: process (state)
    begin
        -- Default State Actions:
        default
        -- State Actions:
        case state is
            when S1=>
                stateaction
            when S2=>
                null;
            when S3=>
                null;
            when S4=>
                null;
            when S5=>
                null;
            when S6=>
                null;
            when S7=>
                null;
            when S8=>
                null;
            when S9=>
                null;
            when S10=>
                null;
            when S11=>
                null;
            when S12=>
                null;
            when S13=>
                null;
            when S14=>
                null;
            when S15=>
                null;
        end case;
    end process;
    -- Global Actions combinatorial:
    global comb
end architecture;
