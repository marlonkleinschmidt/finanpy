from django.conf import settings
from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Profile = apps.get_model('profiles', 'Profile')
    db_alias = schema_editor.connection.alias
    user_ids = (
        User.objects.using(db_alias)
        .filter(profile__isnull=True)
        .values_list('pk', flat=True)
    )
    Profile.objects.using(db_alias).bulk_create(
        [Profile(user_id=user_id) for user_id in user_ids]
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_missing_profiles,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
