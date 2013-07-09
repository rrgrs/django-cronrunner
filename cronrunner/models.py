import os
import traceback
from imp import load_source

from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.conf import settings
from django.core.mail import send_mail

from crontab import CronTab



class ScheduledTask(models.Model):
    """
    A ScheduledTask is a cronjob that runs a script, cron scripts are kept in project cron folders
    """
    name = models.CharField(max_length=255, unique=True)
    schedule = models.CharField(max_length=255)
    last_run = models.DateTimeField(blank=True, null=True, auto_now=True)
    active = models.BooleanField()
    notes = models.TextField(blank=True, null=True)

    file_choices = []
    for app in settings.INSTALLED_APPS:
        cron_dir = __import__(app).__file__.split('/')[:-1]
        cron_dir.append('cron')
        cron_dir = '/'+os.path.join(*cron_dir)
        if not os.path.exists(cron_dir):
            continue
        for file_name in os.listdir( cron_dir ):
            if file_name[len(file_name)-3:] == '.py':
                choice = '%s.%s' % (app, file_name[:len(file_name)-3])
                file_choices.append( (
                    choice,
                    choice,
                ) )
    script = models.CharField(max_length=100, choices=file_choices)

    def get_command(self, name=None):
        """
        Returns the command to be executed in the crontab line
        """
        if not name: name = self.name
        p_name = settings.SITE_NAME
        return "python %s/manage.py runcron %s --settings=%s.%s" % (
            os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', p_name),
                                                        name, p_name, os.environ['DJANGO_SETTINGS_MODULE'])

    def save(self, *args, **kwargs):
        """
        After saving the importer. Write the crontab line to execute the parser
        """
        # detect if first save, if not get the old name so old command can be removed
        first_save = True
        if self.id:
            old_name = ScheduledImport.objects.get(id=self.id).name
            first_save = False
        # Perform regular model save()
        super(ScheduledTask, self).save(*args, **kwargs)
        cron = CronTab()
        if not first_save:
            # if not the models first save remove old cron command before adding new one
            # ie replace in cron list instead of adding
            command = self.get_command(old_name)
            cron.remove_all(command)
        # If the ScheduledImport is active, then add the command to the crontab
        if self.active:
            cron_new = cron.new()
            cron_new.parse('%s %s' % (self.schedule, command))
        # Write the changes
        cron.write()

    def handle_errors(self, errors=(), text=''):
        msg = ''
        if text:
            msg += text
        if errors:
            msg += '\n\nThe following errors occurred:\n'
            for error in errors:
                msg += '\n%s' % error
        admins = [admin[1] for admin in settings.ADMINS]
        subject = 'There was an error while executing the %s %s scheduled task' % (settings.SITE_NAME, self.name)
        send_mail(subject, msg, settings.EMAIL_FROM, admins)

    def handle_success(self, extra_text=''):
        admins = [admin[1] for admin in settings.ADMINS]
        subject = 'The %s %s scheduled task completed successfully' % (settings.SITE_NAME, self.name)
        send_mail(subject, extra_text, settings.EMAIL_FROM, admins)

    def delete(self, *args, **kwargs):
        """
        Removes the command from the crontab and deletes the Parser instance
        """
        cron = CronTab()
        cron.remove_all( self.get_command() )
        cron.write()
        super(self.__class__, self).delete(*args, **kwargs)

    def __unicode__(self):
        if self.active:
            status = 'Active'
        else:
            status = 'Disabled'
        return '%s %s (%s)' % (self.name, self.schedule, status)


class ScheduledImport(ScheduledTask):
    url = models.CharField(max_length=255)

    items = models.TextField(default='', blank=True, null=True)

    def run_import(self):
        appfile = self.script.split('.')
        app = appfile[0]
        file = '.'.join(appfile[1:])
        filepath = __import__(app).__file__.split('/')[:-1]
        filepath.append('cron')
        filepath = '/%s/%s.py' % (os.path.join(*filepath), file)
        m = load_source('m', filepath)
        try:
            #import jobs returns list of unsaved jobs
            items = m.import_items(self)
        except Exception, e:
            #email traceback
            self.handle_errors(text=traceback.format_exc())
            return
        #check to see if returned jobs are valid, delete old jobs and save if so
        num_valid = 0
        errors = []
        for item in items:
            try:
                item.full_clean()
                num_valid += 1
            except ValidationError, e:
                errors.append(e.message_dict[NON_FIELD_ERRORS])
        # if # valid jobs equals total jobs returned, delete old jobs, save new ones
        if num_valid == len(items) and len(items) > 0:
            if self.items:
                items[0].__class__.objects.filter(id__in=eval(self.items+',')).delete()
            new_ids = []
            for item in items:
                item.save()
                new_ids.append(item.id)
            self.items = ','.join( (str(id) for id in new_ids) )
            self.save()
            self.handle_success(extra_text='%s items imported successfully.' % ( num_valid ))
            #update last successful run
            self.save()
        # otherwise email errors to admin
        else:
            msg = 'Only %s of %s items validated.' % ( num_valid, len(items) )
            self.handle_errors(errors, msg)
