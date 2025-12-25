import os
import pymongo
from datetime import datetime

class Database:
    def __init__(self):
        self.mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_name = os.environ.get('MONGO_DB_NAME', 'portfolio_db')
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        if not self.client:
            try:
                self.client = pymongo.MongoClient(self.mongo_uri)
                self.db = self.client[self.db_name]
                print(f"Connected to MongoDB: {self.db_name}")
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                raise e
    
    def get_db(self):
        """Get database instance, connecting if necessary"""
        if self.db is None:
            self.connect()
        return self.db

    def save_holdings(self, user_id, broker, holdings, metadata=None):
        """
        Save extracted holdings to MongoDB
        
        Args:
            user_id: The ID of the user (e.g. email or auth sub)
            broker: Broker name (zerodha, groww, etc.)
            holdings: List of holding dictionaries
            metadata: Optional metadata (email subject, date, etc.)
            
        Returns:
            The inserted document ID
        """
        db = self.get_db()
        collection = db['portfolio_holdings']
        
        document = {
            'user_id': user_id,
            'broker': broker,
            'holdings': holdings,
            'extracted_at': datetime.utcnow(),
            'source': 'gmail_extraction',
            'metadata': metadata or {}
        }
        
        result = collection.insert_one(document)
        print(f"Saved {len(holdings)} holdings for user {user_id} from {broker}. Doc ID: {result.inserted_id}")
        return str(result.inserted_id)

    def get_latest_holdings(self, user_id, broker=None):
        """Get latest holdings for a user, optionally filtered by broker"""
        db = self.get_db()
        collection = db['portfolio_holdings']
        
        query = {'user_id': user_id}
        if broker:
            query['broker'] = broker
            
        # Sort by extraction time descending
        return collection.find_one(query, sort=[('extracted_at', -1)])

# Global instance
db_instance = Database()

def get_db():
    return db_instance
