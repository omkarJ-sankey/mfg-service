"""loyalty apis helper functions"""
# Date - 14/02/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file is contains helper functions for loyalty.
#   Name            - Loyalty helper functions
#   Modified by     - Manish Pawar
#   Modified date   - 14/02/2022


# These are all the imports that we are exporting from
# different module's from project or library.
from rest_framework import status

# pylint:disable=import-error
from sharedServices.common import (
    string_to_array_converter,
)

from sharedServices.loyalty_common_functions import save_user_loyalty_details
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    LoyaltyTransactions,
    LoyaltyBulkUpload,
    LoyaltyProducts,
)
from sharedServices.model_files.station_models import (
    Stations,
)

from sharedServices.model_files.app_user_models import MFGUserEV

from sharedServices.constants import (
    ACTIVE_LOYALTY_PRODUCTS,
    QR_CODE_ELEMENTS_ARRAY_SIZE,
    REDEEMED_ACTION_CODE,
    SALE_QUANTITY,
    SALE_AMOUNT,
    COSTA_COFFEE,
    FREE_LOYALTY
)


def submit_transaction(transaction_data):
    """this function submits a single transaction"""
    qr_code = transaction_data["qr_code"]
    transaction_details = transaction_data["transaction_details"]
    print(f"[DEBUG] qr_code: {qr_code} ")
    print(f"[DEBUG] transaction_details: {transaction_details} ")

    qr_code_used = LoyaltyTransactions.objects.filter(qr_code=qr_code)
    if qr_code_used.first() is not None:
        print("Transaction failed:- QR code is used earlier", qr_code)
        return {
            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
            "status": False,
            "message": "QR code is used earlier.",
        }
    qr_elements = qr_code.split("_")
    if len(qr_elements) != QR_CODE_ELEMENTS_ARRAY_SIZE:
        print("Transaction failed:- Invalid QR code", qr_code)
        return {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "status": False,
            "message": "Invalid QR code.",
        }
    (
        _,
        customer_id,
        _,
        _,
        scheme_bar_code,
        _,
        _,
        _,
        _,
        _,
        _,
        timestamp,
        qr_action_code,
        site_id,
    ) = qr_elements

    user = MFGUserEV.objects.filter(id=customer_id).first()
    loyalty = Loyalty.objects.filter(unique_code=scheme_bar_code).first()
    station = Stations.objects.filter(station_id=site_id).first()
    print(f"[DEBUG] user :{user}")
    print(f"[DEBUG] loyalty :{loyalty}")
    print(f"[DEBUG] station :{station}")
    redeemed_product_sales_amount = 0
    number_of_paid_purchases = None
    if user and loyalty and station:
        number_of_paid_purchases = loyalty.number_of_paid_purchases
        print(f"[DEBUG] number_of_paid_purchases :{number_of_paid_purchases}")
        invalid_transactions = []
        loyalty_products_plus = [
            product.product_plu
            for product in LoyaltyProducts.objects.filter(
                loyalty_id=loyalty,
                status=ACTIVE_LOYALTY_PRODUCTS,
            )
        ]
        print(f"[DEBUG] loyalty_products_plus: {loyalty_products_plus}")
        loyalty_transactions = [
            transaction
            for transaction in transaction_details
            if (
                "plu" in transaction
                and transaction["plu"] in loyalty_products_plus
            )
        ]
        print(f"[DEBUG] loyalty_transactions: {loyalty_transactions}")
        if qr_action_code == REDEEMED_ACTION_CODE:
            print(f"[DEBUG] qr_action_code: {qr_action_code}")
            redeem_product_is_in_basket = False
            for transaction in loyalty_transactions:
                print(f"[DEBUG] transaction: {transaction}")
                loyalty_product = LoyaltyProducts.objects.filter(
                    loyalty_id=loyalty,
                    status=ACTIVE_LOYALTY_PRODUCTS,
                    product_plu=transaction["plu"],
                )
                print(f"[DEBUG] loyalty_product: {loyalty_product}")
                print(f"[DEBUG] redeem_product_promotion_price: {loyalty_product.first().redeem_product_promotion_price}")
                if (
                    loyalty_product.first()
                    and SALE_AMOUNT in transaction
                    and float(transaction[SALE_AMOUNT])
                    == float(
                        loyalty_product.first().redeem_product_promotion_price
                    )
                ):
                    
                    redeem_product_is_in_basket = True
                    redeemed_product_sales_amount = float(
                        transaction[SALE_AMOUNT]
                    )
                    print(f"[DEBUG] redeem_product_is_in_basket: {redeem_product_is_in_basket}")
                if redeem_product_is_in_basket:
                    break
            if redeem_product_is_in_basket is False:
                print(
                    "Redemption product is not available in basket.", qr_code
                )
                return {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": (
                        "Redemption product is not " + "available in basket."
                    ),
                }

        if len(loyalty_transactions) == 0:
            print("No loyalty products in cart.", qr_code)
            return {
                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                "status": False,
                "message": "No loyalty products in cart.",
            }
        purchased_quantity_or_amount = 0
        number_of_loyalty_transaction = 0
        if loyalty.redeem_type == "Amount":
            for loyalty_transaction in loyalty_transactions:
                if (
                    SALE_AMOUNT in loyalty_transaction
                    and float(loyalty_transaction[SALE_AMOUNT]) > 0
                    and SALE_QUANTITY in loyalty_transaction
                    and int(float(loyalty_transaction[SALE_QUANTITY])) > 0
                ):
                    purchased_quantity_or_amount += float(
                        loyalty_transaction[SALE_AMOUNT]
                    )

                    number_of_loyalty_transaction += int(
                        float(loyalty_transaction[SALE_QUANTITY])
                    )

                invalid_transactions = [
                    {
                        "plu": invalid_loyalty_transaction["plu"],
                        "reason": "Sale amount not provided",
                    }
                    for invalid_loyalty_transaction in loyalty_transactions
                    if SALE_AMOUNT not in invalid_loyalty_transaction
                ]

        if loyalty.redeem_type == "Count" and loyalty.transaction_count_for_costa_kwh_consumption is None:
            purchased_quantity_or_amount = sum(
                [
                    loyalty_transaction[SALE_QUANTITY]
                    for loyalty_transaction in loyalty_transactions
                    if SALE_QUANTITY in loyalty_transaction
                    and int(float(loyalty_transaction[SALE_QUANTITY])) > 0
                ]
            )
            print(f"[DEBUG] purchased_quantity_or_amount: {purchased_quantity_or_amount}")
            number_of_loyalty_transaction = purchased_quantity_or_amount
            invalid_transactions = [
                {
                    "plu": invalid_loyalty_transaction["plu"],
                    "reason": "Sale quantity not provided",
                }
                for invalid_loyalty_transaction in loyalty_transactions
                if SALE_QUANTITY not in invalid_loyalty_transaction
            ]
            print(f"[DEBUG] invalid_transactions: {invalid_transactions}")

        if loyalty.redeem_type == "Count" and loyalty.loyalty_type == COSTA_COFFEE and (loyalty.transaction_count_for_costa_kwh_consumption or 0) > 0:
            print(f"[DEBUG] In Costa Consumption Flow")
            purchased_quantity_or_amount = loyalty.number_of_paid_purchases
            print(f"[DEBUG] purchased_quantity_or_amount Costa: {purchased_quantity_or_amount}")
            number_of_loyalty_transaction = purchased_quantity_or_amount
            invalid_transactions = [
                {
                    "plu": invalid_loyalty_transaction["plu"],
                    "reason": "Sale quantity not provided",
                }
                for invalid_loyalty_transaction in loyalty_transactions
                if SALE_QUANTITY not in invalid_loyalty_transaction
            ]
            print(f"[DEBUG] invalid_transactions Costa: {invalid_transactions}")

        if (
            purchased_quantity_or_amount is None
            or purchased_quantity_or_amount <= 0
        ) and loyalty.loyalty_type not in [COSTA_COFFEE,FREE_LOYALTY]:
            print(
                "Not able to get amount or quantity of transactions.", qr_code
            )
            return {
                "status_code": status.HTTP_403_FORBIDDEN,
                "status": False,
                "message": "Not able to get amount or \
                        quantity of transactions",
                "invalid_transactions": invalid_transactions,
            }

        # checking whether user have previous transactions for the loyalty
        print(f"[DEBUG] loyalty: {loyalty}")
        print(f"[DEBUG] user: {user}")
        print(f"[DEBUG] number_of_paid_purchases: {number_of_paid_purchases}")
        print(f"[DEBUG] timestamp: {timestamp}")
        print(f"[DEBUG] purchased_quantity_or_amount: {purchased_quantity_or_amount}")
        print(f"[DEBUG] redeemed_product_sales_amount: {redeemed_product_sales_amount}")
        print(f"[DEBUG] invalid_transactions: {invalid_transactions}")
        print(f"[DEBUG] number_of_loyalty_transaction: {number_of_loyalty_transaction}")
        print(f"[DEBUG] qr_code: {qr_code}")
        print(f"[DEBUG] transaction_details: {transaction_details}")
        print(f"[DEBUG] station: {station}")
        print(f"[DEBUG] qr_action_code: {qr_action_code}")

        return save_user_loyalty_details(
            loyalty,
            user,
            number_of_paid_purchases,
            timestamp,
            purchased_quantity_or_amount,
            redeemed_product_sales_amount,
            invalid_transactions,
            number_of_loyalty_transaction,
            qr_code,
            transaction_details,
            station,
            qr_action_code,
        )

    print("Transaction failed:- Invalid QR code", qr_code)
    return {
        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
        "status": False,
        "message": "Transaction submission not completed!",
    }


def submit_transactions_in_bulk(*args):
    """this function submits loyalty transaction in bulk"""
    bulk_row_id = args[0]
    loyalty_transactions = LoyaltyBulkUpload.objects.filter(id=bulk_row_id)
    if loyalty_transactions.first():
        transactions_list = string_to_array_converter(
            loyalty_transactions.first().transaction_bulk_data
        )
        for transaction in transactions_list:
            submit_transaction(transaction)
