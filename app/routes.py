from flask import Response

from app import app
from app.adapters import json, web


##################################
# API V1 JSON RESPONSE ENDPOINTS #
##################################

@app.route("/api/v1/check-brand-alias", methods=["POST"])
def api_v1_check_brand_alias() -> Response:
    return json.check_brand_alias()


@app.route("/api/v1/check-alias", methods=["POST"])
def api_v1_check_alias() -> Response:
    return json.check_alias()


@app.route("/api/v1/check-verification-code", methods=["POST"])
def api_v1_check_verification_code() -> Response:
    return json.check_verification_code()


@app.route("/api/v1/create-brand", methods=["POST"])
def api_v1_create_brand() -> Response:
    return json.create_brand()


@app.route("/api/v1/create-product", methods=["POST"])
def api_v1_create_product() -> Response:
    return json.create_product()


@app.route("/api/v1/create-store", methods=["POST"])
def api_v1_create_store() -> Response:
    return json.create_store()


@app.route("/api/v1/create-store-product", methods=["POST"])
def api_v1_create_store_product() -> Response:
    return json.create_store_product()


@app.route("/api/v1/delete-brand", methods=["POST"])
def api_v1_delete_brand() -> Response:
    return json.delete_brand()


@app.route("/api/v1/delete-brand-avatar", methods=["POST"])
def api_v1_delete_brand_avatar() -> Response:
    return json.delete_brand_avatar()


@app.route("/api/v1/delete-product", methods=["POST"])
def api_v1_delete_product() -> Response:
    return json.delete_product()


@app.route("/api/v1/delete-store", methods=["POST"])
def api_v1_delete_store() -> Response:
    return json.delete_store()


@app.route("/api/v1/delete-store-avatar", methods=["POST"])
def api_v1_delete_store_avatar() -> Response:
    return json.delete_store_avatar()


@app.route("/api/v1/delete-store-product", methods=["POST"])
def api_v1_delete_store_product() -> Response:
    return json.delete_store_product()


@app.route("/api/v1/delete-user-account", methods=["POST"])
def api_v1_delete_user_account() -> Response:
    return json.delete_user_account()


@app.route("/api/v1/delete-user-avatar", methods=["POST"])
def api_v1_delete_user_avatar() -> Response:
    return json.delete_user_avatar()


@app.route("/api/v1/get-badge", methods=["POST"])
def api_v1_get_badge() -> Response:
    return json.get_badge()


@app.route("/api/v1/get-brand", methods=["POST"])
def api_v1_get_brand() -> Response:
    return json.get_brand()


@app.route("/api/v1/get-brands", methods=["POST"])
def api_v1_get_brands() -> Response:
    return json.get_brands()


@app.route("/api/v1/get-country-list", methods=["POST"])
def api_v1_get_country_list() -> Response:
    return json.get_country_list()


@app.route("/api/v1/get-dialing-code-list", methods=["POST"])
def api_v1_get_dialing_code_list() -> Response:
    return json.get_dialing_code_list()


@app.route("/api/v1/get-localities", methods=["POST"])
def api_v1_get_localities() -> Response:
    return json.get_localities()


@app.route("/api/v1/get-product", methods=["POST"])
def api_v1_get_product() -> Response:
    return json.get_product()


@app.route("/api/v1/get-product-color-list", methods=["POST"])
def api_v1_get_product_color_list() -> Response:
    return json.get_product_color_list()


@app.route("/api/v1/get-product-material-list", methods=["POST"])
def api_v1_get_product_material_list() -> Response:
    return json.get_product_material_list()


@app.route("/api/v1/get-product-variants", methods=["POST"])
def api_v1_get_product_variants() -> Response:
    return json.get_product_variants()


@app.route("/api/v1/get-products", methods=["POST"])
def api_v1_get_products() -> Response:
    return json.get_products()


@app.route("/api/v1/get-store", methods=["POST"])
def api_v1_get_store() -> Response:
    return json.get_store()


@app.route("/api/v1/get-store-product", methods=["POST"])
def api_v1_get_store_product() -> Response:
    return json.get_store_product()


@app.route("/api/v1/get-store-products", methods=["POST"])
def api_v1_get_store_products() -> Response:
    return json.get_store_products()


@app.route("/api/v1/get-stores", methods=["POST"])
def api_v1_get_stores() -> Response:
    return json.get_stores()


@app.route("/api/v1/get-user-account", methods=["POST"])
def api_v1_get_user_account() -> Response:
    return json.get_user_account()


@app.route("/api/v1/get-user-accounts", methods=["POST"])
def api_v1_get_user_accounts() -> Response:
    return json.get_user_accounts()


@app.route("/api/v1/heartbeat", methods=["POST"])
def api_v1_heartbeat() -> Response:
    return json.heartbeat()


@app.route("/api/v1/join", methods=["POST"])
def api_v1_join() -> Response:
    return json.join()


@app.route("/api/v1/log-in", methods=["POST"])
def api_v1_log_in() -> Response:
    return json.log_in()


@app.route("/api/v1/log-out", methods=["POST"])
def api_v1_log_out() -> Response:
    return json.log_out()


@app.route("/api/v1/me", methods=["POST"])
def api_v1_me() -> Response:
    return json.me()


@app.route("/api/v1/remove-brand", methods=["POST"])
def api_v1_remove_brand() -> Response:
    return json.remove_brand()


@app.route("/api/v1/remove-product", methods=["POST"])
def api_v1_remove_product() -> Response:
    return json.remove_product()


@app.route("/api/v1/remove-store", methods=["POST"])
def api_v1_remove_store() -> Response:
    return json.remove_store()


@app.route("/api/v1/report-brand", methods=["POST"])
def api_v1_report_brand() -> Response:
    return json.report_brand()


@app.route("/api/v1/report-product", methods=["POST"])
def api_v1_report_product() -> Response:
    return json.report_product()


@app.route("/api/v1/report-store", methods=["POST"])
def api_v1_report_store() -> Response:
    return json.report_store()


@app.route("/api/v1/report-user-account", methods=["POST"])
def api_v1_report_user_account() -> Response:
    return json.report_user_account()


@app.route("/api/v1/send-verification-code", methods=["POST"])
def api_v1_send_verification_code() -> Response:
    return json.send_verification_code()


@app.route("/api/v1/update-brand", methods=["POST"])
def api_v1_update_brand() -> Response:
    return json.update_brand()


@app.route("/api/v1/update-brand-avatar", methods=["POST"])
def api_v1_update_brand_avatar() -> Response:
    return json.update_brand_avatar()


@app.route("/api/v1/update-product", methods=["POST"])
def api_v1_update_product() -> Response:
    return json.update_product()


@app.route("/api/v1/update-product-media", methods=["POST"])
def api_v1_update_product_media() -> Response:
    return json.update_product_media()


@app.route("/api/v1/update-store", methods=["POST"])
def api_v1_update_store() -> Response:
    return json.update_store()


@app.route("/api/v1/update-store-avatar", methods=["POST"])
def api_v1_update_store_avatar() -> Response:
    return json.update_store_avatar()


@app.route("/api/v1/update-store-product", methods=["POST"])
def api_v1_update_store_product() -> Response:
    return json.update_store_product()


@app.route("/api/v1/update-user-account", methods=["POST"])
def api_v1_update_user_account() -> Response:
    return json.update_user_account()


@app.route("/api/v1/update-user-avatar", methods=["POST"])
def api_v1_update_user_avatar() -> Response:
    return json.update_user_avatar()


#############
# WEB VIEWS #
#############

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def web_index() -> Response:
    return web.index()


@app.route("/privacy", methods=["GET"])
def web_privacy() -> Response:
    return web.privacy()


@app.route("/tos", methods=["GET"])
def web_tos() -> Response:
    return web.tos()
