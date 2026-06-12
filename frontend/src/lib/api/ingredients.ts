export type IngredientType = "мясо" | "жир" | "специя" | "соль" | "щепа" | "жидкий дым" | "добавка" | "прочее";

export const INGREDIENT_TYPES: { id: IngredientType; label: string }[] = [
  { id: "мясо", label: "Мясо" },
  { id: "жир", label: "Жир" },
  { id: "специя", label: "Специя" },
  { id: "соль", label: "Соль" },
  { id: "щепа", label: "Щепа" },
  { id: "жидкий дым", label: "Жидкий дым" },
  { id: "добавка", label: "Добавка" },
  { id: "прочее", label: "Прочее" },
];
