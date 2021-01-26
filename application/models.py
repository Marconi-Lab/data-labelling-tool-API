from application import db


class Datasets(db.Model):
    """This class represents the datasets table"""
    
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    classes = db.Column(db.ARRAY(db.String))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __init__(self, name, classes):
        """initialize with name."""
        self.name = name
        self.classes = classes

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Datasets.query.all()

    def delete(self):
        db.session.delee(self)
        db.session.commit()

    def __repr__(self):
        return "<Dataset: {}>".format(self.name)
