import threading
from services.assignment_service.events import start_assignment_consumer
from services.location_service.events import start_location_consumer
from services.payment_service.events import start_payment_consumer
from services.notification_service.events import start_notification_consumer

if __name__ == "__main__":

    threads = [
        threading.Thread(target=start_assignment_consumer),
        threading.Thread(target=start_location_consumer),
        threading.Thread(target=start_payment_consumer),
        threading.Thread(target=start_notification_consumer)
    ]

    for thread in threads:
        thread.start()

    print("All workers running...")

    for thread in threads:
        thread.join()