# Projekt — Sztuczne Sieci Neuronowe

## Temat

Klasyfikacja wiarygodności artykułów prasowych z wykorzystaniem głębokich sieci neuronowych (BiLSTM + Attention).

## Cel projektu

Zaprojektowanie i wytrenowanie modelu głębokiej sieci neuronowej, który klasyfikuje artykuły prasowe jako wiarygodne (real) lub niewiarygodne (fake). Model wykorzystuje architekturę BiLSTM z mechanizmem attention, co pozwala na interpretację decyzji klasyfikatora poprzez identyfikację fragmentów tekstu o największym wpływie na predykcję.

## Zbiór danych

- **Źródło**: Kaggle — `clmentbisaillon/fake-and-real-news-dataset`
- **Rozmiar po czyszczeniu**: 38 475 artykułów
- **Kolumny**: `text` (treść artykułu), `label` (0 = fake, 1 = real)
- **Balans klas**: zbiór jest w przybliżeniu zbalansowany (~50/50)

## Architektura modelu

- **Embeddingi**: GloVe 300d (pretrenowane wektory słów)
- **Encoder**: Bidirectional LSTM (BiLSTM)
- **Mechanizm attention**: warstwa attention nad sekwencją stanów ukrytych BiLSTM
- **Warstwy ukryte**: aktywacja ReLU / Leaky ReLU
- **Klasyfikator**: warstwa w pełni połączona z wyjściem sigmoid (klasyfikacja binarna)

## Metryki ewaluacji

- Accuracy
- Precision, Recall, F1-score
- Macierz pomyłek (confusion matrix)
- Krzywa ROC / AUC

---

## Terminarz

| # | Etap | Opis | Termin | Status |
|---|------|------|--------|--------|
| 1 | Eksploracyjna analiza danych (EDA) | Analiza rozkładów klas, długości tekstów, dystrybucji tematów, wykrywanie duplikatów | — | Wykonane |
| 2 | Analiza wycieku danych (leakage) | Identyfikacja artefaktów metadanych (markery Reuters, adresy URL, wzorce specyficzne dla źródeł) za pomocą testów chi-kwadrat i informacji wzajemnej | — | Wykonane |
| 3 | Preprocessing tekstu | Usunięcie artefaktów, normalizacja tekstu, filtracja krótkich artykułów, export wyczyszczonego datasetu | — | Wykonane |
| 4 | Tokenizacja i budowa słownika | Tokenizacja tekstów, budowa słownika (word→index), ustalenie max długości sekwencji, padding | 15.04 | Do wykonania |
| 5 | Przygotowanie embeddingów | Załadowanie pretrenowanych wektorów GloVe 300d, utworzenie macierzy embeddingów dla słownika | 15.04 | Do wykonania |
| 6 | Podział danych i implementacja modelu | Podział train/val/test (80/10/10), stratyfikacja; implementacja architektury BiLSTM + Attention | 15.04 | Do wykonania |
| 7 | Trening i walidacja | Trening modelu, monitorowanie loss i metryk na zbiorze walidacyjnym, early stopping | 29.04 | Do wykonania |
| 8 | Tuning hiperparametrów | Dobór hiperparametrów: learning rate, hidden size, liczba warstw LSTM, dropout, batch size | 29.04 | Do wykonania |
| 9 | Ewaluacja na zbiorze testowym | Obliczenie metryk (accuracy, precision, recall, F1, AUC), wygenerowanie macierzy pomyłek i krzywej ROC | 13.05 | Do wykonania |
| 10 | Analiza attention (XAI) | Wizualizacja wag attention dla wybranych przykładów, analiza jakie fragmenty tekstu wpływają na predykcję | 13.05 | Do wykonania |
| 11 | Dokumentacja wyników | Podsumowanie eksperymentów, opis wyników, wnioski | 13.05 | Do wykonania |

**Zajęcia projektowe**: co 2 tygodnie — 15.04, 29.04, 13.05, 27.05, 03.06.2026 (oddanie)

---

## Narzędzia i technologie

- **Język**: Python 3.12
- **Zarządzanie zależnościami**: uv
- **Framework DL**: PyTorch
- **Notebooki**: Jupyter
- **Wizualizacja**: seaborn (EDA), plotly (model/trening), matplotlib (edge-case)
- **Embeddingi**: GloVe 300d (Stanford NLP)

## Autor

Aleksander Oleszkiewicz
