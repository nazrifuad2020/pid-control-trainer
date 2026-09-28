# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:41:39 2019

@author: nazri
"""

import numpy as np

from scipy import optimize

C3_Ant = [4.53678, 1149.36, 24.906]
C4_Ant = [4.35576, 1175.581, -2.071]
C5_Ant = [3.9892, 1070.617, -40.454]
C6_Ant = [4.00266, 1171.53, -48.784]

def calc_Psat(ant_param, T):
    return 10**(ant_param[0]-(ant_param[1]/(T+ant_param[2])))

def cubic_EOS(T, P, x, phase_str, k, Tc, Pc, omega):
    sigma = 1 + np.sqrt(2)
    eps = 1 - np.sqrt(2)
    chi = .07779
    psi = .45724
    
    R_GAS_CONSTANT = 8.31447e-5 # m3.bar/(mol.K)
    
    x = np.array(x)
    Tc = np.array(Tc)
    Pc = np.array(Pc)
    omega = np.array(omega)
    
    Nc = len(x)
    
    Tr = T/Tc
#    Tr = [0]*Nc
#    for i in range(Nc):
#        Tr[i] = T/Tc[i]
    
    eta = .379642 + (1.48503-(.164423-1.016666*omega)*omega)*omega
    alpha = (1 + eta*(1-np.sqrt(Tr)))**2
    
    aval = (psi*(R_GAS_CONSTANT*Tc)**2)/Pc
    bval = chi*R_GAS_CONSTANT*Tc/Pc
    
    a_alpha = 0
    D = 0
    for i in range(Nc):
        a_alpha += np.sum(x[i]*x*(1 - k[i,:])*np.sqrt((aval[i]*alpha[i])*(aval*alpha)))
        D += np.sum(x[i]*x*eta*(1 - k[i,:])*np.sqrt((aval[i]*alpha[i])*aval*Tr))
        
    b_mix = np.sum(x*bval)
    bheta = b_mix*P/(R_GAS_CONSTANT*T)
    q_mix = a_alpha/(b_mix*R_GAS_CONSTANT*T)

    zroots = np.roots([1, (sigma+eps)*bheta-1-bheta, 
                       eps*sigma*bheta**2-(eps+sigma)*bheta-(eps+sigma)*bheta**2+q_mix*bheta, 
                       -(eps*sigma*bheta**2+eps*sigma*bheta**3+q_mix*bheta**2)])
    zreal = zroots[np.where(np.isreal(zroots))]
    if phase_str == 'liq':
        Z = np.min(zreal)
    elif phase_str == 'vap':
        Z = np.max(zreal)
        
    return Z*R_GAS_CONSTANT*T/P, Z



class TWO_PHASE_SEP(object):
    F_in = 38.5
    T = 93+273.15
    zC3 = 0.1 
    zC4 = 0.2
    zC5 = 0.3
    zC6 = 0.4
    At = 0.9144**2*np.pi/4
    
    lift_liq = 0.5
    lift_vap = 0.5
    
    lift_liq_sig = 0.5
    lift_vap_sig = 0.5
    
    tau_liqvalve = 1.0
    deadtime_liqvalve = 1.5
    
    tau_vapvalve = 1.0
    deadtime_vapvalve = 2.0
    
    dt = 1.0
    
    def __init__(self):
        self.two_phase_sep_init()
        x0 = np.copy(self.xstate)
        self.fx0 = self.ode_two_phase_sep(0.0, x0)
        self.lift_liqsig_before = np.ones(1+int(self.deadtime_liqvalve/0.1))*self.lift_liq_sig
        self.lift_vapsig_before = np.ones(1+int(self.deadtime_vapvalve/0.1))*self.lift_vap_sig
        
    def two_phase_sep_init(self):
        sol = optimize.root(self.res_two_phase_sep, [31.3, 7.2, 0.05, 0.17, 0.32, 0.3, 0.33, 0.23, 6.9])
        
        Fliq_out = sol.x[0]
        Fvap_out = sol.x[1]
    
        xC3 = sol.x[2]
        xC4 = sol.x[3]
        xC5 = sol.x[4]
        xC6 = 1 - (xC3+xC4+xC5)
    
        yC3 = sol.x[5]
        yC4 = sol.x[6]
        yC5 = sol.x[7]
        yC6 = 1 - (yC3+yC4+yC5)
    
        self.P = sol.x[8]
        self.Pds = self.P - 0.344738
        self.Pmaxg = 6.6 #barg
    
        k = np.zeros([4,4])
        # molar volume in m3/mol
        vmLiq, Zliq = cubic_EOS(self.T, self.P, [xC3, xC4, xC5, xC6], 'liq', k, 
                                [369.8, 425.1, 469.7, 507.6], 
                                [42.48, 37.96, 33.70, 30.25], 
                                [0.152, 0.200, 0.252, 0.301])
        vmVap, Zvap = cubic_EOS(self.T, self.P, [yC3, yC4, yC5, yC6], 'vap', k, 
                                [369.8, 425.1, 469.7, 507.6], 
                                [42.48, 37.96, 33.70, 30.25], 
                                [0.152, 0.200, 0.252, 0.301])
    
        rhoLiq = (xC3*44.10 + xC4*58.12 + xC5*72.15 + xC6*86.18)/vmLiq #g/m3
        self.hlvl_high = 3.5
        self.hliq = 2.5 #m
        self.hlvl_low = 1.5
        liq_moles = self.hliq*self.At/vmLiq #moles
        P1 = self.P + (rhoLiq/1000)*9.81*self.hliq*1e-5 #bar
        Gf = (rhoLiq/1000.0)/1000.0
        Fvliq_out = Fliq_out*vmLiq*3600 #m3/hr
        self.Cvliq = Fvliq_out/(self.lift_liq*0.865)*np.sqrt(Gf/(P1-self.Pds))
    
        Gg = (yC3*44.10 + yC4*58.12 + yC5*72.15 + yC6*86.18)/28.9647
        Fk = 1.094/1.4
        x = (self.P-self.Pds)/self.P
        Y = 1 - x/(3*Fk*0.75)
        Fvvap_out = Fvap_out*vmVap*3600 #m3/hr
        self.Cvvap = Fvvap_out/(self.lift_vap*417*self.P*Y)*np.sqrt(Gg*self.T*Zvap/x)
        
        self.xstate = np.array([liq_moles, xC3*liq_moles, xC4*liq_moles, xC5*liq_moles])
        
    def res_two_phase_sep(self, y):
        Fliq_out = y[0]
        Fvap_out = y[1]
        xC3 = y[2]
        xC4 = y[3]
        xC5 = y[4]
        yC3 = y[5]
        yC4 = y[6]
        yC5 = y[7]
        P = y[8]
    
        PsatC3 = calc_Psat(C3_Ant, self.T)
        PsatC4 = calc_Psat(C4_Ant, self.T)
        PsatC5 = calc_Psat(C5_Ant, self.T)
        PsatC6 = calc_Psat(C6_Ant, self.T)
    
        Kc3 = PsatC3/P
        Kc4 = PsatC4/P
        Kc5 = PsatC5/P
        Kc6 = PsatC6/P
    
        xC6 = 1 - (xC3+xC4+xC5)
    
        summ = Kc3*xC3 + Kc4*xC4 + Kc5*xC5 + Kc6*xC6
    
        res1 = self.F_in - Fliq_out - Fvap_out
        res2 = self.zC3*self.F_in - xC3*Fliq_out - yC3*Fvap_out
        res3 = self.zC4*self.F_in - xC4*Fliq_out - yC4*Fvap_out
        res4 = self.zC5*self.F_in - xC5*Fliq_out - yC5*Fvap_out
        res5 = yC3 - Kc3*xC3
        res6 = yC4 - Kc4*xC4
        res7 = yC5 - Kc5*xC5
        res8 = 1.0 - summ
        res9 = P - (xC3*PsatC3 + xC4*PsatC4 + xC5*PsatC5 + xC6*PsatC6)
    
        return [res1, res2, res3, res4, res5, res6, res7, res8, res9]
    
    def ode_two_phase_sep(self, t, y):
        moles = y[0]
        molC3 = y[1]
        molC4 = y[2]
        molC5 = y[3]
    
        self.xC3 = molC3/moles
        self.xC4 = molC4/moles
        self.xC5 = molC5/moles
        self.xC6 = 1 - (self.xC3+self.xC4+self.xC5)
    
        PsatC3 = calc_Psat(C3_Ant, self.T)
        PsatC4 = calc_Psat(C4_Ant, self.T)
        PsatC5 = calc_Psat(C5_Ant, self.T)
        PsatC6 = calc_Psat(C6_Ant, self.T)
    
        self.P = self.xC3*PsatC3 + self.xC4*PsatC4 + self.xC5*PsatC5 + self.xC6*PsatC6
    
        Kc3 = PsatC3/self.P
        Kc4 = PsatC4/self.P
        Kc5 = PsatC5/self.P
        Kc6 = PsatC6/self.P
    
        summ = Kc3*self.xC3 + Kc4*self.xC4 + Kc5*self.xC5 + Kc6*self.xC6
        self.yC3 = Kc3*self.xC3/summ
        self.yC4 = Kc4*self.xC4/summ
        self.yC5 = Kc5*self.xC5/summ
        self.yC6 = Kc6*self.xC6/summ
    
        k = np.zeros([4,4])
        # molar volume in m3/mol
        vmLiq, Zliq = cubic_EOS(self.T, self.P, [self.xC3, self.xC4, self.xC5, self.xC6], 'liq', k, 
                                [369.8, 425.1, 469.7, 507.6], 
                                [42.48, 37.96, 33.70, 30.25], 
                                [0.152, 0.200, 0.252, 0.301])
        vmVap, Zvap = cubic_EOS(self.T, self.P, [self.yC3, self.yC4, self.yC5, self.yC6], 'vap', k, 
                                [369.8, 425.1, 469.7, 507.6], 
                                [42.48, 37.96, 33.70, 30.25], 
                                [0.152, 0.200, 0.252, 0.301])
    
        Gg = (self.yC3*44.10 + self.yC4*58.12 + self.yC5*72.15 + self.yC6*86.18)/28.9647
        Fk = 1.094/1.4
        if self.P >= self.Pds:
            x = (self.P-self.Pds)/self.P
        else:
            # reverse flow
            x = (self.Pds-self.P)/self.Pds
        Y = 1 - x/(3*Fk*0.75)
        if self.P >= self.Pds:
            Fvvap_out = self.lift_vap*417*self.Cvvap*self.P*Y*np.sqrt(x/(Gg*self.T*Zvap)) #m3/hr
        else:
            # reverse flow
            Fvvap_out = -1*self.lift_vap*417*self.Cvvap*self.Pds*Y*np.sqrt(x/(Gg*self.T*Zvap)) #m3/hr
    
        rhoLiq = (self.xC3*44.10 + self.xC4*58.12 + self.xC5*72.15 + self.xC6*86.18)/vmLiq #g/m3
        self.hliq = moles*vmLiq/self.At #m
        P1 = self.P + (rhoLiq/1000)*9.81*self.hliq*1e-5 #bar
        Gf = (rhoLiq/1000.0)/1000.0
        if P1 >= self.Pds:
            Fvliq_out = self.lift_liq*0.865*self.Cvliq*np.sqrt((P1-self.Pds)/Gf) #m3/hr
        else:
            # reverse flow
            Fvliq_out = -1*self.lift_liq*0.865*self.Cvliq*np.sqrt((self.Pds-P1)/Gf) #m3/hr
    
        self.Fliq_out = Fvliq_out/vmLiq/3600 #mol/s
        self.Fvap_out = Fvvap_out/vmVap/3600 #mol/s
        mol_dot = self.F_in - self.Fliq_out - self.Fvap_out
        molC3_dot = self.zC3*self.F_in - self.xC3*self.Fliq_out - self.yC3*self.Fvap_out
        molC4_dot = self.zC4*self.F_in - self.xC4*self.Fliq_out - self.yC4*self.Fvap_out
        molC5_dot = self.zC5*self.F_in - self.xC5*self.Fliq_out - self.yC5*self.Fvap_out
    
        return np.array([mol_dot, molC3_dot, molC4_dot, molC5_dot])
    
    def ode_valve_liq(self, t, y):
        delayed_sig = self.lift_liqsig_before[0]
        return (delayed_sig - self.lift_liq)/self.deadtime_liqvalve
    
    def ode_valve_vap(self, t, y):
        delayed_sig = self.lift_vapsig_before[0]
        return (delayed_sig - self.lift_vap)/self.deadtime_vapvalve
    
    def set_inlet_disturbance(self, T=95.0):
        self.T = T+273.15
        
    def unset_inlet_disturbance(self):
        self.T = 93+273.15
        
    def set_controlvalve_liq_sig(self, lift_liqvalve):
        self.lift_liq_sig = lift_liqvalve
        
    def set_controlvalve_vap_sig(self, lift_vapvalve):
        self.lift_vap_sig = lift_vapvalve
        
    def get_Pgauge(self):
        return self.P-1.01325
    
    def step(self):
        step = int(self.dt/0.1)
        x0 = np.copy(self.xstate)
        fx0 = np.copy(self.fx0)
        for i in range(1, step+1):
            
            xnew = x0 + fx0*0.1
            x0 = xnew
            fx0 = self.ode_two_phase_sep(i*0.1, x0)
            
            self.lift_liq += self.ode_valve_liq(i*0.1, self.lift_liq)*0.1
            for j in range(self.lift_liqsig_before.shape[0]-1):
                self.lift_liqsig_before[j] = self.lift_liqsig_before[j+1]
            self.lift_liqsig_before[-1] = self.lift_liq_sig
            
            self.lift_vap += self.ode_valve_vap(i*0.1, self.lift_vap)*0.1
            for j in range(self.lift_vapsig_before.shape[0]-1):
                self.lift_vapsig_before[j] = self.lift_vapsig_before[j+1]
            self.lift_vapsig_before[-1] = self.lift_vap_sig
            
        self.xstate = xnew
        self.fx0 = fx0