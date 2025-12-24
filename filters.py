import config

class ProductFilter:
    def __init__(self):
        self.selected_brands = []
        self.selected_categories = []
        self.search_text = ""
        self.brand_id_to_name = {}
        self.brand_name_to_id = {}
        
    def set_selected_brands(self, brand_ids):
        self.selected_brands = brand_ids
        
    def set_selected_categories(self, categories):
        self.selected_categories = categories
        
    def set_search_text(self, text):
        self.search_text = text.lower().strip()
        
    def load_brand_mappings(self):
        try:
            brands = config.get_all_brands()
            self.brand_id_to_name = {brand['id']: brand['name'] for brand in brands}
            self.brand_name_to_id = {brand['name']: brand['id'] for brand in brands}
        except Exception:
            self.brand_id_to_name = {}
            self.brand_name_to_id = {}
            
    def get_selected_brand_names(self):
        selected_names = []
        for brand_id in self.selected_brands:
            brand_name = self.brand_id_to_name.get(brand_id)
            if brand_name:
                selected_names.append(brand_name)
        return selected_names
        
    def filter_products(self, all_products):
        filtered = all_products
        
        if self.selected_categories:
            filtered = [p for p in filtered if p.get('category') in self.selected_categories]
            
        if self.selected_brands:
            selected_names = self.get_selected_brand_names()
            brand_filtered = []
            for product in filtered:
                product_brand_name = product.get('brand', '').strip()
                if product_brand_name and product_brand_name in selected_names:
                    brand_filtered.append(product)
            filtered = brand_filtered
            
        if self.search_text:
            filtered = [p for p in filtered 
                       if self.search_text in p.get('name', '').lower() 
                       or self.search_text in p.get('article', '').lower()]
                       
        return filtered
        
    def reset_filters(self):
        self.selected_brands = []
        self.selected_categories = []
        self.search_text = ""
        
    def has_active_filters(self):
        return (len(self.selected_brands) > 0 or 
                len(self.selected_categories) > 0 or 
                self.search_text != "")
                
    def get_filter_summary(self):
        parts = []
        
        if self.selected_categories:
            if len(self.selected_categories) == 1:
                parts.append(f"Категория: {self.selected_categories[0]}")
            else:
                categories_text = f"Категории: {', '.join(self.selected_categories[:2])}"
                if len(self.selected_categories) > 2:
                    categories_text += f" (+{len(self.selected_categories) - 2} еще)"
                parts.append(categories_text)
                
        if self.selected_brands:
            selected_names = self.get_selected_brand_names()
            if selected_names:
                if len(selected_names) == 1:
                    parts.append(f"Бренд: {selected_names[0]}")
                else:
                    brand_text = f"Бренды: {', '.join(selected_names[:2])}"
                    if len(selected_names) > 2:
                        brand_text += f" (+{len(selected_names) - 2} еще)"
                    parts.append(brand_text)
                
        if self.search_text:
            parts.append(f"Поиск: '{self.search_text}'")
            
        return "; ".join(parts) if parts else "Без фильтров"