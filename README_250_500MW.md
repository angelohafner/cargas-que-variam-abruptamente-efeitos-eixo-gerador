# Data center intermitente de 250–500 MW — PSCAD 5.1

Os quatro projetos usam **o mesmo comando de carga intermitente entre 250 e 500 MW**. O BESS suaviza a potência solicitada à alimentação; a demanda do data center continua variando. Evidências desta revisão estão em `results/scale_250_500`, `validation/scale_250_500` e `figures/scale_250_500`.

O pacote `DataCenter_250_500MW_Modelos.zip` contém os quatro projetos, workspace, este guia e o resumo de resultados. O pacote `DataCenter_250_500MW_PSCAD_5_1.zip` inclui também scripts, saídas EMTDC, figuras e evidências detalhadas. Cada ZIP contém um manifesto de hashes. O relatório de integridade que inclui os hashes dos próprios ZIPs é entregue separadamente em `delivery/scale_250_500_package_verification.json`.

| Projeto em `pscad/` | Alimentação | BESS |
|---|---|---|
| `DataCenter_Sem_BESS.pscx` | Fonte ideal com impedância de rede | Ausente |
| `DataCenter_Com_BESS.pscx` | Fonte ideal com impedância de rede | 250 MW / 125 MWh |
| `DataCenter_Gerador_Sem_BESS.pscx` | Gerador, turbina a gás e três massas | Ausente |
| `DataCenter_Gerador_Com_BESS.pscx` | Gerador, turbina a gás e três massas | 250 MW / 125 MWh |

## Simulação

1. Extraia os arquivos para uma pasta local gravável. Abra **`pscad/DataCenter_Quatro_Casos.pswx`** no PSCAD **5.1**, com licença de simulação e **GFortran 8.1 (64-bit)** instalado. O workspace tem caminhos relativos.
2. Selecione cada projeto e execute **Run**. A primeira execução recompila o EMTDC. Os componentes são nativos da Master Library; os controles personalizados estão embutidos nos projetos.
3. Configuração entregue: **30 s**, passo EMTDC **10 µs**, amostragem **100 µs**. Nos quatro casos, `DC_Controller.TestMode=0`; nos geradores, `TorsionExperiment.Mode=0`; SOC inicial de 50%.
4. Os gráficos elétricos ficam abaixo da rede; os mecânicos ficam ao lado do gerador. Compare `Pload_command_MW`, `Pload_MW`, `Pgrid_MW`, `Pbess_MW`, tensão, SOC, frequência, torques e velocidades relativas.

## Perfil comum

| Intervalo [s] | Comando [MW] |
|---|---:|
| 0–2 | 250 |
| 2–4 | 458,333 |
| 4–6 | 291,667 |
| 6–10 | Pulsos 250/500; período 0,4 s; duty 50% |
| 10–15 | 500 |
| 15–20 | 250 |
| 20–25 | Pulsos 250/500; período 0,5 s; duty 50% |
| 25–30 | 375 |

A transição da faixa completa leva 20 ms. O perfil determinístico permite comparação reproduzível. A carga nativa representa P/Q agregado, fator de potência nominal 0,98 indutivo. O **comando** fica entre 250 e 500 MW; a potência efetivamente atendida pode apresentar pequenos desvios transitórios, medidos na validação. Não há representação individual de servidores ou UPS.

`Pgrid_MW` é medido no lado de 34,5 kV do transformador da rede, antes do alimentador da carga, positivo no sentido da carga. `Pload_MW` é o consumo medido na carga. `Pbess_MW` é positivo quando o BESS injeta potência no PCC (descarga) e negativo durante carga. Assim, `Pgrid + Pbess ≈ Pload + perdas do alimentador`. A potência nos terminais do gerador inclui também as perdas a montante desse ponto. SOC e tensões CC nos casos sem BESS são sinais de referência constantes, sem bateria física.

## Redimensionamento físico

| Elemento | Valor |
|---|---|
| Frequência | 60 Hz |
| Rede / barramento de carga | 230 / 34,5 kV |
| Transformador da rede | 1.000 MVA, 230/34,5 kV, x=8% |
| Fonte ideal | Scc equivalente de 50.000 MVA; X/R=10 |
| Gerador síncrono equivalente | 1.000 MVA, 20 kV, 3.600 rpm |
| Elevador do gerador | 1.000 MVA, 20/230 kV, x=6% |
| Base do eixo | 1.000 MVA, igual à máquina |
| BESS / transformador | 250 MW / 125 MWh; 312,5 MVA, 34,5/0,69 kV |
| Bateria nativa | 1,5 kV; 83,333333 kAh |
| Filtro equivalente por fase | R=10 µΩ; L=0,8 µH |
| Capacitor CC equivalente | 1 F |
| SOC inicial / limites | 50% / 20–80% |

As impedâncias de rede foram recalculadas por `(Vnova/Vantiga)^2/(Snova/Santiga)`. Parâmetros de máquina, transformadores e eixo em pu foram mantidos. **1.000 MVA é uma base didática equivalente**, não uma especificação de uma turbina comercial. GAST representa potência líquida simplificada: compressor incluído na massa 1 e na potência líquida; massa 2 é uma inércia intermediária equivalente. Após a transição inicial da máquina, o caso com gerador não tem fonte ideal de rede em paralelo. O valor de Scc da fonte ideal não é a potência de curto-circuito declarada do gerador.

O BESS representa **50 módulos equivalentes em paralelo de 5 MW / 2,5 MWh**, usando um VSC agregado de seis IGBTs e seis diodos nativos. Capacidade, capacitância e correntes foram multiplicadas por 50; resistências, indutâncias e ganhos de corrente em ohms foram divididos por 50. As correntes de centenas de kA no lado de 0,69 kV são a **soma equivalente dos módulos**, não a corrente de um único equipamento físico. O equivalente usa PWM comum e não representa diversidade, divisão de corrente ou harmônicos locais de um parque real.

Na bateria nativa, `Qrated` está em kAh e `Inom` é porcentagem da capacidade descarregada por hora; `Inom=100` foi mantido. Veja a [documentação oficial Battery](https://www.pscad.com/webhelp-v502-ol/Master_Library_Models/Sources/Battery/Battery.htm).

## Parâmetros ajustáveis

Duplo clique em `DC_Controller`:

- Perfil: `Pmin=250`, `Pmax=500`, `Pmid=375`, `Pstep1=458.333333`, `Pstep2=291.666667`; tempos `T1` a `T7`, períodos, duty e `Transition=0.02 s`.
- Suavização: `TauSmooth=2 s`, `RampMax=25 MW/s`, `PmaxBess=250 MW`.
- SOC: mínimo 20%, máximo 80%, referência 50%, histerese de 0,05 ponto percentual. SOC inicial é ajustado na bateria.
- Recuperação: ganho de 1 MW/ponto percentual, limite de 25 MW, filtro de 20 s e banda morta de 1 ponto percentual.
- Corrente agregada: `KpI=0.0008`, `KiI=0.4`, `Imax=310 kA`; limite de modulação 0,98 e PWM de 2 kHz.

O limite de rampa atua na referência suavizada; a potência medida também depende da dinâmica, perdas e limites do VSC. Alterar a potência agregada exige redimensionar os componentes físicos e repetir a validação.

## Experimentos torsionais

O eixo nativo `master:multimass2` usa `H=[1.5,1.0,2.5] s`, `K=[40,50] pu/rad mecânico`, amortecimento mútuo `[1,1]`, amortecimento próprio zero, unidades 12/9b e gerador na massa 3. Modos calculados: **10,6109 e 23,2367 Hz**, além da rotação comum. H e K em pu preservam essas frequências na mudança de base.

| `TorsionExperiment.Mode` | Ensaio |
|---:|---|
| 0 | Perfil intermitente comum — padrão entregue |
| 1 | Constante em `Pbase` |
| 2 | Pulso `Amplitude` por `PulseWidth` |
| 3 | Varredura senoidal `Fstart`–`Fend` |
| 4 | Senoide em `Fsine` |

Ensaio de pulso validado: **Pbase=250 MW, Amplitude=25 MW, Start=5 s, PulseWidth=0,025 s**, simulação de 20 s; análise entre 5,3 e 19,8 s.

Para explorar uma varredura: **Pbase=375 MW, Amplitude=25 MW**, 5–30 Hz entre 5 e 25 s, simulação de 30 s. Nos modos 1–4, ajuste também **`DC_Controller.Pmin=Pbase`**, **`sync_machine.P0≈Pbase+5 MW`** e a potência reativa inicial conforme a carga. Confirme o regime antes da perturbação. Esta revisão valida o perfil intermitente e os pulsos; a varredura é uma configuração disponível para experimentação.

Para restaurar a comparação: `Mode=0`, `Pmin=250`, `P0=255 MW`, `Q0=60 Mvar`, SOC inicial 50%. A máquina deixa a inicialização por fonte em 0,3 s e libera o rotor em 1,2 s. Mantenha esses tempos coerentes no experimento, AVR e GAST. Na máquina nativa, **MM=0 habilita a interface multimassa**.

A amplitude torsional com BESS inclui forçamento elétrico ativo e pode ser sensível à discretização do VSC. Consulte a avaliação de passo antes de comparar amplitudes. Os resultados não estimam razão de amortecimento nem comprovam aumento de amortecimento pelo BESS.

## Reprodução automatizada

No diretório raiz do pacote completo, com sessão PSCAD licenciada:

```powershell
py -3.11 -m pip install -r requirements-lock.txt
py -3.11 scripts/run_scale_250_500.py --suite
py -3.11 scripts/validate_scale_250_500.py
py -3.11 scripts/export_scale_views.py
py -3.11 scripts/verify_scale_portability.py
py -3.11 -m unittest discover -s tests -v
```

A suíte executa SOC inferior/superior, pulsos com passos de 10/5 µs, comparação elétrica de passo e os quatro perfis de 30 s. Ao final restaura os padrões de fábrica e deixa os projetos com o perfil intermitente. Preserve eventuais experimentos próprios com outros nomes antes de executar a suíte. Cada resultado inclui fontes, horários e hashes dos `.out`/`.inf` frescos. A portabilidade recompila os quatro casos em outra pasta e compara os primeiros 6 s. Exporte as figuras nativas antes, pois reabrir o projeto limpa as curvas exibidas.

Use os scripts com **`scale` / `250_500`** no nome. Scripts antigos pertencem à escala anterior e podem restaurar 4–10 MW. A reconstrução atual usa a cópia imutável indicada em `validation/scale_250_500/baseline.json`, incluída no pacote completo.

## Evidências e histórico

- [Resultados medidos](validation/scale_250_500/RESULTADOS.md) e [verificações detalhadas](validation/scale_250_500/validation.json).
- [Portabilidade](validation/scale_250_500/portability.json), [revisão](validation/scale_250_500/REVIEW.md) e [integridade dos pacotes](delivery/scale_250_500_package_verification.json).
- [Comparação dos quatro casos](figures/scale_250_500/comparacao_quatro_casos.png).
- Fontes e instruções anteriores preservadas em `history/before_250_500MW_20261026_182420/`.

Relatórios antigos fora de `scale_250_500` descrevem a escala anterior. Os modelos são didáticos e não foram calibrados contra fabricante. Energia da rede deve ser interpretada junto com a variação de SOC; suavização não implica economia de energia.
