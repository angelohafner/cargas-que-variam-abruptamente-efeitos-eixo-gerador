"""Generate the delivery report from the actual validated suite, without simulation."""
from pathlib import Path
from datetime import datetime,timezone
import json

ROOT=Path(__file__).resolve().parents[1]

def main():
    r=json.loads((ROOT/'validation/validation.json').read_text())
    manifest=json.loads((ROOT/'results/latest_suite.json').read_text())
    portability=json.loads((ROOT/'validation/portability.json').read_text())
    assert r['status']=='PASS' and manifest['status']=='COMPLETE' and portability['status']=='PASS'
    comp=r['comparison']['full'];a=comp['without_BESS'];b=comp['with_BESS'];red=comp['reduction_percent']
    rows=[]
    for name,key,unit in [('Desvio padrão','std_MW','MW'),('Rampa máxima','maximum_ramp_MW_per_s','MW/s'),('Pico de importação','maximum_MW','MW'),('Variação pico a pico','peak_to_peak_MW','MW')]:
        rows.append(f"| {name} [{unit}] | {a[key]:.6f} | {b[key]:.6f} | {red[key]:.2f}% |")
    e=r['energy'];runs=[]
    for label,path in manifest['cases'].items():
        receipt=json.loads((ROOT/path/'run_receipt.json').read_text())
        warnings=(ROOT/path/'messages.txt').read_text(encoding='utf-8').count("status='warning'")
        assert receipt['fresh_outputs'] and not receipt['errors'] and receipt['project_unchanged_during_run']
        runs.append(f"| {label} | {receipt['duration_s']:g} | {receipt['time_step_us']:g} | {receipt['sample_step_us']:g} | {warnings} | [{path}](../{path}/run_receipt.json) |")
    checks=[]
    for x in r['checks']:
        value=json.dumps(x['value'],ensure_ascii=False) if x['value'] is not None else 'Condição satisfeita'
        limit=json.dumps(x['limit'],ensure_ascii=False) if x['limit'] is not None else 'Verificação lógica'
        checks.append(f"| `{x['name']}` | {x['status']} | {value} | {limit} |")
    body=f'''# Validação — data center com e sem BESS

**Resultado: {r['status']} — {len(r['checks'])}/{len(r['checks'])} critérios numéricos aprovados.**
Relatório gerado em {datetime.now(timezone.utc).isoformat()} a partir dos arquivos de simulação, metadados e recibos identificados abaixo.

## Comparação nominal

PSCAD 5.1.0, GFortran 8.1 (64-bit), 30 s, passo de integração 10 µs e gravação 100 µs. Carga solicitada idêntica nos dois casos. BESS de ±5 MW e 2,5 MWh nominais, SOC inicial de 50%. Janela de métricas: 0,6–30 s; média móvel de um ciclo a 60 Hz; rampa por diferença em 100 ms. Todos os instantes de saturação da janela foram mantidos.

| Indicador | Sem BESS | Com BESS | Redução |
|---|---:|---:|---:|
{chr(10).join(rows)}

Nas janelas pulsantes 6–10 s e 20–25 s, as reduções do desvio padrão foram {r['comparison']['pulses_6_10']['reduction_percent']['std_MW']:.2f}% e {r['comparison']['pulses_20_25']['reduction_percent']['std_MW']:.2f}%. As amostras com alguma saturação representaram {100*r['comparison']['pulses_6_10']['saturation_fraction']:.2f}% e {100*r['comparison']['pulses_20_25']['saturation_fraction']:.2f}%, respectivamente.

O ajuste de 0,5 MW/s limita a **referência** da rede. A rampa máxima medida foi {b['maximum_ramp_MW_per_s']:.3f} MW/s; o modelo não garante 0,5 MW/s no transitório físico. A potência da rede é medida no lado de 13,8 kV após o transformador principal.

![Comparação principal](../figures/comparacao_principal.png)

## Energia, SOC e proteções

- SOC final nominal: **{e['SOC_final_percent']:.6f}%**; excursão no ensaio: {e['SOC_excursion_percent_points']:.6f} ponto percentual.
- Energia descarregada nos terminais: {1000*e['discharged_terminal_MWh']:.6f} kWh; carregada: {1000*e['charged_terminal_MWh']:.6f} kWh; saldo: {1000*e['battery_terminal_net_MWh']:.6f} kWh.
- Perdas medidas no caminho do conversor: {1000*e['converter_path_losses_MWh']:.6f} kWh. Não incluem um modelo térmico ou perdas de chaveamento por fabricante.
- Energias positiva, negativa, líquida e carga elétrica foram integradas **a cada passo EMTDC**. A corrente e a potência médias da bateria nos gráficos são reconstruídas dos incrementos dessas integrais, evitando alias de PWM por amostragem pontual a 100 µs.
- O balanço inclui variação de energia no capacitor CC e nas indutâncias. A tabela abaixo apresenta o resíduo e a tolerância, sem assumir igualdade exata.
- Ensaios separados alcançam os limites SOC com a capacidade original de 2,5 MWh e comprovam bloqueio do sentido proibido e recuperação no sentido permitido. Um ensaio adicional de referência zero no SOC inferior verifica a cobertura das perdas em vazio.
- O SOC é fornecido pela bateria nativa e conferido por contagem independente de carga. Não foi recortado para esconder violações.

As energias importadas da rede na janela comparativa foram {1000*a['import_energy_MWh']:.6f} kWh sem BESS e {1000*b['import_energy_MWh']:.6f} kWh com BESS. **A diferença não representa economia energética**, pois a energia armazenada final é diferente e o BESS apresenta perdas.

## Execuções verificadas

Cada recibo vincula os hashes da fonte `.pscx`, dos metadados `.inf` e dos dados `.out`. O leitor rejeita fontes alteradas, canais ausentes, dados antigos, duração incompleta, valores não finitos e eixos de tempo incompatíveis. Todas as execuções abaixo tiveram saída nova e nenhum erro informado pelo PSCAD.

| Ensaio | Duração [s] | Integração [µs] | Gravação [µs] | Avisos PSCAD | Recibo |
|---|---:|---:|---:|---:|---|
{chr(10).join(runs)}

O passo reduzido de 5 µs foi comparado com 10 µs no mesmo cenário inicial de 5 s. Isso verifica a sensibilidade numérica desse trecho; não equivale a uma repetição dos 30 s completos com passo reduzido. O ensaio de 1 s com gravação 5 µs confirma a lógica complementar dos pulsos nas três fases.

## Portabilidade e entrega

Os dois `.pscx` foram copiados com o workspace relativo para outra pasta e executados por **2,5 s** cada, reconstruindo os arquivos de compilação. As séries de potência da carga/rede/BESS, SOC e tensão CC coincidiram com o trecho correspondente das execuções nominais, com tolerância de 1e-8 nas unidades dos canais. O workspace canônico foi reaberto com exatamente dois projetos e seus hashes foram preservados. Evidência: [portability.json](portability.json).

Os gráficos nativos foram exportados pelo próprio PSCAD e inspecionados, com escalas explícitas para o caso nominal. Fontes e definições são editáveis. O ZIP contém apenas os resultados selecionados pelo manifesto da suíte atual; o histórico de desenvolvimento permanece na pasta local. O manifesto SHA-256 e o relatório de verificação do ZIP são gerados por `scripts/package_delivery.py`.

As hipóteses, os parâmetros ajustáveis, os sinais, os limites e a sequência de execução estão no [README](../README.md). As correções da revisão técnica estão em [REVIEW.md](REVIEW.md).

## Critérios e resultados completos

Valores em unidades explícitas nos nomes dos critérios. As tolerâncias dinâmicas de corrente e potência não alteram os limites das referências do controlador.

| Critério | Resultado | Valor medido | Limite/critério |
|---|---|---|---|
{chr(10).join(checks)}
'''
    (ROOT/'validation/RELATORIO.md').write_text(body,encoding='utf-8')
    print('Report written:',len(r['checks']),'PASS checks')

if __name__=='__main__':main()
