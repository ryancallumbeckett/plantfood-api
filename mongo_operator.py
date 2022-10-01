from pymongo import MongoClient
from configparser import ConfigParser

class MongoOperator():
    ''' An object to interact with MongoDB'''

    config = ConfigParser()
    config.read('./config.cfg')
    username = config['MONGODB']['username']
    password = config['MONGODB']['password']
    cluster = f"mongodb+srv://{username}:{password}@cluster0.rjktdw5.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(cluster)
    db = client.ingredients

        
    def fuzzy_search(self, search_query, path):

        table = self.db.ingredient_conversions
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

