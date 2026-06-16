export const modelToSlug = (model: string): string =>
  model
    .toLowerCase()
    .replace(/[()]/g, "")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");

export const slugToModel = (slug: string): string => {
  const words = slug
    .replace(/^iphone-/, "iphone-")
    .split("-")
    .filter(Boolean)
    .map((part) => {
      if (part === "iphone") return "iPhone";
      if (part === "se") return "SE";
      if (part === "pro") return "Pro";
      if (part === "max") return "Max";
      if (part === "mini") return "Mini";
      if (part === "plus") return "Plus";
      if (part === "air") return "Air";
      return part;
    });

  return words.join(" ");
};
