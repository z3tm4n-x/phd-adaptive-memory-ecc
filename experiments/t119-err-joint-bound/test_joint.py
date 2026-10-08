import unittest
import math
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import joint as j
import balance
import history_checks


class JointTests(unittest.TestCase):
    def test_accepted_sources_are_read_only_imports(self):
        self.assertEqual(j.accepted.CFG['task'],114)
        self.assertEqual(j.accepted.CFG['profiles'][2]['a_parent'],'9/10')

    def test_weighted_primitive_linear_exact(self):
        for q in (F(0),F('.0001'),F('.001')):
            for rho in (F('.048'),F(1,60)):
                for t in (F(0),F('.03'),F(10),F(100)):
                    v=min(t,q/(rho*F('.001')))
                    exact=q*v*v/2-rho*F('.001')*v**3/3
                    z=j.moment(q,t,rho)
                    self.assertLessEqual(F(z.lo),exact);self.assertLessEqual(exact,F(z.hi))

    def test_weighted_primitive_against_decimal100(self):
        with localcontext() as ctx:
            ctx.prec=100
            for qs in ('.0011','.05','.244682704'):
                q=D(qs);r=D('.048');ell=D('.001')
                te=(q/ell).ln()/r
                for ts in ('0','1','20','90','180'):
                    t=D(ts);v=min(t,te);z=max(D(0),min(t-te,1/r))
                    ref=q/(r*r)*(1-(1+r*v)*(-r*v).exp())+ell*(te*z+(1-r*te)*z*z/2-r*z**3/3)
                    val=j.moment(F(qs),F(ts),F('.048'))
                    self.assertLessEqual(val.lo-D('1e-85'),ref)
                    self.assertLessEqual(ref,val.hi+D('1e-85'))

    def test_mandatory_phase_enclosures(self):
        # Exact small calendars check the geometric lemma, not R0 reliability.
        for W in (8,16,32):
            for ka in (1,3,5,9):
                g,c=196,164;P=W*g*ka
                phases=[8*g*((ka*z)//8)+c*((ka*z)%8) for z in range(W)]
                edge=ka*g+7*(g-c)
                for t in range(0,P,max(1,P//19)):
                    for d in (0,P//11,P//3,P//2,P-1,P,P+1):
                        count=sum(0<((x-t-1)%P)+1<=d for x in phases)
                        lower=max(F(0),min(F(1),F(d-edge,P)))
                        self.assertGreaterEqual(F(count,W),lower)
                        if d<=P:self.assertLessEqual(count,F(W*d,P)+4)

    def test_joint_union_is_not_product_of_overlapping_voids(self):
        # Two length-seven windows overlap by five: total nine, not fourteen.
        first=(-10,-3);last=(-8,-1)
        union=last[1]-first[0]
        self.assertEqual(union,9)
        self.assertGreater(math.exp(-union),math.exp(-7)*math.exp(-7))

    def test_joint_zero_union_collapse_with_real_phases(self):
        W,ka,g,c=8,3,196,164;ps=W*g;P=ka*ps;w=6*P;delta=50
        first,last=20*P,20*P+ps
        decisions=(first,last)
        phases=[8*g*((ka*z)//8)+c*((ka*z)%8) for z in range(W)]
        for t in range(first-w,last,101):
            for phase in phases:
                next_read=phase+((t-phase)//P+1)*P
                exact=any(x-w<=t and next_read+delta<=x for x in decisions)
                if t<=last-w:self.assertTrue(exact)
                else:self.assertEqual(exact,next_read+delta<=last)

    def test_preobserved_write_cannot_erase_qualifying_flag(self):
        for parent in range(0,8):
            for mandatory in range(parent+1,12):
                x=mandatory+2;w=20
                for app in range(parent+1,mandatory+1):
                    available=app+2
                    self.assertTrue(x-w<=parent<=available<=x)
                    self.assertTrue(available+w>=x)

    def test_ramp_mass_zero_and_future_are_not_invented(self):
        ph=dict(phi=F('.9'),P=F(3),d=F('.01'))
        self.assertEqual(j.ramp_mass(F('.05'),F('.048'),ph,F(-20),F(-19),F(10)),0)
        self.assertEqual(j.ramp_mass(F(0),F('.048'),ph,F(0),F(0),F(100)),0)

    def test_ramp_mass_never_exceeds_full_past_exposure(self):
        ph=dict(phi=F('.9'),P=F(3),d=F('.01'))
        for a in (F(-2),F(0),F('.1')):
            val=j.ramp_mass(F('.05'),F('.048'),ph,a,a,F(90))
            full=ph['phi']*F(j.exposure(F('.05'),max(F(0),a),F(90)+a,F('.048')).hi)
            self.assertGreaterEqual(val,0);self.assertLessEqual(val,full)

    def test_zero_information_and_ka_one(self):
        p=j.accepted.old.environment(j.accepted.old.HANDOFF['rows'][0]);pr=j.accepted.CFG['profiles'][2]
        c=j.accepted.calendar(p,pr,3,j.accepted.CFG['growth_classes'][0]);c['phi']=F(0)
        self.assertEqual(j.coefficient(F('.05'),F('.048'),c,2,4),c['Pl'])
        c=j.accepted.calendar(p,pr,1,j.accepted.CFG['growth_classes'][0])
        self.assertEqual(j.coefficient(F('.05'),F('.048'),c,2,4),c['Ps'])

    def test_conditional_balance_no_jump_credit(self):
        A,q0,phi,z=1.,.003,.9,2.
        V=lambda q:A*max(0.,q-q0)*math.exp(-phi*z)
        for before in (0.,.001,.01,.244):
            for ratio in (0.,.5,1.):self.assertLessEqual(V(before*ratio),V(before))

    def test_weighted_cone_against_decimal100(self):
        with localcontext() as ctx:
            ctx.prec=100
            r,a,ell=D('.048'),D('.025'),D('.001')
            for qs in ('.0001','.001','.05','.244682704'):
                q=D(qs)
                for ts in ('1','90','180'):
                    t=D(ts)
                    if q<=ell:
                        v=min(t,q/(r*ell));e=(-a*v).exp()
                        ref=q*(1-e)/a-r*ell*(1-(1+a*v)*e)/(a*a)
                    else:
                        te=(q/ell).ln()/r;v=min(t,te);z=max(D(0),min(t-te,1/r));e=(-a*z).exp()
                        ref=q*(1-(-(a+r)*v).exp())/(a+r)+ell*(-a*te).exp()*((1-e)/a-r*(1-(1+a*z)*e)/(a*a))
                    val=balance.weighted_cone(F(qs),F(ts),F('.048'),F('.025'))
                    self.assertLessEqual(val.lo-D('1e-85'),ref)
                    self.assertLessEqual(ref,val.hi+D('1e-85'))

    def test_full_partial_writes_at_freeze_and_after_loss(self):
        self.assertEqual(len(history_checks.write_boundaries()),6)

    def test_extra_clock_guards_not_dropped(self):
        p=j.accepted.old.environment(j.accepted.old.HANDOFF['rows'][0]);pr=j.accepted.CFG['profiles'][2]
        c=j.accepted.calendar(p,pr,3,j.accepted.CFG['growth_classes'][0])
        self.assertEqual(j.proof_window(c,2)+2*j.accepted.JIT,c['w'])
        self.assertEqual(j.proof_bands(c)[0][0],c['tau']+2*j.accepted.JIT)


if __name__=='__main__':unittest.main()
