import pandas as pd

filename = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2022.txt"
filename2021 = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2021.txt"
filename2020 = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2020.txt"
filename2019 = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2019.txt"
filename2018 = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2018.txt"
filename2023 = "Dataset/SourceTxtFiles/INCSTRAD_Microdati_2023.txt"


def read_file(filename):
    data = pd.read_csv(filename, delimiter="\t", usecols=["anno", 
                                                          "provincia", 
                                                          "comune", 
                                                          "giorno", 
                                                          "localizzazione_incidente", 
                                                          "condizioni_meteorologiche", 
                                                          "fondo_stradale",
                                                          "natura_incidente", 
                                                          "tipo_veicolo_a", 
                                                          "veicolo__a___sesso_conducente", 
                                                          "veicolo__a___et__conducente", 
                                                          "tipo_veicoli__b_", 
                                                          "veicolo__b___sesso_conducente", 
                                                          "veicolo__b___et__conducente", 
                                                          "morti_entro_24_ore", 
                                                          "morti_entro_30_giorni", 
                                                          "feriti", 
                                                          "Ora",
                                                          "tipo_veicolo__c_"])
    #sostituisci valori vuoti con null in tutte le colonne
    data = data.replace(r'^\s*$', pd.NA, regex=True)

    #rimuovi tutte le righe dove tipo_veicolo_c non è null
    data = data[data["tipo_veicolo__c_"].isnull()]

    data['morti'] = data['morti_entro_24_ore'] + data['morti_entro_30_giorni']
    
    #rimuovi colonne morti_entro_24_ore e morti_entro_30_giorni
    data = data.drop(columns=['morti_entro_24_ore', 'morti_entro_30_giorni','tipo_veicolo__c_'])
    
    return data

data2022 = read_file(filename)
data2022.to_csv("Dataset/INCSTRAD_Microdati_2022.csv", index=False)

data2021 = read_file(filename2021)
data2021.to_csv("Dataset/INCSTRAD_Microdati_2021.csv", index=False)

data2020 = read_file(filename2020)
data2020.to_csv("Dataset/INCSTRAD_Microdati_2020.csv", index=False)

data2019 = read_file(filename2019)
data2019.to_csv("Dataset/INCSTRAD_Microdati_2019.csv", index=False)

data2018 = read_file(filename2018)
data2018.to_csv("Dataset/INCSTRAD_Microdati_2018.csv", index=False)

data2023 = read_file(filename2023)
data2023.to_csv("Dataset/INCSTRAD_Microdati_2023.csv", index=False)
