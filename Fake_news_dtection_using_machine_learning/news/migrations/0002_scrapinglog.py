from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapingLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')], default='running', max_length=10)),
                ('triggered_by', models.CharField(choices=[('celery_beat', 'Scheduled (Celery Beat)'), ('manual', 'Manual')], default='celery_beat', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('articles_saved', models.IntegerField(default=0)),
                ('articles_skipped', models.IntegerField(default=0)),
                ('articles_errors', models.IntegerField(default=0)),
                ('error_msg', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Scraping Log',
                'verbose_name_plural': 'Scraping Logs',
                'ordering': ['-started_at'],
            },
        ),
    ]
