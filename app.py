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

sorted_crop_names = sorted(crop_names.keys())
sorted_fert_names = list(fert_names.keys())

# --- Page ---
st.title("Open Farm Tool")
st.subheader("HU-MOD Humus Balance Calculator")

# Site parameters (collapsible, at the top since they apply to all crops)
with st.expander("Site parameters (defaults shown)"):
    site_cn = st.number_input("Soil C:N ratio", value=10.5)
    n_dep = st.number_input("N deposition (kg N/ha/yr)", value=20.0)
    precip = st.number_input("Precipitation (mm/yr)", value=650)
    winter_share = st.number_input("Winter precip. share (0-1)", value=0.5)
    pore_vol = st.number_input("Pore volume (0-1)", value=0.4)

# --- Rotation input ---
st.markdown("---")
st.subheader("Crop rotation")

n_crops = st.number_input("Number of crops in rotation", min_value=1, max_value=12, value=3, step=1)

# Store crop entries
rotation_entries = []

for i in range(int(n_crops)):
    st.markdown(f"**Year {i + 1}**")
    col1, col2 = st.columns(2)
    with col1:
        crop_choice = st.selectbox(f"Crop", sorted_crop_names, key=f"crop_{i}")
    with col2:
        yield_input = st.number_input(f"Yield (kg FM/ha)", value=6000, step=500, key=f"yield_{i}")
    
    col3, col4 = st.columns(2)
    with col3:
        fert_choice = st.selectbox(f"Fertiliser", sorted_fert_names, key=f"fert_{i}")
    with col4:
        fert_amount = st.number_input(f"Amount (kg FM/ha)", value=0, step=1000, key=f"fert_amt_{i}")
    
    rotation_entries.append({
        "year": i + 1,
        "crop_name": crop_choice,
        "crop_id": crop_names[crop_choice],
        "yield_kg": yield_input,
        "fert_name": fert_choice,
        "fert_id": fert_names[fert_choice],
        "fert_amount": fert_amount,
    })

# --- Calculate ---
st.markdown("---")
if st.button("Calculate humus balance"):
    
    results = []
    
    for entry in rotation_entries:
        crop_data = crops[entry["crop_id"]]
        
        fert_data = None
        fert_amt = 0
        if entry["fert_id"] is not None and entry["fert_amount"] > 0:
            fert_data = ferts[entry["fert_id"]]
            fert_amt = entry["fert_amount"]
        
        result = calc_humus_balance(
            crop_data, entry["yield_kg"], site_cn, n_dep,
            precip, winter_share, pore_vol,
            fert_data, fert_amt
        )
        
        results.append({
            "year": entry["year"],
            "crop_name": entry["crop_name"],
            "fert_name": entry["fert_name"] if entry["fert_name"] != "None" else "—",
            "fert_amount": entry["fert_amount"],
            "som_loss": result["som_loss"]["som_loss"],
            "som_supply": result["som_supply"]["som_supply"],
            "balance": result["humus_balance_kg_soc_ha"],
            "full_result": result,
        })
    
    # --- Rotation summary ---
    mean_balance = sum(r["balance"] for r in results) / len(results)
    
    st.markdown("---")
    st.subheader("Rotation Results")
    
    # Overall metric
    if mean_balance >= 0:
        st.success(f"Rotation mean humus balance: **+{mean_balance:.0f} kg SOC/ha/yr**")
    else:
        st.error(f"Rotation mean humus balance: **{mean_balance:.0f} kg SOC/ha/yr**")
    
    # Per-crop table
    st.markdown("#### Per-crop breakdown")
    
    # Header
    header_cols = st.columns([2, 2, 1.5, 1.5, 1.5])
    header_cols[0].markdown("**Crop**")
    header_cols[1].markdown("**Fertiliser**")
    header_cols[2].markdown("**SOM Loss**")
    header_cols[3].markdown("**SOM Supply**")
    header_cols[4].markdown("**Balance**")
    
    # Rows
    for r in results:
        cols = st.columns([2, 2, 1.5, 1.5, 1.5])
        cols[0].write(f"Yr {r['year']}: {r['crop_name']}")
        cols[1].write(f"{r['fert_name']}")
        cols[2].write(f"{r['som_loss']:.0f}")
        cols[3].write(f"{r['som_supply']:.0f}")
        
        bal = r["balance"]
        if bal >= 0:
            cols[4].write(f":green[+{bal:.0f}]")
        else:
            cols[4].write(f":red[{bal:.0f}]")
    
    # Totals row
    st.markdown("---")
    total_cols = st.columns([2, 2, 1.5, 1.5, 1.5])
    total_cols[0].markdown("**Rotation mean**")
    total_cols[1].write("")
    total_cols[2].write(f"**{sum(r['som_loss'] for r in results) / len(results):.0f}**")
    total_cols[3].write(f"**{sum(r['som_supply'] for r in results) / len(results):.0f}**")
    if mean_balance >= 0:
        total_cols[4].markdown(f"**:green[+{mean_balance:.0f}]**")
    else:
        total_cols[4].markdown(f"**:red[{mean_balance:.0f}]**")
    
    # Detailed view per crop (collapsible)
    st.markdown("---")
    st.subheader("Detailed breakdown")
    
    for r in results:
        with st.expander(f"Year {r['year']}: {r['crop_name']} — Balance: {r['balance']:.0f} kg SOC/ha"):
            col_loss, col_supply = st.columns(2)
            
            full = r["full_result"]
            
            with col_loss:
                st.metric("SOM Loss", f"{full['som_loss']['som_loss']:.0f} kg SOC/ha")
                st.caption("N sources offsetting SOM demand:")
                st.write(f"- N deposition: {full['som_loss']['ndep']:.1f} kg N/ha")
                st.write(f"- Fertiliser N: {full['som_loss']['nftlz']:.1f} kg N/ha")
                st.write(f"- BNF (fixation): {full['som_loss']['nbnf']:.1f} kg N/ha")
            
            with col_supply:
                st.metric("SOM Supply", f"{full['som_supply']['som_supply']:.0f} kg SOC/ha")
                st.caption("C and N inputs to soil:")
                st.write(f"- Residue C: {full['som_supply']['csup_hr']:.0f} kg C/ha")
                st.write(f"- Fertiliser C: {full['som_supply']['csup_ftlz']:.0f} kg C/ha")
                st.write(f"- Residue N: {full['som_supply']['nsup_hr']:.1f} kg N/ha")
                st.write(f"- Fertiliser N: {full['som_supply']['nsup_ftlz']:.1f} kg N/ha")
                limiting = "N-limited" if full['som_supply']['n_limited'] < full['som_supply']['c_limited'] else "C-limited"
                st.write(f"- Limiting factor: **{limiting}**")