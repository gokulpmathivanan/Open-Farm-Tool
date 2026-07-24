# Open-Farm-Tool
Development of a sustainability assessment tool from scratch

Current version: https://farm.goku-lab.com/

```mermaid
graph TD
    A[<b>Farm Data</b>] --> C[<b>Soil Carbon</b><br>Pick one or compare</br>]
    A --> D[<b>GHG Emissions</b>]
    A --> E[<b>Co-Benefits</b>]
    
    C --> C1[HU-MOD]
    C --> C2[VDLUFA]
    C --> C3[STAND]
    C --> C4[IPCC]
    
    D --> D1[Soil]
    D --> D2[Livestock]
    D --> D3[Energy]
    
    C1 & C2 & C3 & C4 & D1 & D2 & D3 & E --> F[<b>Balance & Reports</b>]
 

    style A fill:#f0f0f0,stroke:#666,stroke-width:2px,color:#333
    style C fill:#e6f1fb,stroke:#185fa5,color:#185fa5
    style D fill:#faece7,stroke:#993c1d,color:#993c1d
    style E fill:#eeedfe,stroke:#534ab7,color:#534ab7
    style F fill:#e1f5ee,stroke:#0f6e56,stroke-width:2px,color:#0f6e56
    style C1 fill:#e6f1fb,stroke:#85b7eb,color:#333
    style C2 fill:#e6f1fb,stroke:#85b7eb,color:#333
    style C3 fill:#e6f1fb,stroke:#85b7eb,color:#333
    style C4 fill:#e6f1fb,stroke:#85b7eb,color:#333
    style D1 fill:#faece7,stroke:#f0997b,color:#333
    style D2 fill:#faece7,stroke:#f0997b,color:#333
    style D3 fill:#faece7,stroke:#f0997b,color:#333

    style E fill:#eeedfe,stroke:#afa9ec

```
```
openfarmtool/
├── core/                          # Calculation engine
│   ├── farm.py                    # Central farm data model
│   ├── balance.py                 # Aggregates results from all modules
│   ├── soil_carbon/               # Soil carbon methods
│   │   ├── humod.py               # HU-MOD humus balance
│   │   ├── vdlufa.py              # VDLUFA lookup method
│   │   └── ipcc_tier1.py          # IPCC stock change factors
│   ├── emissions/                 # GHG calculations
│   │   ├── soil_n2o.py            # N₂O from soils
│   │   └── energy.py              # Energy CO₂
│   └── cobenefits/                # Biodiversity, soil health, water
├── data/                          # Reference databases
│   ├── humod/                     # HU-MOD parameters
│   │   ├── crop_parameters.json   # 61 crops
│   │   ├── fertiliser_parameters.json  # 29 fertilisers
│   │   └── model_constants.json   # Model constants
│   ├── ipcc/                      # IPCC emission factors
│   └── energy/                    # Grid electricity factors
├── schema/                        # Data validation models
├── io/                            # Excel/CSV/JSON readers and writers
├── tests/                         # Automated tests
├── scripts/                       # Utility scripts (e.g., extraction)
├── docs/                          # Documentation
└── pyproject.toml                 # Package configuration
```
