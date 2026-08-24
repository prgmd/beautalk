from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_userinfo_nickname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skinprofile',
            name='skin_type',
            field=models.CharField(
                choices=[
                    ('dry', '건성'),
                    ('oily', '지성'),
                    ('combination', '복합성'),
                    ('sensitive', '민감성'),
                    ('unknown', '미정'),
                ],
                max_length=15,
            ),
        ),
    ]
