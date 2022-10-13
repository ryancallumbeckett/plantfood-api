class QueryBuilder():

    def __init__(self, select_columns, limit_results):
        self.statement_start = f"SELECT {select_columns} FROM recipe_nutrition JOIN recipes ON recipe_nutrition.id = recipes.id WHERE "
        self.statement_end = "LIMIT {};".format(limit_results)
    
    
    def query_decorator(func):
        def query_wrapper(self, **kwargs):
            query_body = func(**kwargs)
            return self.statement_start + query_body + self.statement_end
        return query_wrapper
            

    @query_decorator
    def build_query(**kwargs):

        query_body = ''
        for arg, value in kwargs.items():

            if arg == "ingredients":
                value =  value.split(',')
                for i in value: 
                    i = i.strip()
                    query_body = query_body + "ingredients_map->>'{}' = 'true' AND ".format(i)

            elif arg == "nutrition":
                for obj in value:
                    if obj["quantity"] > 0:
                        nutrient =  obj["nutrient"]
                        quantity = obj["quantity"]
                        op = obj["operator"]
                        op = ">=" if op == "More than" else "<="
                        query_body  =  query_body  + f"{nutrient}_per_serving_grams {op} {quantity} AND "

            elif arg == "keyword":
                query_body = query_body  + "__ts_vector__ @@ to_tsquery('english', '{}') ".format(value) + "AND "
                
        return query_body.rsplit('AND', 1)[0] 
