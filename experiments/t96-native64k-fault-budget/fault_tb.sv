// One persistent FF toggle at a known half-clock; no change to the DUT.
`timescale 1ns/1ns
module fault_tb;
    reg clk=0, cold=1, err=0;
    wire cs, oe, we, drive, owner, sealed, sent, zero, installed, fault;
    wire [14:0] address;
    wire [15:0] data, count;
    wire [3:0] issued;
    wire [9:0] quiet;
    localparam integer L=1146880, LAST=L-64;
    localparam [15:0] IMAGE=16'ha5bf;
    native64_core dut(.clk(clk),.cold(cold),.loss(1'b0),.err_in(err),.dq_in(IMAGE),
        .app_request(1'b0),.app_address(15'd0),.pad_select_n(cs),.pad_oe_n(oe),
        .pad_we_n(we),.pad_address(address),.dq_out(data),.drive(drive),.protect_owner(owner),
        .sealed(sealed),.report_send(sent),.accepted_zero(zero),.command_strobe(installed),
        .execution_fault(fault),.issued(issued),.quiet(quiet),.count(count));
    task edge1; begin #5; clk=1; #1; clk=0; #4; end endtask
    integer c,t,sample_ns=-1,first_fault=-1,word=-1,pub=-1,confirmed=0,code=-1;
    integer count_at_pub=-1, command=-1, visits=0, next_addr=-1, second_addr=-1, incident=-1;
    integer pre_we_word=-1, first_start_L=-1, base_round;
    reg prev_we,prev_cs,expected_err;
    initial begin
        if(!$value$plusargs("case=%d",c) || c<0 || c>14) $fatal;
        edge1; cold=0; edge1; // first real address launched
        // Reachable threshold prefix as exercised in baseline policy_tb/join_tb.
        // A common scan ending the third complete cell can grant 2L.
        dut.epoch=36'd1536; dut.policy.initialized=1;
        dut.policy.quiet=2; dut.policy.quiet_inv=~10'd2;
        dut.policy.issued=0;
        prev_we=1;prev_cs=1;
        expected_err=(c==1 || c==2 || c==3 || c==4 || c==5 || c==10 || c==11);
        for(t=0;t<=L;t=t+1) begin
            if(t>0) begin
                err=(expected_err && t==LAST+6);
                // The assignment precedes the indicated edge by exactly 5 ns.
                if(t==LAST+7 && (c==2 || c==3)) begin
                    if(!dut.sampled_err || dut.repair_image!=IMAGE) $fatal;
                    if(c==2) dut.sampled_err=0;
                    else dut.repair_image=dut.repair_image ^ 1;
                    incident=t*10-5;
                end
                if(t==LAST+8 && c==4) begin
                    if(!dut.repair_a || dut.repair_b) $fatal;
                    dut.repair_a=0; incident=t*10-5;
                end
                if(t==LAST+6 && c==5) begin
                    dut.phase_a=dut.phase_a ^ 2; incident=t*10-5;
                end
                if(t==L-39 && c==6) begin
                    dut.count=dut.count ^ 1; incident=t*10-5;
                end
                if(t==L-39 && c==7) begin
                    if(!dut.sealed) $fatal;
                    dut.sealed=0; incident=t*10-5;
                end
                if(t==L-29 && (c==8 || c==12)) begin
                    if(c==8) dut.policy.quiet=dut.policy.quiet ^ 8;
                    else dut.policy.proposed=dut.policy.proposed ^ 1;
                    incident=t*10-5;
                end
                if(t==L-9 && c==9) begin
                    if(dut.policy.issued!=1) $fatal;
                    dut.policy.issued=dut.policy.issued ^ 2; incident=t*10-5;
                end
                if(t==LAST+6 && c==10) begin force dut.capture=0; incident=t*10-5; end
                if(t==LAST+16 && c==11) begin
                    if(we || !drive) $fatal;
                    dut.dq_out=dut.dq_out ^ 1; incident=t*10-5;
                end
                if(t==LAST+9 && c==13) begin
                    dut.seen=dut.seen ^ 1; incident=t*10-5;
                end
                if(t==LAST+16) begin #0; if(!we && drive) pre_we_word=data; end
                edge1;
                if(t==LAST+6 && c==10) release dut.capture;
            end
            if(!cs && !oe && owner && prev_cs) begin
                if(t<L && address!=visits) $fatal(1,"address order");
                if(t<L) visits=visits+1;
            end
            if(t==LAST+6 && dut.sampled) begin
                if(dut.sampled_err!==expected_err || dut.repair_image!==IMAGE) $fatal;
                sample_ns=t*10;
            end
            if(!we && address==32767 && drive && t==LAST+15) word=data;
            if(!prev_we && we) begin
                if(address!=32767 || !drive || t!=LAST+16) $fatal;
                command=t*10;
            end
            if(fault && first_fault<0) first_fault=t*10;
            if(sent) begin pub=t*10; count_at_pub=count; end
            if(zero) confirmed=1;
            if(installed) code=issued;
            if(t==L) next_addr=(!cs && !oe && owner && address==0);
            prev_cs=cs;prev_we=we;
        end
        // After a committed 2L command, disturb the waiting register in
        // the first inactive base round. Literally clock this entire gap.
        if(next_addr) first_start_L=1;
        if(c==14) begin
            if(next_addr || dut.wait_rounds!=1) $fatal;
            dut.wait_rounds=dut.wait_rounds ^ 4; incident=L*10+5;
            for(t=1;t<=L;t=t+1) begin
                edge1;
                if(fault && first_fault<0) first_fault=(L+t)*10;
                if(t<L && (owner || !cs || !we)) $fatal;
            end
            second_addr=(!cs && !oe && owner && address==0);
            if(second_addr) first_start_L=2;
        end
        if(c==9) begin
            // Only the idle interiors are elided. Keep the wait value and
            // exercise the actual boundary, pins and address on each round.
            for(base_round=2; base_round<=8; base_round=base_round+1) begin
                if(!cs || owner) $fatal(1,"unexpected prior start");
                dut.frame=8191;dut.phase_a=139;dut.phase_inv=~8'd139;dut.phase_parity=^8'd139;
                edge1;
                if(base_round==2) second_addr=(!cs && !oe && owner && address==0);
                if(!cs && !oe && owner && address==0) first_start_L=base_round;
            end
        end
        if(visits!=32768) $fatal;
        $display("OBS case=%0d incident_ns=%0d reads=%0d sample_ns=%0d write_ns=%0d held_data=%0d data_5ns_before_WE_rise=%0d report_ns=%0d report_count=%0d zero=%0d install_code=%0d addr0_at_L=%0d addr0_at_2L=%0d first_start_L=%0d fault_ns=%0d quiet=%0d",c,incident,visits,sample_ns,command,word,pre_we_word,pub,count_at_pub,confirmed,code,next_addr,second_addr,first_start_L,first_fault,quiet);
        $finish;
    end
endmodule
