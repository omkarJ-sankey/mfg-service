"""
SQS Consumer Service for Valeting Data

This module provides functionality to consume messages from Amazon SQS
and store them in the database using the ThirdPartyServicesData model.
"""

import json
import boto3
import pytz
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from sharedServices.model_files.contactless_models import ThirdPartyServicesData, ValetingTransactionData
from sharedServices.common import redis_connection
from .app_level_constants import (
    COMPLETE,
    FAILED,
    SUCCESSFULLY_FETCHED_DATA,
    VALETING
)
from decimal import Decimal

class SQSValetingConsumer:
    """
    Consumer for valeting data from Amazon SQS
    """
    
    def __init__(self, 
                 queue_url=None, 
                 region_name=None, 
                 aws_access_key_id=None, 
                 aws_secret_access_key=None):
        """
        Initialize the SQS consumer
        
        Args:
            queue_url: The URL of the SQS queue
            region_name: The AWS region name
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
        """
        self.queue_url = queue_url or settings.SQS_QUEUE_URL
        self.region_name = region_name or settings.AWS_REGION
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        
        # Initialize SQS client
        self.sqs_client = boto3.client(
            'sqs',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        print(f"Initialized SQS client for queue: {self.queue_url}")
    
    def start_consuming(self, batch_size=10, wait_time=20):
        """
        Start consuming messages from SQS
        
        Args:
            batch_size: Number of messages to process in one batch
            wait_time: Wait time for long polling in seconds
        """
        print(f"Starting SQS consumer with batch size {batch_size}")
        
        while True:
            try:
                # Receive messages from SQS
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=batch_size,
                    WaitTimeSeconds=wait_time,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                
                if not messages:
                    continue
                
                self._process_messages_bulk(messages)
                
            except Exception as e:
                print(f"Error consuming messages: {str(e)}")
    
    def _process_messages_bulk(self, messages):
        """
        Process a batch of messages in bulk
        
        Args:
            messages: List of messages to process
        """
        message_bodies = []
        receipt_handles = []
        
        for message in messages:
            try:
                # Extract the message body and receipt handle
                # print(f"Message: {message}")
                if 'Body' in message:
                    message_body = json.loads(message['Body'])
                    message_data = {
                        "message_id": message['MessageId'],
                        "receipt_handle": message['ReceiptHandle'],
                        "body": message_body,
                        "timestamp": datetime.now().isoformat()
                    }
                    message_bodies.append(message_data)
                else:
                    print(f"Warning: Message missing Body field: {message}")
                    continue
                
                if 'ReceiptHandle' in message:
                    receipt_handles.append(message['ReceiptHandle'])
                else:
                    print(f"Warning: Message missing ReceiptHandle: {message}")
                    continue
                    
            except json.JSONDecodeError as e:
                print(f"Error decoding message body: {str(e)}")
                continue
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                continue
        
        if not message_bodies:
            print("No valid message bodies found to process")
            return
        
        # print(f"Processing {len(message_bodies)} messages with {len(receipt_handles)} receipt handles")
        
        # Group messages by date
        messages_by_date = {}
        for message_body in message_bodies:
            try:
                data = message_body.get('body', {}).get('Data', {})
                auth_time = data.get('Authorization Time')
                
                if not auth_time:
                    continue
                
                date_obj = datetime.fromisoformat(auth_time.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%Y-%m-%d")
                
                if date_str not in messages_by_date:
                    messages_by_date[date_str] = []
                
                messages_by_date[date_str].append(message_body)
            except (ValueError, TypeError) as e:
                print(f"Error parsing Authorization Time in message: {str(e)}")
        
        success_count = 0
        for date_str, date_messages in messages_by_date.items():
            try:
                # upserted_cache_count = self._bulk_upsert_valeting_data_in_cache(date_str, date_messages)
                added, updated = self._bulk_upsert_valeting_data_in_db(date_str, date_messages)
                success_count += added + updated
                # print(f"Processed {len(date_messages)} messages for date {date_str}: {added} added, {updated} updated")
            except Exception as e:
                print(f"Error processing messages for date {date_str}: {str(e)}")
        
        if success_count > 0 and receipt_handles:
            # print(f"Deleting {min(success_count, len(receipt_handles))} successfully processed messages")
            self._delete_messages(receipt_handles[:min(success_count, len(receipt_handles))])
        elif success_count > 0:
            print(f"Warning: {success_count} messages processed but no receipt handles available for deletion")
    
    def _bulk_upsert_valeting_data_in_db(self, date_str, valeting_data_list):
        """
        Upsert valeting data in bulk, storing each transaction in a separate row
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            valeting_data_list: List of valeting data to upsert
            
        Returns:
            tuple: (number of records added, number of records updated)
        """
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=pytz.UTC)
        current_time = timezone.localtime(timezone.now())
        
        transactions_to_create = []
        transactions_to_update = []
        
        for message_body in valeting_data_list:
            try:
                body = message_body.get('body', {})
                data = body.get('Data', {})
                
                transaction_id = str(body.get('TransactionId', '')).strip()
                if not transaction_id:
                    print(f"Warning: Skipping record with missing transaction ID: {body}")
                    continue
                    
                site_id = str(body.get('SiteId', '')).strip()
                if not site_id:
                    print(f"Warning: Skipping record with missing site ID: {body}")
                    continue
                
                total_amount = float(data.get("Payed Value", 0))
                
                # print(f"Transaction {transaction_id} - Total Amount: £{total_amount:.2f}")
                
                auth_time = data.get('Authorization Time')
                if auth_time:
                    try:
                        transaction_time = datetime.strptime(auth_time, "%Y-%m-%d")
                    except ValueError:
                        try:
                            transaction_time = datetime.strptime(auth_time, "%Y-%m-%d")
                        except ValueError:
                            # print(f"Warning: Invalid authorization time format: {auth_time}")
                            transaction_time = date_obj
                    transaction_time = transaction_time.replace(tzinfo=pytz.UTC)
                else:
                    transaction_time = date_obj
                
                existing_transaction = ValetingTransactionData.objects.filter(
                    transaction_id=transaction_id
                ).first()
                
                transaction_data = {
                    'transaction_id': transaction_id,
                    'card_number': data.get('Card String', ''),
                    'transaction_date': transaction_time,
                    'amount': total_amount,
                    'valeting_site_id': site_id,
                    'data': json.dumps({
                        'message_id': message_body.get('message_id'),
                        'timestamp': message_body.get('timestamp'),
                        'receipt_handle': message_body.get('receipt_handle'),
                        'body': body,
                    }),
                    'updated_date': current_time,
                    'updated_by': "SQS_Consumer"
                }
                
                if existing_transaction:
                    for key, value in transaction_data.items():
                        setattr(existing_transaction, key, value)
                    transactions_to_update.append(existing_transaction)
                else:
                    new_transaction = ValetingTransactionData(
                        created_date=current_time,
                        **transaction_data
                    )
                    transactions_to_create.append(new_transaction)
                    
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                continue
        
        if transactions_to_create:
            try:
                ValetingTransactionData.objects.bulk_create(
                    transactions_to_create,
                    batch_size=1000
                )
            except Exception as e:
                print(f"Error creating transactions: {str(e)}")
                for transaction in transactions_to_create:
                    try:
                        transaction.save()
                    except Exception as e:
                        print(f"Error creating transaction {transaction.transaction_id}: {str(e)}")
        
        if transactions_to_update:
            try:
                fields_to_update = [
                    'card_number', 'transaction_date', 'amount', 
                    'valeting_site_id', 'data', 'updated_date', 'updated_by'
                ]
                ValetingTransactionData.objects.bulk_update(
                    transactions_to_update,
                    fields_to_update,
                )
            except Exception as e:
                print(f"Error updating transactions: {str(e)}")
                for transaction in transactions_to_update:
                    try:
                        transaction.save()
                    except Exception as e:
                        print(f"Error updating transaction {transaction.transaction_id}: {str(e)}")
        
        return len(transactions_to_create), len(transactions_to_update)
    
    # def _bulk_upsert_valeting_data_in_cache(self, date_str, valeting_data_list):
    #     """Upsert valeting data in cache
        
    #     Args:
    #         date_str: Date string in YYYY-MM-DD format
    #         valeting_data_list: List of valeting data to upsert
            
    #     Returns:
    #         int: Number of records added/updated in cache
    #     """
    #     cache_key = f"{VALETING}-{transaction_id}"
    #     existing_cache = redis_connection.get(cache_key)
    #     current_time = timezone.localtime(timezone.now())
        
    #     if existing_cache:
    #         existing_data = json.loads(existing_cache)
    #     else:
    #         existing_data = []
        
    #     new_data = []
    #     for message_body in valeting_data_list:
    #         try:
    #             body = message_body.get('body', {})
    #             data = body.get('Data', {})
                
    #             transaction_id = str(body.get('TransactionId', '')).strip()
    #             if not transaction_id:
    #                 continue
                    
    #             site_id = str(body.get('SiteId', '')).strip()
    #             if not site_id:
    #                 continue
                
    #             total_amount = 0.0
    #             total_vat = 0.0
    #             total_excl_vat = 0.0
    #             products = data.get('Products', [])
    #             for product in products:
    #                 try:
    #                     net_price = float(str(product.get('Product Net Price', 0)))
    #                     vat_amount = float(str(product.get('Product Vat Amount', 0)))
    #                     product_amount = net_price - vat_amount
                        
    #                     total_amount += net_price
    #                     total_vat += vat_amount
    #                     total_excl_vat += product_amount
    #                 except (ValueError, TypeError):
    #                     continue
                
    #             # if total_amount <= 0:
    #             #     continue
                
    #             auth_time = data.get('Authorization Time')
    #             if auth_time:
    #                 try:
    #                     transaction_time = datetime.strptime(auth_time, "%Y-%m-%dT%H:%M:%S.%f")
    #                 except ValueError:
    #                     try:
    #                         transaction_time = datetime.strptime(auth_time, "%Y-%m-%dT%H:%M:%S")
    #                     except ValueError:
    #                         continue
    #                 transaction_time = transaction_time.replace(tzinfo=pytz.UTC)
    #             else:
    #                 continue
                
    #             cache_transaction = {
    #                 'transaction_id': transaction_id,
    #                 'card_number': data.get('Card String', ''),
    #                 'transaction_date': transaction_time.isoformat(),
    #                 'amount': total_amount,
    #                 'valeting_site_id': site_id,
    #                 'data': json.dumps({
    #                     'message_id': message_body.get('message_id'),
    #                     'timestamp': message_body.get('timestamp'),
    #                     'receipt_handle': message_body.get('receipt_handle'),
    #                     'body': body,
    #                 }),
    #                 'updated_date': current_time.isoformat(),
    #                 'updated_by': "SQS_Consumer"
    #             }
                
    #             if not any(t.get('transaction_id') == transaction_id for t in existing_data):
    #                 new_data.append(cache_transaction)
                    
    #         except Exception as e:
    #             print(f"Error processing message for cache: {str(e)}")
    #             continue
        
    #     if new_data:
    #         existing_data.extend(new_data)
    #         redis_connection.set(cache_key, json.dumps(existing_data))
        
    #     return len(new_data)
    
    def _delete_messages(self, receipt_handles):
        """
        Delete processed messages from the queue
        
        Args:
            receipt_handles: List of receipt handles to delete
        """
        if not receipt_handles:
            print("No receipt handles provided for deletion")
            return
            
        # print(f"Attempting to delete {len(receipt_handles)} messages from SQS queue")
        
        for receipt_handle in receipt_handles:
            try:
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
                # print(f"Successfully deleted message with receipt handle: {receipt_handle[:10]}...")
            except Exception as e:
                print(f"Error deleting message with receipt handle {receipt_handle[:10]}...: {str(e)}")


class Command(BaseCommand):
    """
    Django management command to run the SQS consumer
    """
    help = 'Consume valeting service messages from SQS'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of messages to process in one batch'
        )
        parser.add_argument(
            '--wait-time',
            type=int,
            default=20,
            help='Wait time for long polling in seconds'
        )
        parser.add_argument(
            '--queue-url',
            type=str,
            help='SQS queue URL'
        )
        parser.add_argument(
            '--region',
            type=str,
            help='AWS region name'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        wait_time = options['wait_time']
        queue_url = options.get('queue_url')
        region = options.get('region')
        
        consumer = SQSValetingConsumer(
            queue_url=queue_url,
            region_name=region
        )
        
        self.stdout.write(self.style.SUCCESS(f'Starting SQS consumer with batch size {batch_size}'))
        
        try:
            consumer.start_consuming(batch_size=batch_size, wait_time=wait_time)
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('SQS consumer stopped'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 