"""Comparisons from the scaled, hash-verified EMTDC output channels."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis import average
from torsion_identification import spectrum, relative_speeds
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures/scale_250_500'
CASES=['ideal_base','ideal_bess','generator_base','generator_bess']
NAMES=['Fonte ideal / sem BESS','Fonte ideal / com BESS','Gerador / sem BESS','Gerador / com BESS']
COLORS=['#a56d37','#3d60a8','#c44843','#148774']
def style(ax,title,unit):
    ax.set_title(title,loc='left',fontsize=11,fontweight='bold');ax.set_ylabel(unit);ax.grid(alpha=.2);ax.legend(fontsize=8)
def save(fig,file,title):
    fig.suptitle(title,fontsize=15);fig.tight_layout(rect=(0,0,1,.95));fig.savefig(FIG/file,dpi=160);plt.close(fig)
def weighted(d,h):
    t=d['time'];m=(t>=5.3)&(t<=19.8);w=np.column_stack([d[f'Shaft_dw{i}_rad_s'] for i in (1,2,3)])
    f,z=spectrum(t[m],relative_speeds(w[m],h));return f,np.sqrt(np.sum(abs(z)**2*np.asarray(h),axis=1)/np.sum(h))
def make_figures(data,result):
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(3,2,figsize=(15,12),sharex=True)
    for i,key in enumerate(CASES):
        d=data[key];t=d['time'];ix=np.flatnonzero(t>=1.5)[::10]
        for ax,ch in [(axs[0,0],'Pload_MW'),(axs[0,1],'Pgrid_MW'),(axs[1,0],'Vload_kV')]:
            ax.plot(t[ix],average(t,d[ch])[ix],color=COLORS[i],ls='--' if i<2 else '-',lw=1,alpha=.8,label=NAMES[i])
        if i%2:
            axs[2,0].plot(t[ix],average(t,d['Pbess_MW'])[ix],color=COLORS[i],label=NAMES[i])
            axs[2,1].plot(t[ix],d['SOC_pct'][ix],color=COLORS[i],label=NAMES[i])
        if i>=2:axs[1,1].plot(t[ix],d['Generator_Hz'][ix],color=COLORS[i],label=NAMES[i])
    axs[0,0].plot(t[ix],d['Pload_command_MW'][ix],c='black',ls=':',lw=.7,label='Comando comum: 250–500 MW')
    axs[1,1].axhline(60,c='gray',ls=':',label='Referência ideal: 60 Hz')
    for ax,(title,unit) in zip(axs.flat,[('Demanda atendida: permanece intermitente','MW'),('Potência solicitada à alimentação','MW'),
        ('Tensão RMS no barramento de 34,5 kV','kV'),('Frequência elétrica do gerador','Hz'),('BESS: positivo = descarga','MW'),('SOC: janela operacional de 20–80%','%')]):
        style(ax,title,unit);ax.set_xlim(1.5,30)
    for ax in axs[-1]:ax.set_xlabel('Tempo [s]')
    save(fig,'comparacao_quatro_casos.png','Data center intermitente de 250–500 MW | BESS agregado de 250 MW / 125 MWh\nResultados PSCAD/EMTDC; potências com média de um ciclo')
    fig,axs=plt.subplots(2,2,figsize=(14,9))
    for col,prefix in enumerate(['ideal','generator']):
        for suffix,color in [('base',COLORS[2]),('bess',COLORS[3])]:
            d=data[prefix+'_'+suffix];t=d['time'];p=average(t,d['Pgrid_MW']);title='Sem BESS' if suffix=='base' else 'Com BESS'
            axs[0,col].plot(t,p,color=color,label=title,lw=1)
            n=round(.1/np.median(np.diff(t)));axs[1,col].plot(t[n:],(p[n:]-p[:-n])/(t[n:]-t[:-n]),color=color,label=title,lw=.8)
        style(axs[0,col],('Fonte ideal' if col==0 else 'Gerador')+': pulsos de carga','MW');axs[0,col].set_xlim(6,7.5)
        style(axs[1,col],'Rampa calculada em janela de 100 ms','MW/s');axs[1,col].set_xlim(1.5,30)
    for ax in axs.flat:ax.set_xlabel('Tempo [s]')
    save(fig,'suavizacao_potencia.png','Comparação com a mesma demanda nos quatro casos')
    fig,axs=plt.subplots(3,1,figsize=(14,10),sharex=True)
    for key,color,title in [('generator_base',COLORS[2],'Sem BESS'),('generator_bess',COLORS[3],'Com BESS')]:
        d=data[key];t=d['time'];ix=np.flatnonzero(t>=1.5)[::5]
        axs[0].plot(t[ix],d['Gas_Tm_pu'][ix],color=color,label='Turbina / '+title)
        axs[0].plot(t[ix],average(t,d['Generator_Te_pu'])[ix],color=color,ls='--',alpha=.7,label='Elétrico / '+title)
        for ax,ch in zip(axs[1:],['Shaft_T12_pu','Shaft_rel12_rad_s']):ax.plot(t[ix],d[ch][ix],color=color,lw=.7,label=title)
    for ax,title,unit in zip(axs,['Torque da turbina e torque elétrico','Torque no trecho 1–2','Velocidade relativa das massas 1 e 2'],['pu / 1.000 MVA','pu / 1.000 MVA','rad/s']):style(ax,title,unit);ax.set_xlim(1.5,30)
    axs[-1].set_xlabel('Tempo [s]');save(fig,'gerador_multimassa.png','Turbina a gás e eixo de três massas | carga intermitente de 250–500 MW')
    fig,axs=plt.subplots(2,2,figsize=(14,10));h=result['shaft']['H'];refs=result['calculated_frequencies_Hz'][1:]
    for col,case in enumerate(['generator_base','generator_bess']):
        for suffix,color,title in [('',COLORS[2],'10 µs'),('_fine',COLORS[1],'5 µs')]:
            key='pulse_'+case+suffix;d=data[key];f,a=weighted(d,h);m=(f>=4)&(f<=32)
            axs[0,col].semilogy(f[m],a[m],color=color,label=title)
            axs[1,col].plot([1,2],[x['relative_speed_amplitude'] for x in result['modal_identification'][key]],'o-',color=color,label=title)
        for i,f in enumerate(refs,1):axs[0,col].axvline(f,c='gray',ls=':',lw=.8,label=f'Modo {i}: {f:.3f} Hz')
        style(axs[0,col],('Sem BESS' if col==0 else 'Com BESS')+': espectro após pulso','rad/s');axs[0,col].set_xlabel('Frequência [Hz]')
        style(axs[1,col],'Sensibilidade da amplitude ao passo de integração','rad/s');axs[1,col].set_xticks([1,2],['Modo 1','Modo 2'])
    save(fig,'modos_torcionais.png','Pulso de 25 MW sobre carga de 250 MW | janela de 5,3–19,8 s\nFrequências e formas modais verificadas; amplitudes com BESS exigem análise separada')
    fig,axs=plt.subplots(2,2,figsize=(14,8),sharex=True)
    for col,key in enumerate(['soc_low','soc_high']):
        d=data[key];t=d['time'];bound=20 if col==0 else 80
        axs[0,col].plot(t,d['SOC_pct'],label='SOC medido');axs[0,col].axhline(bound,c='red',ls='--',label=f'Limite: {bound}%')
        power=average(t,np.gradient(d['Ebat_MJ'],t));axs[1,col].plot(t,power,label='Potência da bateria CC')
        axs[1,col].plot(t,average(t,d['Pbess_MW']),label='Potência BESS CA',alpha=.8)
        style(axs[0,col],'Proteção no limite '+('inferior' if col==0 else 'superior'),'SOC [%]')
        style(axs[1,col],'Bloqueio e recuperação por inversão da potência','MW');axs[1,col].set_xlabel('Tempo [s]')
    save(fig,'limites_soc.png','Bateria de 125 MWh | limites de SOC 20–80% | ensaios de ±150 MW')
