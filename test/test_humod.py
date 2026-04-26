import json
from core.soil_carbon.humod import calc_n_plant_biomass

with open("data/humod/crop_parameters.json", "r", encoding= "utf-8") as f:
    crops = json.load(f)



result = calc_n_plant_biomass(crops["1001"], 6000)
print("Winter wheat (6000 kg/ha):")
for key, value in result.items():
    print(f"  {key}: {value:.2f}")

from core.soil_carbon.humod import calc_fert_n_available
import json

with open("data/humod/fertiliser_parameters.json") as f:
    ferts = json.load(f)

result = calc_fert_n_available(ferts["1041"], 15000, 0.423)
print(result)

import json
from core.soil_carbon.humod import calc_n_plant_biomass, calc_ftlznue, calc_som_loss, calc_som_supply, calc_humus_balance

with open("data/humod/crop_parameters.json") as f:
    crops = json.load(f)

result = calc_humus_balance(crops["1004"], 5500, site_cn=10,
                            fert=ferts["1041"], fert_amount_fm_kg_ha=45000)
print(f"Humus balance: {result['humus_balance_kg_soc_ha']:.0f} kg SOC/ha")