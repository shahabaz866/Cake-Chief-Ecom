class PaymentStatus:
    PENDING = 'Pending'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    REFUNDED = 'Refunded'
    CANCELLED = 'Cancelled'

    CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
        (CANCELLED, 'Cancelled'),
    ]
