import { useEffect, useState } from "react";

import { iphoneModels as fallbackModels, storageByModel as fallbackStorageByModel } from "@/data/iphoneCatalog";
import { API_URL } from "@/utils/apiClient";

const storageGbToLabel = (value: number) => {
  if (value === 1024) return "1TB";
  if (value === 2048) return "2TB";
  return `${value}GB`;
};

const normalizeModelName = (value: string) => {
  let model = value.replace(/\s+/g, " ").trim();
  if (!model) return model;

  if (!/^iphone\b/i.test(model)) {
    model = `iPhone ${model}`;
  }

  return model
    .replace(/\biPhone\s+16\s+E\b/i, "iPhone 16e")
    .replace(/\biPhone\s+16e\b/i, "iPhone 16e")
    .replace(/\biPhone\s+17\s+Air\b/i, "iPhone Air")
    .replace(/\biPhone\s+Air\b/i, "iPhone Air")
    .replace(/\biPhone\s+SE\s*\(?2020\)?/i, "iPhone SE 2020")
    .replace(/\biPhone\s+SE\s*\(?2022\)?/i, "iPhone SE 2022")
    .replace(/\bmini\b/gi, "Mini")
    .replace(/\bpro max\b/gi, "Pro Max")
    .replace(/\bpro\b/gi, "Pro")
    .replace(/\bplus\b/gi, "Plus")
    .replace(/\s+/g, " ")
    .trim();
};

const filterStorageForModel = (model: string, storages: number[]) => {
  const labels = [...new Set(storages)].sort((a, b) => a - b).map(storageGbToLabel);
  const allowed = fallbackStorageByModel[model];
  if (!allowed) return labels;
  return labels.filter((label) => allowed.includes(label));
};

const sortModels = (models: string[]) => {
  const unique = [...new Set(models.map(normalizeModelName).filter(Boolean))];
  const fallbackRank = new Map(fallbackModels.map((model, index) => [model, index]));

  return unique.sort((a, b) => {
    const aRank = fallbackRank.get(a);
    const bRank = fallbackRank.get(b);
    if (aRank !== undefined && bRank !== undefined) return aRank - bRank;
    if (aRank !== undefined) return -1;
    if (bRank !== undefined) return 1;
    return a.localeCompare(b, "sv-SE");
  });
};

export const useIphoneCatalog = () => {
  const [models, setModels] = useState(fallbackModels);
  const [storageByModel, setStorageByModel] = useState(fallbackStorageByModel);

  useEffect(() => {
    const controller = new AbortController();

    const loadCatalog = async () => {
      try {
        const [modelsResponse, storageResponse] = await Promise.all([
          fetch(`${API_URL}/api/models`, { signal: controller.signal }),
          fetch(`${API_URL}/api/models/storage-options`, { signal: controller.signal }),
        ]);

        if (modelsResponse.ok) {
          const apiModels = (await modelsResponse.json()) as string[];
          if (apiModels.length) setModels(sortModels(apiModels));
        }

        if (storageResponse.ok) {
          const apiStorage = (await storageResponse.json()) as Record<string, number[]>;
          const storageEntries = new Map<string, number[]>();

          Object.entries(apiStorage).forEach(([model, storages]) => {
            const normalizedModel = normalizeModelName(model);
            if (!normalizedModel) return;
            storageEntries.set(normalizedModel, [...(storageEntries.get(normalizedModel) ?? []), ...storages]);
          });

          const nextStorage = Object.fromEntries(
            [...storageEntries.entries()]
              .map(([model, storages]) => [model, filterStorageForModel(model, storages)] as const)
              .filter(([, storages]) => storages.length),
          );
          if (Object.keys(nextStorage).length) setStorageByModel({ ...fallbackStorageByModel, ...nextStorage });
        }
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
      }
    };

    loadCatalog();

    return () => controller.abort();
  }, []);

  return { models, storageByModel };
};
