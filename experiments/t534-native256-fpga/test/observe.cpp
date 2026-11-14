// Independent integer-time pin plan. Units below are 10 ns clock periods.
#include "Vharness.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <deque>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int addresses=131072, half=65536, L=4587520, fixed_period=8642900;
constexpr int offsets[]={0,24,52,76};
constexpr int threshold[]={0,10,19,38,75,149,298,596};
constexpr int app_address=0x15678;

int physical(int j) { // independent of the Verilog concatenation
    int half_index=j/half, block=(j%half)/32;
    return (j%32)+32*half_index+64*(block/2)+half*(block%2);
}
int datum(int j) { return (173*j+0xa5b7+(j>>16)*31)&65535; }

struct Check {
    Vharness d;
    long long time=0;
    Check() {
        d.clk=0; d.cold=1; d.loss=0; d.err=0; d.req=0; d.dq=0;
        d.app=app_address; d.edit=0; d.action=0; d.prior_level=0;
        d.prefix=0; d.prefix_epoch=0; d.eval(); tick(); tick(); d.cold=0;
    }
    // The observation point is the falling edge, 5 ns after the deciding
    // rising edge. Test deposits at this point cannot change that decision.
    void tick() {
        d.clk=0;d.eval();Verilated::timeInc(5);
        d.clk=1;d.eval();Verilated::timeInc(5);
        d.clk=0;d.eval();++time;
    }
    void edit(int code) { d.action=code;d.edit=1;d.eval();d.edit=0;d.eval(); }
    void need(bool ok,const char* what) {
        if(!ok) throw std::runtime_error(std::string(what)+" at observed tick "+std::to_string(time));
    }
};

void physical_run(bool adaptive,bool triple,const std::string& test) {
    Check c; auto& d=c.d;
    const bool fault_err=test=="one_err",fault_data=test=="one_data",common=test=="common_err";
    const bool inject=fault_data||fault_err||common;
    const bool contaminated=triple&&(fault_err||fault_data);
    const bool seeded=inject&&adaptive;
    const bool false_zero=(common||(fault_err&&!triple));
    const int span=adaptive?L:fixed_period;
    std::vector<unsigned char> visited(addresses);
    std::vector<int> first_sample(half,-1);
    std::vector<int> window(100000);
    int busy=0, peak=0,rolling=0, app_reads=0,writes=0,read=0,packets=0;
    int end_write=-1,end_read=-1,cut=-1,install=-1,repair_at=-1,partial=-1;
    int bad_writes=0, last_grant=-100004, observed_count=0,fault_ticks=0;
    bool prev_cs=true,prev_we=true;
    for(int t=0;t<span;t++) {
        int f=t/140,h=t%140,l=h<24?0:h<52?1:h<76?2:3,a=h-offsets[l],j=f*4+l;
        bool active=t<L, last=(j==addresses-1);
        bool edge_set=(j<2||j==half-1||j==half||j>=addresses-2);
        bool hit=active&&(test=="all"||(test=="edges"&&edge_set)||(last&&(test=="last"||inject)));
        bool write=hit&&!(last&&false_zero);
        bool owner=active&&a<(write?20:10);
        bool app_frame=(f%715==0); // >=1,001,000 ns between grants, also through Fixed pause
        bool app_cs=app_frame&&h>=102&&h<112;
        bool drives=owner&&write&&a>=10&&a<18;
        d.req=app_frame&&h==102;
        // In common_err the modeled defect exists but the shared input pin
        // stays LOW on the sample edge. Every undamaged lane sees that pin.
        bool observed_err=hit&&!(common&&last);
        d.err=(a==6)?observed_err:!hit;
        d.dq=(h==108)?datum(app_address):(a==6)?datum(j):(datum(j)^65535);
        c.tick();
        if(t==0&&seeded) {
            d.prefix=9;d.prefix_epoch=1280;d.prior_level=0;c.edit(1);
        }
        c.need(d.owner==owner&&d.cs==!(owner||app_cs)&&d.oe==!((owner&&a<7)||(app_cs&&h<109))
            &&d.we==!(owner&&write&&a>=11&&a<16)&&d.t_n==(drives?0:65535),"CS/OE/WE/ownership/turnaround");
        if(owner||app_cs)c.need(d.addr==physical(owner?j:app_address),"external address");
        c.need(d.grant==(app_frame&&h==102)&&d.valid==(app_frame&&h==112),"application timing");
        if(d.grant){c.need(t-last_grant>=100003,"application envelope");last_grant=t;}
        if(d.valid){c.need(d.app_data==datum(app_address),"application DQ");++app_reads;}
        if(active&&a==6) {
            c.need(d.image0==datum(j)&&d.err_trace==(observed_err?(triple?7:1):0),"DQ/ERR sampling aperture");
            if(j<half)first_sample[j]=t;
            else c.need(t-first_sample[j-half]==L/2&&((physical(j)^physical(j-half))==32),"half-word sampling gap");
            if(last&&(fault_err||fault_data))c.edit(fault_err?4:5);
        }
        if(drives) {
            bool damaged=fault_data&&!triple&&last;
            c.need(d.data==(datum(j)^(damaged?1:0)),"actual write DQ");
        }
        if(prev_cs&&!d.cs&&d.owner) {
            c.need(!visited[d.addr]&&j==read,"duplicate or out-of-order read");
            visited[d.addr]=1;++read;
        }
        if(!prev_we&&d.we) {
            c.need(!d.cs&&d.addr==physical(j)&&a==16,"write end");++writes;
            if(d.data!=datum(j))++bad_writes;
            if(last)repair_at=t;
        }
        if(last&&a==13&&write){partial=busy*10;c.need(!d.sealed&&!d.pkt&&d.owner&&!d.we,"truncated write before commit");}
        if(active&&write&&a==20)++observed_count;
        c.need(d.count==observed_count,"pre-release or omitted count");
        if(last&&a==(write?20:10)){end_read=t;c.need(!d.owner&&d.cs,"last release");}
        if(d.pkt){++packets;end_write=t;c.need(active&&last&&!d.owner&&d.sealed,"unsealed or early report");}
        if(d.zero){cut=t;c.need(t==L-30,"cut");}
        if(d.strobe){install=t;c.need(t==L-10,"installation");}
        if(d.fault)++fault_ticks;
        busy+=d.owner;int idx=t%100000;rolling+=d.owner-window[idx];window[idx]=d.owner;peak=std::max(peak,rolling);
        prev_cs=d.cs;prev_we=d.we;
    }
    c.need(read==addresses&&std::count(visited.begin(),visited.end(),1)==addresses,"full coverage");
    c.need(packets==1&&end_read==end_write&&busy==10*(addresses+writes),"accounting and publication");
    c.need((fault_ticks>0)==contaminated,"detected discrepancy");
    c.need(install==(adaptive?L-10:-1)&&cut==(adaptive&&writes==0&&!contaminated?L-30:-1),"decision on actual count");
    int issued=d.issued;
    c.need(issued==int(seeded&&false_zero),"false zero endpoints");
    c.tick();
    if(issued==0)c.need(d.owner&&!d.cs&&!d.oe&&d.addr==0,"next physical start");
    else {
        c.need(!d.owner&&d.cs,"invalid early 2L start");
        c.edit(2);c.tick();c.need(d.owner&&!d.cs&&d.addr==0,"actual deferred start");
    }
    std::cout<<"FULL mode="<<adaptive<<" protected="<<triple<<" case="<<test<<" reads="<<read<<" writes="<<writes
        <<" owner_ns="<<busy*10<<" peak_1ms_ns="<<peak*10<<" app_reads="<<app_reads<<" app_reserved_ns="<<app_reads*240
        <<" sample_last_ns="<<(L-58)*10<<" we_last_ns="<<(repair_at<0?-1:repair_at*10)
        <<" release_last_ns="<<end_read*10<<" publication_ns="<<end_write*10<<" zero_tick="<<cut<<" install_tick="<<install
        <<" next_ns="<<static_cast<long long>(span)*(1<<issued)*10<<" partial_ns="<<partial
        <<" wrong_write="<<bad_writes<<" disagreement_ticks="<<fault_ticks<<"\n";
}

void boundary(bool triple,int level,int defect) {
    Check c; auto& d=c.d; int reads=0, packet=-1,zero=-1,inst=-1;
    d.dq=0x57a3;d.prefix=threshold[level]-1;d.prior_level=level-1;d.prefix_epoch=128*threshold[level];
    bool prev=true;
    for(int t=0;t<L;t++){
        if(t==L-30&&defect==1)c.edit(8); // valid and stable before the cut edge
        c.tick();
        if(t==0)c.edit(1);
        if(d.owner&&prev&&!d.cs) {c.need(d.addr==physical(reads),"boundary address");++reads;}
        prev=d.cs;
        if(d.pkt&&packet<0){packet=t;c.need(d.sealed&&d.count==0&&d.cs&&!d.owner,"physical report");
            if(defect>=1&&defect<=3)c.edit(7);}
        if(t==L-30){
            zero=d.zero;
            if(defect==2)c.edit(8); // between this cut and its following sampling edge
        }
        if(t==L-10){
            c.need(d.strobe,"installation missing");inst=d.issued;
            if(defect==4)c.edit(9); // one replica loses its already installed command
        }
        if(t==L-9 && defect==5)d.loss=1;
        if(t==L-8 && defect==5)d.loss=0;
    }
    int expected=defect==2||defect==3?0:level;
    c.need(reads==addresses&&packet==L-54&&zero==(defect!=2&&defect!=3)&&inst==expected,"deadline/prefix");
    int actual_level=defect==4&&!triple?(expected^2):expected;
    int next=1<<actual_level,apps=0;
    for(int i=1;i<=next;i++){
        c.tick();
        if(i==next)c.need(d.owner&&!d.oe&&!d.cs&&d.we&&d.addr==0,"committed start");
        else {
            c.need(!d.owner&&d.cs,"spurious start");
            if(level==1&&defect==0){
                for(int t=1;t<L;t++){
                    d.req=t==102;c.tick();
                    c.need(!d.owner&&d.we&&d.t_n==65535&&d.cs==(t<102||t>=112),"literal quiet epoch");
                    if(d.valid){c.need(t==112&&d.app_data==0x57a3,"idle application response");++apps;}
                }
            } else c.edit(2);
        }
    }
    std::cout<<"BOUNDARY protected="<<triple<<" level="<<level<<" defect="<<defect<<" reads="<<reads
        <<" packet_tick="<<packet<<" accepted="<<zero<<" installed="<<inst<<" actual_round="<<next
        <<" literal_idle_apps="<<apps<<"\n";
}

void recovery(bool triple,int kind) {
    Check c;auto& d=c.d;const int first=1280, gap=128;
    d.dq=0x7b5e;d.prefix=9;d.prior_level=0;d.prefix_epoch=first;
    c.tick();c.edit(1);int due=first, first_up=-1,commands=0,starts=0, common_checks=0;
    for(int ep=first;ep<=first+11*gap+2;ep++){
        bool active=ep==due;
        c.need(d.epoch==ep&&(bool(d.owner&&!d.cs&&!d.oe&&d.addr==0)==active),"recovery actual calendar");
        starts+=active;int code=-1;
        for(int t=0;t<L;t++){
            if(t!=0)c.tick();
            if(t==136){
                c.need(d.cs&&!d.owner&&d.we,"prefix splice outside idle");c.edit(3);t=32766*140+136;
            }
            if(ep==first&&t==L-55)d.loss=1; // preceding report was complete, history invalidated
            if(ep==first&&t==L-31&&kind==0)d.loss=0;
            if(ep==first&&t==L-29&&kind==1)d.loss=0; // straddles start of next cell
            if(active&&t==L-30&&ep%gap==0){
                int n=(ep-first)/gap,expected=kind==2?0:std::max(0,n-(kind==1));
                c.need(d.z==expected&&bool(d.zero)==(n>0&&kind!=2),"fresh common-cell history");++common_checks;
            }
            if(d.strobe){c.need(active&&t==L-10,"recovery installation");code=d.issued;++commands;
                if(code>0&&first_up<0)first_up=ep;}
        }
        if(active){c.need(code>=0,"missing command");due=ep+(1<<code);}
        c.tick();
    }
    c.need(first_up==(kind==2?-1:first+(10+(kind==1))*gap),"first promotion/recovery");
    std::cout<<"RECOVERY protected="<<triple<<" loss_case="<<kind<<" first_2L_epoch="<<first_up
        <<" next_2L_epoch="<<(first_up<0?-1:first_up+2)<<" starts="<<starts<<" commands="<<commands
        <<" common_checks="<<common_checks<<"\n";
}
int main(int argc,char** argv){
    if(argc<5)return 2;
    bool adaptive=std::stoi(argv[1]),triple=std::stoi(argv[2]);
    try{
        if(std::string(argv[3])=="full")physical_run(adaptive,triple,argv[4]);
        else if(std::string(argv[3])=="boundary"&&argc==6)boundary(triple,std::stoi(argv[4]),std::stoi(argv[5]));
        else if(std::string(argv[3])=="recovery")recovery(triple,std::stoi(argv[4]));
        else return 2;
    }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
    return 0;
}
