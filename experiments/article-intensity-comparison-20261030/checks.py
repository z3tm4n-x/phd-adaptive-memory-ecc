"""Directed checks of the new substitutions; no replay of the accepted small16."""
from decimal import Decimal, localcontext, ROUND_CEILING, ROUND_FLOOR
from fractions import Fraction as F
from math import nextafter, inf
import unittest
import calculation as c


def decimal_lower(old, p):
    """Independent high-precision arithmetic and cell counts for the five witnesses."""
    W,d,r,_,delta,_ = c.parameters(old)
    with localcontext() as ctx:
        ctx.prec=110
        def dec(q):
            return Decimal(q.numerator)/Decimal(q.denominator)
        dt,dd,dp,delay,rr=map(dec,(c.T,d,p,delta,r))
        nu=dec(F(c.N,c.DREF)*c.BREF)
        begin=(dt-dd)/2
        parts=[(Decimal(0),begin,nu),(begin,begin+dd,nu*rr),(begin+dd,dt,nu)]
        hazard=Decimal(0); counts=[]
        for a,b,intensity in parts:
            # Decimal rounding is independent of the Fraction floor/ceil in the accepted helper.
            first=max(W,int(((a+dp-delay)*W/dp).to_integral_value(rounding=ROUND_CEILING)))
            last=int((b*W/dp).to_integral_value(rounding=ROUND_FLOOR))
            count=max(0,last-first+1); counts.append(count)
            mu=intensity*(dp-delay)
            hazard+=count*dec(c.BW)*mu*mu*(-mu).exp()
        return Decimal(1)-(-hazard).exp(), counts


class DirectedChecks(unittest.TestCase):
    def test_r1_three_roots_equal_for_each_service(self):
        for rule in ('B','I','C'):
            for delta in (F(0),F(1,10_000_000),F(1,5_000_000)):
                s=c.profile_statistics(1048576,F(86400),F(1))
                self.assertEqual(s['S_mean'],s['S_event'])
                self.assertEqual(s['S_event'],s['S_peak'])
                roots=[c.root(s[k],1048576,delta,rule) for k in ('S_mean','S_event','S_peak')]
                self.assertEqual(len(set(roots)),1)

    def test_zero_delta_and_B_have_no_transverse_term(self):
        W,d,r=1048576,F(86400),F(100)
        s=c.profile_statistics(W,d,r)['S_event']
        p=c.EPS/(c.BW/W*s)
        for rule in ('B','I','C'):
            self.assertEqual(c.root(s,W,F(0),rule),p)
        self.assertEqual(c.root(s,W,F(1,5_000_000),'B'),p)
        self.assertEqual(c.upper(s,p,W,F(0),'C'),c.EPS)

    def test_per_bit_normalization_and_exposure(self):
        one=c.profile_statistics(131072,F(86400),F(1000))
        two=c.profile_statistics(262144,F(86400),F(1000))
        self.assertEqual(two['b'],2*one['b'])
        self.assertEqual(two['excess'],2*one['excess'])
        self.assertEqual(two['S_event'],4*one['S_event'])
        self.assertEqual(c.BW/262144*two['S_event'],2*c.BW/131072*one['S_event'])
        self.assertEqual(one['excess']/one['scale'],c.BREF*999*86400)
        self.assertLess(one['excess'],one['global_cap'])
        self.assertGreater(one['S_global'],one['S_event'])

    def test_profile_bound_and_empty_family_rejected(self):
        for d in (F(10800),F(86400),F(864000)):
            s=c.profile_statistics(1048576,d,F(100))
            self.assertEqual(s['S_event'],s['b']**2*(c.T-d)+s['peak']**2*d)
            self.assertLessEqual(s['S_event'],s['S_global'])
        with self.assertRaises(AssertionError):
            c.profile_statistics(1048576,F(864000),c.RMAX)

    def test_round_down_is_greatest_binary64(self):
        for exact in (F(1,10),F(2,3),F(2)**-40,F(100_000,3)):
            selected=c.binary64_down(exact)
            self.assertLessEqual(selected,exact)
            self.assertGreater(F(nextafter(float(selected),inf)),exact)

    def test_distinct_empty_and_rounding_statuses(self):
        W,cost,delta,rule=1,F(1,10),F(1,10),'C'
        impossible_S=2*c.EPS/(c.BW*delta)
        out=c.prescription(impossible_S,impossible_S,W,cost,delta,rule,'event')
        self.assertEqual(out['status'],'nonpositive_root')
        self.assertIsNone(out['candidate_bus_fraction'])
        boundary_S=c.EPS/(c.BW*c.kernel(cost,W,delta,rule))
        at=c.prescription(boundary_S,boundary_S,W,cost,delta,rule,'event')
        self.assertEqual(at['status'],'rounding_loses_resource_boundary')
        below=c.prescription(2*boundary_S,2*boundary_S,W,cost,delta,rule,'event')
        self.assertEqual(below['status'],'positive_root_resource_infeasible')
        self.assertFalse(below['actual_profile_U_applicable'])

    def test_full_horizon_edges_against_enumeration(self):
        for end in (F(1,20),F(1),F(11,10),F(13,10),F(2)):
            for delta in (F(0),F(1,10)):
                W,P,cost=3,F(3,5),F(1,10)
                starts=[]; j=0
                while j*P/W < end:
                    starts.append(j*P/W); j+=1
                occupied=sum((min(cost,end-t) for t in starts),F(0))
                q=c.horizon_reservation(W,P,cost,delta,end)
                self.assertEqual(q['started_actions'],len(starts))
                self.assertEqual(F(q['reserved_to_T_s']['exact']),occupied)
                self.assertEqual(q['completed_actions'],sum(t+delta<=end for t in starts))

    def test_operation_smallness_only_when_both_feasible(self):
        for old in c.ACCEPTED['sensitivity']:
            W,d,r,cost,delta,rule=c.parameters(old)
            s=c.profile_statistics(W,d,r)['S_event']
            p0=c.root(s,W,F(0),rule); pd=c.root(s,W,delta,rule)
            if pd>=W*cost/c.RHO:
                self.assertGreaterEqual(pd/p0,F(W,W+2))
                self.assertLessEqual(delta/pd,c.RHO/W)
            if old['label']=='operation c=1us':
                self.assertLess(p0,W*cost/c.RHO)

    def test_new_main_lower_independent_decimal(self):
        unique=set()
        for old in c.ACCEPTED['sensitivity']:
            if old['label']!='main':
                continue
            W,d,r,_,delta,rule=c.parameters(old)
            s=c.profile_statistics(W,d,r)['S_mean']
            p=c.binary64_down(c.root(s,W,delta,rule))
            key=(W,p,delta,d,r)
            if key in unique:
                continue
            unique.add(key)
            enclosure,counts=c.new_lower(*key)
            independent,other_counts=decimal_lower(old,p)
            self.assertEqual(counts,other_counts)
            self.assertLessEqual(Decimal(enclosure['lower']),independent)
            self.assertGreaterEqual(Decimal(enclosure['upper']),independent)
            self.assertEqual(F(enclosure['lower'])>c.EPS,r!=1)
        self.assertEqual(len(unique),10)

    def test_exact_resource_boundary_brackets(self):
        W,d,cost,delta=1048576,F(86400),F(1,5_000_000),F(1,5_000_000)
        for kind in ('event','peak'):
            lo,hi=c.resource_ratio_boundary(W,d,cost,delta,'C',kind)
            for r,feasible in ((lo,True),(hi,False)):
                s=c.profile_statistics(W,d,r)['S_'+kind]
                self.assertEqual(c.root(s,W,delta,'C')>=W*cost,feasible)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(DirectedChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    return result.testsRun


if __name__=='__main__':
    run()
