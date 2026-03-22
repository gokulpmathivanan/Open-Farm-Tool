import json
from core.soil_carbon.humod import calc_n_plant_biomass

with open("data/humod/crop_parameters.json", "r", encoding= "utf-8") as f:
    crops = json.load(f)



result = calc_n_plant_biomass(crops["1001"], 6000)
print("Winter wheat (6000 kg/ha):")
for key, value in result.items():
    print(f"  {key}: {value:.2f}")
