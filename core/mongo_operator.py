from pymongo import MongoClient
from configparser import ConfigParser
from config import settings

class MongoOperator():
    ''' An object to interact with MongoDB'''

    cluster = f"mongodb+srv://{settings.mongo_username}:{settings.mongo_password}@cluster0.rjktdw5.mongodb.net/?retryWrites=true&w=majority"
 
    def fuzzy_search(self, search_query, path):

        client = MongoClient(self.cluster)
        db = client.ingredients
        table = db.ingredient_conversions
        result = table.aggregate([
            {
                "$search": {
                    "index" : "language_search", 
                    "text": {
                        "query": search_query,
                        "path":  path,
                        "fuzzy": {}
                    }   
                }
            }, {
            '$limit': 1
            }
        ])

        return result

