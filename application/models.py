from application import db


class DataSets(db.Model):
    """This class represents the datasets table"""
    
    __tablename__ = "datasets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    classes = db.Column(db.ARRAY(String))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __init__(self, name):
        """initialize with name."""
        self.name = name

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Bucketlist.query.all()

    def delete(self):
        db.session.delee(self)
        db.session.commit()

    def __repr__(self):
        return "<Dataset: {}>".format(self.name)
