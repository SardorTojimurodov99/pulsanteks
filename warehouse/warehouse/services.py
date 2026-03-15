from django.db import transaction
from production.models import BatchStatus


@transaction.atomic
def receive_batch_to_warehouse(batch, user=None, note=""):
    """
    Batch omborga qabul qilindi
    """

    batch.status = BatchStatus.WAREHOUSE
    batch.save(update_fields=["status"])

    return batch