# Data center intermitente — PSCAD 5.1

## Video and reproducibility

The current English video illustrates abrupt loads, a parallel BESS and the observed generator-shaft response using the existing PSCAD simulations.

- [Final video — 1080p, 30 fps, 88.3 s](video/BESS_Load_Smoothing/output/BESS_Abrupt_Loads_1080p.mp4)
- [Video sources, data and reproduction instructions](video/BESS_Load_Smoothing/README.md)
- [Video frame overview](video/BESS_Load_Smoothing/evidence/contact_sheet_final.jpg)
- [Editable four-case PSCAD model package](delivery/DataCenter_250_500MW_Modelos.zip)
- [GitHub snapshot scope](GITHUB_SYNC.md)

The latest video has five scenes, ends on measured power results, and uses the corrected converter symbol: AC at the upper bus connection and DC at the lower battery connection. Electrical smoothing is measured; the shaft traces do not establish a convergence-validated torsional damping improvement.

## PSCAD study

A revisão atual contém **quatro simulações com carga intermitente de 250–500 MW**: fonte ideal ou gerador acionado por turbina a gás com eixo multimassa, cada um com e sem BESS de 250 MW/125 MWh.

Abra [o workspace com os quatro casos](pscad/DataCenter_Quatro_Casos.pswx). Consulte [as instruções completas](README_250_500MW.md), [os resultados desta revisão](validation/scale_250_500/RESULTADOS.md) e [a comparação gráfica](figures/scale_250_500/comparacao_quatro_casos.png).

As instruções e modelos anteriores foram preservados em `history/before_250_500MW_20261026_182420/`. Resultados e pacotes antigos descrevem a escala anterior. Use somente os scripts `scale` / `250_500` para reconstruir e executar esta revisão.
