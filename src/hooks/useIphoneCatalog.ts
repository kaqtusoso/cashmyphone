import { useEffect, useState } from "react";

import { iphoneModels as fallbackModels, storageByModel as fallbackStorageByModel } from "@/data/iphoneCatalog";
import { API_URL } from "@/utils/apiClient";

const storageGbToLabel = (value: number) => {
  if (value === 1024) return "1TB";
  if (value === 2048) return "2TB";
  return `${value}GB`;
};

const sortModels = (models: string[]) => {
  const unique = [...new Set(models)];
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
          const nextStorage = Object.fromEntries(
            Object.entries(apiStorage).map(([model, storages]) => [
              model,
              [...new Set(storages)].sort((a, b) => a - b).map(storageGbToLabel),
            ]),
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
