from app import app
from app.controllers.infrastructure import infrastructure_bp
from app.controllers.landslide import landslide_bp
from app.controllers.tree import tree_bp
from app.controllers.damage_assessment import damage_assessment_bp



# Register the blueprint with the application
app.register_blueprint(landslide_bp, url_prefix='/v1/detect')
app.register_blueprint(infrastructure_bp, url_prefix='/v1/detect')
app.register_blueprint(tree_bp, url_prefix='/v1/detect')
app.register_blueprint(damage_assessment_bp, url_prefix='/v1/detect')
