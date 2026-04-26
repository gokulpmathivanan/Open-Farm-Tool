import streamlit as st
import json
from core.soil_carbon.humod import calc_humus_balance

# Load databases
with open("data/humod/crop_parameters.json", "r", encoding="utf-8") as f:
    crops = json.load(f)

with open("data/humod/fertiliser_parameters.json", "r", encoding="utf-8") as f:
    ferts = json.load(f)

# Build lookup dictionaries (name → ID)
crop_names = {crops[cid]["name"]: cid for cid in crops}
fert_names = {"None": None}
fert_names.update({ferts[fid]["name"]: fid for fid in ferts})

# --- Page ---
st.title("Open Farm Tool")
st.subheader("HU-MOD Humus Balance Calculator")

# Crop selection
col1, col2 = st.columns(2)
with col1:
    selected_crop = st.selectbox("Select crop", sorted(crop_names.keys()))
with col2:
    yield_input = st.number_input("Yield (kg FM/ha)", value=6000, step=500)

# Fertiliser selection
col3, col4 = st.columns(2)
with col3:
    selected_fert = st.selectbox("Select fertiliser", fert_names.keys())
with col4:
    fert_amount = st.number_input("Amount (kg FM/ha)", value=0, step=1000)

# Site parameters (collapsible)
with st.expander("Site parameters (defaults shown)"):
    site_cn = st.number_input("Soil C:N ratio", value=10.5)
    n_dep = st.number_input("N deposition (kg N/ha/yr)", value=20.0)
    precip = st.number_input("Precipitation (mm/yr)", value=650)
    winter_share = st.number_input("Winter precip. share (0-1)", value=0.5)
    pore_vol = st.number_input("Pore volume (0-1)", value=0.4)

# Calculate
if st.button("Calculate humus balance"):
    crop_id = crop_names[selected_crop]
    crop_data = crops[crop_id]
    
    fert_data = None
    fert_amt = 0
    if selected_fert != "None" and fert_amount > 0:
        fert_id = fert_names[selected_fert]
        fert_data = ferts[fert_id]
        fert_amt = fert_amount

    result = calc_humus_balance(
        crop_data, yield_input, site_cn, n_dep,
        precip, winter_share, pore_vol,
        fert_data, fert_amt
    )

    # Display result
    balance = result["humus_balance_kg_soc_ha"]
    
    if balance >= 0:
        st.success(f"Humus balance: +{balance:.0f} kg SOC/ha")
    else:
        st.error(f"Humus balance: {balance:.0f} kg SOC/ha")

    # Breakdown
    col_loss, col_supply = st.columns(2)
    with col_loss:
        st.metric("SOM Loss", f"{result['som_loss']['som_loss']:.0f} kg SOC/ha")
        st.caption("N sources offsetting SOM demand:")
        st.write(f"- N deposition: {result['som_loss']['ndep']:.1f} kg N/ha")
        st.write(f"- Fertiliser N: {result['som_loss']['nftlz']:.1f} kg N/ha")
        st.write(f"- BNF (fixation): {result['som_loss']['nbnf']:.1f} kg N/ha")

    with col_supply:
        st.metric("SOM Supply", f"{result['som_supply']['som_supply']:.0f} kg SOC/ha")
        st.caption("C and N inputs to soil:")
        st.write(f"- Residue C: {result['som_supply']['csup_hr']:.0f} kg C/ha")
        st.write(f"- Fertiliser C: {result['som_supply']['csup_ftlz']:.0f} kg C/ha")
        st.write(f"- Residue N: {result['som_supply']['nsup_hr']:.1f} kg N/ha")
        st.write(f"- Fertiliser N: {result['som_supply']['nsup_ftlz']:.1f} kg N/ha")
        limiting = "N-limited" if result['som_supply']['n_limited'] < result['som_supply']['c_limited'] else "C-limited"
        st.write(f"- Limiting factor: **{limiting}**")