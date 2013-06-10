from django.core.management.base import BaseCommand, CommandError
from cronrunner.models import ScheduledImport

class Command(BaseCommand):
    args = '<scheduledtask_name>'
    help = 'runs a scheduled task from its name'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('please provide the name of the scheduled import to run this command')
        try:
            si = ScheduledImport.objects.get(name=args[0])
        except ScheduledImport.DoesNotExist:
            raise CommandError('scheduled import does not exist, try another name')
        si.run_import()
