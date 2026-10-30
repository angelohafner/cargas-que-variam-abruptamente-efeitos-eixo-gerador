from pathlib import Path
import argparse, json, math, shutil, time
import mhi.pscad
from controller import definition, OUTPUTS
from pscad_session import get_app

ROOT=Path(__file__).resolve().parents[1]

def build(app,bess):
    name='DataCenter_Com_BESS' if bess else 'DataCenter_Sem_BESS'
    folder=ROOT/'pscad'; folder.mkdir(exist_ok=True)
    path=folder/(name+'.pscx')
    if path.exists():
        backup=ROOT/'history'/time.strftime('%Y%m%d_%H%M%S'); backup.mkdir(parents=True,exist_ok=True); shutil.copy2(path,backup/path.name)
    if any(q['name']==name for q in app.projects()): app.project(name).unload()
    if path.exists():
        assert path.resolve().parent == folder.resolve()
        path.unlink()  # A complete source backup was made above.
    p=app.create_case(name,folder=str(folder)); c=p.canvas('Main')
    p.create_definition(definition())
    p.parameters(time_duration=30,time_step=10,sample_step=100,branch_threshold=1e-8,PlotType='OUT',
                 StartType='STANDARD',SnapType='NONE',output_filename=name+'.out',
                 description='Data center 4-10 MW | '+('BESS 5 MW / 2.5 MWh | switched VSC' if bess else 'grid baseline'))
    c.parameters(size='100X100')
    def comp(n,x,y,**kw): return c.create_component('master:'+n,x,y,**kw)
    def xy(o,k): v=o.ports()[k]; return (v.x,v.y)
    def wire(*a): return c.create_wire(*a)
    def link(a,ak,b,bk): return wire(xy(a,ak),xy(b,bk))
    def sig(o,k,s):
        pt=xy(o,k); comp('datalabel',*pt,Name=s)
    def note(x,y,title,body=''): c.create_annotation(x,y,title,body)
    def meter(x,y,prefix,reverse=False):
        o=comp('multimeter',x,y,MeasP=1,MeasQ=1,RMS=1,IRMS=1,MeasV=1,MeasI=1,
            P='P'+prefix+'_MW',Q='Q'+prefix+'_Mvar',Vrms='V'+prefix+'_kV',Crms='I'+prefix+'_kA',
            VolI='V'+prefix+'_abc',CurI='I'+prefix+'_abc',TS='.001 [s]',BaseV=1,BaseA=1,S=1,Freq=60)
        if reverse:o.mirror()
        return o
    note(80,3,name,'69/13.8 kV | 60 Hz | deterministic 4-10 MW | compare identical load profiles')
    note(45,10,'REDE E TRANSFORMADOR','Scc 1000 MVA; X/R=10 | 20 MVA, 8% leakage, grounded Y-Y')
    source=comp('source_3',10,22,Name='Grid69kV',Type=6,Grnd=1,View=1,Vm='69 [kV]',f='60 [Hz]',Tc='.02 [s]')
    r=comp('resistor',20,22,Name='Grid_R',R=f'{69**2/1000/math.sqrt(101):.10f} [ohm]')
    l=comp('inductor',30,22,Name='Grid_L',L=f'{69**2/1000*10/math.sqrt(101)/(2*math.pi*60):.10f} [H]')
    link(source,'N',r,'A');link(r,'B',l,'A')
    tr=comp('xfmr-3p2w',45,22,Name='Grid_20MVA',Tmva='20 [MVA]',V1='69 [kV]',V2='13.8 [kV]',f=60,YD1=0,YD2=0,Xl=.08,CuL=.005,NLL=0,Enab=0)
    link(l,'B',tr,'N1')
    for port in ('G1','G2'):
        pt=xy(tr,port);wire(pt,(pt[0],pt[1]+5));comp('ground',pt[0],pt[1]+5)
    mg=meter(60,22,'grid');link(tr,'N2',mg,'A')
    rf=comp('resistor',72,22,Name='Feeder_R',R='.02 [ohm]')
    lf=comp('inductor',82,22,Name='Feeder_L',L='.1 [mH]')
    link(mg,'B',rf,'A');link(rf,'B',lf,'A');wire(xy(lf,'B'),(95,22),(105,22))
    ml=meter(112,22,'load');wire((105,22),xy(ml,'A'))
    load=comp('fixed_load',132,22,Name='DataCenter_PQ',PO='1 [MW]',QO=f'{math.tan(math.acos(.98))} [MVAR]',VBO=f'{13.8/math.sqrt(3)} [kV]',NP=0,NQ=0,NPB=0,NQB=0,Scale='Load_scale',NCYC=1,FR=60)
    wire(xy(ml,'B'),(124,22),(124,21),xy(load,'IA'))
    gp=xy(load,'G');wire(gp,(gp[0],gp[1]+6));comp('ground',gp[0],gp[1]+6)
    note(116,34,'CARGA AGREGADA P/Q','PF = 0.98 indutivo | controles no bloco abaixo | medidas na entrada da carga')
    print(name,'grid created',flush=True);p.save()
    if bess:
        note(238,14,'BATERIA E VSC CHAVEADO','Bateria nativa | 1.5 kV x 1.6667 kAh = 2.5 MWh nominal | 6 IGBTs + 6 diodos')
        bat=comp('battery',205,65,Name='Battery_2p5MWh',Enom='1.5 [kV]',Qrated='1.6666666667 [kA*hr]',Inom=100,SOCint=50,SOC='SOC_pct',Type=0,Qnom=.95,loss=.005,Eexp=1.03,Qexp=.4,Efull=1.10)
        wire(xy(bat,'A'),(205,35),(210,35));wire(xy(bat,'B'),(205,105),(282,105))
        rg=comp('resistor',205,110,Name='DC_reference_only',R='1e6 [ohm]');rg.rotate_right()
        ends=sorted([xy(rg,'A'),xy(rg,'B')],key=lambda a:a[1]);wire((205,105),ends[0]);wire(ends[1],(205,115));comp('ground',205,115)
        rp=comp('resistor',211,35,Name='Precharge_R',R='.5 [ohm]');wire((210,35),xy(rp,'A'))
        br=comp('breaker1',212,29,NAME='Precharge_open',RON='.0001 [ohm]',ROFF='1e8 [ohm]')
        wire((210,35),(208,35),(208,29),xy(br,'B'));wire(xy(br,'A'),(216,29),(216,35),xy(rp,'B'))
        ib=comp('ammeter',220,35,Name='Ibat_kA');wire(xy(rp,'B'),xy(ib,'N1'));wire(xy(ib,'N2'),(282,35))
        cap=comp('capacitor',227,65,Name='DC_cap',C='20000 [uF]');cap.rotate_right()
        ends=sorted([xy(cap,'A'),xy(cap,'B')],key=lambda a:a[1]);wire((227,35),ends[0]);wire(ends[1],(227,105))
        for x,s,top in [(231,'Vdc_kV',231),(201,'Vbat_kV',205)]:
            vm=comp('voltmeter',x,55,Name=s);wire((top,35),(x,35),xy(vm,'N1'));wire(xy(vm,'N2'),(x,105),(205,105))
        legs=[]
        for phase,x in zip('ABC',[240,260,280]):
            for side,yt,yb in [('H',40,61),('L',72,99)]:
                g=comp('peswitch',x+3,yt+5,Name=phase+side,L='IGBT',Type=3,SNUB=0,INTR=0,RON='.00005 [ohm]',ROFF='1e8 [ohm]',EFVD='.001 [kV]',PFB=1)
                g.flip();d=comp('peswitch',x-3,yt+7,Name='D'+phase+side,L='D',Type=0,SNUB=0,RON='.00005 [ohm]',ROFF='1e8 [ohm]',EFVD='.0008 [kV]',PFB=1)
                for o,up,down in [(g,'DP','DN'),(d,'DN','DP')]:
                    a,b=xy(o,up),xy(o,down);wire((x,yt),(a[0],yt),a);wire(b,(b[0],yb),(x,yb))
                sig(g,'APUL','Gate_'+phase+side)
            wire((x,35),(x,40));wire((x,61),(x,72));wire((x,99),(x,105));legs.append((x,66))
        mb=meter(108,128,'bess',True);wire((95,22),(95,128),xy(mb,'B'))
        tb=comp('xfmr-3p2w',130,128,Name='BESS_6p25MVA',Tmva='6.25 [MVA]',V1='13.8 [kV]',V2='.69 [kV]',f=60,YD1=0,YD2=0,Xl=.06,CuL=.005,NLL=0,Enab=0)
        link(mb,'A',tb,'N1')
        for port in ('G1','G2'):
            pt=xy(tb,port);wire(pt,(pt[0],pt[1]+6));comp('ground',pt[0],pt[1]+6)
        bo=comp('breakout',153,128,Dis=1);link(tb,'N2',bo,'N')
        for idx,(ph,leg,pn) in enumerate(zip('ABC',legs,['N1','N2','N3'])):
            yy=120+8*idx
            am=comp('ammeter',170,yy,Name='IL'+ph+'_kA');am.mirror()
            rr=comp('resistor',178,yy,Name='Rf_'+ph,R='.0005 [ohm]')
            ll=comp('inductor',186,yy,Name='Lf_'+ph,L='.04 [mH]')
            wire(leg,(leg[0]+8,leg[1]),(leg[0]+8,yy),xy(ll,'B'));link(ll,'A',rr,'B');link(rr,'A',am,'N1')
            bp=xy(bo,pn);wire(xy(am,'N2'),(160,yy),(160,bp[1]),bp)
            comp('nodelabel',165,yy,Name='LV_'+ph,MeasV=1,VName='VL'+ph+'_kV')
            wire((160,yy),(165,yy))
        note(136,144,'INTERFACE BESS','6.25 MVA 13.8/0.69 kV Yg-Yg | L=40 uH/phase | positive BESS power injects into PCC')
    else:
        for i,(sn,val) in enumerate([('SOC_pct',50),('Vdc_kV',1.5),('Vbat_kV',1.5),('Ibat_kA',0),('Pbess_MW',0),('Qbess_Mvar',0),*[(f'VL{ph}_kV',0) for ph in 'ABC'],*[(f'IL{ph}_kA',0) for ph in 'ABC']]):
            o=comp('const',10+(i%5)*25,60+(i//5)*12,Value=val);sig(o,'OUT',sn)
        note(65,104,'SEM RAMAL BESS','Sinais BESS iguais a zero por ausencia fisica do equipamento; SOC mostrado apenas como referencia.')
    ctl=c.create_component(name+':DC_Controller',70,170,BessEnabled=int(bess))
    note(75,181,'PARAMETROS AJUSTAVEIS','Duplo clique no bloco: perfil, suavizacao, rampa, SOC, PLL, corrente e PWM. Bateria/rede: parametros nos componentes.')
    print(name,'power circuit and controls created',flush=True);p.save()
    channels={}
    common=[('Pload_command_MW','MW'),('Pload_MW','MW'),('Pgrid_MW','MW'),('Pgrid_ref_MW','MW'),('Pbess_MW','MW'),('Pbess_ref_MW','MW'),('Pbess_raw_MW','MW'),('Qgrid_Mvar','Mvar'),('Qload_Mvar','Mvar'),('Qbess_Mvar','Mvar'),('Vload_kV','kV'),('Vgrid_kV','kV'),('Igrid_kA','kA'),('SOC_pct','%'),('Vdc_kV','kV'),('Vbat_kV','kV'),('Ibat_kA','kA'),('Precovery_MW','MW'),('SOC_block',''),('Power_limit',''),('Current_limit',''),('Modulation_limit','')]
    if bess:common += [(v,'') for k,v in OUTPUTS.items() if k in ['ModA','ModB','ModC','GAH','GAL','GBH','GBL','GCH','GCL','Frequency','IdMeas','IqMeas','IdRef','Vd','Vq','Carrier','Enable']] + [(f'IL{ph}_kA','kA') for ph in 'ABC']+[(f'VL{ph}_kV','kV') for ph in 'ABC']
    for i,(sn,unit) in enumerate(common):
        x=12+(i//16)*42;y=202+(i%16)*7
        comp('datalabel',x,y,Name=sn);wire((x,y),(x+16,y));channels[sn]=comp('pgb',x+16,y,Name=sn,UseSignalName=0,Units=unit,Group='DataCenter',Min=-10,Max=15)
    plots=[('Potencias - MW',['Pload_MW','Pgrid_MW','Pbess_MW','Pgrid_ref_MW']),('SOC - percent',['SOC_pct']),('Tensao CC - kV',['Vdc_kV','Vbat_kV']),('Tensao barramento - kV',['Vload_kV']),('Controle BESS - MW',['Pbess_ref_MW','Pbess_MW']),('Protecoes',['SOC_block','Power_limit','Current_limit','Modulation_limit'])]
    for i,(title,sigs) in enumerate(plots):
        frame=c.create_graph_frame(165+(i%2)*95,185+(i//2)*42)
        frame.size=(90,38)
        frame.parameters(title=title,xtitle='Time [s]',xmin=0,xmax=30)
        graph,curves=frame.add_overlay_graph(*(channels[sn] for sn in sigs))
        from fix_graph_ranges import RANGES
        lo,hi=RANGES[title]
        graph.parameters(title=title,manualscale=True,ymin=lo,ymax=hi)
        frame.auto_sizing=True
        graph.zoom(0,30,lo,hi)
    p.save()
    if bess:
        from audit_component import enrich
        enrich(p)
    print(name,'saved',flush=True)
    return p

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int);ap.add_argument('--case',choices=['both','bess','base'],default='both');a=ap.parse_args()
    app=get_app(a.port);app.flags(silence=True);app.settings(fortran_version='GFortran 8.1 (64-bit)')
    from fix_graph_ranges import apply
    for b in ([False,True] if a.case=='both' else [a.case=='bess']):
        path=apply(build(app,b));app.load(str(path));app.wait_for_idle()
    app.save_workspace(str(ROOT/'pscad/DataCenter_BESS.pswx'),save_projects=False)
