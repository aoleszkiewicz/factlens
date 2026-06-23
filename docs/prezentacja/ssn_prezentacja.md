---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Klasyfikacja fake-news: TF-IDF → MLP'
footer: 'Sztuczne Sieci Neuronowe'
style: |
  section { font-size: 26px; }
  h1 { color: #1f4e8c; }
  h2 { color: #1f4e8c; }
  table { font-size: 22px; }
  section.lead { text-align: center; }
  .small { font-size: 20px; }
  .cols { display: flex; gap: 1.2em; }
  .cols > div { flex: 1; }
---

<!-- _class: lead -->
# Klasyfikacja fake-news
## Sieć neuronowa TF-IDF → MLP (od zera w PyTorchu)

**Aleksander Oleszkiewicz**
Sztuczne Sieci Neuronowe — projekt

---

## Problem

- **Zadanie:** klasyfikacja binarna artykułów prasowych — *Real* vs *Fake*.
- **Konwencja:** `1 = Real`, `0 = Fake`.
- Zbiór *Fake and Real News* (Kaggle), ~45 tys. artykułów po angielsku.

> **Prawdziwa trudność nie leży w modelu, lecz w danych.**
> Zbiór jest pełen *wycieku informacji* — można uzyskać ~100% trafności
> nie ucząc się treści, tylko artefaktów technicznych.

---

## Zbiór danych — pierwsze spojrzenie

<div class="cols">
<div>

- **44 898** artykułów, klasy niemal zrównoważone (~52% Fake / 48% Real).
- **~14% duplikatów** — niemal wyłącznie w klasie Fake.
- ~1,4% tekstów pustych (same odnośniki YouTube).

</div>
<div>

- Rozkład długości prawoskośny.
- **95. percentyl ≈ 900 słów** → kandydat na `max_seq_len`
  dla modelu sekwencyjnego.

</div>
</div>

---

## Pułapka: data leakage

Informacja wzajemna (MI) demaskuje markery zdradzające klasę bez treści:

| Marker | MI [nat] | Klasa |
|---|---|---|
| słowo „reuters” | **0,650** | Real |
| dateline „MIASTO (Reuters) –” | 0,456 | Real |
| „featured image” | 0,136 | Fake |
| `@handle` | 0,076 | Fake |

- Kolumna `subject` rozdziela klasy **w 100%** → odrzucona.
- `title`, `date` też niosą wyciek → **model używa tylko kolumny `text`**.

---

## Czyszczenie danych

Kaskada wyrażeń regularnych (`src/data/cleaning.py`) usuwa m.in.:
markery Reuters · URL-e · `@handle` · prefiksy clickbait · podpisy zdjęć (getty) ·
HTML · sygnatury serwisów → normalizacja + małe litery.

<div class="cols">
<div>

**Filtr:** `min_words = 10`

**Efekt:**
44 898 → **38 470** artykułów

</div>
<div>

- duplikaty: 13,9% → **0%**
- kluczowe markery: → **0%**
- pokrycie GloVe: OOV ≤ 0,2%

</div>
</div>

Podział **stratyfikowany** 60/20/20 → train 23 082 · val 7 694 · test 7 694.

---

## Reprezentacja: TF-IDF

- Tekst → wektor **TF-IDF** (1–2-gramy, `max_features=50 000`, `min_df=5`, `sublinear_tf`).
- To **nieparametryczna inżynieria cech** — *nie* model pretrenowany.
  → sieć uczy się w całości **od zera**.
- Dopasowanie **tylko na train**; ten sam wektoryzator co baseline
  → uczciwe porównanie LogReg vs MLP.

---

## Architektura MLP

```
TF-IDF (50 000) → Linear(50000, 256) → ReLU → Dropout(0.3) → Linear(256, 1) → logit
```

<div class="cols">
<div>

- Wyjście = **logit** (bez sigmoidy)
  → `BCEWithLogitsLoss` (stabilne numerycznie).
- **12 800 513** parametrów
  (głównie pierwsza warstwa 50k × 256).

</div>
<div>

- Optymalizator: **Adam**, lr = 1e-3
- batch = 256, maks. 20 epok
- **early stopping** na F1 (walidacja),
  `patience = 3`, przywracanie najlepszych wag

</div>
</div>

---

## Trening: krzywe uczenia

![w:760 center](../raport/figures/mlp_krzywe_uczenia.png)

Sieć zbiega w pierwszych epokach; early stopping zatrzymał trening po **11 epokach**.

---

## Wyniki na teście

<div class="cols">
<div>

| Metryka | Walidacja | Test |
|---|---|---|
| accuracy | 0,9908 | 0,9864 |
| precision | 0,9899 | 0,9838 |
| recall | 0,9934 | 0,9915 |
| **F1** | 0,9916 | **0,9877** |
| **ROC-AUC** | 0,9992 | **0,9987** |

</div>
<div>

![w:380](../raport/figures/mlp_macierz_pomylek.png)

</div>
</div>

Metryki ~0,99 — praktyczny **sufit jakości** tego zbioru.

---

## Krzywa ROC

![w:560 center](../raport/figures/mlp_roc.png)

Pole pod krzywą (AUC) = 0,9987 — model niemal idealnie separuje klasy.

---

## Diagnoza bias–variance

<div class="cols">
<div>

![w:480](../raport/figures/mlp_learning_curve.png)

</div>
<div>

- F1 treningowe ≈ 1,0 → **niski bias**
- luka train–val ~0,8 pp i maleje → **niska wariancja**
- krzywa walidacji szybko na plateau

**Wniosek:** więcej danych ani większy model **nie pomogą** — jesteśmy przy suficie zbioru.

</div>
</div>

---

## Baseline vs MLP

| Metryka | LogReg | **MLP** |
|---|---|---|
| accuracy | 0,9795 | **0,9864** |
| F1 | 0,9815 | **0,9877** |
| ROC-AUC | 0,9970 | **0,9987** |

- MLP lepszy o **~0,6 pp F1** — różnica marginalna.
- Klasy niemal liniowo separowalne w TF-IDF → nieliniowość nie daje przewagi.
- **Wartość etapu:** zweryfikowana pętla treningowa PyTorcha pod model docelowy.

---

## Przykładowe predykcje

| Fragment | Prawd. | P(Real) | Pred. | |
|---|---|---|---|---|
| „germany foreign minister said…” | Real | 1,0000 | Real | ✓ |
| „patrick henningsen the longer…” | Fake | 0,0000 | Fake | ✓ |
| „the washington post nearly third…” | Fake | 0,9998 | Real | ✗ |
| „- below are the highlights…” | Real | 0,0015 | Fake | ✗ |

<span class="small">Błędy mają **czytelne przyczyny**: FP — styl agencyjny w tekście Fake; FN — format listy / tematyka rozrywkowa w tekście Real.</span>

---

## Interpretowalność cech

![w:620 center](../raport/figures/logreg_cechy.png)

<span class="small">Real: `said`, `on wednesday`, `president donald` · Fake: `via`, `read more`, `watch`, `video`. **Żaden** usunięty marker wycieku nie wraca — model uczy się stylu, nie stempla.</span>

---

## Wnioski i dalszy krok

- Pierwsza **sieć od zera** w projekcie: TF-IDF → MLP, F1/AUC ~0,99 na teście.
- Na tym zbiorze sieć dorównuje modelowi liniowemu — reżim **low bias / low variance**, sufit metryk.
- Zbudowana i zweryfikowana **pętla treningowa PyTorcha**: Adam, BCEWithLogitsLoss, early stopping, dropout, weight decay, GPU (ROCm).

> **Następny etap:** BiLSTM + Attention z GloVe 300d — modelowanie kontekstu
> i **wyjaśnialność przez wagi atencji** na poziomie pojedynczego artykułu.

---

<!-- _class: lead -->
# Dziękuję za uwagę

Pytania?
