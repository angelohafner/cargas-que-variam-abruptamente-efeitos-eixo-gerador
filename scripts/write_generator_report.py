"""Generate concise teaching results directly from the checked evidence."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def main():
    r=json.loads((ROOT/'validation/generator/validation.json').read_text());p=json.loads((ROOT/'validation/generator/portability.json').read_text())
    lines=['# Resultados — gerador, turbina a gás e eixo multimassa','',
      f"Verificações funcionais/numéricas: **{r['status']} — {sum(c['status']=='PASS' for c in r['checks'])}/{len(r['checks'])}**. Portabilidade: **{p['status']}**.",'',
      'A conclusão se aplica aos parâmetros didáticos entregues. A convergência da amplitude espectral com BESS é avaliada separadamente abaixo; não se confunde com os testes funcionais.','',
      '## Modos identificados','',
      '| Ensaio | Modo 1 [Hz] | MAC 1 | Modo 2 [Hz] | MAC 2 |','|---|---:|---:|---:|---:|']
    for label,items in r['modal_identification'].items():
        a,b=items;lines.append(f"| {label} | {a['frequency_Hz']:.5f} | {a['MAC']:.6f} | {b['frequency_Hz']:.5f} | {b['MAC']:.6f} |")
    lines+=['',f"Cálculo mecânico: **{r['calculated_frequencies_Hz'][1]:.5f} e {r['calculated_frequencies_Hz'][2]:.5f} Hz**. O modo rígido tem frequência zero.",
      'A rigidez multiplicada por 1,44 desloca ambos os modos aproximadamente por 1,20. A comparação das formas modais e esse deslocamento sustentam a associação física dos picos.',
      '',f"No ensaio sem BESS, a resposta harmônica em velocidade relativa por MW de carga efetiva, a 10,61 Hz, foi **{r['resonance_gain']:.2f} vezes** a resposta a 8 Hz. Essa razão é do ensaio forçado entregue; não é um fator de amplificação universal.",
      '', '## Sensibilidade numérica do espectro','',
      '| Comparação de passo | Mudança da amplitude do modo 1 | Modo 2 | Ambas dentro de 10%? |','|---|---:|---:|---|']
    for label,s in r['spectral_amplitude_step_sensitivity'].items():
        a,b=s['modal_amplitude_change_percent'];lines.append(f"| {label} | {a:+.2f}% | {b:+.2f}% | {'Sim' if s['amplitude_convergence_within_10percent'] else '**Não**'} |")
    lines+=['',
      '**Limite de interpretação:** o caso com BESS continua recebendo forçamento elétrico e de controle após o pulso. Seus picos não fornecem, por si só, taxa de amortecimento. Onde a tabela indica Não, a amplitude torsional não demonstrou convergência ao passo. Não utilizar essas amplitudes para cálculo de fadiga, classificação de estabilidade ou benefício quantitativo de amortecimento.',
      'O algoritmo seleciona máximos locais com MAC ≥ 0,95, mantendo o pico mais forte da banda como diagnóstico. Isso evita chamar uma componente concorrente de modo mecânico apenas por sua amplitude.',
      '', '| Ensaio/modo | Maior pico da banda [Hz] | MAC desse pico | Foi associado ao modo? |','|---|---:|---:|---|']
    for label,items in r['modal_identification'].items():
        if not label.startswith('pulse_bess'):continue
        for i,item in enumerate(items,1):
            q=item['strongest_band_peak'];lines.append(f"| {label} / {i} | {q['frequency_Hz']:.5f} | {q['MAC']:.6f} | {'Sim' if q['selected_as_mode'] else 'Não; pico modal compatível selecionado separadamente'} |")
    lines+=['','## Comparação dos quatro casos','',
      'Mesmo comando de carga; janela 1,5–30 s; potência com média de 1/60 s; rampa em 100 ms. A fonte ideal mantém sua frequência prescrita; não possui eixo mecânico para comparar torção.',
      '', '| Caso | Potência média [MW] | Desvio padrão [MW] | Rampa máxima [MW/s] | Energia entregue à carga [MJ] |','|---|---:|---:|---:|---:|']
    for label,v in r['four_case_power_metrics'].items():lines.append(f"| {label} | {v['mean_MW']:.5f} | {v['std_MW']:.5f} | {v['maximum_ramp_MW_per_s']:.3f} | {r['served_load_energy_MJ'][label]:.3f} |")
    lines+=['']
    for label,v in r['BESS_reductions_percent'].items():lines.append(f"- {label}: BESS reduziu o desvio padrão da potência em **{v['std_MW']:.2f}%** e a rampa máxima em **{v['maximum_ramp_MW_per_s']:.2f}%**, nesta janela.")
    lines+=['','O SOC final não é idêntico ao inicial. Essas métricas de suavização não constituem uma alegação de economia de energia. O gerador inclui seu transformador elevador e impedância interna; a comparação não mantém impedâncias de fonte idênticas.',
      '', '## Verificação e rastreabilidade','',
      f"- {len(r['run_folders'])-2} execuções aceitas do novo conjunto e 2 referências ideais anteriores preservadas, todas vinculadas a fontes e saídas por SHA-256.",
      '- Comprovação de liberação do rotor, continuidade de frequência/tensão, balanço angular, potência da turbina na massa acionada, balanço de potência no PCC, energia do BESS, SOC e limites do conversor.',
      '- Os dois casos novos foram copiados para outra pasta e executados por 6 s, incluindo a liberação mecânica e o início da varredura. Os dez canais comparados coincidiram com o trecho correspondente do ensaio canônico.',
      '- Os quatro projetos foram reabertos no workspace canônico. Os hashes dos dois arquivos originais foram preservados.',
      '- Testes Python: ver `unit_tests.txt`. Capturas nativas: `native_exports.json`. Revisão independente: `REVIEW.md`. Resultados e critérios completos: `validation.json`.',
      '- Todos os parâmetros de máquina e eixo são hipóteses didáticas ajustáveis. Não houve validação contra ensaios de fabricante.',
      '', '## Gráficos','',
      '- `../../figures/generator/comparacao_quatro_casos.png`',
      '- `../../figures/generator/identificacao_modos.png`',
      '- `../../figures/generator/varredura_torcional.png`',
      '- `../../figures/generator/ressonancia_e_turbina.png`',
      '- `../../figures/generator/sensibilidade_passo_BESS.png`','']
    (ROOT/'validation/generator/RESULTADOS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('Generated validation/generator/RESULTADOS.md',flush=True)
if __name__=='__main__':main()
