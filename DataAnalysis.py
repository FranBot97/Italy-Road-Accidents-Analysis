import pandas as pd
import matplotlib.pyplot as plt

data2022 = pd.read_csv("Dataset/INCSTRAD_Microdati_2022.csv")
data2018 = pd.read_csv("Dataset/INCSTRAD_Microdati_2018.csv")

#calcola quanti maschi coinvolti negli incidenti sia su veicolo a che su veicolo b
maschi2018 = data2018['veicolo__a___sesso_conducente'].value_counts()[1] + data2018['veicolo__b___sesso_conducente'].value_counts()[1]
femmine2018 = data2018['veicolo__a___sesso_conducente'].value_counts()[2] + data2018['veicolo__b___sesso_conducente'].value_counts()[2]


#calcola quanti maschi coinvolti negli incidenti sia su veicolo a che su veicolo b
maschi2022 = data2022['veicolo__a___sesso_conducente'].value_counts()[1] + data2022['veicolo__b___sesso_conducente'].value_counts()[1]
femmine2022 = data2022['veicolo__a___sesso_conducente'].value_counts()[2] + data2022['veicolo__b___sesso_conducente'].value_counts()[2]


#crea un grafico a barre maschi e femmine sommati divisi per anno
fig, ax = plt.subplots()
barWidth = 0.25
r1 = [1,2]
r2 = [x + barWidth for x in r1]
plt.bar(r1, [maschi2018, femmine2018], color='b', width=barWidth, edgecolor='grey', label='2018')
plt.bar(r2, [maschi2022, femmine2022], color='r', width=barWidth, edgecolor='grey', label='2022')
plt.xlabel('Sesso')
plt.xticks([1.5, 2.5], ['Maschi', 'Femmine'])
plt.ylabel('Numero di persone')
plt.title('Conducenti che hanno causato l\'incidente divisi per sesso')
plt.legend()
plt.show()
