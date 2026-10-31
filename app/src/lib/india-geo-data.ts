/**
 * Configuration-driven geographic hierarchy and sign language classification
 * for GESTURA's India-first dataset strategy.
 */

export const COUNTRY_NAME = "India";

export type RegionKey =
  | "NORTH"
  | "SOUTH"
  | "EAST"
  | "WEST"
  | "CENTRAL"
  | "NORTHEAST";

export const INDIA_REGIONS: Record<RegionKey, string[]> = {
  NORTH: [
    "Delhi",
    "Chandigarh",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Ladakh",
    "Punjab",
    "Rajasthan",
    "Uttarakhand",
    "Uttar Pradesh",
  ],
  SOUTH: [
    "Andhra Pradesh",
    "Karnataka",
    "Kerala",
    "Tamil Nadu",
    "Telangana",
    "Puducherry",
    "Lakshadweep",
    "Andaman and Nicobar Islands",
  ],
  EAST: [
    "Bihar",
    "Jharkhand",
    "Odisha",
    "West Bengal",
  ],
  WEST: [
    "Goa",
    "Gujarat",
    "Maharashtra",
    "Dadra and Nagar Haveli and Daman and Diu",
  ],
  CENTRAL: [
    "Chhattisgarh",
    "Madhya Pradesh",
  ],
  NORTHEAST: [
    "Arunachal Pradesh",
    "Assam",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Sikkim",
    "Tripura",
  ],
};

export const REGION_LABELS: Record<RegionKey, string> = {
  NORTH: "North India",
  SOUTH: "South India",
  EAST: "East India",
  WEST: "West India",
  CENTRAL: "Central India",
  NORTHEAST: "Northeast India",
};

export const SIGN_LANGUAGE_TYPES = [
  "Indian Sign Language (ISL)",
  "Regional ISL Variant",
  "Local Community Sign Language",
  "Other",
  "Unsure",
] as const;

export type SignLanguageType = (typeof SIGN_LANGUAGE_TYPES)[number];

export function getRegions(): RegionKey[] {
  return Object.keys(INDIA_REGIONS) as RegionKey[];
}

export function getStatesForRegion(region: string): string[] {
  const key = region.toUpperCase() as RegionKey;
  return INDIA_REGIONS[key] || [];
}

export function isValidRegionState(region: string, state: string): boolean {
  const states = getStatesForRegion(region);
  return states.some((s) => s.toLowerCase() === state.trim().toLowerCase());
}

export function requiresVarietyName(type: string): boolean {
  return [
    "Regional ISL Variant",
    "Local Community Sign Language",
    "Other",
  ].includes(type);
}

