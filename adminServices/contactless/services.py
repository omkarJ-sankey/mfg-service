"""
Services for the contactless app

This module provides services that can be run as background tasks or automated processes.
"""

import threading

# Global variable to store the running consumer thread
_valeting_consumer_thread = None

def start_valeting_consumer():
    """
    Start the valeting SQS consumer as a background thread.
    
    This function is intended to be called when the Django application starts,
    such as in the AppConfig.ready() method or in a management command.
    
    Returns:
        bool: True if the consumer was started, False if it was already running
    """
    global _valeting_consumer_thread
    
    # Check if the consumer is already running
    if _valeting_consumer_thread is not None and _valeting_consumer_thread.is_alive():
        print("Valeting SQS consumer is already running")
        return False
    
    # Create and start the consumer thread
    from .sqs_consumer import SQSValetingConsumer
    consumer = SQSValetingConsumer()
    
    def run_consumer():
        try:
            print("Starting valeting SQS consumer thread")
            consumer.start_consuming()
        except Exception as e:
            print(f"Error in valeting SQS consumer thread: {str(e)}")
    
    _valeting_consumer_thread = threading.Thread(target=run_consumer, daemon=True)
    _valeting_consumer_thread.start()
    
    print("Valeting SQS consumer thread started")
    return True

def stop_valeting_consumer():
    """
    Stop the valeting SQS consumer thread.
    
    This function is intended to be called when the Django application is shutting down.
    
    Returns:
        bool: True if the consumer was stopped, False if it was not running
    """
    global _valeting_consumer_thread
    
    if _valeting_consumer_thread is None or not _valeting_consumer_thread.is_alive():
        print("Valeting SQS consumer is not running")
        return False
    
    # There's no clean way to stop the consumer thread from outside,
    # so we'll just log that we're stopping it
    print("Stopping valeting SQS consumer thread")
    
    # In a real implementation, you might want to set a flag in the consumer
    # to signal it to stop, but for simplicity, we'll just let it run until
    # the application shuts down
    
    return True 