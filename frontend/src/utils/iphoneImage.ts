import iphoneAir from "@/assets/iphone_generation_groups/iphone_air/sky_blue.png";
import iphone17 from "@/assets/iphone_generation_groups/iphone_17/iphone_17_mist_blue.png";
import iphone17Pro from "@/assets/iphone_generation_groups/iphone_17/iphone_17_pro_deep_blue.png";
import iphone17ProMax from "@/assets/iphone_generation_groups/iphone_17/iphone_17_pro_max_deep_blue.png";
import iphone16 from "@/assets/iphone_generation_groups/iphone_16/iphone_16_ultramarine.png";
import iphone16Pro from "@/assets/iphone_generation_groups/iphone_16/iphone_16_pro_natural_titanium.png";
import iphone16ProMax from "@/assets/iphone_generation_groups/iphone_16/iphone_16_pro_max_natural_titanium.png";
import iphone15 from "@/assets/iphone_generation_groups/iphone_15/iphone_15_green.png";
import iphone15Pro from "@/assets/iphone_generation_groups/iphone_15/iphone_15_pro_natural_titanium.png";
import iphone15ProMax from "@/assets/iphone_generation_groups/iphone_15/iphone_15_pro_max_natural_titanium.png";
import iphone14 from "@/assets/iphone_generation_groups/iphone_14/iphone_14_blue.png";
import iphone14Pro from "@/assets/iphone_generation_groups/iphone_14/iphone_14_pro_space_black.png";
import iphone14ProMax from "@/assets/iphone_generation_groups/iphone_14/iphone_14_pro_max_space_black.png";
import iphone13 from "@/assets/iphone_generation_groups/iphone_13/iphone_13_midnight.png";
import iphone13Pro from "@/assets/iphone_generation_groups/iphone_13/iphone_13_pro_graphite.png";
import iphone13ProMax from "@/assets/iphone_generation_groups/iphone_13/iphone_13_pro_max_graphite.png";
import iphone12 from "@/assets/iphone_generation_groups/iphone_12/iphone_12_blue.png";
import iphone12Pro from "@/assets/iphone_generation_groups/iphone_12/iphone_12_pro_graphite.png";
import iphone12ProMax from "@/assets/iphone_generation_groups/iphone_12/iphone_12_pro_max_graphite.png";
import iphone11 from "@/assets/iphone_generation_groups/iphone_11/iphone_11_black.png";
import iphone11Pro from "@/assets/iphone_generation_groups/iphone_11/iphone_11_pro_space_grey.png";
import iphone11ProMax from "@/assets/iphone_generation_groups/iphone_11/iphone_11_pro_max_space_grey.png";

const modelImages: Record<string, string> = {
  "iPhone Air": iphoneAir,
  "iPhone 17 Pro Max": iphone17ProMax,
  "iPhone 17 Pro": iphone17Pro,
  "iPhone 17": iphone17,
  "iPhone 16e": iphone16,
  "iPhone 16 Pro Max": iphone16ProMax,
  "iPhone 16 Pro": iphone16Pro,
  "iPhone 16 Plus": iphone16,
  "iPhone 16": iphone16,
  "iPhone 15 Pro Max": iphone15ProMax,
  "iPhone 15 Pro": iphone15Pro,
  "iPhone 15 Plus": iphone15,
  "iPhone 15": iphone15,
  "iPhone 14 Pro Max": iphone14ProMax,
  "iPhone 14 Pro": iphone14Pro,
  "iPhone 14 Plus": iphone14,
  "iPhone 14": iphone14,
  "iPhone 13 Pro Max": iphone13ProMax,
  "iPhone 13 Pro": iphone13Pro,
  "iPhone 13 Mini": iphone13,
  "iPhone 13": iphone13,
  "iPhone 12 Pro Max": iphone12ProMax,
  "iPhone 12 Pro": iphone12Pro,
  "iPhone 12 Mini": iphone12,
  "iPhone 12": iphone12,
  "iPhone 11 Pro Max": iphone11ProMax,
  "iPhone 11 Pro": iphone11Pro,
  "iPhone 11": iphone11,
  "iPhone SE 2022": iphone11,
  "iPhone SE 2020": iphone11,
};

export const getIphoneImage = (model: string) => modelImages[model] ?? iphone15;
