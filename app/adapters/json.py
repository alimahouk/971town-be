from flask import make_response, request, Response
import functools
import warnings

from app import app
from app.config import ProtocolKey, ResponseStatus
from app.modules import (brand, brand_report, common,
                         country, country_dialing_code, locality,
                         product, product_color, product_material,
                         product_report, store, store_product,
                         store_report, user, user_account,
                         user_account_report, user_account_session, user_phone_number_verification_code)
from app.modules.user_account_session import UserAccountSession


def _auth_required(func):
    """
    [DECORATOR] Makes sure a valid session exists for the user
    making the request before proceeding with the called function.
    """

    @functools.wraps(func)
    def wrapper_auth_required(*args, **kwargs):
        authenticated = True

        if ProtocolKey.USER_ACCOUNT_SESSION_ID.value not in request.cookies:
            authenticated = False
        else:
            session_id = request.cookies.get(ProtocolKey.USER_ACCOUNT_SESSION_ID.value)

            if not UserAccountSession.session_exists(session_id):
                authenticated = False

        if authenticated:
            value = func(*args, **kwargs)
        else:
            error = {
                ProtocolKey.ERROR: {
                    ProtocolKey.ERROR_CODE: ResponseStatus.UNAUTHORIZED.value,
                    ProtocolKey.ERROR_MESSAGE: "A valid session is required to perform this function.",
                }
            }
            value = make_response(error, _map_response_status(ResponseStatus.UNAUTHORIZED))

        return value

    return wrapper_auth_required


def _deprecated(func):
    """
    [DECORATOR] This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter("always", DeprecationWarning)  # Turn off filter.
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter("default", DeprecationWarning)  # Reset filter.

        return func(*args, **kwargs)
    return new_func


def _map_response_status(response_status: ResponseStatus) -> int:
    """
    Maps service response status codes to HTTP response status codes."""

    """Set to the HTTP Internal Server Error code by default because if
    this doesn't get set to the correct code later on then it's likely
    because of an internal server error.
    """

    ret = 500
    if response_status == ResponseStatus.OK:
        ret = 200
    elif response_status == ResponseStatus.BAD_REQUEST:
        ret = 400
    elif response_status == ResponseStatus.FORBIDDEN:
        ret = 403
    elif response_status == ResponseStatus.INTERNAL_SERVER_ERROR:
        ret = 500
    elif response_status == ResponseStatus.NOT_FOUND:
        ret = 404
    elif response_status == ResponseStatus.NOT_IMPLEMENTED:
        ret = 501
    elif response_status == ResponseStatus.PAYLOAD_TOO_LARGE:
        ret = 413
    elif response_status == ResponseStatus.TOO_MANY_REQUESTS:
        ret = 429
    elif response_status == ResponseStatus.UNAUTHORIZED:
        ret = 401
    return ret


def _stub(func):
    """
    [DECORATOR]
    """

    @functools.wraps(func)
    def wrapper_stub():
        error = {
            ProtocolKey.ERROR: {
                ProtocolKey.ERROR_CODE: ResponseStatus.NOT_IMPLEMENTED.value,
                ProtocolKey.ERROR_MESSAGE: "This function has not been implemented yet.",
            }
        }
        response = make_response(error, _map_response_status(ResponseStatus.NOT_IMPLEMENTED))
        # Clients would cache this response by default - disable that behavior.
        response.headers["Cache-Control"] = "no-store"

        return response

    return wrapper_stub


@_deprecated
@_auth_required
def check_brand_alias() -> Response:
    """
    This endpoint is deprecated and will be removed.
    Use check_alias() instead.
    """

    alias = request.form.get(ProtocolKey.ALIAS)

    service_response = common.check_alias(alias)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def check_alias() -> Response:
    alias = request.form.get(ProtocolKey.ALIAS)

    service_response = common.check_alias(alias)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def check_verification_code() -> Response:
    phone_number_id = request.form.get(ProtocolKey.PHONE_NUMBER_ID)
    code = request.form.get(ProtocolKey.CODE)

    service_response = user_phone_number_verification_code.check_verification_code(phone_number_id, code)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def create_brand() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    name = request.form.get(ProtocolKey.NAME)
    tags = request.form.get(ProtocolKey.TAGS)

    service_response = brand.create_brand(
        alias=alias,
        name=name,
        tags=tags
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def create_product() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    name = request.form.get(ProtocolKey.NAME)
    parent_product_id = request.form.get(ProtocolKey.PARENT_PRODUCT_ID)
    tags = request.form.get(ProtocolKey.TAGS)

    service_response = product.create_product(
        alias=alias,
        brand_id=brand_id,
        name=name,
        parent_product_id=parent_product_id,
        tags=tags
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def create_store() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    latitude = request.form.get(ProtocolKey.LATITUDE)
    longitude = request.form.get(ProtocolKey.LONGITUDE)
    locality_alpha_2_code = request.form.get(ProtocolKey.ALPHA_2_CODE)
    locality_name = request.form.get(ProtocolKey.LOCALITY)
    name = request.form.get(ProtocolKey.NAME)
    tags = request.form.get(ProtocolKey.TAGS)

    service_response = store.create_store(
        alias=alias,
        brand_id=brand_id,
        latitude=latitude,
        longitude=longitude,
        locality_alpha_2_code=locality_alpha_2_code,
        locality_name=locality_name,
        name=name,
        tags=tags
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def create_store_product() -> Response:
    user_account_session.update_session()

    price = request.form.get(ProtocolKey.PRICE)
    product_id = request.form.get(ProtocolKey.PRODUCT_ID)
    store_id = request.form.get(ProtocolKey.STORE_ID)

    service_response = store_product.create_store_product(
        price=price,
        product_id=product_id,
        store_id=store_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def delete_brand() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)

    service_response = brand.delete_brand(brand_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_stub
@_auth_required
def delete_brand_avatar() -> Response:
    pass


@_auth_required
def delete_product() -> Response:
    user_account_session.update_session()

    product_id = request.form.get(ProtocolKey.PRODUCT_ID)

    service_response = product.delete_product(product_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def delete_store() -> Response:
    user_account_session.update_session()

    store_id = request.form.get(ProtocolKey.STORE_ID)

    service_response = store.delete_store(store_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_stub
@_auth_required
def delete_store_avatar() -> Response:
    pass


@_auth_required
def delete_store_product() -> Response:
    user_account_session.update_session()

    store_product_id = request.form.get(ProtocolKey.STORE_PRODUCT_ID)

    service_response = store_product.delete_store_product(store_product_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def delete_user_account() -> Response:
    user_account_session.update_session()

    account_id = request.form.get(ProtocolKey.USER_ACCOUNT_ID)

    service_response = user_account.delete_account(account_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_stub
@_auth_required
def delete_user_avatar() -> Response:
    pass


@_stub
@_auth_required
def get_badge() -> Response:
    pass


@_auth_required
def get_brand() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    brand_id = request.form.get(ProtocolKey.BRAND_ID)

    service_response = brand.get_brand(
        alias=alias,
        brand_id=brand_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_brands() -> Response:
    user_account_session.update_session()

    query = request.form.get(ProtocolKey.QUERY)

    service_response = brand.get_brands(query)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def get_country_list() -> Response:
    is_enabled = request.form.get(ProtocolKey.IS_ENABLED)

    service_response = country.get_all(is_enabled)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def get_dialing_code_list() -> Response:
    is_enabled = request.form.get(ProtocolKey.IS_ENABLED)

    service_response = country_dialing_code.get_all(is_enabled)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_localities() -> Response:
    user_account_session.update_session()

    query = request.form.get(ProtocolKey.QUERY)

    service_response = locality.get_localities(query)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_product() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    product_id = request.form.get(ProtocolKey.PRODUCT_ID)

    service_response = product.get_product(
        alias=alias,
        product_id=product_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_product_color_list() -> Response:
    service_response = product_color.get_all()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_product_material_list() -> Response:
    service_response = product_material.get_all()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def get_product_variants() -> Response:
    offset = request.form.get(ProtocolKey.OFFSET)
    parent_product_id = request.form.get(ProtocolKey.PARENT_PRODUCT_ID)

    service_response = product.get_product_variants(
        offset=offset,
        parent_product_id=parent_product_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_products() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    query = request.form.get(ProtocolKey.QUERY)

    service_response = product.get_products(
        brand_id=brand_id,
        query=query
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_store() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    store_id = request.form.get(ProtocolKey.STORE_ID)

    service_response = store.get_store(
        alias=alias,
        store_id=store_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_store_product() -> Response:
    user_account_session.update_session()

    store_product_id = request.form.get(ProtocolKey.STORE_PRODUCT_ID)

    service_response = store_product.get_store_product(store_product_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_store_products() -> Response:
    user_account_session.update_session()

    store_id = request.form.get(ProtocolKey.STORE_ID)

    service_response = store_product.get_store_products(store_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_stores() -> Response:
    user_account_session.update_session()

    query = request.form.get(ProtocolKey.QUERY)
    latitude = request.form.get(ProtocolKey.LATITUDE)
    longitude = request.form.get(ProtocolKey.LONGITUDE)

    service_response = store.get_stores(
        query=query,
        latitude=latitude,
        longitude=longitude
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_user_account() -> Response:
    user_account_session.update_session()

    alias = request.form.get(ProtocolKey.ALIAS)
    account_id = request.form.get(ProtocolKey.USER_ACCOUNT_ID)

    service_response = user_account.get_account(
        alias=alias,
        account_id=account_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def get_user_accounts() -> Response:
    user_account_session.update_session()

    query = request.form.get(ProtocolKey.QUERY)

    service_response = user_account.get_accounts(query)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@_auth_required
def heartbeat() -> Response:
    service_response = user_account_session.update_session()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def join() -> Response:
    alias = request.form.get(ProtocolKey.ALIAS)
    client_id = request.form.get(ProtocolKey.CLIENT_ID)
    code = request.form.get(ProtocolKey.CODE)
    phone_number_id = request.form.get(ProtocolKey.PHONE_NUMBER_ID)

    service_response = user.join(
        alias=alias,
        client_id=client_id,
        code=code,
        phone_number_id=phone_number_id
    )
    # Update after joining because session won't exist before it.
    user_account_session.update_session()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    if ProtocolKey.USER_ACCOUNT_SESSION in service_response[0]:
        if app.debug:
            secure_cookie = False
        else:
            secure_cookie = True

        session = service_response[0][ProtocolKey.USER_ACCOUNT_SESSION]
        session_id = session[ProtocolKey.ID]
        http_response.set_cookie(ProtocolKey.USER_ACCOUNT_SESSION_ID.value, session_id, secure=secure_cookie)

    return http_response


def log_in() -> Response:
    client_id = request.form.get(ProtocolKey.CLIENT_ID)
    code = request.form.get(ProtocolKey.CODE)
    phone_number_id = request.form.get(ProtocolKey.PHONE_NUMBER_ID)
    user_account_id = request.form.get(ProtocolKey.USER_ACCOUNT_ID)

    service_response = user.log_in(
        client_id=client_id,
        code=code,
        phone_number_id=phone_number_id,
        user_account_id=user_account_id
    )

    if service_response[1] == ResponseStatus.OK:
        # Update after logging in because session won't exist before it.
        user_account_session.update_session()

    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    if ProtocolKey.USER_ACCOUNT_SESSION in service_response[0]:
        if app.debug:
            secure_cookie = False
        else:
            secure_cookie = True

        session = service_response[0][ProtocolKey.USER_ACCOUNT_SESSION]
        session_id = session[ProtocolKey.ID]
        http_response.set_cookie(ProtocolKey.USER_ACCOUNT_SESSION_ID.value, session_id, secure=secure_cookie)

    return http_response


@ _auth_required
def log_out() -> Response:
    user_account_session.update_session()
    service_response = user.log_out()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    http_response.set_cookie(ProtocolKey.USER_ACCOUNT_SESSION_ID.value, "", expires=0)

    return http_response


@ _auth_required
def me() -> Response:
    user_account_session.update_session()
    service_response = user_account.get_current_account()
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def remove_brand() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)

    service_response = brand.remove_brand(brand_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def remove_product() -> Response:
    user_account_session.update_session()

    product_id = request.form.get(ProtocolKey.PRODUCT_ID)

    service_response = product.remove_product(product_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def remove_store() -> Response:
    user_account_session.update_session()

    store_id = request.form.get(ProtocolKey.STORE_ID)

    service_response = store.remove_store(store_id)
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def report_brand() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    comment = request.form.get(ProtocolKey.COMMENT)
    report_type = request.form.get(ProtocolKey.TYPE)

    service_response = brand_report.report_brand(
        brand_id=brand_id,
        comment=comment,
        report_type=report_type
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def report_product() -> Response:
    user_account_session.update_session()

    comment = request.form.get(ProtocolKey.COMMENT)
    product_id = request.form.get(ProtocolKey.PRODUCT_ID)
    report_type = request.form.get(ProtocolKey.TYPE)

    service_response = product_report.report_product(
        comment=comment,
        product_id=product_id,
        report_type=report_type
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def report_store() -> Response:
    user_account_session.update_session()

    comment = request.form.get(ProtocolKey.COMMENT)
    report_type = request.form.get(ProtocolKey.TYPE)
    store_id = request.form.get(ProtocolKey.PRODUCT_ID)

    service_response = store_report.report_store(
        comment=comment,
        report_type=report_type,
        store_id=store_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def report_user_account() -> Response:
    user_account_session.update_session()

    account_id = request.form.get(ProtocolKey.USER_ACCOUNT_ID)
    comment = request.form.get(ProtocolKey.COMMENT)
    report_type = request.form.get(ProtocolKey.TYPE)

    service_response = user_account_report.report_account(
        account_id=account_id,
        comment=comment,
        report_type=report_type
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


def send_verification_code() -> Response:
    alpha_2_code = request.form.get(ProtocolKey.ALPHA_2_CODE)
    dialing_code = request.form.get(ProtocolKey.DIALING_CODE)
    phone_number = request.form.get(ProtocolKey.PHONE_NUMBER)

    service_response = user_phone_number_verification_code.send_verification_code(
        alpha_2_code=alpha_2_code,
        dialing_code=dialing_code,
        phone_number=phone_number
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def update_brand() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    description = request.form.get(ProtocolKey.DESCRIPTION)
    name = request.form.get(ProtocolKey.NAME)
    tags = request.form.get(ProtocolKey.TAGS)
    website = request.form.get(ProtocolKey.WEBSITE)

    service_response = brand.update_brand(
        brand_id=brand_id,
        description=description,
        name=name,
        tags=tags,
        website=website
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def update_brand_avatar() -> Response:
    user_account_session.update_session()

    brand_id = request.form.get(ProtocolKey.BRAND_ID)
    media_mode = request.form.get(ProtocolKey.MEDIA_MODE)

    service_response = brand.update_avatar(
        brand_id=brand_id,
        media_mode=media_mode
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def update_product() -> Response:
    user_account_session.update_session()

    description = request.form.get(ProtocolKey.DESCRIPTION)
    display_name_override = request.form.get(ProtocolKey.OVERRIDES_DISPLAY_NAME)
    material_id = request.form.get(ProtocolKey.MATERIAL_ID)
    main_color_code = request.form.get(ProtocolKey.MAIN_COLOR_CODE)
    name = request.form.get(ProtocolKey.NAME)
    parent_product_id = request.form.get(ProtocolKey.PARENT_PRODUCT_ID)
    preorder_timestamp = request.form.get(ProtocolKey.PREORDER_TIMESTAMP)
    product_id = request.form.get(ProtocolKey.PRODUCT_ID)
    release_timestamp = request.form.get(ProtocolKey.RELEASE_TIMESTAMP)
    status = request.form.get(ProtocolKey.STATUS)
    tags = request.form.get(ProtocolKey.TAGS)
    upc = request.form.get(ProtocolKey.UPC)
    url = request.form.get(ProtocolKey.URL)

    service_response = product.update_product(
        description=description,
        display_name_override=display_name_override,
        main_color_code=main_color_code,
        material_id=material_id,
        name=name,
        parent_product_id=parent_product_id,
        preorder_timestamp=preorder_timestamp,
        product_id=product_id,
        release_timestamp=release_timestamp,
        status=status,
        tags=tags,
        upc=upc,
        url=url
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def update_product_media() -> Response:
    user_account_session.update_session()

    media_mode = request.form.get(ProtocolKey.MEDIA_MODE)
    metadata = request.form.get(ProtocolKey.MEDIA)
    product_id = request.form.get(ProtocolKey.PRODUCT_ID)

    service_response = product.update_media(
        media_mode=media_mode,
        metadata=metadata,
        product_id=product_id
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _auth_required
def update_store() -> Response:
    user_account_session.update_session()

    building = request.form.get(ProtocolKey.BUILDING)
    description = request.form.get(ProtocolKey.DESCRIPTION)
    floor = request.form.get(ProtocolKey.FLOOR)
    latitude = request.form.get(ProtocolKey.LATITUDE)
    locality_alpha_2_code = request.form.get(ProtocolKey.ALPHA_2_CODE)
    locality_name = request.form.get(ProtocolKey.LOCALITY)
    longitude = request.form.get(ProtocolKey.LONGITUDE)
    name = request.form.get(ProtocolKey.NAME)
    post_code = request.form.get(ProtocolKey.POST_CODE)
    status = request.form.get(ProtocolKey.STATUS)
    store_id = request.form.get(ProtocolKey.STORE_ID)
    street = request.form.get(ProtocolKey.STREET)
    tags = request.form.get(ProtocolKey.TAGS)
    unit = request.form.get(ProtocolKey.UNIT)
    website = request.form.get(ProtocolKey.WEBSITE)

    service_response = store.update_store(
        building=building,
        description=description,
        floor=floor,
        latitude=latitude,
        locality_alpha_2_code=locality_alpha_2_code,
        locality_name=locality_name,
        longitude=longitude,
        name=name,
        post_code=post_code,
        status=status,
        store_id=store_id,
        street=street,
        tags=tags,
        unit=unit,
        website=website
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _stub
@ _auth_required
def update_store_avatar() -> Response:
    pass


@ _auth_required
def update_store_product() -> Response:
    user_account_session.update_session()

    condition = request.form.get(ProtocolKey.CONDITION)
    description = request.form.get(ProtocolKey.DESCRIPTION)
    price = request.form.get(ProtocolKey.PRICE)
    status = request.form.get(ProtocolKey.STATUS)
    store_product_id = request.form.get(ProtocolKey.STORE_PRODUCT_ID)
    url = request.form.get(ProtocolKey.URL)

    service_response = store_product.update_store_product(
        condition=condition,
        description=description,
        price=price,
        status=status,
        store_product_id=store_product_id,
        url=url
    )
    http_response = make_response(service_response[0], _map_response_status(service_response[1]))

    return http_response


@ _stub
@ _auth_required
def update_user_account() -> Response:
    pass


@ _stub
@ _auth_required
def update_user_avatar() -> Response:
    pass
