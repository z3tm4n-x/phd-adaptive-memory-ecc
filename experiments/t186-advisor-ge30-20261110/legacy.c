/* Full-horizon audit with exactly the original binary64 clock recurrences.
   The independent integer-clock calculation is a separate sensitivity. */
#define REPLAY_LIBRARY
#include "replay.c"

static Tick stamp(double t){ return (Tick)((long double)t*1.e9L); }
static void births(Word *x,const Up *up,const int *link,int *j,double limit,int inclusive,Stat *s){
    while(*j>=0 && (up[*j].t<limit || (inclusive && up[*j].t==limit))){
        const Up *a=&up[*j];
        x->mask ^= UINT64_C(1)<<a->b;
        watch(s,x->mask,stamp(a->t)); *j=link[*j];
    }
}
static Stat full(const Up *up,int n,int mode,double p1,double p2,int W,double L,double T,Bank *b,int *link){
    Stat z={.fail_at=LLONG_MAX}; double t=0,td=0,previous=mode==0?p1:L;
    long double fast=0;
    memset(b->word,0,(size_t)W*sizeof(Word)); b->ncarry=b->count=b->ndue=0;
    int i=0;
    while(t<T){
        const double P=period(mode,t-td,L,p1,p2), end=t+L, cut=fmin(end,T);
        double tn=i<n?up[i].t:1e300, step=P, next;
        Tick count=1;
        if(!b->ncarry && tn>=end){
            double limit=1e300;
            if(mode==1 && t-td<p1) limit=ceil((td+p1-t)/L);
            if(mode==3){
                double age=t-td;
                if(p1*age<L) limit=ceil((td+L/p1-t)/L);
                else if(p1*age<p2){
                    double level=2*P; if(level>p2*1.0000001) level=p2;
                    limit=fmax(1,ceil((td+level/p1-t)/P));
                }
            }
            double m=fmax(1,fmin(ceil((T-t)/P),fmin(limit,floor((tn-L-t)/P)+1)));
            count=(Tick)m; next=t+m*P;
        } else {
            for(int k=0;k<b->ncarry;k++) enlist(b,b->carry[k]);
            b->ncarry=0;
            while(i<n && up[i].t<cut){
                Word *x=&b->word[up[i].w]; enlist(b,up[i].w);
                if(x->last<0) x->first=i; else link[x->last]=i;
                x->last=i;link[i]=-1;i++;
            }
            int detected=0;double latest=td;
            for(int k=0;k<b->count;k++){
                int w=b->list[k];Word *x=&b->word[w];int j=x->first;
                double rw=t+(double)w*L/W;
                if(rw<T){
                    births(x,up,link,&j,rw,1,&z);
                    int due;uint64_t bit=correction(x->mask,&due);
                    if(bit){ z.repairs++; detected=1; if(rw>latest)latest=rw; x->mask^=bit; }
                }
                births(x,up,link,&j,cut,0,&z);x->listed=0;
                if(correction(x->mask,&x->due)) b->carry[b->ncarry++]=w;
            }
            b->count=0;td=latest;
            if(mode && detected)step=L;
            next=t+step;
        }
        double final=t+(double)(count-1)*step;
        int prefix_words=W;
        if(final+L>T){
            prefix_words=0;while(prefix_words<W && final+(double)prefix_words*L/W<T)prefix_words++;
            z.partial=prefix_words;
        }
        z.reads+=(count-1)*W+prefix_words;z.passes+=count;
        z.last_end=stamp(fmin(T,final+L));
        if(step!=previous) z.switches++;
        if(mode && step==L) fast+=(long double)fmin(T,next)-t;
        previous=step; t=next;
    }
    while(i<n){
        Word *x=&b->word[up[i].w];
        x->mask^=UINT64_C(1)<<up[i].b;watch(&z,x->mask,stamp(up[i].t)); i++;z.open_tail++;
    }
    z.tail_first=z.fail_at!=LLONG_MAX && z.fail_at>=z.last_end;
    z.fast=(Tick)llroundl(fast*1.e9L);
    return z;
}
int main(int argc,char **argv){
    if(argc!=4)return 2;
    const int W=656,trials=atoi(argv[2]);const double L=.012845056,T=315576000.;
    FILE *f=fopen(argv[1],"r");if(!f)return 2;
    int ns=0;double area=0;Seg *ss=malloc(400000*sizeof(Seg));
    while(ns<400000 && fscanf(f,"%lf %lf %lf %lf",&ss[ns].t0,&ss[ns].t1,&ss[ns].r0,&ss[ns].r1)==4){
        Seg a=ss[ns++]; area+=(a.t1-a.t0)*(a.r0+a.r1)/2;
    }
    fclose(f);
    int n_rules=0,mode[6];double p1[6],p2[6];char label[64];
    f=fopen(argv[3],"r");if(!f)return 2;
    while(n_rules<6 && fscanf(f,"%d %lf %lf %63s",&mode[n_rules],&p1[n_rules],&p2[n_rules],label)==4)n_rules++;
    fclose(f);assert(n_rules==6);
    int cap=(int)(area*3+200000);Up *up=malloc(cap*sizeof(Up));int *link=malloc(cap*sizeof(int));
    Bank b=bank(W);int *err=malloc(W*sizeof(int)),*lw=malloc(W*sizeof(int));double *arr=malloc(W*sizeof(double));
    for(int w=0;w<W;w++)err[w]=-1;
    seed(1);MARKS=2;
    puts("trial rule raw_fail corrected_fail tail_first passes reads repairs fast_ns switches tail_hits");
    for(int j=0;j<trials;j++){
        int n=gen(ss,ns,up,cap,W,39,T);
        for(int k=0;k<n_rules;k++){
            double truncated;
            int source=sim(up,n,mode[k],p1[k],p2[k],L,W,T,err,arr,lw,&truncated);
            Stat z=full(up,n,mode[k],p1[k],p2[k],W,L,T,&b,link);
            printf("%d %s %d %d %"PRId64" %"PRId64" %"PRId64" %"PRId64" %"PRId64" %"PRId64" %"PRId64"\n",
                   j,rules[k].name,source,z.fail_at!=LLONG_MAX,z.tail_first,z.passes,z.reads,z.repairs,z.fast,z.switches,z.open_tail);
        }
    }
    return 0;
}
