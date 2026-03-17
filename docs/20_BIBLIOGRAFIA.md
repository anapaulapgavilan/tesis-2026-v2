> **Archivos fuente:**
> - *(Documento teórico — no referencia scripts directamente)*

# Bibliografía clave (DiD / econometría aplicada) y dónde se referencian

Este documento resume las referencias metodológicas esenciales usadas para justificar:
(i) limitaciones del TWFE con adopción escalonada, (ii) event studies y dinámica con heterogeneidad,
(iii) estimandos ATT por cohortes, (iv) stacked DiD, y (v) buenas prácticas/robustez en DiD.

---

## 1) Mapa de referencias (qué justifica cada paper y dónde citarlo)

| Tema que justificas | Referencia(s) | Dónde citar en la tesis/docs |
|---|---|---|
| Problema de TWFE con adopción escalonada (*staggered adoption*) | Goodman-Bacon (2021) | **Doc 09** (estrategia/identificación: TWFE ≠ ATT bajo timing heterogéneo), **Doc 10 §4.5–§4.6** (motivación e interpretación de discrepancias TWFE vs stacked), **Doc 11** (nota técnica del estimador) |
| Event study: problemas de dinámica bajo heterogeneidad y alternativas | Sun & Abraham (2021) | **Doc 09** (especificación de event study y advertencias), **Doc 10 §4.3** (diagnóstico de tendencias paralelas / interpretación), **Doc 11** (definición de event time y discusión técnica) |
| ATT por cohortes / DiD con múltiples periodos | Callaway & Sant’Anna (2021) | **Doc 09** (sección de estimandos modernos; ATT por cohorte/tiempo), **Doc 10 §4.5** (cuando defines el estimando y el rol del grupo control), **Doc 11** (como benchmark conceptual, aun usando stacked) |
| Stacked DiD (extensión futura recomendada) | Cengiz, Dube, Lindner & Zipperer (2019) | **Doc 10 §11** (recomendación como extensión), **Doc 17 §4.6** (recomendación formal), **Doc 09** (estimadores modernos) |
| Buenas prácticas: sensibilidad, pre-trends, transparencia en DiD | Roth et al. (2023) | **Doc 09** (justificación de robusteces pre-especificadas y sensibilidad), **Doc 10 §4.5–§4.6** (enmarcar comparación de estimadores como práctica recomendada), opcional en **README** (1 línea de motivación metodológica) |

---

## 2) Bibliografía (formato autor–año estilo economía)

### Goodman-Bacon (2021)
Goodman-Bacon, Andrew. 2021. “Difference-in-Differences with Variation in Treatment Timing.” *Journal of Econometrics* 225(2): 254–277.

**Uso recomendado en el texto:** para explicar por qué TWFE puede mezclar comparaciones tratadas-vs-tratadas y producir ponderaciones problemáticas cuando hay heterogeneidad temporal del efecto.

---

### Sun & Abraham (2021)
Sun, Liyang, and Sarah Abraham. 2021. “Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects.” *Journal of Econometrics* 225(2): 175–199.

**Uso recomendado en el texto:** para motivar cautela en event studies “naive” bajo adopción escalonada, y para enmarcar alternativas/diagnósticos robustos de dinámica.

---

### Callaway & Sant’Anna (2021)
Callaway, Brantly, and Pedro H. C. Sant’Anna. 2021. “Difference-in-Differences with Multiple Time Periods.” *Journal of Econometrics* 225(2): 200–230.

**Uso recomendado en el texto:** para definir ATT por cohorte/tiempo con timing heterogéneo y clarificar el estimando causal en diseños con múltiples periodos.

---

### Cengiz, Dube, Lindner & Zipperer (2019)
Cengiz, Doruk, Arindrajit Dube, Attila Lindner, and Ben Zipperer. 2019. “The Effect of Minimum Wages on Low-Wage Jobs.” *The Quarterly Journal of Economics* 134(3): 1405–1454.

**Uso recomendado en el texto:** para citar el enfoque stacked (apilar ventanas por cohorte) como estrategia de identificación/estimación usada en la robustez moderna.

---

### Roth et al. (2023)
Roth, Jonathan, Pedro H. C. Sant’Anna, Alyssa Bilinski, and John Poe. 2023. “What’s Trending in Difference-in-Differences? A Synthesis of the Recent Econometrics Literature.” Working paper / survey.

**Uso recomendado en el texto:** para justificar buenas prácticas (robusteces, sensibilidad, reporte de pre-trends, transparencia) y enmarcar la comparación entre estimadores como parte de una estrategia de inferencia responsable.

> Nota: Este documento circula en distintas versiones (working paper). En la versión final de la tesis conviene fijar una versión específica (NBER/SSRN/arXiv o enlace oficial de los autores) y citar esa.

---

## 3) BibTeX (opcional para Overleaf/Zotero)

```bibtex
@article{goodmanbacondid2021,
  title={Difference-in-Differences with Variation in Treatment Timing},
  author={Goodman-Bacon, Andrew},
  journal={Journal of Econometrics},
  volume={225},
  number={2},
  pages={254--277},
  year={2021}
}

@article{sunabraham2021,
  title={Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects},
  author={Sun, Liyang and Abraham, Sarah},
  journal={Journal of Econometrics},
  volume={225},
  number={2},
  pages={175--199},
  year={2021}
}

@article{callawaysantanna2021,
  title={Difference-in-Differences with Multiple Time Periods},
  author={Callaway, Brantly and Sant'Anna, Pedro H. C.},
  journal={Journal of Econometrics},
  volume={225},
  number={2},
  pages={200--230},
  year={2021}
}

@article{cengiz2019qje,
  title={The Effect of Minimum Wages on Low-Wage Jobs},
  author={Cengiz, Doruk and Dube, Arindrajit and Lindner, Attila and Zipperer, Ben},
  journal={The Quarterly Journal of Economics},
  volume={134},
  number={3},
  pages={1405--1454},
  year={2019}
}

@techreport{roth2023trendingdid,
  title={What’s Trending in Difference-in-Differences? A Synthesis of the Recent Econometrics Literature},
  author={Roth, Jonathan and Sant’Anna, Pedro H. C. and Bilinski, Alyssa and Poe, John},
  year={2023},
  institution={Working Paper}
}

