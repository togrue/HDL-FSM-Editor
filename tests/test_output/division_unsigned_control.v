// Filename: division_unsigned_control.v
// Created by HDL-FSM-Editor
module division_unsigned_control
    #(parameter
    g_counter_max = 8
    )
    (
        input res_i,
        input clk_i,
        input start_i,
        output reg ready_o,
        output reg reg_enable_o
    );
    reg [0:0] state;
    localparam
        idle = 0,
        run  = 1;
    integer counter;
    always @(posedge clk_i or posedge res_i) begin: p_states
        if (res_i==1'b1) begin
            state <= idle;
            counter <=  0 ;
            ready_o <= 1'b0;
        end
        else begin
            // State Machine:
            case (state)
                idle: begin
                    if (start_i==1'b1) begin
                        ready_o <= 1'b0;
                        if (counter==g_counter_max) begin
                            ready_o   <= 1'b1;
                            counter   <=  0 ;
                        end else begin
                            counter <= counter + 1;
                            state <= run;
                        end
                    end else begin
                        ready_o <= 1'b0;
                    end
                end
                run: begin
                    if (counter==g_counter_max) begin
                        ready_o   <= 1'b1;
                        counter   <=  0 ;
                        state <= idle;
                    end else begin
                        counter <= counter + 1;
                    end
                end
                default:
                    ;
            endcase
        end
    end
    always @(state) begin: p_state_actions
        // State Actions:
        case (state)
            idle: begin
                reg_enable_o <= 1'b0;
            end
            run: begin
                reg_enable_o <= 1'b1;
            end
            default:
                ;
        endcase
    end
endmodule
