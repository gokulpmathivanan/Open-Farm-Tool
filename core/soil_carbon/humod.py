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


def calc_som_loss (npb_result, crop, site_params, fertiliser_n_available = 0):
    """
    Calculate management-induced SOM loss (SOMLOSS).
    
    Based on the nitrogen balance: total plant N minus N from
    all non-SOM sources = N that must have come from SOM mineralisation.
    
    Parameters:
        npb_result: output from calc_n_plant_biomass()
        crop: crop parameters (for legume fixation and NYRN)
        site_params: site C:N ratio, N deposition, NUR values
        fertiliser_n_available: total available N from fertilisers (kg N/ha)
    
    Returns:
        SONMIM, SOMLOSS, and intermediate values (all in kg/ha)
    """

    npb = npb_result["npb_total"]
    leg = crop["legume_fixation"]
    ndyn = crop["n_dynamics"]

    #N from biological fixation
    n_fix = npb * (leg["leg_share"] or 0) * (leg["NDFA"] or 0)

    #N from atmospheric deposition
    n_dep = site_params["n_deposition"]

    #NUR values
    nur_dep = site_params["nur"]        # for deposition
    nur_fert = site_params["nur"]       # same NUR for both deposition and 
    nur_som = site_params["nur_som"]

    #Calculate SONMIM
    