"""
HU-MOD Humus Balance Model

From Brock et al. (2012)

A simple model for the assessment of management impact in arable farming systems on soil organic matter (SOM) levels.
The humus balance model (HU-MOD) is designed for application by farmers and extension workers in practice as a tool for management support.
To enable practice applicability, HU-MOD bypasses the need for data on soil parameters and can be run with simple management data. 
HU-MOD is based on a simplified model on carbon and nitrogen pools and fluxes in the soil–plant system. The model proved to be an applicable 
simple tool for the comparison of management systems in arable farming with regard to the impact on SOM levels. Even though an absolute quantification of
SOM level changes is not possible due to the methodical approach bypassing the need for any data on soil parameters, the model may be used to assess a positive
or negative impact of a management system or management period compared to a reference and thus may be used to assess the impact of management changes,
or to analyse a specific impact for different management periods on a defined spatial unit. 

DOI: 10.1007/s10705-012-9487-z

"""

def calc_n_plant_biomass(crop, yield_fm_kg_ha):
    """
    Calculate total nitrogen in plant biomass (NPB) — all compartments.
    
    Parameters:
        crop_id: HU-MOD crop ID (e.g., "1001" for winter wheat)
        yield_fm_kg_ha: main product fresh matter yield (kg/ha)
    
    Returns:
        N in each compartment and total NPB (kg N/ha)
    """
    mp = crop["main_product"]
    sp = crop["side_product"]
    lt = crop["litter"]
    st = crop["stubble"]
    rt = crop["root"]

    #Main product
    mp_dm = yield_fm_kg_ha * (mp["dm_content_mp"] or 0)
    n_main = mp_dm * (mp["n_content_mp"] or 0)

    #Side product
    sp_fm = yield_fm_kg_ha * (sp["ratio_sp_mp"] or 0)
    sp_dm = sp_fm * (sp["dm_content_sp"] or 0)
    n_side = sp_dm * (sp["n_content_sp"] or 0)

    #Litter
    lt_fm = yield_fm_kg_ha * (lt["ratio_lt_mp"] or 0)
    lt_dm = lt_fm * (lt["dm_content_lt"] or 0)
    n_litter = lt_dm * (lt["n_content_lt"] or 0)

    #Stubble
    st_fm = yield_fm_kg_ha * (st["ratio_st_mp"] or 0)
    st_dm = st_fm * (st["dm_content_st"] or 0)
    n_stubble = st_dm * (st["n_content_st"] or 0)

    #Root
    rt_fm = mp_dm * (rt["ratio_root_shoot"] or 0)
    rt_dm = rt_fm * (rt["dm_content_rt"] or 0)
    n_root = rt_dm * (rt["n_content_rt"] or 0 )


    npb = n_main + n_side + n_litter + n_stubble + n_root

    return {
         "n_main_product": n_main,
         "n_side_product": n_side,
         "n_litter": n_litter,
         "n_stubble": n_stubble,
         "n_root": n_root,
         "npb_total": npb,

         # DM values needed for SOMSUP calculation later
         "mp_dm": mp_dm,
         "sp_dm": sp_dm,
         "litter_dm": lt_dm,
         "stubble_dm": st_dm,
         "root_dm": rt_dm,
    }

def calc_ftlznue(default_precipitation_mm, default_winter_precip_share, default_pore_volume):
    """
    Calculate nitrogen utilisation efficiency (NUR) from site parameters.
    
    Based on a leaching model: how much available N can plants capture
    before it moves beyond the root zone?
    
    Parameters:
        default_precipitation_mm: float — mean annual precipitation (mm)
        default_winter_precip_share: float — fraction of precipitation falling Nov-Mar (0-1)
        default_pore_volume: float — soil pore volume in 0-90cm depth (fraction, 0-1)
    
    Returns:
        nitrogen utilisation efficiency (0-1) #float
    """
    nur = 1 - ((default_precipitation_mm/10 * default_winter_precip_share) / (default_precipitation_mm/10 * default_winter_precip_share + default_pore_volume)) ** (0.5 * 90)
    return nur

def calc_fert_n_available(fert, amount_fm_kg_ha, nur):
    """
    Calculate plant-available N from an organic fertiliser application.
    
    Parameters:
        fert: dict — fertiliser parameters from the database
        amount_fm_kg_ha: float — amount applied (kg fresh matter per ha)
        nur: float — nitrogen utilisation rate (from calc_ftlznue)
    
    Returns:
        dict with total N, available fraction, and plant-available N (kg N/ha)
    """
    dm = fert["dm_content_fert"] or 0
    c_content = fert["c_content_fert"] or 0
    n_content = fert["n_content_fert"] or 0

    if n_content == 0 or c_content == 0:
        return {
            "total_n": 0,
            "fnav": 0,
            "available_n":0
        }

    cn_ratio = c_content / n_content

    fnav = 1.6674 * (cn_ratio ** -0.768)

    total_n = amount_fm_kg_ha * dm * n_content

    available_n = total_n * fnav * nur

    return {
        "total_n": total_n,
        "fnav": fnav,
        "available_n": available_n
    }

def calc_som_loss(npb_result, crop, site_cn, n_deposition, nur, fert_n_available=0):
    """
    Calculate management-induced SOM loss (SOMLOSS).
    
    Parameters:
        npb_result: dict — output from calc_n_plant_biomass()
        crop: dict — crop parameters (for legume fixation and NYRN)
        site_cn: float — site C:N ratio (default 10.5)
        n_deposition: float — atmospheric N deposition (kg N/ha/yr)
        nur: float — nitrogen utilisation rate (from calc_ftlznue)
        fert_n_available: float — plant-available N from fertiliser (kg N/ha)
    
    Returns:
        dict with NDEP, NFTLZ, NBNF, NNYR, SOMLOSS (all in kg/ha)
    """
    ndep = n_deposition * nur

    npb = npb_result["npb_total"]
    nftlzmax = 0.6 # Max 60% of crop N from fertiliser
    nftlz = min(npb * nftlzmax, fert_n_available)

    leg_share = crop["legume_fixation"]["leg_share"] or 0
    ndfa = crop["legume_fixation"]["NDFA"] or 0
    nbnf = max(0, npb * leg_share * ndfa - nftlz - ndep)

    nyrn = crop["n_dynamics"]["NYRN"] or 0
    nnyr = nyrn * (1- nur)

    som_loss = site_cn * (max(0, npb - nbnf - nftlz - ndep) - nnyr)

    return {
        "ndep": ndep,
        "nftlz": nftlz,
        "nbnf": nbnf,
        "nnyr": nnyr,
        "som_loss": som_loss
    }

def calc_som_supply(npb_result, crop, fert=None, fert_amount_fm_kg_ha=0, site_cn=10.5, extra_c=0, extra_n=0):
    """
    Calculate SOM supply (SOMSUP)
    
    Parameters:
        npb_result: dict — output from calc_n_plant_biomass()
        crop: dict — crop parameters (for C and N contents)
        fert: dict or None — fertiliser parameters (None if no fertiliser)
        fert_amount_fm_kg_ha: float — fertiliser amount (kg FM/ha)
        site_cn: float — site C:N ratio
    
    Returns:
        dict with CSUP_HR, NSUP_HR, CSUP_FTLZ, NSUP_FTLZ, SOMSUP
    """
    lt = crop["litter"]
    st = crop["stubble"]
    rt = crop["root"]

    # C supply from harvest residues (litter + stubble + roots)
    csup_hr = (npb_result["litter_dm"] * (lt["c_content_lt"] or 0)
             + npb_result["stubble_dm"] * (st["c_content_st"] or 0)
             + npb_result["root_dm"] * (rt["c_content_rt"] or 0))

    # N supply from harvest residues
    nsup_hr = (npb_result["litter_dm"] * (lt["n_content_lt"] or 0)
             + npb_result["stubble_dm"] * (st["n_content_st"] or 0)
             + npb_result["root_dm"] * (rt["n_content_rt"] or 0))

    # Fertiliser C and N supply
    csup_ftlz = 0
    nsup_ftlz = 0

    if fert is not None and fert_amount_fm_kg_ha > 0:
        dm = fert["dm_content_fert"] or 0
        c_content = fert["c_content_fert"] or 0
        n_content = fert["n_content_fert"] or 0

        csup_ftlz = fert_amount_fm_kg_ha * dm * c_content

        if n_content > 0 and c_content > 0:
            cn_ratio = c_content / n_content
            nfav = 1.6674 * (cn_ratio ** -0.768)
            # N retained in soil = total N × (1 - fraction taken by plants)
            nsup_ftlz = fert_amount_fm_kg_ha * dm * n_content * (1 - nfav)

    # Add carry-forward C and N from previous year's residues
    csup_ftlz = csup_ftlz + extra_c
    nsup_ftlz = nsup_ftlz + extra_n

    # SOMSUP = MIN of N-limited and C-limited
    n_limited = (nsup_hr + nsup_ftlz) * site_cn
    c_limited = csup_hr + csup_ftlz

    som_supply = min(n_limited, c_limited)

    return {
        "csup_hr": csup_hr,
        "nsup_hr": nsup_hr,
        "csup_ftlz": csup_ftlz,
        "nsup_ftlz": nsup_ftlz,
        "n_limited": n_limited,
        "c_limited": c_limited,
        "som_supply": som_supply
    }

def process_rotation(rotation_entries, crops, ferts, site_cn=10.5,
                     n_deposition=20, precipitation_mm=650,
                     winter_precip_share=0.5, pore_volume=0.4):
    """
    Process a crop rotation, carrying forward straw and green manure
    from one year to the next.
    """
    results = []
    carry_forward_c = 0
    carry_forward_n = 0
    
    nur = calc_ftlznue(precipitation_mm, winter_precip_share, pore_volume)
    
    for i, entry in enumerate(rotation_entries):
        crop_data = crops[entry["crop_id"]]
        
        npb_result = calc_n_plant_biomass(crop_data, entry["yield_kg"])
        
        # Fertiliser inputs
        fert_data = None
        fert_amt = 0
        fert_n = 0
        if entry["fert_id"] is not None and entry["fert_amount"] > 0:
            fert_data = ferts[entry["fert_id"]]
            fert_amt = entry["fert_amount"]
            fert_result = calc_fert_n_available(fert_data, fert_amt, nur)
            fert_n = fert_result["available_n"]
        
        # Use carry-forward from previous year
        extra_c = carry_forward_c
        extra_n = carry_forward_n
        
        # Calculate loss and supply
        loss = calc_som_loss(npb_result, crop_data, site_cn, n_deposition, nur, fert_n)
        supply = calc_som_supply(npb_result, crop_data, fert_data, fert_amt, site_cn, extra_c, extra_n)
        balance = supply["som_supply"] - loss["som_loss"]
        
        # Determine what carries forward to NEXT year
        carry_forward_c = 0
        carry_forward_n = 0
        
        sp = crop_data["side_product"]
        
        if entry["sp_use"] == "Left on field":
            carry_forward_c = npb_result["sp_dm"] * (sp["c_content_sp"] or 0)
            carry_forward_n = npb_result["sp_dm"] * (sp["n_content_sp"] or 0)
        
        elif entry["sp_use"] == "Crop mulched (green manure)":
            mp = crop_data["main_product"]
            carry_forward_c = (npb_result["mp_dm"] * (mp["c_content_mp"] or 0)
                             + npb_result["sp_dm"] * (sp["c_content_sp"] or 0))
            carry_forward_n = (npb_result["mp_dm"] * (mp["n_content_mp"] or 0)
                             + npb_result["sp_dm"] * (sp["n_content_sp"] or 0))
        
        results.append({
            "year": entry["year"],
            "crop_name": entry["crop_name"],
            "fert_name": entry.get("fert_name", "—"),
            "sp_use": entry["sp_use"],
            "carry_forward_c": extra_c,
            "carry_forward_n": extra_n,
            "som_loss": loss,
            "som_supply": supply,
            "balance": balance,
            "npb": npb_result,
        })
    
    return results

