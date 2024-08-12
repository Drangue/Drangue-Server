from app import app
from app.controllers.infrastructure import infrastructure_bp
from app.controllers.landslide import landslide_bp


# Register the blueprint with the application
app.register_blueprint(landslide_bp, url_prefix='/v1/detect')
app.register_blueprint(infrastructure_bp, url_prefix='/v1/detect')

# Function to print the routes in a blueprint
def list_blueprint_endpoints(application, blueprint):
    print(f"Listing routes for blueprint '{blueprint.name}':")
    for rule in application.url_map.iter_rules():
        if rule.endpoint.startswith(f'{blueprint.name}.'):
            print(f"{rule.endpoint}: {rule}")

# Call the function to list endpoints for detection_bp
list_blueprint_endpoints(app, landslide_bp)
list_blueprint_endpoints(app, infrastructure_bp)

