import logging
from sqlalchemy.exc import IntegrityError
from __init__ import db


# SearchHistory Model
# SearchHistory Model
class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # Exact item name
    query = db.Column(db.String(255), nullable=True)  # Not used here but left for compatibility
    tags = db.Column(db.JSON, nullable=False)  # Tags from the dictionary

    def __init__(self, user, name=None, query=None, tags=None):
        self.user = user
        self.name = name
        self.query = query
        self.tags = tags

    def read(self):
        return {
            "id": self.id,
            "user": self.user,
            "name": self.name,
            "query": self.query,
            "tags": self.tags,
        }

    def __repr__(self):
        return f"SearchHistory(user={self.user}, name={self.name}, query={self.query}, tags={self.tags})"

    def create(self):
        """
        Adds a new SearchHistory entry to the database.
        """
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            logging.warning(f"Error creating SearchHistory entry: {self.name}. Error: {str(e)}")
            return None
        return self

    def read(self):
        """
        Converts a SearchHistory object to a dictionary for JSON serialization.
        """
        return {
            "id": self.id,
            "user": self.user,
            "name": self.name,
            "query": self.query,
            "tags": self.tags,
        }

    @staticmethod
    def init_search_history():
        """
        Ensures the SearchHistory table is created and ready for use.
        """
        try:
            db.create_all()  # Create table if it doesn't already exist
            logging.info("SearchHistory table initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize SearchHistory table: {str(e)}")

    @staticmethod
    def get_user_preferences(user):
        """
        Retrieves a user's preferences based on their search and click history.
        """
        try:
            user_history = SearchHistory.query.filter_by(user=user).all()
            if not user_history:
                return {"message": f"No history found for user: {user}"}

            # Aggregate tags and clicked items
            tag_counts = {}
            for entry in user_history:
                if entry.tags:
                    for tag, count in entry.tags.items():
                        tag_counts[tag] = tag_counts.get(tag, 0) + count

            return {"tags": tag_counts}
        except Exception as e:
            logging.error(f"Error retrieving preferences for user {user}: {str(e)}")
            return {"error": str(e)}
