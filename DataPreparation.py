import pandas as pd
import matplotlib.pyplot as plt

#UTILITY FUNCTIONS

#remove rows with null values in specific columns
def remove_rows(data):
    data = data.dropna(subset=["veicolo__a___et__conducente"])
    data = data.dropna(subset=["Ora"])
    data = data.dropna(subset=["giorno"])
    data = data[data["tipo_veicoli__b_"].notnull()].dropna(subset=["veicolo__b___sesso_conducente"])
    data = data[data["tipo_veicoli__b_"].notnull()].dropna(subset=["veicolo__b___et__conducente"])
    return data

#READ DATA
data2018 = pd.read_csv("Dataset/INCSTRAD_Microdati_2018.csv")
data2019 = pd.read_csv("Dataset/INCSTRAD_Microdati_2019.csv")
data2020 = pd.read_csv("Dataset/INCSTRAD_Microdati_2020.csv")
data2021 = pd.read_csv("Dataset/INCSTRAD_Microdati_2021.csv")
data2022 = pd.read_csv("Dataset/INCSTRAD_Microdati_2022.csv")

#add all data in a single array
data = [data2018, data2019, data2020, data2021, data2022]

#execute remove_rows function for each dataset
for i in range(len(data)):
    data[i] = remove_rows(data[i])
    print(data[i].shape)
    #print(data[i].isna().sum())


#plot the number of accidents per year
years = [2018, 2019, 2020, 2021, 2022]
#use data array
accidents = [data[i].shape[0] for i in range(len(data))]
#build histogram
plt.bar(years, accidents)
plt.xlabel("Year")
plt.ylabel("Number of accidents")
plt.title("Number of accidents per year")
#plt.show()

#plot the number of deaths in accident per year
percentage = [(data[i]["morti"].sum()/(data[i].shape[0]))*100 for i in range(len(data))]
#build histogram
plt.bar(years, percentage)
plt.xlabel("Year")
plt.ylabel("Percentage of deaths")
plt.title("Percentage of deaths per year")
plt.show()
