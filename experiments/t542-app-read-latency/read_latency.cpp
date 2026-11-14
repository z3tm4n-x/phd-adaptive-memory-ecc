// Integer time on the 100 MHz clock. The SRAM model is indexed by the pad
// address that is actually selected. Oracle addresses use a separate bit map.
#include "Vlatency_probe.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>

constexpr int frame=140, length=4587520, fixed=8642900;
constexpr int count_period=((100003+2+frame-1)/frame)*frame;
constexpr std::array<int,8> thresholds={0,10,19,38,75,149,298,596};
constexpr int previous_address=0x10020;
int external(int j) {
    return (j%32)+32*(j/65536)+64*((j%65536)/64)+65536*((j/32)%2);
}
int memory(int pin,int plane) {
    const int low=pin&65535, high=pin>>16;
    return plane?((low^0x39c6^(high?0xffff:0))&65535):((low*173+0x5a37)&65535);
}
int parity(int v){return __builtin_parity(unsigned(v));}
int target(int n){return (0x14a2b+7919*n)&0x1ffff;}

struct Record {
    int arrival=-1,eligible=-1,grant=-1,valid=-1;
    int want=-1,launched=-1,word=-1,expected=-1,source_rise=-1;
    bool completed=false;
};

class Bench {
  public:
    VerilatedContext clock_model;
    Vlatency_probe d;
    const int plane;
    bool protect_hit=false;
    int t=-1,repairs=0;
    Bench(int n):d(&clock_model),plane(n) {
        d.clk=0;d.reset_core=1;d.sem_ok=0;d.req=0;d.err=0;d.preload=0;
        d.prefix_z=0;d.prefix_level=0;d.prefix_epoch=0;d.read_data=0;d.request_addr=previous_address;
        d.eval();
    }
    void ensure(bool check,const std::string& name) const{
        if(!check) throw std::runtime_error(name+" tick="+std::to_string(t)+" phase="+std::to_string(d.phase));
    }
    void step(){
        ++t;
        // DQ is driven by the simulated chip throughout a valid read and is
        // allowed to change only after the physical address or controls change.
        d.read_data=!d.cs&&!d.oe?memory(d.pad_addr,plane):0xdead;
        d.err=protect_hit;
        const bool was_writing=d.running&&!d.cold&&d.owner&&!d.cs&&!d.we;
        const int old_addr=d.pad_addr;
        clock_model.timeInc(5);d.clk=1;d.eval();
        if(was_writing&&d.we){
            ensure(d.drive&&!d.cs&&d.pad_addr==old_addr&&d.driven_data==memory(old_addr,plane),
                   "mandatory repair did not commit the captured data");
            ++repairs;
        }
        if(!d.we)ensure(d.owner&&!d.cs&&d.drive&&d.driven_data==memory(d.pad_addr,plane),"repair data on pads");
        clock_model.timeInc(5);d.clk=0;d.eval();
    }
    void external_start(){
        for(int n=0;n<4;n++)step();
        d.reset_core=0;t=-1;step();
        ensure(t==0&&d.owner&&d.pad_addr==0&&d.phase==0,"initial core access");
    }
    void board_start(int delayed){
        for(int n=0;n<delayed;n++){
            step();ensure(d.cold&&d.request_line&&d.source_addr==0&&!d.grant&&!d.valid,"service before readiness");
        }
        d.sem_ok=1;
        while(d.cold){step();ensure(!d.grant&&!d.valid,"commissioning acknowledgement");ensure(t<delayed+18,"ready");}
        std::cout<<"READY,"<<delayed<<","<<t<<","<<t+1<<"\n";
        t=-1;step();ensure(d.owner&&!d.cold&&d.phase==0&&d.pad_addr==0,"first commissioned address");
    }
    void plant(int level){
        ensure(t==0&&!d.cs&&d.pad_addr==0,"prefix placement");
        d.prefix_z=thresholds.at(level)-1;d.prefix_level=level-1;
        d.prefix_epoch=128*thresholds.at(level);d.preload=1;d.eval();d.preload=0;d.eval();
    }
    void advance(int to){while(t<to)step();}
    void pins_at_grant(Record& row){
        ensure(!d.cs&&!d.oe&&d.we&&!d.owner&&!d.drive&&d.phase==102,"grant on pins");
        row.grant=t;row.launched=d.pad_addr;
        // Exercise the real DQ/capture. The expected address for equality with
        // the application request is checked independently by the caller.
    }
    void sample(Record& row){
        if(row.grant<0||row.completed)return;
        int age=t-row.grant;
        ensure(d.we&&!d.drive&&!d.owner,"overlapping SRAM owner");
        if(age<10)ensure(!d.cs&&d.pad_addr==row.launched&&d.oe==(age>=7),"app read pins");
        if(age==6)ensure(d.capture_data==memory(row.launched,plane),"sample edge");
        if(age==7)ensure(d.app_data==memory(row.launched,plane),"capture to data register");
        ensure(d.valid==(age==10),"valid offset");
        if(d.valid){
            ensure(d.cs&&d.oe,"application did not release");
            row.valid=t;row.word=d.app_data;row.expected=memory(external(row.want),plane);row.completed=true;
            ensure(row.word==memory(row.launched,plane),"data read from different pad address");
        }
    }
};

void print_row(const char* kind,bool adaptive,int plane,const std::string& context,const std::string& discipline,int h,const Record& r){
    std::cout<<kind<<","<<adaptive<<","<<plane<<","<<context<<","<<discipline<<","<<h<<","
             <<r.source_rise<<","<<r.arrival<<","<<r.eligible<<","<<r.grant<<","<<r.valid<<","
             <<r.want<<","<<r.launched<<","<<r.expected<<","<<r.word<<"\n";
}

void trial(Bench& b,bool adaptive,const std::string& context,const std::string& policy,int when) {
    bool early=policy=="early",gate=policy=="gate";
    int h=when%frame, seek=when-17; // preload before the presenting frame; use full previous frame for h=102
    b.ensure(seek>b.t&&when>0,"overlapping requests");
    int wanted=target((when/140)*3+h);
    if(wanted==previous_address)wanted^=1;
    b.d.req=0;b.d.request_addr=early?wanted:previous_address;
    b.advance(seek);
    Record row;row.want=wanted;row.arrival=when;
    int first=when+(102-h+frame)%frame;
    int g=first+((gate&&when==first)?frame:0);
    row.eligible=(gate&&when==first)?when+1:when;
    bool wrong=!early&&!gate&&when==first;
    for(int k=b.t+1;k<=g+12;k++){
        if(k==when)b.d.request_addr=wanted;
        if(k==row.eligible)b.d.req=1;
        if(k==g+1){b.d.req=0;b.d.request_addr=wanted^0x15555;}
        b.step();
        b.ensure(b.d.grant==(k==g),"unexpected acceptance latency");
        if(b.d.grant){
            b.pins_at_grant(row);
            b.ensure(b.d.pad_addr==external(wrong?previous_address:wanted),"wrong captured address class");
        }
        if(k<=g+10)b.sample(row);
        else b.ensure(!b.d.valid,"second response");
        if(context=="active_clean"&&policy=="hold"&&h==102&&k>=g-2&&k<=g+11){
            auto& d=b.d;
            std::cout<<"SIGNAL,"<<adaptive<<","<<b.plane<<","<<k<<","<<int(d.phase)<<","<<int(d.request_line)
              <<","<<d.source_addr<<","<<d.candidate<<","<<int(d.grant)<<","<<int(d.valid)<<","<<d.pad_addr
              <<","<<int(d.cs)<<","<<int(d.oe)<<","<<int(d.we)<<","<<d.read_data<<","<<d.capture_data<<","<<d.app_data<<"\n";
        }
    }
    b.ensure(row.completed&&row.valid==g+10&&row.grant>=row.eligible,"missing response");
    if(wrong)b.ensure(row.word!=row.expected,"old and new data alias in sentinel");
    else b.ensure(row.word==row.expected,"incorrect requested value");
    print_row("EXT",adaptive,b.plane,context,policy,h,row);
}

void sweep(Bench& b,bool a,const std::string& context) {
    int first=b.t+3*frame; first-=first%frame;
    for(int kind=0;kind<3;kind++)for(int h=0;h<frame;h++){
        int when=first+3*frame*(kind*frame+h)+h;
        trial(b,a,context,std::array<std::string,3>{"early","hold","gate"}[kind],when);
    }
}

void edge_trial(Bench& b,bool a,const std::string& name,int edge,bool active){
    // One pending request arrives on the last edge of the preceding frame;
    // the very next frame must deliver its actual address and word.
    trial(b,a,name,"hold",edge-1);
    b.ensure(b.d.active==active,"wrong calendar side");
}

void external_test(bool a,int plane) {
    Bench b(plane);b.external_start();if(a)b.plant(1);
    sweep(b,a,"active_clean");
    // Present the same waveform at the same absolute ticks to F and A,
    // including both distinct restart instants and the common repair run.
    edge_trial(b,a,"into_pause",length,false);
    if(a)b.ensure(b.d.installed==1,"adaptive pause");
    sweep(b,a,"pause");
    edge_trial(b,a,"fixed_restart",fixed,!a);
    edge_trial(b,a,"adaptive_restart",2*length,true);
    b.protect_hit=true;sweep(b,a,"active_repair");b.protect_hit=false;
    b.ensure(b.repairs>0,"missing repair");
    int before=b.repairs;b.protect_hit=true;
    // One stable pending item at each grant. Present subsequent heads only
    // after acceptance, keeping request asserted for four consecutive slots.
    b.advance(b.t+frame);while(b.t%frame!=0)b.step();
    Record rows[4];
    b.d.req=1;
    int start=b.t;
    for(int i=0;i<4;i++){
        auto& r=rows[i];r.want=target(200+i);r.arrival=start+1;r.eligible=b.t+1;
        b.d.request_addr=r.want;
        const int g=start+102+i*frame;
        for(int k=b.t+1;k<=g+10;k++){
            b.step();b.ensure(b.d.grant==(k==g),"queued grants");
            if(b.d.grant){b.pins_at_grant(r);b.ensure(r.launched==external(r.want),"queue address");}
            b.sample(r);
        }
        b.ensure(r.completed&&r.word==r.expected,"queue delivery");
        print_row("QUEUE",a,plane,"four_pending","early",i,r);
    }
    b.d.req=0;b.ensure(b.repairs-before>=12,"repairs interleaved with held queue");
    std::cout<<"CHECK,external,"<<a<<","<<plane<<","<<b.repairs<<"\n";
}

void dormant_level(int plane,int level) {
    Bench b(plane);b.external_start();b.plant(level);
    const std::string key="level_"+std::to_string(level);
    trial(b,true,key,"early",length-1);
    b.ensure(!b.d.active&&b.d.installed==level,"unreached installed slow level");
}

void board_test(bool a,int plane,bool seeded,int delay){
    Bench b(plane);b.board_start(delay);if(a&&seeded)b.plant(1);
    // For seeded A the long prehistory ends after its first clean full scan.
    const int stop=seeded?2*length+2*count_period:2*count_period+200;
    Record row;row.want=0;row.arrival=0;row.eligible=0;row.source_rise=-1;
    int rises=-1,ng=0,nv=0,g_last=-1;
    int pauses=0,protected_reads=0;
    for(int t=0;t<=stop;t++){
        if(t>0){
            bool pre=b.d.request_line;int preaddr=b.d.source_addr;
            b.protect_hit=(!seeded||t>=2*length)&&(t%frame>=76&&t%frame<=83);
            b.step();
            if(!pre&&b.d.request_line){
                rises=t;row=Record{};row.source_rise=t;row.arrival=t;row.eligible=t+1;row.want=b.d.source_addr;
            }
            if((t==row.eligible)||(row.grant<0&&t>row.eligible&&pre))
                b.ensure(pre&&preaddr==row.want,"source did not hold pending address");
            if(b.d.grant)b.ensure(pre&&preaddr==row.want,"wrong source head");
        }
        b.ensure(b.d.phase==t%frame,"calendar changed across scan boundary");
        if(t==0&&(!b.d.cs&&b.d.owner))++protected_reads;
        if(b.d.grant){
            b.ensure(t==(ng==0?102:g_last+count_period),"board grant spacing");
            b.ensure(row.grant<0&&b.d.candidate==row.want,"stale lookahead for built-in source");
            b.pins_at_grant(row);b.ensure(row.launched==external(row.want),"board pad/request mismatch");
            ++ng;g_last=t;if(!b.d.active)++pauses;
        }
        if(row.grant>=0&&!row.completed)b.sample(row);
        else if(b.d.valid)b.ensure(false,"duplicate valid");
        if(b.d.valid){
            ++nv;b.ensure(row.word==row.expected,"board returned wrong address");
            int d0=row.grant-row.eligible;
            b.ensure(d0==(nv==1?102:95),"first-eligible delay");
            if(nv!=1)b.ensure(row.grant-rises==96,"source edge delay");
            print_row("BOARD",a,plane,seeded?"cross":delay<7?"cold_early":"cold_late","internal",ng-1,row);
        }
        if(row.completed&&t==row.valid+1)
            b.ensure(b.d.consumed_parity==parity(row.word),"registered client consumer");
    }
    b.ensure(ng==nv&&ng>=3&&protected_reads==1&&b.repairs>0,"incomplete board test");
    if(seeded)b.ensure(pauses>0,"no real app in a pause");
    std::cout<<"CHECK,board,"<<a<<","<<plane<<","<<seeded<<","<<ng<<","<<pauses<<","<<b.repairs<<"\n";
}

int main(int argc,char** argv){
    if(argc<4||argc>5)return 2;
    bool a=std::atoi(argv[1]),board=std::atoi(argv[2]);int plane=std::atoi(argv[3]);
    if(argc==5){
        if(board||std::string(argv[4])!="strict-held")return 2;
        try{
            Bench b(plane);b.external_start();b.d.req=0;b.d.request_addr=previous_address;b.advance(3*frame+101);
            int wanted=0x10001;b.d.req=1;b.d.request_addr=wanted;b.step();
            b.ensure(b.d.grant,"ordinary source not granted");
            for(int n=0;n<10;n++)b.step();
            b.ensure(b.d.valid&&b.d.app_data==memory(external(wanted),plane),"strict ordinary request returned another address");
        }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
        return 0;
    }
    try{if(board){board_test(a,plane,false,2);board_test(a,plane,false,37);board_test(a,plane,true,157);}
        else {external_test(a,plane);if(a)for(int level=2;level<=7;level++)dormant_level(plane,level);}}
    catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
    return 0;
}
