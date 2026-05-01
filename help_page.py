# ==========================================================
# HELP PAGE MODULE
# ==========================================================

from flask import render_template

def register_help_page(app):

    @app.route("/help")
    def help_page():
        return render_template("help.html")