# Resultados — data center intermitente de 250–500 MW

**168/168 verificações físicas aprovadas**, em 11 ensaios EMTDC frescos. Quatro simulações finais de 30 s vinculadas por SHA-256 aos arquivos entregues. Quatro casos recompilados e executados por 6 s em outra pasta; comparação com as referências: **PASS**.

PSCAD 5.1.0, GFortran 8.1 (64-bit). Passo entregue 10 µs, amostragem 100 µs; sensibilidade verificada com 5 µs. Bases: 1.000 MVA, rede 230 kV, carga 34,5 kV, gerador 20 kV. BESS equivalente de 250 MW/125 MWh.

## Comparação elétrica

Mesma referência de carga entre 250 e 500 MW nos quatro casos. Métricas na janela de 1,5–30 s, potências com média móvel de 1/60 s e rampa em 100 ms.

| Caso | Potência média da alimentação [MW] | Desvio padrão [MW] | Maior rampa [MW/s] | Tensão PCC [pu] |
|---|---:|---:|---:|---|
| Fonte ideal sem BESS | 374.088 | 106.352 | 2509.25 | 0.9827–0.9928 |
| Fonte ideal com BESS | 373.214 | 54.751 | 244.20 | 0.9844–0.9954 |
| Gerador sem BESS | 373.855 | 105.681 | 2515.35 | 0.9439–1.0129 |
| Gerador com BESS | 374.241 | 54.682 | 259.23 | 0.9498–1.0063 |

| Alimentação | Redução do desvio padrão | Redução da maior rampa |
|---|---:|---:|
| Fonte ideal | 48.52% | 90.27% |
| Gerador | 48.26% | 89.69% |

O BESS mantém a demanda intermitente e suaviza a potência da alimentação. Os patamares longos ainda exigem a potência elevada da rede/gerador; a redução global de pico a pico é pequena. Estes resultados não implicam economia de energia, pois o SOC final difere do inicial.

## Gerador e BESS

- Gerador sem BESS: frequência de 59.1670 a 60.3882 Hz.
- Gerador com BESS: frequência de 59.3598 a 59.9996 Hz.
- Fonte ideal com BESS: SOC 49.81996–50.01096%; resíduo de balanço energético 0.491% da energia total carregada/descarregada.
- Gerador com BESS: SOC 49.81640–50.00754%; resíduo de balanço energético 0.493% da energia total carregada/descarregada.

Os ensaios próximos de 20% e 80% confirmaram bloqueio da direção proibida de potência e recuperação ao inverter a solicitação. Contagem de carga independente, limites de corrente/modulação, balanço de potência no PCC, conservação de momento angular e potência da turbina na massa acionada foram verificados.

## Modos torsionais e limite da análise

| Ensaio de pulso, passo 10 µs | Modo 1 [Hz] | Modo 2 [Hz] | MAC mínimo |
|---|---:|---:|---:|
| Sem BESS | 10.61022 | 23.23639 | 1.000000 |
| Com BESS | 10.59130 | 23.22424 | 0.999297 |

Frequências calculadas pelas matrizes de inércia/rigidez: **10.61087 e 23.23671 Hz**. Identificação por espectro de velocidades mecânicas relativas, remoção da velocidade comum e associação por forma modal (MAC). Pulso de 25 MW por 25 ms sobre 250 MW; janela de análise 5,3–19,8 s.

| Alteração 10 → 5 µs | Variação da amplitude do modo 1 | Variação da amplitude do modo 2 |
|---|---:|---:|
| Sem BESS | +1.11% | -0.10% |
| Com BESS | -67.81% | -67.27% |

**As amplitudes torsionais com BESS não convergiram entre os dois passos.** Frequências e formas passaram nos critérios, assim como as grandezas elétricas médias. O VSC ativo mantém forçamento elétrico após o pulso; portanto, as amplitudes não devem ser usadas para quantificar amortecimento físico ou benefício torsional do BESS. Não foi estimada razão de amortecimento.

## Arquivos e rastreabilidade

- [Guia de execução e parâmetros](../../README_250_500MW.md).
- [Verificação numérica completa](validation.json), [portabilidade](portability.json), [revisão](REVIEW.md).
- [Comparação dos quatro casos](../../figures/scale_250_500/comparacao_quatro_casos.png), [suavização](../../figures/scale_250_500/suavizacao_potencia.png), [torques](../../figures/scale_250_500/gerador_multimassa.png), [modos](../../figures/scale_250_500/modos_torcionais.png), [SOC](../../figures/scale_250_500/limites_soc.png).
- Fontes e instruções anteriores preservadas no histórico indicado em `baseline.json`; pacotes anteriores mantidos.

Modelo didático agregado, sem calibração contra máquina ou bateria de fabricante. Não é um projeto executivo de uma instalação de 500 MW.
