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

## Narzędzia i technologie

- **Język**: Python 3.12
- **Zarządzanie zależnościami**: uv
- **Framework DL**: PyTorch
- **Notebooki**: Jupyter
- **Wizualizacja**: seaborn (EDA), plotly (model/trening), matplotlib (edge-case)
- **Embeddingi**: GloVe 300d (Stanford NLP)

## Autor

Aleksander Oleszkiewicz
