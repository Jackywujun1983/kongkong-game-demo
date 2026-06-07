import { Layers3 } from "lucide-react";

import type { Category } from "../../types/domain";

interface CategoryRailProps {
  categories: Category[];
  selectedCategory: string;
  onSelectCategory: (category: string) => void;
}

export function CategoryRail({
  categories,
  selectedCategory,
  onSelectCategory,
}: CategoryRailProps) {
  return (
    <section className="panel category-panel">
      <div className="section-heading">
        <Layers3 size={18} />
        <span>分类</span>
      </div>
      <button
        className={`category-button ${selectedCategory === "" ? "is-active" : ""}`}
        type="button"
        onClick={() => onSelectCategory("")}
      >
        <strong>全部游戏</strong>
        <span>综合评分排序</span>
      </button>
      {categories.map((category) => (
        <button
          className={`category-button ${
            selectedCategory === category.slug ? "is-active" : ""
          }`}
          key={category.slug}
          type="button"
          onClick={() => onSelectCategory(category.slug)}
        >
          <strong>{category.name}</strong>
          <span>{category.description}</span>
        </button>
      ))}
    </section>
  );
}

