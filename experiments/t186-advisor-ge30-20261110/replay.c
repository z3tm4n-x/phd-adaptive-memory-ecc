/* Independent executor; only the author's generator is shared for paired inputs.
   Compile with -I /path/to/verified/private/sources. */
#define main private_author_main
#include "advisor_sanity_model.c"
#undef main
#include <assert.h>
#include <inttypes.h>
#include <limits.h>

typedef int64_t Tick;
typedef struct { Tick t; int word, bit, next; } Hit;
typedef struct { int kind, cap, k_ppm; const char *name; } Rule;
enum { FIXED, AGE_HOLD, AGE_LADDER, CELL_HOLD, CELL_LADDER };
static const Rule rules[] = {
    {FIXED,4,0,"fixed4"}, {AGE_HOLD,32,0,"age32"}, {AGE_HOLD,64,0,"age64"},
    {AGE_LADDER,512,3360,"age3360_512"}, {AGE_LADDER,512,1680,"age1680_512"},
    {AGE_LADDER,128,1680,"age1680_128"}, {FIXED,1,0,"fixed1"},
    {CELL_HOLD,32,0,"cell32"}, {CELL_HOLD,64,0,"cell64"}, {CELL_LADDER,512,1680,"cell_ladder"}
};
typedef struct { int w, physical; Tick L,T,read,repair,drain; int *rank; } Port;
typedef struct { uint64_t mask; int first,last,listed,due; } Word;
typedef struct { Word *word; int *list,*carry; int count,ncarry,ndue;
                 Tick *write_starts,recent[2048]; int nwrite,front,nrecent; } Bank;
typedef struct {
    Tick fail_at,passes,reads,repairs,switches,fast,scan,last_end,tail_first,open_tail;
    Tick partial,invalid_passes,aperture_hits,max_writes_window;
} Stat;
typedef struct { Tick last_detection,last_bad; int step; } State;

static Tick earlier(Tick a, Tick b) { return a<b?a:b; }
static Tick ceil_pos(Tick a, Tick b) { return a<=0?0:1+(a-1)/b; }
static Tick offset(const Port *p,int j) {
    return p->physical ? 1400*(j/2)+520*(j%2) : (Tick)j*p->L/p->w;
}
static int prefix(const Port *p,Tick length) {
    if(length>=p->L) return p->w;
    int lo=0,hi=p->w;
    while(lo<hi){ int m=(lo+hi)/2; if(offset(p,m)<length) lo=m+1; else hi=m; }
    return lo;
}
static int registered_cells(const Port *p,const Rule *rule,int level) {
    if(rule->kind==CELL_HOLD) return (int)ceil_pos(300000000000LL,rule->cap*p->L);
    /* ceil(((level*L/k+2J)/xi_minus+L)/(512L)), exact rational in ns. */
    __int128 num=((__int128)level*p->L*1000000+rule->k_ppm)*100000
                 +(__int128)p->L*rule->k_ppm*99999;
    __int128 den=(__int128)rule->cap*p->L*rule->k_ppm*99999;
    return (int)((num+den-1)/den);
}

/* Select the gap leaving this actual sweep, and the first possible tick of
   another selection if no further repair/invalid is produced. */
static int choose(const Port *p,const Rule *rule,State *s,Tick round,Tick det,int bad,Tick *change) {
    Tick now=round*p->L;
    *change=LLONG_MAX;
    if(rule->kind==FIXED) return rule->cap;
    if(rule->kind==AGE_HOLD || rule->kind==AGE_LADDER){
        Tick age=now-s->last_detection;
        if(det>=0){ s->last_detection=det; *change=now+p->L; return 1; }
        if(rule->kind==AGE_HOLD){
            if(age>=300060000000LL) return rule->cap;
            *change=s->last_detection+300060000000LL;
            return 1;
        }
        int level=1;
        while(level<rule->cap && age>=ceil_pos((Tick)(2*level)*p->L*1000000,rule->k_ppm))
            level*=2;
        if(level<rule->cap)
            *change=s->last_detection+ceil_pos((Tick)(2*level)*p->L*1000000,rule->k_ppm);
        return level;
    }
    int anchor=rule->cap;
    if(round && (det>=0 || bad)) s->last_bad=ceil_pos(round,anchor);
    int step=s->step;
    if(round%anchor==0){
        Tick z=round/anchor-s->last_bad;
        step=1;
        if(rule->kind==CELL_HOLD){
            if(z>=registered_cells(p,rule,anchor)) step=anchor;
        } else {
            while(step<anchor && z>=registered_cells(p,rule,2*step)) step*=2;
        }
    } else if(rule->kind==CELL_LADDER && (det>=0 || bad)) step=1;
    if(step<anchor && !bad){
        int target=rule->kind==CELL_HOLD?anchor:2*step;
        *change=(s->last_bad+registered_cells(p,rule,target))*anchor*p->L;
    }
    return step;
}

static void watch(Stat *z,uint64_t mask,Tick t) {
    if((mask & (mask-1)) && t<z->fail_at) z->fail_at=t;
}
/* Shortened extended Hamming on 1..38 and global parity at 39.
   Following the reference continuation, detected double errors do not write.
   Beyond radius one the model is charged even on a miscorrection. */
static uint64_t correction(uint64_t mask,int *due) {
    *due=0;
    if(!(mask & (mask-1))) return mask;
    unsigned syndrome=0;
    for(uint64_t a=mask & ((UINT64_C(1)<<38)-1);a;a&=a-1)
        syndrome^=(unsigned)__builtin_ctzll(a)+1;
    if(__builtin_parityll(mask) && syndrome<=38)
        return UINT64_C(1)<<((syndrome?syndrome:39)-1);
    *due=(syndrome!=0);
    return 0;
}
static void apply(Word *w,const Hit *hits,int *i,Tick limit,Stat *z) {
    while(*i>=0 && hits[*i].t<limit){
        const Hit *h=&hits[*i];
        w->mask^=UINT64_C(1)<<h->bit;
        watch(z,w->mask,h->t);
        *i=h->next;
    }
}
static void enlist(Bank *b,int w) {
    if(!b->word[w].listed){
        b->word[w].listed=1;
        b->word[w].first=b->word[w].last=-1;
        b->list[b->count++]=w;
    }
}
static int tick_order(const void *a,const void *b){
    Tick x=*(const Tick*)a,y=*(const Tick*)b;
    return (x>y)-(x<y);
}
static void track_peak(Bank *b,Stat *s){
    if(b->nwrite>1) qsort(b->write_starts,b->nwrite,sizeof(Tick),tick_order);
    for(int j=0;j<b->nwrite;j++){
        Tick t=b->write_starts[j];
        while(b->nrecent && t-b->recent[b->front]>=1000260){
            b->front=(b->front+1)%2048;b->nrecent--;
        }
        assert(b->nrecent<2048);
        b->recent[(b->front+b->nrecent)%2048]=t;b->nrecent++;
        if(b->nrecent>s->max_writes_window)s->max_writes_window=b->nrecent;
    }
    b->nwrite=0;
}

/* Enumerate words carrying new hits or correctable residuals. Persistent
   detected words are counted without executing billions of identical reads. */
static void scan(const Port *p,Bank *b,Hit *hits,int n,int *next,Tick start,Stat *z,Tick *det,int *bad) {
    Tick cut=earlier(start+p->L,p->T);
    for(int i=0;i<b->ncarry;i++) enlist(b,b->carry[i]);
    b->ncarry=0;
    while(*next<n && hits[*next].t<cut){
        int i=(*next)++,w=hits[i].word;
        enlist(b,w);
        if(b->word[w].last>=0) hits[b->word[w].last].next=i;
        else b->word[w].first=i;
        b->word[w].last=i; hits[i].next=-1;
    }
    int untouched_due=b->ndue;
    for(int j=0;j<b->count;j++){
        int w=b->list[j],i=b->word[w].first;
        Word *x=&b->word[w]; untouched_due-=x->due; b->ndue-=x->due;
        Tick read=start+offset(p,p->rank[w]);
        apply(x,hits,&i,earlier(read,cut),z);
        if(read<cut){
            int due=0;
            uint64_t bit=correction(x->mask,&due);
            Tick release=read+p->read+(bit?p->repair:0);
            if(bit){
                z->repairs++;
                if(p->physical && read+p->read<p->T) b->write_starts[b->nwrite++]=read+p->read;
            }
            for(int k=i;k>=0 && hits[k].t<release;k=hits[k].next) z->aperture_hits++;
            apply(x,hits,&i,earlier(release,cut),z);
            if(release<=cut){
                x->mask^=bit; watch(z,x->mask,release);
                if(bit && release>*det) *det=release;
                *bad|=due;
            }
        }
        apply(x,hits,&i,cut,z);
        if(correction(x->mask,&x->due)) b->carry[b->ncarry++]=w;
        b->ndue+=x->due; x->listed=0;
    }
    *bad|=untouched_due>0;
    if(p->physical) track_peak(b,z);
    b->count=0;
}
static Stat replay(const Port *p,Bank *b,Hit *hits,int n,const Rule *rule,int skip) {
    memset(b->word,0,(size_t)p->w*sizeof(Word));
    b->count=b->ncarry=b->ndue=b->nwrite=b->front=b->nrecent=0;
    Stat z={.fail_at=LLONG_MAX};
    State state={.step=rule->kind==FIXED?rule->cap:1};
    Tick round=0; int i=0;
    while(round*p->L<p->T){
        Tick start=round*p->L,end=earlier(start+p->L,p->T);
        Tick hit=i<n?hits[i].t:p->T;
        int empty=!b->ncarry && hit>=end;
        Tick det=-1, change=LLONG_MAX;
        int bad=empty && b->ndue>0;
        if(!empty) scan(p,b,hits,n,&i,start,&z,&det,&bad);
        int step=state.step;
        if(start+p->drain<p->T) step=choose(p,rule,&state,round,det,bad,&change);
        Tick gap=step*p->L, m=1;
        if(skip && empty && end-start==p->L){
            m=1+(hit-end)/gap;
            if(change!=LLONG_MAX)
                m=earlier(m,change<=start?1:ceil_pos(change-start,gap));
            if(bad && (rule->kind==CELL_HOLD || rule->kind==CELL_LADDER) && step!=1) m=1;
        }
        assert(m>=1);
        if(bad && round+(m-1)*step && rule->kind>=CELL_HOLD)
            state.last_bad=ceil_pos(round+(m-1)*step,rule->cap);
        z.switches+=step!=state.step; state.step=step;
        z.passes+=m; z.reads+=(m-1)*p->w+prefix(p,end-start);
        z.scan+=(m-1)*p->L+(end-start);
        z.last_end=end+(m-1)*gap;
        if(end-start<p->L) z.partial=prefix(p,end-start);
        if(bad) z.invalid_passes+=m;
        Tick next_start=start+m*gap;
        if(step==1 && rule->kind!=FIXED) z.fast+=earlier(next_start,p->T)-start;
        round+=m*step;
    }
    /* The last scheduled word can precede T by a whole idle interval. */
    while(i<n){
        Word *w=&b->word[hits[i].word];
        w->mask^=UINT64_C(1)<<hits[i].bit; watch(&z,w->mask,hits[i].t); i++;
        z.open_tail++;
    }
    z.tail_first=z.fail_at!=LLONG_MAX && z.fail_at>=z.last_end;
    return z;
}

static Port port(int w,Tick L,Tick T,int physical){
    Port p={.w=w,.physical=physical,.L=L,.T=T,.read=physical?240:0,.repair=physical?260:0,
            .drain=physical?L-300:L,.rank=calloc((size_t)w,sizeof(int))};
    for(int j=0;j<w;j++) p.rank[physical?(3*j)%w:j]=j;
    return p;
}
static Bank bank(int w){
    Bank b={.word=calloc((size_t)w,sizeof(Word)),.list=malloc((size_t)w*sizeof(int)),
            .carry=malloc((size_t)w*sizeof(int)),.write_starts=malloc((size_t)w*sizeof(Tick))};
    assert(b.word && b.list && b.carry && b.write_starts);return b;
}
static void selftest(void){
    Port p=port(8,5600,20001,1);
    Bank b=bank(8);
    Hit idle[]={{5001,0,0,0},{5001,3,3,0},{19000,0,1,0},{19000,6,2,0}};
    Stat a=replay(&p,&b,idle,4,&rules[0],1);
    assert(a.fail_at==19000 && a.tail_first && a.passes==1 && a.reads==8);
    Up original_hits[4]; int err[8],dirty[8];double arrivals[8],np;
    for(int j=0;j<4;j++)
        original_hits[j]=(Up){(double)idle[j].t/1.e9,idle[j].word,idle[j].bit};
    for(int w=0;w<8;w++)err[w]=-1;
    assert(sim(original_hits,4,0,22400.e-9,0,5600.e-9,8,20001.e-9,err,arrivals,dirty,&np)==0);
    idle[2].bit=0;
    assert(replay(&p,&b,idle,4,&rules[0],1).fail_at==LLONG_MAX);
    p.T=11300;
    Hit busy[]={{1,0,0,0},{1,3,5,0},{5650,0,1,0},{5650,6,2,0}};
    a=replay(&p,&b,busy,4,&rules[6],1);
    assert(a.fail_at==5650 && a.passes==3 && a.reads==17 && a.partial==1 && a.repairs==4);
    free(b.word); free(b.carry); free(b.list); free(b.write_starts); free(p.rank);
    /* At real W and clock, a short trace spans both the 300 s gates and the
       first ladder upgrades. Walk every scheduled sweep as an oracle for skips. */
    p=port(65536,45875200,720000000200LL,1); b=bank(p.w);
    Hit trace[]={{3,0,0,0},{3,3,1,0},{325000000001LL,129,2,0},
                 {325000000001LL,15,4,0},{610000000001LL,9,2,0},
                 {610000000001LL,12,3,0},{610000000030LL,12,7,0},
                 {719999999999LL,27,2,0}};
    for(size_t k=0;k<sizeof rules/sizeof *rules;k++){
        Stat rapid=replay(&p,&b,trace,8,&rules[k],1);
        Stat walk=replay(&p,&b,trace,8,&rules[k],0);
        assert(rapid.fail_at==walk.fail_at && rapid.passes==walk.passes && rapid.reads==walk.reads
               && rapid.repairs==walk.repairs && rapid.fast==walk.fast && rapid.switches==walk.switches
               && rapid.scan==walk.scan && rapid.open_tail==walk.open_tail
               && rapid.max_writes_window==walk.max_writes_window);
    }
    free(b.word); free(b.carry); free(b.list); free(b.write_starts); free(p.rank);
    puts("PASS: tail, cancellation, finite write, post-failure, partial pass, all ten rules vs sweep-by-sweep");
}
#ifndef REPLAY_LIBRARY
int main(int argc,char **argv){
    if(argc==2 && !strcmp(argv[1],"--test")){ selftest(); return 0; }
    if(argc<4){fprintf(stderr,"replay profile trials ideal|ge [--step]\n");return 2;}
    FILE *f=fopen(argv[1],"r"); if(!f){perror(argv[1]);return 2;}
    int nseg=0, trials=atoi(argv[2]), phys=!strcmp(argv[3],"ge");
    Seg *segments=malloc(400000*sizeof(Seg)); double area=0;
    while(nseg<400000){
        Seg *s=&segments[nseg];
        if(fscanf(f,"%lf %lf %lf %lf",&s->t0,&s->t1,&s->r0,&s->r1)!=4) break;
        area+=(s->t1-s->t0)*(s->r0+s->r1)/2;nseg++;
    }
    fclose(f);
    Port p=port(phys?65536:656,phys?45875200:12845056,315576000000000000LL,phys);
    Bank b=bank(p.w);
    int cap=(int)(area*3+200000),nr=phys?10:6;
    Up *src=malloc((size_t)cap*sizeof(Up));Hit *hits=malloc((size_t)cap*sizeof(Hit));
    assert(src && hits); seed(1); MARKS=2;
    puts("trial rule flips fail first_ns passes reads repairs fast_ns switches scan_ns partial_reads idle_tail_hits tail_first invalid_passes aperture_hits max_writes_window");
    for(int trial=0;trial<trials;trial++){
        int n=gen(segments,nseg,src,cap,p.w,39,315576000.0);
        for(int j=0;j<n;j++)
            hits[j]=(Hit){.t=(Tick)((long double)src[j].t*1000000000.L),.word=src[j].w,.bit=src[j].b};
        for(int ri=0;ri<nr;ri++){
            Stat s=replay(&p,&b,hits,n,&rules[ri],argc==4);
            printf("%d %s %d %d",trial,rules[ri].name,n,s.fail_at!=LLONG_MAX);
            Tick vals[]={s.fail_at==LLONG_MAX?-1:s.fail_at,s.passes,s.reads,s.repairs,s.fast,s.switches,s.scan,s.partial,
                         s.open_tail,s.tail_first,s.invalid_passes,s.aperture_hits,s.max_writes_window};
            for(size_t j=0;j<sizeof vals/sizeof *vals;j++) printf(" %"PRId64,vals[j]);
            puts("");
        }
    }
    free(src);free(hits);free(b.word);free(b.carry);free(b.list);free(b.write_starts);free(p.rank);free(segments);
    return 0;
}
#endif
