# helper/ingredients.py

SKIN_TYPE_EXCEPTIONS = {
    "sensitive": [
        {"name": "Fragrance", "category": "Sensitizer", "reason": "Causes contact dermatitis, stinging, and micro-inflammation."},
        {"name": "Alcohol Denat", "category": "Drying Alcohol", "reason": "Strips intercellular lipids and damages weakened skin barriers."},
        {"name": "Essential Oils", "category": "Volatile Botanical", "reason": "Contains terpenes (linalool, limonene) that trigger flare-ups."},
        {"name": "Sodium Lauryl Sulfate", "category": "Harsh Surfactant", "reason": "Disrupts the acid mantle and produces severe barrier disruption."},
        {"name": "Oxybenzone", "category": "Chemical UV Filter", "reason": "High incidence of photoallergic contact sensitization."},
        {"name": "Synthetic Dyes", "category": "Colorant", "reason": "Artificial color additives often provoke inflammatory reactions."}
    ],
    "oily": [
        {"name": "Coconut Oil", "category": "Comedogenic Lipid", "reason": "Kizman Comedogenicity Scale rating 4-5; rapidly occludes follicular openings."},
        {"name": "Mineral Oil", "category": "Heavy Occlusive", "reason": "Forms heavy film on epidermis, trapping excess sebum in hyperseborrheic skin."},
        {"name": "Lanolin", "category": "Comedogenic Wax", "reason": "Promotes microcomedone formation in oil-rich follicular environments."},
        {"name": "Isopropyl Myristate", "category": "Comedogenic Ester", "reason": "Penetrates and clogs follicular infundibulum, aggravating acne."},
        {"name": "Cocoa Butter", "category": "Heavy Lipid", "reason": "Extremely rich in saturated fats that occlude pores."}
    ],
    "dry": [
        {"name": "Alcohol Denat", "category": "Drying Alcohol", "reason": "Accelerates transepidermal water loss (TEWL) and causes flaking."},
        {"name": "Isopropyl Alcohol", "category": "Astringent Alcohol", "reason": "Dehydrates the stratum corneum, compromising natural moisturizing factors (NMF)."},
        {"name": "High-dose Salicylic Acid", "category": "BHA Keratolytic", "reason": "Depletes residual epidermal lipids without sufficient barrier replenishment."},
        {"name": "Kaolin / Bentonite Clay", "category": "Adsorbent", "reason": "Excessively adsorbs moisture and protective sebum from hyposeborrheic skin."},
        {"name": "Witch Hazel", "category": "Astringent", "reason": "High tannin and alcohol content induce excessive tissue tightness and dehydration."}
    ],
    "combination": [
        {"name": "Coconut Oil", "category": "Comedogenic Lipid", "reason": "Triggers follicular clogging on the seborrheic T-Zone."},
        {"name": "Alcohol Denat", "category": "Drying Alcohol", "reason": "Aggravates dehydration and dryness on the lateral cheeks/U-Zone."}
    ],
    "acne-prone": [
        {"name": "Isopropyl Palmitate", "category": "Comedogenic Ester", "reason": "Known hyperkeratotic trigger leading to comedogenesis."},
        {"name": "Ethylhexyl Palmitate", "category": "Comedogenic Solvent", "reason": "Proven high comedogenicity; accelerates Cutibacterium acnes proliferation."},
        {"name": "Algae Extract", "category": "Irritant / Comedogenic", "reason": "Can inflame sebaceous canals and accelerate follicular hyperkeratosis."},
        {"name": "Laureth-4", "category": "Comedogenic Emulsifier", "reason": "High comedogenic score (5/5); direct contributor to breakout cycles."},
        {"name": "D&C Red Dyes", "category": "Comedogenic Colorant", "reason": "Coal tar derivatives specifically associated with acne cosmetica."}
    ],
    "normal": [
        {"name": "Harsh Physical Scrubs (Walnut/Apricot)", "category": "Physical Exfoliant", "reason": "Produces micro-tears on healthy stratum corneum."},
        {"name": "Concentrated Sulfates", "category": "Harsh Surfactant", "reason": "Unnecessary harsh stripping of balanced lipid barrier."}
    ]
}

SKIN_TYPE_TIPS = {
    "sensitive": [
        "Prioritize fragrance-free, hypoallergenic formulations with minimal ingredient lists.",
        "Look for barrier-repair ingredients such as Ceramides, Centella Asiatica, and Madecassoside.",
        "Always perform a 24-hour patch test before introducing new active treatments."
    ],
    "oily": [
        "Use lightweight, gel-based or water-based hydrating serums.",
        "Incorporate Niacinamide and Zinc PCA to regulate excess sebum production.",
        "Cleanse with gentle non-comedogenic foaming cleansers twice daily."
    ],
    "dry": [
        "Layer humectants (Hyaluronic Acid, Glycerin) followed by rich emollient creams.",
        "Avoid steaming hot water when washing facial skin to preserve natural lipids.",
        "Incorporate squalane or fatty acid-rich moisturizers to seal moisture."
    ],
    "combination": [
        "Practice zone-mapping: use lightweight hydration on T-zone and richer creams on U-zone.",
        "Use mild chemical exfoliants (like Mandelic Acid or low-dose BHA) selectively on congested areas."
    ],
    "acne-prone": [
        "Look for non-comedogenic labels on all moisturizers and sunscreens.",
        "Incorporate Salicylic Acid (BHA) or Azelaic Acid to unclog pores and calm redness.",
        "Never pick or squeeze active lesions to prevent secondary bacterial infection and scarring."
    ],
    "normal": [
        "Maintain skin equilibrium with daily broad-spectrum SPF 30+ sunscreen.",
        "Support cellular antioxidant defense using Vitamin C or E in morning routines."
    ]
}

def get_avoided_ingredients_for_skin(skin_type: str) -> list:
    """Retrieve structured avoided ingredients for a given skin classification."""
    clean_type = (skin_type or "").strip().lower()
    return SKIN_TYPE_EXCEPTIONS.get(clean_type, SKIN_TYPE_EXCEPTIONS.get("normal", []))

def get_skin_health_tips(skin_type: str) -> list:
    """Retrieve dermatological skin care tips for a given skin classification."""
    clean_type = (skin_type or "").strip().lower()
    return SKIN_TYPE_TIPS.get(clean_type, SKIN_TYPE_TIPS.get("normal", []))

# Backward compatibility aliases
ingredients_avoid_oily = [
    "Mineral Oil", "Lanolin", "Petrolatum", "Coconut Oil", "Isopropyl Myristate",
    "Isopropyl Palmitate", "Myristyl Myristate", "Stearic Acid", "Beeswax", "Silicone",
    "Dimethicone", "Sodium Lauryl Sulfate", "Alcohol Denat", "Fragrance", "Cocoa Butter",
    "PEGs (Polyethylene Glycols)", "Algae Extract", "Butyl Stearate", "Oleyl Alcohol"
]

ingredients_avoid_dry = [
    "Alcohol Denat", "Ethanol", "SD Alcohol", "Isopropyl Alcohol",
    "Fragrance", "Menthol", "Camphor", "Witch Hazel", "Sodium Lauryl Sulfate",
    "Benzoyl Peroxide", "Retinol (tanpa moisturizer)", "Clay", "Charcoal",
    "Salicylic Acid (dalam kadar tinggi)", "AHA/BHA"
]

ingredients_avoid_normal = [
    "Fragrance", "Essential Oils (Tea Tree, Peppermint, Citrus Oils)",
    "Alcohol Denat", "Sodium Lauryl Sulfate", "Harsh Exfoliants (Walnut Shells, Apricot Scrub)",
    "Synthetic Dyes", "Bismuth Oxychloride", "Parabens (bagi yang sensitif)"
]

ingredients_avoid_acne = [
    "Coconut Oil", "Lanolin", "Isopropyl Myristate", "Isopropyl Palmitate", "Laureth-4",
    "Myristyl Myristate", "Butyl Stearate", "Algae Extract", "Silicone", "Fragrance",
    "Alcohol Denat", "Sodium Lauryl Sulfate", "Benzaldehyde", "Cocoa Butter",
    "Ethylhexyl Palmitate", "Oxybenzone", "Mineral Oil", "Petrolatum", "D&C Red Dyes"
]

ingredients_avoid_sensitive = [
    "Fragrance", "Essential Oils (Lavender, Citrus, Peppermint, Eucalyptus)",
    "Alcohol Denat", "Ethanol", "SD Alcohol", "Menthol", "Camphor",
    "Witch Hazel", "Benzoyl Peroxide", "Salicylic Acid (konsentrasi tinggi)",
    "Retinol/Retinoids (tanpa pengawasan dokter)", "AHA/BHA",
    "Sodium Lauryl Sulfate", "Artificial Colorants", "Methylisothiazolinone",
    "Formaldehyde Releasers (DMDM Hydantoin, Quaternium-15)", "Phenoxyethanol",
    "Aluminum Compounds", "Propylene Glycol", "Octinoxate", "Oxybenzone"
]
