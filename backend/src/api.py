from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

database_filename = "database.db"
app = Flask(__name__)
setup_db(app, database_filename)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()


# ROUTES

@app.route("/drinks")
def get_drinks():
    drinks = [drink.short() for drink in Drink.query.order_by(Drink.title).all()]
    if len(drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route("/drinks-detail")
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail():
    drinks = [drink.long() for drink in Drink.query.order_by(Drink.title).all()]
    if len(drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": drinks
    })


@app.route("/drinks", methods=["POST"])
@requires_auth(permission='post:drinks')
def create_drink():
    body = request.get_json()
    title = body.get("title", None)
    recipe = body.get("recipe", None)
    if not (title and recipe):
        abort(400)
    try:
        recipe = json.dumps(recipe)
        drink = Drink(title=title, recipe=recipe)
        # Check for duplicate name
        drink.insert()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as ex:
        print(ex)
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth(permission='patch:drinks')
def update_drink(drink_id):
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if not drink:
        abort(404)
    body = request.get_json()
    title = body.get("title", None)
    recipe = body.get("recipe", None)
    try:
        if title:
            drink.title = title
        if recipe:
            recipe = json.dumps(recipe)
            drink.recipe = recipe
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        })
    except Exception as ex:
        print(ex)
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth(permission='delete:drinks')
def delete_drink(drink_id):
    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if not drink:
        abort(404)
    try:
        drink.delete()
        return jsonify({
            "success": True,
            "delete": drink_id
        })
    except Exception as ex:
        print(ex)
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404


@app.errorhandler(AuthError)
def not_found(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code


# Default port:
if __name__ == '__main__':
    app.run()
