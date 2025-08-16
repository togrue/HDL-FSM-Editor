-- Filename: regression2_fsm.vhd
-- Created by HDL-FSM-Editor

architecture fsm of regression2 is
    type t_state is (S1, S2, S3, S4, S5, S6, S7, S8, S9, S10,
    S11, S12, S13, S14, S15, S16, S17, S18);
    signal state : t_state;
begin
    p_states: process (res_i, clk_i)
    begin
        if res_i='1' then
            state <= S1;
        elsif rising_edge(clk_i) then
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
                        action20
                        state <= S15;
                        if cond21 then
                            action21
                            action30
                            if cond22 then
                                action22
                            else
                                action22_else
                            end if;
                        elsif cond24 then
                            action23
                            action24
                            action30
                        elsif cond25 then
                            action23
                            action25
                            action30
                        else
                            action23
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
                    state <= S16;
                when S15 =>
                when S16 =>
                    naction1
                    if ncond1 then
                        if ncond2 then
                            naction2
                            state <= S17;
                        else
                            state <= S18;
                        end if;
                    else
                    end if;
                when S17 =>
                when S18 =>
                    if ncond2 then
                        naction2
                        state <= S17;
                    end if;
            end case;
        end if;
    end process;
end architecture;
