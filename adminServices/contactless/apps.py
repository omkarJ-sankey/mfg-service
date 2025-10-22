from django.apps import AppConfig
import threading

class ContactlessConfig(AppConfig):
    name = 'adminServices.contactless'
    
    def ready(self):
        # This method is called when Django starts
        print("=" * 50)
        print("ContactlessConfig.ready() called")
        print("=" * 50)
        
        # Start the SQS consumer in a separate thread
        try:
            from sharedServices.common import filter_function_for_base_configuration
            enable_sqs = filter_function_for_base_configuration("ENABLE_SQS_CONSUMER", "False")
            if str(enable_sqs).lower() == "true":
                from . import services
                print("Starting SQS consumer from AppConfig.ready()")
                consumer_thread = threading.Thread(target=services.start_valeting_consumer)
                consumer_thread.daemon = True  # This ensures the thread will exit when the main process exits
                consumer_thread.start()
                print("SQS consumer started successfully in background thread")
            else:
                print("SQS consumer is disabled for this environment.")
        except Exception as e:
            import traceback
            print(f"Error starting SQS consumer: {str(e)}")
            print(traceback.format_exc())
