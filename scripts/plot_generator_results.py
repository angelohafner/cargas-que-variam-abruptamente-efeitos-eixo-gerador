"""Scientific figures from the validated EMTDC channels, not synthetic traces."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis import average
from torsion_identification import spectrum,relative_speeds

ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures/generator'
COLORS=['#ad7542','#405e9b','#c44748','#138875']
LABELS=['Fonte ideal / sem BESS','Fonte ideal / com BESS','Gerador / sem BESS','Gerador / com BESS']
def style(ax,title,unit):
    ax.set_title(title,loc='left',fontsize=11,fontweight='bold');ax.set_ylabel(unit);ax.grid(alpha=.22)
    ax.legend(fontsize=8,loc='best')
def save(fig,name,title):
    fig.suptitle(title,fontsize=15);fig.tight_layout(rect=(0,0,1,.95));fig.savefig(FIG/name,dpi=165);plt.close(fig)
def weighted_spectrum(d,h):
    t=d['time'];m=(t>=5.3)&(t<=19.8)
    w=np.column_stack([d[f'Shaft_dw{i}_rad_s'] for i in (1,2,3)])
    f,z=spectrum(t[m],relative_speeds(w[m],h))
    return f,np.sqrt(np.sum(abs(z)**2*np.asarray(h),axis=1)/np.sum(h))
def make_figures(data,result):
    FIG.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(3,2,figsize=(15,12),sharex=True)
    for i,label in enumerate(['ideal_base','ideal_bess','profile_base','profile_bess']):
        d=data[label];t=d['time'];idx=np.flatnonzero(t>=1.5)[::10]
        for ax,key in [(axs[0,0],'Pgrid_MW'),(axs[0,1],'Pload_MW'),(axs[1,0],'Vload_kV')]:
            ax.plot(t[idx],average(t,d[key])[idx],color=COLORS[i],lw=1.1,ls='--' if i<2 else '-',alpha=.85,label=LABELS[i])
        if i%2:
            axs[2,0].plot(t[idx],average(t,d['Pbess_MW'])[idx],color=COLORS[i],lw=1.1,label=LABELS[i])
        if i>=2:
            axs[1,1].plot(t[idx],d['Generator_Hz'][idx],color=COLORS[i],label=LABELS[i])
            for k,ls in [('Shaft_T12_pu','-'),('Shaft_T23_pu','--')]:
                axs[2,1].plot(t[idx],d[k][idx],color=COLORS[i],ls=ls,lw=.8,label=LABELS[i]+(' / T12' if '12' in k else ' / T23'))
    axs[1,1].axhline(60,c='#777',ls=':',label='Referência da fonte ideal: 60 Hz')
    titles=[('Potência no mesmo ponto da rede','MW'),('Carga efetivamente atendida','MW'),('Tensão RMS no barramento da carga','kV'),('Frequência elétrica do gerador','Hz'),('BESS: positivo = descarga','MW'),('Torques nos eixos do gerador','pu (base 20 MVA)')]
    for ax,(title,unit) in zip(axs.flat,titles):style(ax,title,unit);ax.set_xlim(1.5,30)
    for ax in axs[-1]:ax.set_xlabel('Tempo [s]')
    save(fig,'comparacao_quatro_casos.png','Mesmo perfil de carga: fonte ideal e turbina a gás com eixo multimassa\nPotências: média de 1/60 s; torques e frequência: sinais mecânicos sem essa média')
    fig,axs=plt.subplots(2,2,figsize=(15,10));h=result['shaft']['H'];refs=result['calculated_frequencies_Hz'][1:]
    for label,col,title in [('pulse_base',COLORS[2],'Sem BESS'),('pulse_bess',COLORS[3],'Com BESS')]:
        d=data[label];t=d['time'];m=(t>=5)&(t<=7)
        axs[0,0].plot(t[m],d['Shaft_rel12_rad_s'][m],c=col,lw=.8,label=title)
        f,a=weighted_spectrum(d,h);m=(f>4)&(f<32)
        axs[0,1].semilogy(f[m],a[m],c=col,label=title)
    for j,f in enumerate(refs,1):axs[0,1].axvline(f,c='#555',ls=':',lw=1,label=f'Modo {j}: {f:.3f} Hz')
    shapes=np.asarray(result['calculated_shapes'])
    for j,col in [(0,'#405e9b'),(1,'#ad7542')]:
        shape=shapes[:,j+1];shape=shape*np.sign(shape[np.argmax(abs(shape))])
        axs[1,0].plot([1,2,3],shape,'o-',c=col,label=f'Modo {j+1}: cálculo')
        axs[1,0].plot([1,2,3],result['modal_identification']['pulse_base'][j]['observed_shape_real'],'x--',c=col,label=f'Modo {j+1}: EMTDC')
    for label,col,title in [('pulse_base',COLORS[2],'K = 40 / 50'),('pulse_stiffer','#7657a4','K × 1,44')]:
        f,a=weighted_spectrum(data[label],h);m=(f>4)&(f<32);axs[1,1].semilogy(f[m],a[m],color=col,label=title)
    for ax,title,unit in [(axs[0,0],'Após pulso de carga de 0,5 MW por 25 ms','ω1 − ω2 [rad/s]'),(axs[0,1],'Após pulso: BESS mantém forçamento elétrico ativo','Amplitude ponderada [rad/s]'),(axs[1,0],'Formas modais: movimento relativo ao centro de inércia','Amplitude normalizada'),(axs[1,1],'Aumento da rigidez: frequências × 1,20','Amplitude ponderada [rad/s]')]:style(ax,title,unit)
    axs[0,0].set_xlabel('Tempo [s]');axs[0,1].set_xlabel('Frequência [Hz]');axs[1,1].set_xlabel('Frequência [Hz]')
    axs[1,0].set_xticks([1,2,3],['1: turbina + compressor','2: inércia intermediária','3: gerador']);axs[1,0].set_ylim(-1.2,1.2)
    save(fig,'identificacao_modos.png','Identificação dos modos torsionais em resultados PSCAD/EMTDC\nEspectro de velocidades mecânicas relativas; componente comum removida')
    fig,axs=plt.subplots(3,1,figsize=(14,11),sharex=True)
    d=data['chirp_base'];t=d['time'];m=(t>=4.5)&(t<=29.5);ix=np.flatnonzero(m)[::5]
    axs[0].plot(t[ix],d['Excitation_Hz'][ix],c='#405e9b',label='Frequência imposta à carga')
    for j,f in enumerate(refs,1):axs[0].axhline(f,ls=':',label=f'Modo {j} calculado: {f:.2f} Hz')
    for label,col,title in [('chirp_base',COLORS[2],'Sem BESS'),('chirp_bess',COLORS[3],'Com BESS')]:
        d=data[label]
        for ax,key in zip(axs[1:],['Shaft_rel12_rad_s','Shaft_rel23_rad_s']):ax.plot(t[ix],d[key][ix],c=col,lw=.65,alpha=.85,label=title)
    for ax,title,unit in zip(axs,['Varredura de 5 a 30 Hz (5–25 s)','Velocidade relativa entre massas 1 e 2','Velocidade relativa entre massas 2 e 3'],['Hz','rad/s','rad/s']):style(ax,title,unit)
    axs[-1].set_xlabel('Tempo [s]');axs[-1].set_xlim(4.5,29.5)
    save(fig,'varredura_torcional.png','Ensaio padrão ao abrir os dois novos projetos\nA varredura localiza regiões de resposta; a resposta livre confirma os modos')
    fig,axs=plt.subplots(2,2,figsize=(14,9))
    for label,col,title in [('sine_off','#405e9b','8 Hz'),('sine_mode1',COLORS[2],'10,611 Hz')]:
        d=data[label];t=d['time'];m=(t>=9)&(t<=10)
        axs[0,0].plot(t[m],d['Pload_MW'][m],c=col,lw=.8,label=title)
        axs[0,1].plot(t[m],d['Shaft_rel12_rad_s'][m],c=col,lw=.8,label=title)
    gains=[result['forced_response'][k]['gain_rad_s_per_MW'] for k in ['sine_off','sine_mode1']]
    axs[1,0].bar(['8 Hz','10,611 Hz'],gains,color=['#405e9b',COLORS[2]],label='Amplitude relativa / harmônica real da carga')
    for label,col,title in [('profile_base',COLORS[2],'Sem BESS'),('profile_bess',COLORS[3],'Com BESS')]:
        d=data[label];t=d['time'];ix=np.flatnonzero(t>=1.5)[::10]
        axs[1,1].plot(t[ix],d['Gas_Tm_pu'][ix],c=col,label='Turbina / '+title,lw=1)
        axs[1,1].plot(t[ix],average(t,d['Generator_Te_pu'])[ix],c=col,ls='--',alpha=.65,label='Elétrico / '+title,lw=.8)
    for ax,title,unit in [(axs[0,0],'Carga medida: excitações de mesma amplitude nominal','MW'),(axs[0,1],'Resposta mecânica fora e próxima da ressonância','ω1 − ω2 [rad/s]'),(axs[1,0],f'Ganho ressonante relativo: {result["resonance_gain"]:.1f} vezes','(rad/s) / MW'),(axs[1,1],'Torque da turbina e torque elétrico: carga intermitente','pu (base 20 MVA)')]:style(ax,title,unit)
    for ax in [axs[0,0],axs[0,1],axs[1,1]]:ax.set_xlabel('Tempo [s]')
    save(fig,'ressonancia_e_turbina.png','Resposta forçada e balanço mecânico\nEnsaios senoidais sem BESS; ganho ajustado pela amplitude da carga efetivamente medida')
    fig,axs=plt.subplots(2,1,figsize=(13,9))
    for label,color,title in [('pulse_bess',COLORS[3],'10 µs'),('pulse_bess_fine','#405e9b','5 µs'),('pulse_bess_finer','#ad7542','2,5 µs')]:
        d=data[label];f,a=weighted_spectrum(d,h);m=(f>6)&(f<28)
        axs[0].semilogy(f[m],a[m],c=color,label=title,lw=1)
        items=result['modal_identification'][label]
        axs[1].plot([1,2],[x['relative_speed_amplitude'] for x in items],'o-',c=color,label=title)
    for j,f in enumerate(refs,1):axs[0].axvline(f,color='#777',ls=':',lw=.8,label=f'Modo {j} calculado')
    style(axs[0],'Espectro mecânico pós-pulso: janela de 5,3–19,8 s','Amplitude ponderada [rad/s]');axs[0].set_xlabel('Frequência [Hz]')
    style(axs[1],'Amplitudes dos picos associados por frequência e forma','Amplitude ponderada [rad/s]');axs[1].set_xticks([1,2],['Modo 1','Modo 2'])
    save(fig,'sensibilidade_passo_BESS.png','Sensibilidade ao passo EMTDC com BESS\nConvergência de frequência e potência média não garante convergência de amplitude torsional')
