export const modelToSlug = (model: string): string =>
  model
    .toLowerCase()
    .replace(/[()]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
