// Port-driven 32+6 SRAM paired to the actual Yosys-compiled native8.
#include "dut.cc"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

using Top = cxxrtl_design::p_native8;
#include "snapshot.h"

constexpr int L = 2800, prefix_time = 1280*L;
using Mask = uint64_t;

struct Code {
    std::array<unsigned,38> columns{};
    std::array<Mask,4> clean{};
    Code() {
        int d=0, p=32;
        for (unsigned c=1; c<=38; ++c) {
            if ((c & (c-1))==0) columns[p++]=c;
            else columns[d++]=c;
        }
        for (int w=0; w<4; ++w) {
            uint32_t payload=0xa5bc3410u+0x10001u*w;
            unsigned s=0;
            for (int i=0; i<32; ++i) if ((payload>>i)&1u) s^=columns[i];
            clean[w]=Mask(payload) | (Mask(s)<<32);
        }
    }
    unsigned half(Mask raw, unsigned a) const {
        unsigned w=a&3, syndrome=0;
        Mask delta=raw^clean[w];
        if (delta) {
            // A multi-error continuation follows No. 500's diagnostic oracle.
            if (delta & (delta-1)) raw=clean[w];
            else {
                for (int i=0; i<38; ++i) if ((raw>>i)&1) syndrome^=columns[i];
                unsigned pos=0;
                while (pos<38 && columns[pos]!=syndrome) ++pos;
                if (pos==38) throw std::runtime_error("invalid single-bit syndrome");
                raw^=Mask(1)<<pos;
            }
        }
        return (raw>>(16*(a/4))) & 65535;
    }
} const code;

struct Parent { int t, word, bit, other; };
struct Memory {
    std::array<Mask,4> raw=code.clean;
    Mask recent=0;
    int visiting=-1;
    int first=-1;
    Mask errors(int w) const { return raw[w]^code.clean[w]; }
    void toggle(int t, int w, int bit) {
        Mask flag=Mask(1)<<bit;
        raw[w]^=flag;
        auto m=errors(w);
        if (w==visiting) recent=(recent & ~flag) | (m & flag);
        if (first<0 && (m & (m-1))) first=t;
    }
    void write(int a, unsigned bus) {
        unsigned w=a&3;
        if (int(w)!=visiting) throw std::runtime_error("write outside the selected word");
        // Feed the actual 16 pins back. An incorrect bus value corrupts the
        // stored payload and is also reported in W, prior to any later read.
        unsigned shift=16*(a/4);
        Mask image=(code.clean[w] & ~(Mask(65535)<<shift)) | (Mask(bus)<<shift);
        unsigned parity=0;
        for (int i=0; i<32; ++i) if ((image>>i)&1) parity^=code.columns[i];
        raw[w]=(Mask(uint32_t(image)) | (Mask(parity)<<32)) ^ recent;
    }
};

struct Stats { int passes=0, read=0, write=0, rises=0, sealed=0, positive=0,
                   switches=0, fast=0; };
struct Pins {
    int a, s, oe, we, drive;
    bool changed(const Pins &b) const {
        return s!=b.s || oe!=b.oe || we!=b.we || drive!=b.drive || (s && a!=b.a);
    }
};

struct Bench {
    Top top;
    Memory mem;
    Stats st;
    int now=0, launch=-10000, scan=-10000, installed=1;
    bool old_sealed=false;
    Pins prior={0,0,1,1,0};
    std::ostream *out=nullptr;
    template<typename... Args> void row(int t, const char *kind, Args... values) {
        if (out) {
            *out << t << ' ' << kind;
            ((*out << ' ' << values), ...);
            *out << '\n';
        }
    }
    Pins pins() const {
        return {int(top.p_addr.get<unsigned>()),int(top.p_selected.get<unsigned>()),
                int(top.p_oe__n.get<unsigned>()),int(top.p_we__n.get<unsigned>()),
                int(top.p_drive.get<unsigned>())};
    }
    void read_bus() {
        unsigned a=top.p_addr.get<unsigned>(), w=a&3;
        auto p=pins();
        // Two-state sentinel outside the selected read window. Only a real
        // read of the stored codeword may deliver a qualified observation.
        bool reading=p.s && !p.oe && p.we && !p.drive;
        top.p_err__in.set<unsigned>(reading ? mem.errors(w)!=0 : true);
        top.p_dq__in.set<unsigned>(reading ? code.half(mem.raw[w], a) : 0xdead);
    }
    void reset() {
        top.p_clk.set(false); top.p_reset.set(true);
        top.p_release__ok.set(true); top.p_report__ok.set(true); top.p_install__ok.set(true);
        top.step(); top.p_clk.set(true); top.step();
        top.p_reset.set(false); top.p_clk.set(false); top.step();
        observe();
    }
    void copy_from(const Bench &src) {
        restore(top, src.top);
        if (!equal_state(top,src.top)) throw std::runtime_error("incomplete RTL snapshot");
        mem=src.mem; st=src.st; now=src.now; launch=src.launch; scan=src.scan;
        installed=src.installed; prior=src.prior; old_sealed=src.old_sealed;
    }
    bool matches(const Bench &b) const {
        return equal_state(top,b.top) && mem.raw==b.mem.raw && mem.recent==b.mem.recent &&
               mem.visiting==b.mem.visiting && mem.first==b.mem.first &&
               st.passes==b.st.passes && st.read==b.st.read && st.write==b.st.write &&
               st.rises==b.st.rises && st.sealed==b.st.sealed && st.positive==b.st.positive &&
               st.switches==b.st.switches && st.fast==b.st.fast && now==b.now &&
               launch==b.launch && scan==b.scan && installed==b.installed &&
               prior.a==b.prior.a && !prior.changed(b.prior) && old_sealed==b.old_sealed;
    }
    void observe() {
        auto p=pins();
        if (p.changed(prior)) row(now,"P",p.a,p.s,p.oe,p.we,p.drive);
        if (p.s && !p.oe && (!prior.s || prior.oe || p.a!=prior.a)) {
            launch=now;
            mem.visiting=p.a&3; mem.recent=0;
            if (p.a==0) { scan=now; ++st.passes; }
        }
        if (p.s && now-launch==60)
            row(now,"S",p.a,top.p_hit.get<unsigned>(),top.p_dq__out.get<unsigned>());
        if (!prior.we && p.we) {
            if (!p.s || !p.drive || p.a!=prior.a) throw std::runtime_error("unqualified write edge");
            unsigned value=top.p_dq__out.get<unsigned>();
            mem.write(p.a,value);
            ++st.rises;
            row(now,"W",p.a,value,mem.errors(p.a&3));
        }
        if (prior.s && !p.s) mem.visiting=-1;
        bool sealed=top.p_sealed.get<unsigned>();
        if (!old_sealed && sealed) {
            unsigned count=top.p_count.get<unsigned>();
            ++st.sealed; st.positive+=count!=0;
            row(now,"R",count);
        }
        if (now-scan==2500) row(now,"C",top.p_proposed.get<unsigned>());
        unsigned command=top.p_step.get<unsigned>();
        if (now-scan==2700) row(now,"I",command);
        if (int(command)!=installed) { ++st.switches; installed=command; }
        old_sealed=sealed; prior=p;
    }
    void simulate(const std::vector<Parent>& hits, size_t &i, int stop) {
        while (now<stop) {
            int len=std::min(10,stop-now);
            if (prior.s) {
                if (prior.drive || now-launch>=100) st.write+=len;
                else st.read+=len;
            }
            if (installed==1) st.fast+=len;
            while (i<hits.size() && hits[i].t<now+len) {
                const auto &h=hits[i++];
                if (h.t<now) throw std::runtime_error("input order");
                mem.toggle(h.t,h.word,h.bit);
                if (h.other>=0) mem.toggle(h.t,(h.word+1)%4,h.other);
                row(h.t,"H",mem.errors(0),mem.errors(1),mem.errors(2),mem.errors(3));
            }
            now+=len;
            if (now==stop) break;  // half-open horizon; edge at stop is pending
            edge();
        }
    }
    void edge() {
        read_bus();
        top.p_clk.set(false); top.step();
        top.p_clk.set(true); top.step();
        // Register commits precede the external combinational pin observer.
        // A second eval at the same clock level adds no clock edge or ns.
        top.step();
        observe();
    }
    void finish(std::ostream &o) const {
        o << "M " << mem.first << ' ' << st.passes << ' ' << st.read << ' ' << st.write
          << ' ' << st.rises << ' ' << st.sealed << ' ' << st.positive << ' '
          << st.switches << ' ' << st.fast << ' ' << installed;
        for (int w=0;w<4;++w) o << ' ' << mem.errors(w);
        o << '\n';
    }
};

int main(int argc,char **argv) {
    if (argc!=3) { std::cerr<<"usage: pins input output\n"; return 2; }
    std::ifstream input(argv[1]); std::ofstream out(argv[2]);
    if (!input || !out) return 2;
    Bench prefix;
    std::vector<Parent> empty;
    size_t none=0;
    prefix.reset();
    prefix.simulate(empty,none,prefix_time);
    // Prefix excludes the rising edge that launches the first trial-specific scan.
    std::string id;
    int horizon,n,literal,trace_from;
    while (input>>id>>horizon>>n>>literal>>trace_from) {
        std::vector<Parent> hits(n);
        for (auto &h:hits) if (!(input>>h.t>>h.word>>h.bit>>h.other)) return 2;
        Bench b;
        out << "T " << id << '\n';
        size_t i=0;
        if (literal) {
            if (trace_from==0) b.out=&out;
            b.reset();
            if (trace_from==prefix_time) {
                b.simulate(hits,i,prefix_time);
                if (!b.matches(prefix))
                    throw std::runtime_error("literal checkpoint differs");
                b.out=&out;
                b.edge();
            }
        } else {
            if (trace_from!=prefix_time || horizon<=prefix_time || (!hits.empty() && hits.front().t<prefix_time))
                throw std::runtime_error("invalid prefix reuse");
            b.copy_from(prefix);
            b.out=&out;
            b.edge();
        }
        b.simulate(hits,i,horizon);
        if (i!=hits.size()) throw std::runtime_error("unconsumed events");
        b.finish(out);
    }
    if (!input.eof() || !out) return 2;
}
