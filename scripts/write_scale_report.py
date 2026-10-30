"""Produce the concise report directly from the scaled verification records."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'validation/scale_250_500'
def main():
    v=json.loads((OUT/'validation.json').read_text());p=json.loads((OUT/'portability.json').read_text())
    assert v['status']==p['status']=='PASS'
    checks={c['name']:c for c in v['checks']};lines=['# Resultados — data center intermitente de 250–500 MW','',
        f"**{len(v['checks'])}/{len(v['checks'])} verificações físicas aprovadas**, em {len(v['run_folders'])} ensaios EMTDC frescos. Quatro simulações finais de 30 s vinculadas por SHA-256 aos arquivos entregues. Quatro casos recompilados e executados por 6 s em outra pasta; comparação com as referências: **{p['status']}**.",'',
        'PSCAD 5.1.0, GFortran 8.1 (64-bit). Passo entregue 10 µs, amostragem 100 µs; sensibilidade verificada com 5 µs. Bases: 1.000 MVA, rede 230 kV, carga 34,5 kV, gerador 20 kV. BESS equivalente de 250 MW/125 MWh.','',
        '## Comparação elétrica','',
        'Mesma referência de carga entre 250 e 500 MW nos quatro casos. Métricas na janela de 1,5–30 s, potências com média móvel de 1/60 s e rampa em 100 ms.','',
        '| Caso | Potência média da alimentação [MW] | Desvio padrão [MW] | Maior rampa [MW/s] | Tensão PCC [pu] |',
        '|---|---:|---:|---:|---|']
    titles={'ideal_base':'Fonte ideal sem BESS','ideal_bess':'Fonte ideal com BESS','generator_base':'Gerador sem BESS','generator_bess':'Gerador com BESS'}
    for key,title in titles.items():
        m=v['four_case_power_metrics'][key];voltage=checks[key+'_PCC_voltage_pu']['value']
        lines.append(f"| {title} | {m['mean_MW']:.3f} | {m['std_MW']:.3f} | {m['maximum_ramp_MW_per_s']:.2f} | {voltage[0]:.4f}–{voltage[1]:.4f} |")
    lines+=['','| Alimentação | Redução do desvio padrão | Redução da maior rampa |','|---|---:|---:|']
    for key,title in [('ideal','Fonte ideal'),('generator','Gerador')]:
        r=v['BESS_reductions_percent'][key];lines.append(f"| {title} | {r['std_MW']:.2f}% | {r['maximum_ramp_MW_per_s']:.2f}% |")
    lines+=['','O BESS mantém a demanda intermitente e suaviza a potência da alimentação. Os patamares longos ainda exigem a potência elevada da rede/gerador; a redução global de pico a pico é pequena. Estes resultados não implicam economia de energia, pois o SOC final difere do inicial.','',
        '## Gerador e BESS','']
    for key in ['generator_base','generator_bess']:
        x=checks[key+'_frequency_Hz']['value'];lines.append(f"- {titles[key]}: frequência de {x[0]:.4f} a {x[1]:.4f} Hz.")
    for key in ['ideal_bess','generator_bess']:
        soc=checks[key+'_SOC_limits']['value'];e=checks[key+'_energy_balance_relative']['value']
        lines.append(f"- {titles[key]}: SOC {soc[0]:.5f}–{soc[1]:.5f}%; resíduo de balanço energético {100*e['relative']:.3f}% da energia total carregada/descarregada.")
    lines+=['','Os ensaios próximos de 20% e 80% confirmaram bloqueio da direção proibida de potência e recuperação ao inverter a solicitação. Contagem de carga independente, limites de corrente/modulação, balanço de potência no PCC, conservação de momento angular e potência da turbina na massa acionada foram verificados.','',
        '## Modos torsionais e limite da análise','',
        '| Ensaio de pulso, passo 10 µs | Modo 1 [Hz] | Modo 2 [Hz] | MAC mínimo |','|---|---:|---:|---:|']
    for key,title in [('pulse_generator_base','Sem BESS'),('pulse_generator_bess','Com BESS')]:
        a=v['modal_identification'][key];lines.append(f"| {title} | {a[0]['frequency_Hz']:.5f} | {a[1]['frequency_Hz']:.5f} | {min(x['MAC'] for x in a):.6f} |")
    f=v['calculated_frequencies_Hz'];lines+=['',f'Frequências calculadas pelas matrizes de inércia/rigidez: **{f[1]:.5f} e {f[2]:.5f} Hz**. Identificação por espectro de velocidades mecânicas relativas, remoção da velocidade comum e associação por forma modal (MAC). Pulso de 25 MW por 25 ms sobre 250 MW; janela de análise 5,3–19,8 s.','',
        '| Alteração 10 → 5 µs | Variação da amplitude do modo 1 | Variação da amplitude do modo 2 |','|---|---:|---:|']
    for key,title in [('generator_base','Sem BESS'),('generator_bess','Com BESS')]:
        c=v['modal_step_sensitivity'][key]['amplitude_change_percent'];lines.append(f'| {title} | {c[0]:+.2f}% | {c[1]:+.2f}% |')
    lines+=['','**As amplitudes torsionais com BESS não convergiram entre os dois passos.** Frequências e formas passaram nos critérios, assim como as grandezas elétricas médias. O VSC ativo mantém forçamento elétrico após o pulso; portanto, as amplitudes não devem ser usadas para quantificar amortecimento físico ou benefício torsional do BESS. Não foi estimada razão de amortecimento.','',
        '## Arquivos e rastreabilidade','',
        '- [Guia de execução e parâmetros](../../README_250_500MW.md).',
        '- [Verificação numérica completa](validation.json), [portabilidade](portability.json), [revisão](REVIEW.md).',
        '- [Comparação dos quatro casos](../../figures/scale_250_500/comparacao_quatro_casos.png), [suavização](../../figures/scale_250_500/suavizacao_potencia.png), [torques](../../figures/scale_250_500/gerador_multimassa.png), [modos](../../figures/scale_250_500/modos_torcionais.png), [SOC](../../figures/scale_250_500/limites_soc.png).',
        '- Fontes e instruções anteriores preservadas no histórico indicado em `baseline.json`; pacotes anteriores mantidos.',
        '', 'Modelo didático agregado, sem calibração contra máquina ou bateria de fabricante. Não é um projeto executivo de uma instalação de 500 MW.']
    (OUT/'RESULTADOS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('REPORT WRITTEN',OUT/'RESULTADOS.md')
if __name__=='__main__':main()
