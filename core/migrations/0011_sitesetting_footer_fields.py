from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_order_payment_method_order_razorpay_order_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='footer_address',
            field=models.TextField(default='Studio Address\nAdd your workshop or store address from Admin Settings.'),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='footer_facebook_url',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='footer_hours',
            field=models.CharField(default='Mon - Sat | 10:00 AM - 7:00 PM', max_length=120),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='footer_instagram_url',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='footer_tagline',
            field=models.TextField(default='Thoughtfully handcrafted pieces for calm, soulful spaces.'),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='footer_whatsapp_url',
            field=models.URLField(blank=True, default=''),
        ),
    ]
